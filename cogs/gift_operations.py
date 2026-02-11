import discord
from discord.ext import commands
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
import json
from datetime import datetime
import sqlite3
from discord.ext import tasks
import asyncio
import base64
import re
import os
import traceback
import time
import random
import logging
import logging.handlers
from .alliance_member_operations import AllianceSelectView
from .alliance import PaginatedChannelView
from .permission_handler import PermissionManager
from .gift_operationsapi import GiftCodeAPI
from .gift_captchasolver import GiftCaptchaSolver
from collections import deque
from .pimp_my_bot import theme
from i18n import get_guild_language, t

def _get_lang(interaction: discord.Interaction | None) -> str:
    guild_id = interaction.guild.id if interaction and interaction.guild else None
    return get_guild_language(guild_id)

class GiftOperations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Logger Setup for gift_ops.txt
        self.logger = logging.getLogger('gift_ops')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Prevent propagation to root logger
        log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        log_dir = 'log'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, 'gift_ops.txt')
        self.log_directory = log_dir

        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path, maxBytes=3 * 1024 * 1024, backupCount=1, encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(file_handler)

        # Logger Setup for giftlog.txt
        self.giftlog = logging.getLogger("giftlog")
        self.giftlog.setLevel(logging.INFO)
        self.giftlog.propagate = False

        giftlog_file = os.path.join(log_dir, 'giftlog.txt')
        giftlog_handler = logging.handlers.RotatingFileHandler(
            giftlog_file, maxBytes=3 * 1024 * 1024, backupCount=1, encoding='utf-8'
        )
        giftlog_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        if not self.giftlog.hasHandlers():
            self.giftlog.addHandler(giftlog_handler)

        self.logger.info("GiftOperations Cog initializing...")

        if hasattr(bot, 'conn'):
            self.conn = bot.conn
            self.cursor = self.conn.cursor()
        else:
            if not os.path.exists('db'):
                os.makedirs('db')
            self.conn = sqlite3.connect('db/giftcode.sqlite', timeout=30.0)
            self.cursor = self.conn.cursor()

            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=10000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            self.conn.commit()

        # API Setup
        self.api = GiftCodeAPI(bot)

        # Gift Code Control Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS giftcodecontrol (
                alliance_id INTEGER PRIMARY KEY,
                status INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

        # Settings DB Connection
        if not os.path.exists('db'): os.makedirs('db')
        self.settings_conn = sqlite3.connect('db/settings.sqlite')
        self.settings_cursor = self.settings_conn.cursor()

        # Alliance DB Connection
        if not os.path.exists('db'): os.makedirs('db')
        self.alliance_conn = sqlite3.connect('db/alliance.sqlite')
        self.alliance_cursor = self.alliance_conn.cursor()

        # Gift Code Channel Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS giftcode_channel (
                alliance_id INTEGER,
                channel_id INTEGER,
                PRIMARY KEY (alliance_id)
            )
        """)
        self.conn.commit()
        
        # Add scan_history column if it doesn't exist (defaults to 0/False)
        try:
            self.cursor.execute("ALTER TABLE giftcode_channel ADD COLUMN scan_history INTEGER DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Add validation_status column to gift_codes table if it doesn't exist
        try:
            self.cursor.execute("ALTER TABLE gift_codes ADD COLUMN validation_status TEXT DEFAULT 'pending'")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Add priority column to giftcodecontrol table if it doesn't exist
        try:
            self.cursor.execute("ALTER TABLE giftcodecontrol ADD COLUMN priority INTEGER DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # WOS API URLs and Key
        self.wos_player_info_url = "https://wos-giftcode-api.centurygame.com/api/player"
        self.wos_giftcode_url = "https://wos-giftcode-api.centurygame.com/api/gift_code"
        self.wos_captcha_url = "https://wos-giftcode-api.centurygame.com/api/captcha"
        self.wos_giftcode_redemption_url = "https://wos-giftcode.centurygame.com"
        self.wos_encrypt_key = "tB87#kPtkxqOS2"

        # Retry Configuration for Requests
        self.retry_config = Retry(
            total=10,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )

        # Initialization of Locks and Cooldowns
        self.captcha_solver = None
        self._validation_lock = asyncio.Lock()
        self.last_validation_attempt_time = 0
        self.validation_cooldown = 5
        self._last_cleanup_date = None  # Track when we last ran cleanup (daily)
        
        # Gift Code Validation Queue System
        self.validation_queue = deque()
        self.validation_in_progress = False
        self.validation_queue_lock = asyncio.Lock()
        self.validation_queue_task = None
        self.test_captcha_cooldowns = {} # User ID: last test timestamp for test button
        self.test_captcha_delay = 60

        # Batch redemption tracking for consolidated progress messages
        self.redemption_batches = {}  # batch_id -> {message, alliances: {id: status}, giftcode}

        self.processing_stats = {
        "ocr_solver_calls": 0,       # Times solver.solve_captcha was called
        "ocr_valid_format": 0,     # Times solver returned success=True
        "captcha_submissions": 0,  # Times a solved code was sent to API
        "server_validation_success": 0, # Captcha accepted by server (not CAPTCHA_ERROR)
        "server_validation_failure": 0, # Captcha rejected by server (CAPTCHA_ERROR)
        "total_fids_processed": 0,   # Count of completed claim_giftcode calls
        "total_processing_time": 0.0 # Sum of durations for completed calls
        }

        # Captcha Solver Initialization Attempt
        try:
            self.settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS ocr_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enabled INTEGER DEFAULT 1,
                    save_images INTEGER DEFAULT 0
                    -- Remove use_gpu and gpu_device columns if they existed
                )""")
            self.settings_conn.commit()

            # Load latest OCR settings
            self.settings_cursor.execute("SELECT enabled, save_images FROM ocr_settings ORDER BY id DESC LIMIT 1")
            ocr_settings = self.settings_cursor.fetchone()

            if ocr_settings:
                enabled, save_images = ocr_settings
                if enabled == 1:
                    self.logger.info("GiftOps __init__: OCR is enabled. Initializing ONNX solver...")
                    self.captcha_solver = GiftCaptchaSolver(save_images=save_images)
                    if not self.captcha_solver.is_initialized:
                        self.logger.error("GiftOps __init__: ONNX solver FAILED to initialize.")
                        self.captcha_solver = None
                    else:
                        self.logger.info("GiftOps __init__: ONNX solver initialized successfully.")
                else:
                    self.logger.info("GiftOps __init__: OCR is disabled in settings.")
            else:
                self.logger.warning("GiftOps __init__: No OCR settings found in DB. Inserting defaults (Enabled=1, SaveImages=0).")
                self.settings_cursor.execute("""
                    INSERT INTO ocr_settings (enabled, save_images) VALUES (1, 0)
                """)
                self.settings_conn.commit()
                self.logger.info("GiftOps __init__: Attempting initialization with default settings...")
                self.captcha_solver = GiftCaptchaSolver(save_images=0)
                if not self.captcha_solver.is_initialized:
                    self.logger.error("GiftOps __init__: ONNX solver FAILED to initialize with defaults.")
                    self.captcha_solver = None
                else: # Ensure success is logged here for the CI
                    self.logger.info("GiftOps __init__: ONNX solver initialized successfully.")

        except ImportError as lib_err:
            self.logger.exception(f"GiftOps __init__: ERROR - Missing required library for OCR (likely onnxruntime): {lib_err}. Captcha solving disabled.")
            self.captcha_solver = None
        except Exception as e:
            self.logger.exception(f"GiftOps __init__: Unexpected error during Captcha solver setup: {e}")
            self.logger.exception(f"Traceback: {traceback.format_exc()}")
            self.captcha_solver = None

        # Test ID Settings Table
        try:
            self.settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_fid_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_fid TEXT NOT NULL
                )
            """)
            
            self.settings_cursor.execute("SELECT test_fid FROM test_fid_settings ORDER BY id DESC LIMIT 1")
            result = self.settings_cursor.fetchone()
            
            if not result: # Insert the default test ID if no entry exists
                self.settings_cursor.execute("INSERT INTO test_fid_settings (test_fid) VALUES (?)", ("244886619",))
                self.settings_conn.commit()
                self.logger.info("Initialized default test ID (244886619) in database")
        except Exception as e:
            self.logger.exception(f"Error setting up test ID table: {e}")

    async def _execute_with_retry(self, operation, *args, max_retries=3, delay=0.1):
        """Execute a database operation with retry logic for handling locks."""
        for attempt in range(max_retries):
            try:
                return operation(*args)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    self.logger.warning(f"Database locked, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    raise

    def clean_gift_code(self, giftcode):
        """Remove invisible Unicode characters (like RLM) that can contaminate gift codes"""
        import unicodedata
        cleaned = ''.join(char for char in giftcode if unicodedata.category(char)[0] != 'C')
        return cleaned.strip()
    
    async def add_to_validation_queue(self, giftcode, source, message=None, channel=None, operation_type='automatic', alliance_id=None, interaction=None, batch_id=None):
        """Add a gift code to the validation queue for processing."""
        async with self.validation_queue_lock:
            queue_item = {
                'giftcode': giftcode,
                'source': source,
                'message': message,
                'channel': channel,
                'timestamp': datetime.now(),
                'status': 'queued',
                'operation_type': operation_type,
                'alliance_id': alliance_id,
                'interaction': interaction,
                'batch_id': batch_id
            }
            self.validation_queue.append(queue_item)
            self.logger.info(f"Added gift code '{giftcode}' to validation queue (source: {source}, type: {operation_type}, queue length: {len(self.validation_queue)})")
            
            # Start queue processing if not already running
            if not self.validation_queue_task or self.validation_queue_task.done():
                self.validation_queue_task = asyncio.create_task(self.process_validation_queue())
    
    async def process_validation_queue(self):
        """Process the validation queue one item at a time."""
        self.logger.info("Starting validation queue processing")
        
        while True:
            async with self.validation_queue_lock:
                if not self.validation_queue:
                    self.logger.info("Validation queue is empty, stopping processing")
                    break
                
                queue_item = self.validation_queue.popleft()
                self.validation_in_progress = True
                
            try:
                await self._process_queue_item(queue_item)
            except Exception as e:
                self.logger.exception(f"Error processing queue item {queue_item['giftcode']}: {e}")
            finally:
                self.validation_in_progress = False
                await asyncio.sleep(0.5)  # Small delay between validations
        
        self.logger.info("Validation queue processing completed")
    
    async def _process_queue_item(self, queue_item):
        """Process a single queue item."""
        giftcode = queue_item['giftcode']
        source = queue_item['source']
        message = queue_item.get('message')
        channel = queue_item.get('channel')
        operation_type = queue_item.get('operation_type', 'automatic')
        alliance_id = queue_item.get('alliance_id')
        interaction = queue_item.get('interaction')
        batch_id = queue_item.get('batch_id')

        self.logger.info(f"Processing gift code '{giftcode}' from queue (source: {source}, type: {operation_type})")

        # Handle redemption
        if operation_type == 'redemption':
            if alliance_id:
                try:
                    # Get alliance name
                    self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (alliance_id,))
                    alliance_result = self.alliance_cursor.fetchone()
                    alliance_name = alliance_result[0] if alliance_result else f"Alliance {alliance_id}"
                    lang = _get_lang(interaction) if interaction else get_guild_language(
                        channel.guild.id if channel and channel.guild else None
                    )

                    # Handle batch progress update
                    if batch_id and batch_id in self.redemption_batches:
                        batch = self.redemption_batches[batch_id]
                        batch['alliances'][alliance_id]['status'] = 'processing'
                        await self._update_batch_progress(batch_id)

                    # Send starting message only if interaction exists (non-batch)
                    progress_message = None
                    if interaction and not batch_id:
                        start_embed = discord.Embed(
                            title=f"{theme.refreshIcon} {t('gift.redeem.process_title', lang)}",
                            description=t(
                                "gift.redeem.process_desc",
                                lang,
                                alliance=alliance_name,
                                code=giftcode
                            ),
                            color=theme.emColor1
                        )
                        progress_message = await interaction.followup.send(embed=start_embed, ephemeral=True)

                    # Execute the redemption
                    await self.use_giftcode_for_alliance(alliance_id, giftcode)

                    # Handle batch completion update
                    if batch_id and batch_id in self.redemption_batches:
                        batch = self.redemption_batches[batch_id]
                        total_codes = batch.get('total_codes', 1)

                        # Increment codes completed for this alliance
                        batch['alliances'][alliance_id]['codes_completed'] = batch['alliances'][alliance_id].get('codes_completed', 0) + 1
                        codes_done = batch['alliances'][alliance_id]['codes_completed']

                        # Mark alliance as completed only when all codes are done for it
                        if codes_done >= total_codes:
                            batch['alliances'][alliance_id]['status'] = 'completed'
                        else:
                            batch['alliances'][alliance_id]['status'] = 'processing'

                        await self._update_batch_progress(batch_id)

                        # Clean up batch if all alliances complete
                        all_done = all(info['status'] in ('completed', 'error') for info in batch['alliances'].values())
                        if all_done:
                            del self.redemption_batches[batch_id]

                    # Update the message with completion status if we have a message to update (non-batch)
                    elif interaction and progress_message:
                        complete_embed = discord.Embed(
                            title=f"{theme.verifiedIcon} {t('gift.redeem.complete_title', lang)}",
                            description=t(
                                "gift.redeem.complete_desc",
                                lang,
                                alliance=alliance_name,
                                code=giftcode
                            ),
                            color=theme.emColor3
                        )
                        try:
                            await progress_message.edit(embed=complete_embed)
                        except:
                            pass
                except Exception as e:
                    self.logger.exception(f"Error in manual redemption for alliance {alliance_id}: {e}")

                    # Handle batch error update
                    if batch_id and batch_id in self.redemption_batches:
                        batch = self.redemption_batches[batch_id]
                        total_codes = batch.get('total_codes', 1)

                        # Still count this as a code attempt for progress
                        batch['alliances'][alliance_id]['codes_completed'] = batch['alliances'][alliance_id].get('codes_completed', 0) + 1
                        codes_done = batch['alliances'][alliance_id]['codes_completed']

                        # Mark alliance as error (but continue with other alliances)
                        if codes_done >= total_codes:
                            batch['alliances'][alliance_id]['status'] = 'error'

                        await self._update_batch_progress(batch_id)

                        # Clean up batch if all alliances complete
                        all_done = all(info['status'] in ('completed', 'error') for info in batch['alliances'].values())
                        if all_done:
                            del self.redemption_batches[batch_id]

                    elif interaction:
                        error_embed = discord.Embed(
                            title=f"{theme.deniedIcon} {t('gift.redeem.error_title', lang)}",
                            description=t(
                                "gift.redeem.error_desc",
                                lang,
                                alliance=alliance_name,
                                error=str(e)
                            ),
                            color=theme.emColor2
                        )
                        if progress_message:
                            try:
                                await progress_message.edit(embed=error_embed)
                            except:
                                await interaction.followup.send(embed=error_embed, ephemeral=True)
                        else:
                            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        # Check if code already exists
        self.cursor.execute("SELECT 1 FROM gift_codes WHERE giftcode = ?", (giftcode,))
        if self.cursor.fetchone():
            self.logger.info(f"Code '{giftcode}' already exists in database.")
            if message and channel:
                await self._send_existing_code_response(message, giftcode, channel)
            return
        
        # Show processing message if from channel
        processing_message = None
        if message and channel:
            lang = get_guild_language(message.guild.id if message.guild else None)
            processing_embed = discord.Embed(
                title=f"{theme.refreshIcon} {t('gift.validation.processing_title', lang)}",
                description=t(
                    "gift.validation.processing_desc",
                    lang,
                    code=giftcode
                ),
                color=theme.emColor1
            )
            processing_message = await channel.send(embed=processing_embed)
        
        # Perform validation
        is_valid, validation_msg = await self.validate_gift_code_immediately(giftcode, source)
        
        # Handle validation result
        if message and channel:
            await self._send_validation_response(message, giftcode, is_valid, validation_msg, processing_message)
        
        # Process auto-use if valid
        if is_valid:
            await self._process_auto_use(giftcode)
    
    async def _send_existing_code_response(self, message, giftcode, channel):
        """Send response for existing gift code."""
        lang = get_guild_language(message.guild.id if message and message.guild else None)
        reply_embed = discord.Embed(
            title=f"{theme.infoIcon} {t('gift.validation.exists_title', lang)}",
            color=theme.emColor1
        )
        reply_embed.description = (
            f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
            f"{theme.userIcon} **{t('gift.validation.sender_label', lang)}** {message.author.mention}\n"
            f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
            f"{theme.editListIcon} **{t('gift.common.status_label', lang)}** {t('gift.validation.exists_status', lang)}\n"
            f"{theme.lowerDivider}\n"
        )
        await channel.send(embed=reply_embed)
        
        try:
            await message.add_reaction(theme.infoIcon)
        except (discord.Forbidden, discord.NotFound):
            pass
    
    async def _send_validation_response(self, message, giftcode, is_valid, validation_msg, processing_message=None):
        """Send validation response to channel."""
        lang = get_guild_language(message.guild.id if message and message.guild else None)
        if is_valid:
            reply_embed = discord.Embed(
                title=f"{theme.verifiedIcon} {t('gift.validation.validated_title', lang)}",
                color=theme.emColor3
            )
            reply_embed.description = (
                f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
                f"{theme.userIcon} **{t('gift.validation.sender_label', lang)}** {message.author.mention}\n"
                f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                f"{theme.verifiedIcon} **{t('gift.common.status_label', lang)}** {validation_msg}\n"
                f"{theme.lowerDivider}\n"
            )
            reaction = f"{theme.verifiedIcon}"
        elif is_valid is False:
            reply_embed = discord.Embed(
                title=f"{theme.deniedIcon} {t('gift.validation.invalid_title', lang)}",
                color=theme.emColor2
            )
            reply_embed.description = (
                f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
                f"{theme.userIcon} **{t('gift.validation.sender_label', lang)}** {message.author.mention}\n"
                f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                f"{theme.deniedIcon} **{t('gift.common.status_label', lang)}** {validation_msg}\n"
                f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.validation.action_not_added', lang)}\n"
                f"{theme.lowerDivider}\n"
            )
            reaction = f"{theme.deniedIcon}"
        else:
            reply_embed = discord.Embed(
                title=f"{theme.warnIcon} {t('gift.validation.pending_title', lang)}",
                color=discord.Color.yellow()
            )
            reply_embed.description = (
                f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
                f"{theme.userIcon} **{t('gift.validation.sender_label', lang)}** {message.author.mention}\n"
                f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                f"{theme.warnIcon} **{t('gift.common.status_label', lang)}** {validation_msg}\n"
                f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.validation.action_pending', lang)}\n"
                f"{theme.lowerDivider}\n"
            )
            reaction = theme.warnIcon
        
        if processing_message:
            await processing_message.edit(embed=reply_embed)
        else:
            await message.channel.send(embed=reply_embed)
        
        try:
            await message.add_reaction(reaction)
        except (discord.Forbidden, discord.NotFound):
            pass
    
    async def _process_auto_use(self, giftcode):
        """Process auto-use for valid gift codes."""
        self.cursor.execute("SELECT alliance_id FROM giftcodecontrol WHERE status = 1 ORDER BY priority ASC, alliance_id ASC")
        auto_alliances = self.cursor.fetchall()
        
        if auto_alliances:
            self.logger.info(f"Queueing auto-use for {len(auto_alliances)} alliances for code '{giftcode}'")
            for alliance in auto_alliances:
                # Add to queue instead of direct execution
                await self.add_to_validation_queue(
                    giftcode=giftcode,
                    source='auto',
                    operation_type='redemption',
                    alliance_id=alliance[0],
                    interaction=None  # No interaction for auto-use
                )
    
    async def get_queue_status(self):
        """Get current queue status."""
        async with self.validation_queue_lock:
            # Group queue items by gift code
            queue_by_code = {}
            for idx, item in enumerate(self.validation_queue):
                code = item['giftcode']
                if code not in queue_by_code:
                    queue_by_code[code] = []
                queue_by_code[code].append({
                    'position': idx + 1,
                    'alliance_id': item.get('alliance_id'),
                    'source': item.get('source')
                })
            
            return {
                'queue_length': len(self.validation_queue),
                'processing': self.validation_in_progress,
                'items': [{'giftcode': item['giftcode'], 'source': item['source']} for item in self.validation_queue],
                'queue_by_code': queue_by_code
            }
    
    async def add_manual_redemption_to_queue(self, giftcodes, alliance_ids, interaction):
        """Add manual redemption requests to validation queue.

        Args:
            giftcodes: Single gift code string or list of gift codes
            alliance_ids: List of alliance IDs
            interaction: Discord interaction for progress messages
        """
        # Normalize giftcodes to list
        if isinstance(giftcodes, str):
            giftcodes = [giftcodes]

        queue_positions = []
        total_redemptions = len(giftcodes) * len(alliance_ids)

        # Create batch for multiple redemptions
        batch_id = None
        if total_redemptions > 1 and interaction:
            import uuid
            batch_id = str(uuid.uuid4())
            lang = _get_lang(interaction)

            # Get alliance names for the batch
            alliances_info = {}
            for aid in alliance_ids:
                self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (aid,))
                result = self.alliance_cursor.fetchone()
                name = result[0] if result else f"Alliance {aid}"
                alliances_info[aid] = {'name': name, 'status': 'pending', 'codes_completed': 0}

            # Send initial consolidated progress message
            embed = self._build_batch_progress_embed(giftcodes, alliances_info, lang=lang)
            progress_message = await interaction.followup.send(embed=embed, ephemeral=True)

            # Store batch info
            self.redemption_batches[batch_id] = {
                'message': progress_message,
                'alliances': alliances_info,
                'giftcodes': giftcodes,
                'total_codes': len(giftcodes),
                'lang': lang
            }

        # Queue order: Alliance 1 -> all codes, then Alliance 2 -> all codes, etc.
        for alliance_id in alliance_ids:
            for giftcode in giftcodes:
                await self.add_to_validation_queue(
                    giftcode=giftcode,
                    source='manual',
                    operation_type='redemption',
                    alliance_id=alliance_id,
                    interaction=interaction if not batch_id else None,
                    batch_id=batch_id
                )

                queue_status = await self.get_queue_status()
                queue_positions.append(queue_status['queue_length'])

        return queue_positions

    def _build_batch_progress_embed(self, giftcodes, alliances_info, total_codes=None, lang: str | None = None):
        """Build the consolidated progress embed for batch redemption."""
        lang = lang or get_guild_language(None)
        # Handle both single code (string) and multiple codes (list)
        if isinstance(giftcodes, str):
            giftcodes = [giftcodes]

        if total_codes is None:
            total_codes = len(giftcodes)

        lines = []
        for aid, info in alliances_info.items():
            status = info['status']
            codes_completed = info.get('codes_completed', 0)

            if status == 'pending':
                icon = f"{theme.timeIcon}"
            elif status == 'processing':
                icon = f"{theme.refreshIcon}"
            elif status == 'completed':
                icon = f"{theme.verifiedIcon}"
            elif status == 'error':
                icon = f"{theme.deniedIcon}"
            else:
                icon = f"{theme.timeIcon}"

            # Show code progress for multi-code batches
            if total_codes > 1:
                codes_label = t("gift.batch.codes_label_plural", lang)
                lines.append(
                    f"{icon} **{info['name']}** ({codes_completed}/{total_codes} {codes_label})"
                )
            else:
                lines.append(f"{icon} **{info['name']}**")

        completed_alliances = sum(1 for info in alliances_info.values() if info['status'] == 'completed')
        total_alliances = len(alliances_info)

        # Build description based on single or multiple codes
        if total_codes > 1:
            code_display = t("gift.batch.code_all_display", lang, count=total_codes)
            codes_label = t("gift.batch.codes_label_plural", lang)
        else:
            code_display = f"`{giftcodes[0]}`"
            codes_label = t("gift.batch.codes_label_singular", lang)

        embed = discord.Embed(
            title=f"{theme.giftIcon} {t('gift.batch.title', lang)}",
            description=(
                f"**{codes_label}:** {code_display}\n"
                f"**{t('gift.batch.progress_label', lang)}** {completed_alliances}/{total_alliances} {t('gift.batch.alliances_label', lang)}\n\n"
                + "\n".join(lines)
            ),
            color=theme.emColor3 if completed_alliances == total_alliances else discord.Color.blue()
        )
        return embed

    async def _update_batch_progress(self, batch_id):
        """Update the batch progress message."""
        if batch_id not in self.redemption_batches:
            return

        batch = self.redemption_batches[batch_id]
        giftcodes = batch.get('giftcodes', batch.get('giftcode', []))
        total_codes = batch.get('total_codes', 1)
        embed = self._build_batch_progress_embed(
            giftcodes,
            batch['alliances'],
            total_codes,
            batch.get('lang')
        )

        try:
            await batch['message'].edit(embed=embed)
        except Exception as e:
            self.logger.warning(f"Failed to update batch progress message: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Handles cog setup when the bot is ready.
        Initializes database tables, loads OCR settings, initializes the captcha solver if enabled,
        validates gift code channels, and starts the background task loop.
        """
        self.logger.info("GiftOps Cog: on_ready triggered.")
        try:
            try:
                self.logger.info("Checking ocr_settings table schema...")
                conn_info = sqlite3.connect('db/settings.sqlite')
                cursor_info = conn_info.cursor()
                cursor_info.execute("PRAGMA table_info(ocr_settings)")
                columns = [col[1] for col in cursor_info.fetchall()]
                columns_to_drop = []
                if 'use_gpu' in columns: columns_to_drop.append('use_gpu')
                if 'gpu_device' in columns: columns_to_drop.append('gpu_device')
                    
                if columns_to_drop:
                    sqlite_version = sqlite3.sqlite_version_info
                    if sqlite_version >= (3, 35, 0):
                        self.logger.info(f"Found old columns {columns_to_drop} in ocr_settings. SQLite version {sqlite3.sqlite_version} supports DROP COLUMN. Attempting removal.")
                        for col_name in columns_to_drop:
                            try:
                                self.settings_cursor.execute(f"ALTER TABLE ocr_settings DROP COLUMN {col_name}")
                                self.logger.info(f"Successfully dropped column: {col_name}")
                            except Exception as drop_err:
                                self.logger.error(f"Error dropping column {col_name}: {drop_err}")
                        self.settings_conn.commit()
                    else:
                        self.logger.warning(f"Found old columns {columns_to_drop} in ocr_settings, but SQLite version {sqlite3.sqlite_version} (< 3.35.0) does not support DROP COLUMN easily. Columns will be ignored.")
                else:
                    self.logger.info("ocr_settings table schema is up to date.")
                conn_info.close()
            except Exception as schema_err:
                self.logger.error(f"Error during ocr_settings schema check/cleanup: {schema_err}")

            # OCR Settings Table Setup
            self.logger.info("Setting up ocr_settings table (ensuring correct schema)...")
            self.settings_cursor.execute("""
                CREATE TABLE IF NOT EXISTS ocr_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enabled INTEGER DEFAULT 1,
                    save_images INTEGER DEFAULT 0
                )
            """)
            self.settings_conn.commit()
            self.logger.info("ocr_settings table checked/created.")

            # Initialize Default OCR Settings if Needed
            self.settings_cursor.execute("SELECT COUNT(*) FROM ocr_settings")
            count = self.settings_cursor.fetchone()[0]
            if count == 0:
                self.logger.info("No OCR settings found, inserting defaults (Enabled=1, SaveImages=0)...")
                self.settings_cursor.execute("""
                    INSERT INTO ocr_settings (enabled, save_images) VALUES (1, 0)
                """)
                self.settings_conn.commit()
                self.logger.info("Default OCR settings inserted.")
            else:
                self.logger.info(f"Found {count} existing OCR settings row(s). Using the latest.")

            # Load OCR Settings and Initialize Solver
            if self.captcha_solver is None:
                self.logger.warning("Captcha solver not initialized in __init__, attempting again in on_ready...")
                self.settings_cursor.execute("SELECT enabled, save_images FROM ocr_settings ORDER BY id DESC LIMIT 1")
                ocr_settings = self.settings_cursor.fetchone()

                if ocr_settings:
                    enabled, save_images_setting = ocr_settings
                    self.logger.info(f"on_ready loaded settings: Enabled={enabled}, SaveImages={save_images_setting}")
                    if enabled == 1:
                        self.logger.info("OCR is enabled, attempting ONNX initialization...")
                        try:
                            self.captcha_solver = GiftCaptchaSolver(save_images=save_images_setting)
                            if not self.captcha_solver.is_initialized:
                                self.logger.error("ONNX solver FAILED to initialize in on_ready.")
                                self.captcha_solver = None
                        except Exception as e:
                            self.logger.exception("Failed to initialize Captcha Solver in on_ready.")
                            self.captcha_solver = None
                    else:
                        self.logger.info("OCR is disabled in settings (checked in on_ready).")
                else:
                    self.logger.warning("Could not load OCR settings from database in on_ready.")
            else:
                self.logger.info("Captcha solver was already initialized.")

            # Gift Code Channel Validation
            self.logger.info("Validating gift code channels...")
            self.cursor.execute("SELECT channel_id, alliance_id FROM giftcode_channel")
            channel_configs = self.cursor.fetchall()
            self.logger.info(f"Found {len(channel_configs)} gift code channel configurations in DB.")

            invalid_channels = []
            for channel_id, alliance_id in channel_configs:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    self.logger.warning(f"Channel ID {channel_id} (Alliance: {alliance_id}) is invalid or bot cannot access it. Marking for removal.")
                    invalid_channels.append(channel_id)
                elif not isinstance(channel, discord.TextChannel):
                    self.logger.warning(f"Channel ID {channel_id} (Alliance: {alliance_id}) is not a Text Channel. Marking for removal.")
                    invalid_channels.append(channel_id)
                elif not channel.permissions_for(channel.guild.me).send_messages:
                    self.logger.warning(f"Missing send message permissions in channel {channel_id}. Functionality may be limited.")

            if invalid_channels:
                unique_invalid_channels = list(set(invalid_channels))
                self.logger.info(f"Removing {len(unique_invalid_channels)} invalid channel configurations from database: {unique_invalid_channels}")
                placeholders = ','.join('?' * len(unique_invalid_channels))
                try:
                    self.cursor.execute(f"DELETE FROM giftcode_channel WHERE channel_id IN ({placeholders})", unique_invalid_channels)
                    self.conn.commit()
                    self.logger.info("Successfully removed invalid channel configurations.")
                except sqlite3.Error as db_err:
                    self.logger.exception(f"DATABASE ERROR removing invalid channels from database: {db_err}")
            else:
                self.logger.info("All configured gift code channels appear valid.")

            # Start periodic validation loop
            if not self.periodic_validation_loop.is_running():
                self.periodic_validation_loop.start()
                self.logger.info("Started periodic validation loop (2 hour interval)")
            
            self.logger.info("GiftOps Cog: on_ready setup finished successfully.")

        except sqlite3.Error as db_err:
            self.logger.exception(f"DATABASE ERROR during on_ready setup: {db_err}")
        except Exception as e:
            self.logger.exception(f"UNEXPECTED ERROR during on_ready setup: {e}")

    @discord.ext.commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        log_file_path = os.path.join(self.log_directory, 'giftlog.txt')
        try:
            if message.author.bot or not message.guild:
                return

            self.cursor.execute("SELECT alliance_id FROM giftcode_channel WHERE channel_id = ?", (message.channel.id,))
            channel_info = self.cursor.fetchone()
            if not channel_info:
                return

            content = message.content.strip()
            if not content:
                return

            # Extract potential gift code
            giftcode = None
            if len(content.split()) == 1:
                if re.match(r'^[a-zA-Z0-9]+$', content):
                    giftcode = content
            else:
                code_match = re.search(r'Code:\s*(\S+)', content, re.IGNORECASE)
                if code_match:
                    giftcode = code_match.group(1)
            
            if giftcode:
                giftcode = self.clean_gift_code(giftcode)
            
            if not giftcode:
                # No valid gift code format found, skip silently
                return

            log_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info(f"{log_timestamp} GiftOps: [on_message] Detected potential code '{giftcode}' in channel {message.channel.id} (Msg ID: {message.id})")

            # Add to validation queue
            await self.add_to_validation_queue(giftcode, "channel", message, message.channel)

        except Exception as e:
            self.logger.exception(f"GiftOps: UNEXPECTED Error in on_message handler: {str(e)}")
            traceback.print_exc()
            error_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            error_details = traceback.format_exc()
            log_message_handler = (
                f"\n--- ERROR in on_message Handler ({error_timestamp}) ---\n"
                f"Message ID: {message.id if 'message' in locals() else 'N/A'}\n"
                f"Channel ID: {message.channel.id if 'message' in locals() else 'N/A'}\n"
                f"Error: {str(e)}\n"
                f"Traceback:\n{error_details}\n"
                f"---------------------------------------------------------\n"
            )
            try:
                self.giftlog.info(log_message_handler.strip())
            except Exception as log_e:
                self.logger.exception(f"GiftOps: CRITICAL - Failed to write on_message handler error log: {log_e}")

    async def verify_test_fid(self, fid):
        """
        Verify that a ID is valid by attempting to login to the account.
        
        Args:
            fid (str): The ID to verify
            
        Returns:
            tuple: (is_valid, message) where is_valid is a boolean and message is a string
        """
        try:
            self.logger.info(f"Verifying test ID: {fid}")
            
            session, response_stove_info = self.get_stove_info_wos(player_id=fid)
            
            try:
                player_info_json = response_stove_info.json()
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON response when verifying ID {fid}")
                return False, "Invalid response from server"
            
            login_successful = player_info_json.get("msg") == "success"
            
            if login_successful:
                try:
                    nickname = player_info_json.get("data", {}).get("nickname", "Unknown")
                    furnace_lv = player_info_json.get("data", {}).get("stove_lv", "Unknown")
                    self.logger.info(f"Test ID {fid} is valid. Nickname: {nickname}, Level: {furnace_lv}")
                    return True, "Valid account"
                except Exception as e:
                    self.logger.exception(f"Error parsing player info for ID {fid}: {e}")
                    return True, "Valid account (but error getting details)"
            else:
                error_msg = player_info_json.get("msg", "Unknown error")
                self.logger.info(f"Test ID {fid} is invalid. Error: {error_msg}")
                return False, f"Login failed: {error_msg}"
        
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Connection error verifying test ID {fid}. Check bot connectivity to the WOS Gift Code API.")
            return False, "Connection error: WOS API unavailable"
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout verifying test ID {fid}. Check bot connectivity to the WOS Gift Code API.")
            return False, "Connection error: Request timed out"
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Request error verifying test ID {fid}: {type(e).__name__}")
            return False, f"Connection error: {type(e).__name__}"
        except Exception as e:
            self.logger.exception(f"Error verifying test ID {fid}: {e}")
            return False, f"Verification error: {str(e)}"

    async def update_test_fid(self, new_fid):
        """
        Update the test ID in the database.
        
        Args:
            new_fid (str): The new test ID
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            self.logger.info(f"Updating test ID to: {new_fid}")
            
            self.settings_cursor.execute("""
                INSERT INTO test_fid_settings (test_fid) VALUES (?)
            """, (new_fid,))
            self.settings_conn.commit()
            
            self.logger.info(f"Test ID updated successfully to {new_fid}")
            return True
        
        except sqlite3.Error as db_err:
            self.logger.exception(f"Database error updating test ID: {db_err}")
            return False
        except Exception as e:
            self.logger.exception(f"Unexpected error updating test ID: {e}")
            return False

    def get_test_fid(self):
        """
        Get the current test ID from the database.
        
        Returns:
            str: The current test ID, or the default "244886619" if not found
        """
        try:
            self.settings_cursor.execute("SELECT test_fid FROM test_fid_settings ORDER BY id DESC LIMIT 1")
            result = self.settings_cursor.fetchone()
            return result[0] if result else "244886619"
        except Exception as e:
            self.logger.exception(f"Error getting test ID: {e}")
            return "244886619"
    
    async def get_validation_fid(self):
        """Get the best available ID for gift code validation.
        
        Hierarchy:
        1. Configured test ID (if valid)
        2. Random alliance member ID (if no test ID)
        3. Relo default ID (244886619) as fallback
        
        Returns:
            tuple: (fid, source) where source is 'test_fid', 'alliance_member', or 'default'
        """
        try:
            # First try: Use configured test ID if it's valid
            test_fid = self.get_test_fid()
            
            # Check if test ID is actually configured (not default)
            self.settings_cursor.execute("SELECT test_fid FROM test_fid_settings ORDER BY id DESC LIMIT 1")
            result = self.settings_cursor.fetchone()
            
            if result and result[0] != "244886619":
                # Test ID is configured, verify it's valid
                is_valid, _ = await self.verify_test_fid(test_fid)
                if is_valid:
                    self.logger.info(f"Using configured test ID for validation: {test_fid}")
                    return test_fid, 'test_fid'
            
            # Second try: Use a random alliance member
            with sqlite3.connect('db/users.sqlite') as users_conn:
                users_cursor = users_conn.cursor()
                users_cursor.execute("""
                    SELECT fid, nickname FROM users 
                    WHERE alliance IS NOT NULL AND alliance != '' 
                    ORDER BY RANDOM() 
                    LIMIT 1
                """)
                member = users_cursor.fetchone()
                
                if member:
                    fid, nickname = member
                    self.logger.info(f"Using alliance member ID for validation: {fid} ({nickname})")
                    return fid, 'alliance_member'
            
            # Third try: Fall back to default ID
            self.logger.info("No alliance members found, using default ID for validation: 244886619")
            return "244886619", 'default'
            
        except Exception as e:
            self.logger.exception(f"Error in get_validation_fid: {e}")
            return "244886619", 'default'
    
    async def validate_gift_code_immediately(self, giftcode, source="unknown"):
        """Immediately validate a gift code when it's added from any source.
        
        Args:
            giftcode: The gift code to validate
            source: Where the code came from ('api', 'button', 'channel')
            
        Returns:
            tuple: (is_valid, status_message)
        """
        try:
            # Clean the gift code
            giftcode = self.clean_gift_code(giftcode)
            
            # Get the best ID for validation
            validation_fid, fid_source = await self.get_validation_fid()
            
            self.logger.info(f"Validating gift code '{giftcode}' from {source} using {fid_source} ID: {validation_fid}")
            
            # Check if already validated
            self.cursor.execute("SELECT validation_status FROM gift_codes WHERE giftcode = ?", (giftcode,))
            existing = self.cursor.fetchone()
            
            if existing:
                status = existing[0]
                if status == 'invalid':
                    self.logger.info(f"Gift code '{giftcode}' already marked as invalid")
                    return False, "Code already marked as invalid"
                elif status == 'validated':
                    self.logger.info(f"Gift code '{giftcode}' already validated")
                    return True, "Code already validated"
            
            # Perform validation using the selected ID
            status = await self.claim_giftcode_rewards_wos(validation_fid, giftcode)
            
            # Handle validation results
            if status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE", "TOO_SMALL_SPEND_MORE", "TOO_POOR_SPEND_MORE"]:
                # Valid code - mark as validated
                self.cursor.execute("""
                    INSERT OR REPLACE INTO gift_codes (giftcode, date, validation_status) 
                    VALUES (?, date('now'), 'validated')
                """, (giftcode,))
                self.conn.commit()
                
                # These statuses mean the code is valid but has requirements
                if status in ["TOO_SMALL_SPEND_MORE", "TOO_POOR_SPEND_MORE"]:
                    validation_msg = f"Code validated (has requirements)"
                    self.logger.info(f"Gift code '{giftcode}' is valid but has requirements: {status}")
                else:
                    validation_msg = f"Code validated successfully ({status})"
                    self.logger.info(f"Gift code '{giftcode}' validated successfully using {fid_source} ID")
                
                return True, validation_msg
                
            elif status in ["TIME_ERROR", "CDK_NOT_FOUND", "USAGE_LIMIT"]:
                # Invalid code - mark as invalid
                self.mark_code_invalid(giftcode)
                
                reason_map = {
                    "TIME_ERROR": "Code has expired",
                    "CDK_NOT_FOUND": "Code not found or incorrect",
                    "USAGE_LIMIT": "Usage limit reached"
                }
                reason = reason_map.get(status, f"Invalid ({status})")
                
                self.logger.warning(f"Gift code '{giftcode}' is invalid: {reason}")
                
                # Remove from API if needed
                if hasattr(self, 'api') and self.api:
                    asyncio.create_task(self.api.remove_giftcode(giftcode, from_validation=True))
                
                return False, reason
                
            else: # Other statuses - don't mark as invalid yet
                self.logger.warning(f"Gift code '{giftcode}' validation returned: {status}")
                return None, f"Validation inconclusive ({status})"
                
        except Exception as e:
            self.logger.exception(f"Error validating gift code '{giftcode}': {e}")
            return None, f"Validation error: {str(e)}"

    def encode_data(self, data):
        secret = self.wos_encrypt_key
        sorted_keys = sorted(data.keys())
        encoded_data = "&".join(
            [
                f"{key}={json.dumps(data[key]) if isinstance(data[key], dict) else data[key]}"
                for key in sorted_keys
            ]
        )
        sign = hashlib.md5(f"{encoded_data}{secret}".encode()).hexdigest()
        return {"sign": sign, **data}

    def batch_insert_user_giftcodes(self, user_giftcode_data):
        """Batch insert/update user giftcode records for better performance."""
        if not user_giftcode_data:
            return
        
        try: # Executemany for batch operations - much faster than individual inserts
            self.cursor.executemany("""
                INSERT OR REPLACE INTO user_giftcodes (fid, giftcode, status)
                VALUES (?, ?, ?)
            """, user_giftcode_data)
            
            self.conn.commit()
            self.logger.info(f"GiftOps: Batch inserted/updated {len(user_giftcode_data)} user giftcode records")
            
        except Exception as e:
            self.logger.exception(f"GiftOps: Error in batch_insert_user_giftcodes: {e}")
            self.conn.rollback()
            
    def batch_update_gift_codes_validation(self, giftcodes_to_validate):
        """Batch update gift codes validation status."""
        if not giftcodes_to_validate:
            return
            
        try:
            validation_data = [(giftcode,) for giftcode in giftcodes_to_validate]
            self.cursor.executemany("""
                UPDATE gift_codes 
                SET validation_status = 'validated' 
                WHERE giftcode = ? AND validation_status = 'pending'
            """, validation_data)
            
            self.conn.commit()
            updated_count = self.cursor.rowcount
            if updated_count > 0:
                self.logger.info(f"GiftOps: Batch validated {updated_count} gift codes")
            
        except Exception as e:
            self.logger.exception(f"GiftOps: Error in batch_update_gift_codes_validation: {e}")
            self.conn.rollback()
            
    def batch_get_user_giftcode_status(self, giftcode, fids):
        """Batch retrieve user giftcode status for multiple IDs."""
        if not fids:
            return {}
            
        try:
            placeholders = ','.join('?' * len(fids))
            self.cursor.execute(f"""
                SELECT fid, status FROM user_giftcodes 
                WHERE giftcode = ? AND fid IN ({placeholders})
            """, (giftcode, *fids))
            
            results = dict(self.cursor.fetchall())
            self.logger.debug(f"GiftOps: Batch retrieved {len(results)} user giftcode statuses")
            return results
            
        except Exception as e:
            self.logger.exception(f"GiftOps: Error in batch_get_user_giftcode_status: {e}")
            return {}

    def mark_code_invalid(self, giftcode):
        """Mark a single gift code as invalid."""
        try:
            self.cursor.execute("""
                UPDATE gift_codes 
                SET validation_status = 'invalid' 
                WHERE giftcode = ? AND validation_status != 'invalid'
            """, (giftcode,))
            
            self.conn.commit()
            if self.cursor.rowcount > 0:
                self.logger.info(f"GiftOps: Marked gift code '{giftcode}' as invalid")
                
        except Exception as e:
            self.logger.exception(f"GiftOps: Error marking code '{giftcode}' as invalid: {e}")
            self.conn.rollback()

    def batch_process_alliance_results(self, results_batch):
        """Process a batch of alliance redemption results efficiently."""
        if not results_batch:
            return
        
        try:
            # Separate successful results
            successful_records = []
            codes_to_validate = set()
            
            for fid, giftcode, status in results_batch:
                if status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE"]:
                    successful_records.append((fid, giftcode, status))
                    codes_to_validate.add(giftcode)
            
            # Batch insert successful records
            if successful_records:
                self.batch_insert_user_giftcodes(successful_records)
                
            # Batch validate codes
            if codes_to_validate:
                self.batch_update_gift_codes_validation(list(codes_to_validate))
                
            self.logger.info(f"GiftOps: Batch processed {len(successful_records)} successful, {len(codes_to_validate)} validated")
            
        except Exception as e:
            self.logger.exception(f"GiftOps: Error in batch_process_alliance_results: {e}")

    def get_stove_info_wos(self, player_id):
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=self.retry_config))

        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": self.wos_giftcode_redemption_url,
        }

        data_to_encode = {
            "fid": f"{player_id}",
            "time": f"{int(datetime.now().timestamp())}",
        }
        data = self.encode_data(data_to_encode)

        try:
            response_stove_info = session.post(
                self.wos_player_info_url,
                headers=headers,
                data=data,
            )
            return session, response_stove_info
        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"Connection error reaching WOS API for player {player_id}: {type(e).__name__}")
            raise
        except requests.exceptions.Timeout as e:
            self.logger.warning(f"Timeout reaching WOS API for player {player_id}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Request error reaching WOS API for player {player_id}: {type(e).__name__}")
            raise

    async def attempt_gift_code_with_api(self, player_id, giftcode, session):
        """Attempt to redeem a gift code."""
        max_ocr_attempts = 4
        
        for attempt in range(max_ocr_attempts):
            self.logger.info(f"GiftOps: Attempt {attempt + 1}/{max_ocr_attempts} to fetch/solve captcha for ID {player_id}")
            
            # Fetch captcha
            captcha_image_base64, error = await self.fetch_captcha(player_id, session)
            
            if error:
                if error == "CAPTCHA_TOO_FREQUENT":
                    self.logger.info(f"GiftOps: API returned CAPTCHA_TOO_FREQUENT for ID {player_id}")
                    return "CAPTCHA_TOO_FREQUENT", None, None, None
                else:
                    self.logger.error(f"GiftOps: Captcha fetch error for ID {player_id}: {error}")
                    return "CAPTCHA_FETCH_ERROR", None, None, None
            
            if not captcha_image_base64:
                self.logger.warning(f"GiftOps: No captcha image returned for ID {player_id}")
                return "CAPTCHA_FETCH_ERROR", None, None, None
            
            # Decode captcha image
            try:
                if captcha_image_base64.startswith("data:image"):
                    img_b64_data = captcha_image_base64.split(",", 1)[1]
                else:
                    img_b64_data = captcha_image_base64
                image_bytes = base64.b64decode(img_b64_data)
            except Exception as decode_err:
                self.logger.error(f"Failed to decode base64 image for ID {player_id}: {decode_err}")
                return "CAPTCHA_FETCH_ERROR", None, None, None
            
            # Solve captcha
            self.processing_stats["ocr_solver_calls"] += 1
            captcha_code, success, method, confidence, _ = await self.captcha_solver.solve_captcha(
                image_bytes, fid=player_id, attempt=attempt)
            
            if not success:
                self.logger.info(f"GiftOps: OCR failed for ID {player_id} on attempt {attempt + 1}")
                if attempt == max_ocr_attempts - 1:
                    return "MAX_CAPTCHA_ATTEMPTS_REACHED", None, None, None
                continue
            
            self.processing_stats["ocr_valid_format"] += 1
            self.logger.info(f"GiftOps: OCR solved for {player_id}: {captcha_code} (method:{method}, conf:{confidence:.2f}, attempt:{attempt+1})")
            
            # Submit gift code with solved captcha
            data_to_encode = {
                "fid": f"{player_id}",
                "cdk": giftcode,
                "captcha_code": captcha_code,
                "time": f"{int(datetime.now().timestamp()*1000)}"
            }
            data = self.encode_data(data_to_encode)
            self.processing_stats["captcha_submissions"] += 1
            
            # Submit to gift code API
            response_giftcode = session.post(self.wos_giftcode_url, data=data)
            
            # Log the redemption attempt
            log_entry_redeem = f"\n{datetime.now()} API REQ - Gift Code Redeem\nID:{player_id}, Code:{giftcode}, Captcha:{captcha_code}\n"
            try:
                response_json_redeem = response_giftcode.json()
                log_entry_redeem += f"Resp Code: {response_giftcode.status_code}\nResponse JSON:\n{json.dumps(response_json_redeem, indent=2)}\n"
            except json.JSONDecodeError:
                response_json_redeem = {}
                log_entry_redeem += f"Resp Code: {response_giftcode.status_code}\nResponse Text (Not JSON): {response_giftcode.text[:500]}...\n"
            log_entry_redeem += "-" * 50 + "\n"
            self.giftlog.info(log_entry_redeem.strip())
            
            # Parse response
            msg = str(response_json_redeem.get("msg", "Unknown Error")).strip('.')
            err_code = response_json_redeem.get("err_code")
            
            # Check if this is a rate limit error - these need special handling
            rate_limit_errors = {
                ("CAPTCHA GET TOO FREQUENT", 40100),
                ("CAPTCHA CHECK TOO FREQUENT", 40101)
            }
            
            if (msg, err_code) in rate_limit_errors:
                self.logger.info(f"GiftOps: Rate limit hit for ID {player_id} (msg: {msg}, code: {err_code})")
                return "CAPTCHA_TOO_FREQUENT", image_bytes, captcha_code, method
            
            # Handle other captcha errors with retry logic
            other_captcha_errors = {
                ("CAPTCHA CHECK ERROR", 40103),
                ("CAPTCHA EXPIRED", 40102)
            }
            
            if (msg, err_code) in other_captcha_errors:
                self.processing_stats["server_validation_failure"] += 1
                if attempt == max_ocr_attempts - 1:
                    return "CAPTCHA_INVALID", image_bytes, captcha_code, method
                else:
                    self.logger.info(f"GiftOps: CAPTCHA_INVALID for ID {player_id} on attempt {attempt + 1} (msg: {msg}). Retrying...")
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                    continue
            else:
                self.processing_stats["server_validation_success"] += 1
            
            # Determine final status
            if msg == "SUCCESS":
                status = "SUCCESS"
            elif msg == "RECEIVED" and err_code == 40008:
                status = "RECEIVED"
            elif msg == "SAME TYPE EXCHANGE" and err_code == 40011:
                status = "SAME TYPE EXCHANGE"
            elif msg == "TIME ERROR" and err_code == 40007:
                status = "TIME_ERROR"
            elif msg == "CDK NOT FOUND" and err_code == 40014:
                status = "CDK_NOT_FOUND"
            elif msg == "USED" and err_code == 40005:
                status = "USAGE_LIMIT"
            elif msg == "TIMEOUT RETRY" and err_code == 40004:
                status = "TIMEOUT_RETRY"
            elif msg == "NOT LOGIN":
                status = "LOGIN_EXPIRED_MID_PROCESS"
            elif "sign error" in msg.lower():
                status = "SIGN_ERROR"
                self.logger.error(f"[SIGN ERROR] Sign error detected for ID {player_id}, code {giftcode}")
                self.logger.error(f"[SIGN ERROR] Response: {response_json_redeem}")
            elif msg == "STOVE_LV ERROR" and err_code == 40006:
                status = "TOO_SMALL_SPEND_MORE"
                self.logger.error(f"[FURNACE LVL ERROR] Furnace level is too low for ID {player_id}, code {giftcode}")
                self.logger.error(f"[FURNACE LVL ERROR] Response: {response_json_redeem}")
            elif (msg == "RECHARGE_MONEY ERROR" and err_code == 40017) or (msg == "RECHARGE_MONEY_VIP ERROR" and err_code == 40018):
                status = "TOO_POOR_SPEND_MORE"
                self.logger.error(f"[VIP LEVEL ERROR] VIP level is too low for ID {player_id}, code {giftcode}")
                self.logger.error(f"[VIP LEVEL ERROR] Response: {response_json_redeem}")
            else:
                status = "UNKNOWN_API_RESPONSE"
                self.logger.info(f"Unknown API response for {player_id}: msg='{msg}', err_code={err_code}")
            
            return status, image_bytes, captcha_code, method
        
        return "MAX_CAPTCHA_ATTEMPTS_REACHED", None, None, None

    async def claim_giftcode_rewards_wos(self, player_id, giftcode):

        giftcode = self.clean_gift_code(giftcode)
        process_start_time = time.time()
        status = "ERROR"
        image_bytes = None
        captcha_code = None
        method = "N/A"

        try:
            # Cache Check
            test_fid = self.get_test_fid()
            if player_id != test_fid:
                self.cursor.execute("SELECT status FROM user_giftcodes WHERE fid = ? AND giftcode = ?", (player_id, giftcode))
                existing_record = self.cursor.fetchone()
                if existing_record:
                    if existing_record[0] in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE", "TIME_ERROR", "CDK_NOT_FOUND", "USAGE_LIMIT"]:
                        self.logger.info(f"CACHE HIT - User {player_id} code '{giftcode}' status: {existing_record[0]}")
                        return existing_record[0]

            # Check if OCR Enabled and Solver Ready
            self.settings_cursor.execute("SELECT enabled FROM ocr_settings ORDER BY id DESC LIMIT 1")
            ocr_settings_row = self.settings_cursor.fetchone()
            ocr_enabled = ocr_settings_row[0] if ocr_settings_row else 0

            if not (ocr_enabled == 1 and self.captcha_solver):
                status = "OCR_DISABLED" if ocr_enabled == 0 else "SOLVER_ERROR"
                log_msg = f"{datetime.now()} Skipping captcha: OCR disabled (Enabled={ocr_enabled}) or Solver not ready ({self.captcha_solver is None}) for ID {player_id}.\n"
                self.logger.info(log_msg.strip())
                return status

            # Initialize captcha solver stats
            self.logger.info(f"GiftOps: OCR enabled and solver initialized for ID {player_id}.")
            self.captcha_solver.reset_run_stats()
            
            # Get player session
            session, response_stove_info = self.get_stove_info_wos(player_id=player_id)
            log_entry_player = f"\n{datetime.now()} API REQUEST - Player Info\nPlayer ID: {player_id}\n"
            try:
                response_json_player = response_stove_info.json()
                log_entry_player += f"Response Code: {response_stove_info.status_code}\nResponse JSON:\n{json.dumps(response_json_player, indent=2)}\n"
            except json.JSONDecodeError:
                log_entry_player += f"Response Code: {response_stove_info.status_code}\nResponse Text (Not JSON): {response_stove_info.text[:500]}...\n"
            log_entry_player += "-" * 50 + "\n"
            self.giftlog.info(log_entry_player.strip())

            try:
                player_info_json = response_stove_info.json()
            except json.JSONDecodeError:
                player_info_json = {}
            login_successful = player_info_json.get("msg") == "success"

            if not login_successful:
                status = "LOGIN_FAILED"
                log_message = f"{datetime.now()} Login failed for ID {player_id}: {player_info_json.get('msg', 'Unknown')}\n"
                self.giftlog.info(log_message.strip())
                return status

            # Try gift code redemption
            self.logger.info(f"GiftOps: Starting gift code redemption for ID {player_id}")
            
            status, image_bytes, captcha_code, method = await self.attempt_gift_code_with_api(
                player_id, giftcode, session
            )

            # Handle database updates for successful redemptions
            if player_id != self.get_test_fid() and status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE"]:
                try:
                    user_giftcode_data = [(player_id, giftcode, status)]
                    self.batch_insert_user_giftcodes(user_giftcode_data)
                    
                    # Check if code needs validation
                    self.cursor.execute("""
                        SELECT validation_status FROM gift_codes 
                        WHERE giftcode = ? AND validation_status = 'pending'
                    """, (giftcode,))
                    
                    if self.cursor.fetchone():
                        giftcodes_to_validate = [giftcode]
                        self.batch_update_gift_codes_validation(giftcodes_to_validate)
                        
                        # If this code was just validated for the first time, send to API
                        self.logger.info(f"Code '{giftcode}' validated for the first time - sending to API")
                        try:
                            asyncio.create_task(self.api.add_giftcode(giftcode))
                        except Exception as api_err:
                            self.logger.exception(f"Error sending validated code '{giftcode}' to API: {api_err}")
                    
                    self.giftlog.info(f"DATABASE - Saved/Updated status for User {player_id}, Code '{giftcode}', Status {status}\n")
                except Exception as db_err:
                    self.giftlog.exception(f"DATABASE ERROR saving/replacing status for {player_id}/{giftcode}: {db_err}\n")
                    self.giftlog.exception(f"STACK TRACE: {traceback.format_exc()}\n")
                
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"GiftOps: Connection error for ID {player_id}. Check bot connectivity to the WOS Gift Code API.")
            status = "CONNECTION_ERROR"
        except requests.exceptions.Timeout:
            self.logger.warning(f"GiftOps: Timeout for ID {player_id}. Check bot connectivity to the WOS Gift Code API.")
            status = "CONNECTION_ERROR"
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"GiftOps: Request error for ID {player_id}: {type(e).__name__}")
            status = "CONNECTION_ERROR"
        except Exception as e:
            error_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            error_details = traceback.format_exc()
            log_message = (
                f"\n--- UNEXPECTED ERROR in claim_giftcode_rewards_wos ({error_timestamp}) ---\n"
                f"Player ID: {player_id}, Gift Code: {giftcode}\nError: {str(e)}\n"
                f"Traceback:\n{error_details}\n"
                f"---------------------------------------------------------------------\n"
            )
            self.logger.exception(f"GiftOps: UNEXPECTED Error claiming code {giftcode} for ID {player_id}. Details logged.")
            try:
                self.giftlog.error(log_message.strip())
            except Exception as log_e: self.logger.exception(f"GiftOps: CRITICAL - Failed to write unexpected error log: {log_e}")
            status = "ERROR"

        finally:
            process_end_time = time.time()
            duration = process_end_time - process_start_time
            self.processing_stats["total_fids_processed"] += 1
            self.processing_stats["total_processing_time"] += duration
            self.logger.info(f"GiftOps: claim_giftcode_rewards_wos completed for ID {player_id}. Status: {status}, Duration: {duration:.3f}s")

        # Image save handling
        if image_bytes and self.captcha_solver and self.captcha_solver.save_images_mode > 0:
            save_mode = self.captcha_solver.save_images_mode
            should_save = False
            filename_base = None
            log_prefix = ""

            is_success = status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE"]
            is_fail_server = status == "CAPTCHA_INVALID"

            if is_success and save_mode in [2, 3]:
                should_save = True
                log_prefix = f"Captcha OK (Solver: {method})"
                solved_code_str = captcha_code if captcha_code else "UNKNOWN_SOLVE"
                filename_base = f"{solved_code_str}.png"
            elif is_fail_server and save_mode in [1, 3]:
                should_save = True
                log_prefix = f"Captcha Fail Server (Solver: {method} -> {status})"
                solved_code_str = captcha_code if captcha_code else "UNKNOWN_SENT"
                timestamp = int(time.time())
                filename_base = f"FAIL_SERVER_{solved_code_str}_{timestamp}.png"

            if should_save and filename_base:
                try:
                    save_path = os.path.join(self.captcha_solver.captcha_dir, filename_base)
                    counter = 1
                    base, ext = os.path.splitext(filename_base)
                    while os.path.exists(save_path) and counter <= 100:
                        save_path = os.path.join(self.captcha_solver.captcha_dir, f"{base}_{counter}{ext}")
                        counter += 1

                    if counter > 100:
                        self.logger.warning(f"Could not find unique filename for {filename_base} after 100 tries. Discarding image.")
                    else:
                        with open(save_path, "wb") as f:
                            f.write(image_bytes)
                        self.logger.info(f"GiftOps: {log_prefix} - Saved captcha image as {os.path.basename(save_path)}")

                except Exception as save_err:
                    self.logger.exception(f"GiftOps: Error saving captcha image ({filename_base}): {save_err}")

        self.logger.info(f"GiftOps: Final status for ID {player_id} / Code '{giftcode}': {status}")
        return status
    
    async def scan_historical_messages(self, channel: discord.TextChannel, alliance_id: int) -> dict:
        """Scan historical messages in a channel for gift codes with consolidated results.
        
        Args:
            channel: The Discord channel to scan
            alliance_id: The alliance ID for this channel
            
        Returns:
            dict: Scan results with detailed breakdown
        """
        try:
            fetch_limit = 75  # Limit to prevent excessive scanning
            
            self.logger.info(f"Scanning historical messages in channel {channel.id} for alliance {alliance_id}")
            
            # Collect messages to process
            messages_to_process = []
            async for message in channel.history(limit=fetch_limit, oldest_first=False):
                # Skip bot messages and empty messages
                if message.author == self.bot.user or not message.content:
                    continue
                
                # Check if we've already reacted to this message
                bot_reactions = {str(reaction.emoji) for reaction in message.reactions if reaction.me}
                if bot_reactions.intersection([f"{theme.verifiedIcon}", f"{theme.deniedIcon}", f"{theme.warnIcon}", f"{theme.questionIcon}", f"{theme.infoIcon}"]):
                    continue
                
                messages_to_process.append(message)
            
            self.logger.info(f"Found {len(messages_to_process)} messages to process")
            
            # Results tracking
            scan_results = {
                'total_codes_found': 0,
                'new_codes': [],
                'existing_valid': [],
                'existing_invalid': [],
                'existing_pending': [],
                'validation_results': {},
                'messages_scanned': len(messages_to_process)
            }
            
            # Process each message and collect codes
            codes_to_validate = []
            message_code_map = {}
            
            for message in messages_to_process:
                content = message.content.strip()
                giftcode = None
                
                # Check for gift code patterns
                if len(content.split()) == 1:
                    if re.match(r'^[a-zA-Z0-9]+$', content):
                        giftcode = content
                else:
                    code_match = re.search(r'Code:\s*(\S+)', content, re.IGNORECASE)
                    if code_match:
                        potential_code = code_match.group(1)
                        if re.match(r'^[a-zA-Z0-9]+$', potential_code):
                            giftcode = potential_code
                
                if giftcode:
                    giftcode = self.clean_gift_code(giftcode)
                    scan_results['total_codes_found'] += 1
                    message_code_map[giftcode] = message
                    
                    # Check if code already exists
                    self.cursor.execute("SELECT validation_status FROM gift_codes WHERE giftcode = ?", (giftcode,))
                    result = self.cursor.fetchone()
                    
                    if result:
                        # Code exists, categorize by status
                        status = result[0]
                        if status == 'validated':
                            scan_results['existing_valid'].append(giftcode)
                        elif status == 'invalid':
                            scan_results['existing_invalid'].append(giftcode)
                        else:
                            scan_results['existing_pending'].append(giftcode)
                    else:
                        # New code found - will need validation
                        scan_results['new_codes'].append(giftcode)
                        codes_to_validate.append(giftcode)
            
            # Validate new codes in batch without individual messages
            if codes_to_validate:
                self.logger.info(f"Validating {len(codes_to_validate)} new codes from history scan")
                
                for giftcode in codes_to_validate:
                    # Add to database first
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO gift_codes (giftcode, alliance_id, validation_status, created_at)
                        VALUES (?, ?, 'pending', ?)
                    """, (giftcode, alliance_id, datetime.now().isoformat()))
                    self.conn.commit()
                    
                    # Validate the code silently (no individual messages)
                    is_valid = await self._validate_gift_code_silent(giftcode)
                    
                    # Update database with result
                    new_status = 'validated' if is_valid else 'invalid'
                    self.cursor.execute("""
                        UPDATE gift_codes 
                        SET validation_status = ?
                        WHERE giftcode = ?
                    """, (new_status, giftcode))
                    self.conn.commit()
                    
                    # Store validation result
                    scan_results['validation_results'][giftcode] = is_valid
                    
                    # Add appropriate reaction to message
                    if giftcode in message_code_map:
                        message = message_code_map[giftcode]
                        emoji = f"{theme.verifiedIcon}" if is_valid else f"{theme.deniedIcon}"
                        await message.add_reaction(emoji)
                    
                    # Small delay between validations
                    await asyncio.sleep(1.0)
            
            # Add reactions to existing codes
            for giftcode in scan_results['existing_valid']:
                if giftcode in message_code_map:
                    await message_code_map[giftcode].add_reaction(f"{theme.verifiedIcon}")
            
            for giftcode in scan_results['existing_invalid']:
                if giftcode in message_code_map:
                    await message_code_map[giftcode].add_reaction(f"{theme.deniedIcon}")
                    
            for giftcode in scan_results['existing_pending']:
                if giftcode in message_code_map:
                    await message_code_map[giftcode].add_reaction(f"{theme.warnIcon}")
            
            # Send consolidated results message
            await self._send_scan_results_message(channel, scan_results, alliance_id)
            
            self.logger.info(f"History scan complete. Results: {scan_results}")
            return scan_results
            
        except Exception as e:
            self.logger.exception(f"Error scanning historical messages: {e}")
            return {'total_codes_found': 0, 'messages_scanned': 0}

    async def _validate_gift_code_silent(self, giftcode: str) -> bool:
        """Validate a gift code silently without sending Discord messages.
        
        Args:
            giftcode: The gift code to validate
            
        Returns:
            bool: True if valid, False if invalid
        """
        try:
            # Use the existing validate_gift_code_immediately method
            is_valid, validation_msg = await self.validate_gift_code_immediately(giftcode, "historical_scan")
            return is_valid
        except Exception as e:
            self.logger.exception(f"Error in silent validation for {giftcode}: {e}")
            return False

    async def _send_scan_results_message(self, channel: discord.TextChannel, results: dict, alliance_id: int):
        """Send a consolidated scan results message to the channel.
        
        Args:
            channel: The Discord channel to send the message to
            results: The scan results dictionary
            alliance_id: The alliance ID
        """
        try:
            # Get alliance name
            self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (alliance_id,))
            alliance_result = self.alliance_cursor.fetchone()
            alliance_name = alliance_result[0] if alliance_result else f"Alliance {alliance_id}"
            
            # Build results embed
            embed = discord.Embed(
                title=f"{theme.searchIcon} History Scan Results",
                description=f"**Alliance:** {alliance_name}\n**Channel:** #{channel.name}",
                color=theme.emColor1
            )
            
            # Summary stats
            total_found = results['total_codes_found']
            messages_scanned = results['messages_scanned']
            
            embed.add_field(
                name=f"{theme.chartIcon} Scan Summary",
                value=f"**Messages Scanned:** {messages_scanned}\n**Total Codes Found:** {total_found}",
                inline=False
            )
            
            # New codes validation results
            if results['new_codes']:
                new_valid = [code for code, is_valid in results['validation_results'].items() if is_valid]
                new_invalid = [code for code, is_valid in results['validation_results'].items() if not is_valid]
                
                validation_text = ""
                if new_valid:
                    validation_text += f"{theme.verifiedIcon} **Valid Codes ({len(new_valid)}):**\n"
                    for code in new_valid[:5]: # Limit display to avoid message length issues
                        validation_text += f"  • `{code}`\n"
                    if len(new_valid) > 5:
                        validation_text += f"  • ... and {len(new_valid) - 5} more\n"
                    validation_text += "\n"
                
                if new_invalid:
                    validation_text += f"{theme.deniedIcon} **Invalid Codes ({len(new_invalid)}):**\n"
                    for code in new_invalid[:5]:
                        validation_text += f"  • `{code}`\n"
                    if len(new_invalid) > 5:
                        validation_text += f"  • ... and {len(new_invalid) - 5} more\n"
                
                if validation_text:
                    embed.add_field(
                        name=f"{theme.newIcon} New Codes Validated",
                        value=validation_text,
                        inline=False
                    )
            
            # Existing codes summary
            existing_summary = ""
            if results['existing_valid']:
                existing_summary += f"{theme.verifiedIcon} Previously Valid: {len(results['existing_valid'])}\n"
            if results['existing_invalid']:
                existing_summary += f"{theme.deniedIcon} Previously Invalid: {len(results['existing_invalid'])}\n"
            if results['existing_pending']:
                existing_summary += f"{theme.warnIcon} Pending Validation: {len(results['existing_pending'])}\n"
            
            if existing_summary:
                embed.add_field(
                    name=f"{theme.listIcon} Previously Found Codes",
                    value=existing_summary,
                    inline=False
                )
            
            # Add footer
            embed.set_footer(text="History scan complete. Check message reactions for individual code status.")
            
            # Send the message
            await channel.send(embed=embed)
            
        except Exception as e:
            self.logger.exception(f"Error sending scan results message: {e}")

    async def cleanup_old_invalid_codes(self):
        """Remove invalid gift codes older than 7 days from the database."""
        try:
            # Calculate the cutoff date (7 days ago)
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            
            # Get count of codes that will be deleted for logging
            self.cursor.execute("""
                SELECT COUNT(*) FROM gift_codes 
                WHERE validation_status = 'invalid' 
                AND date < ?
            """, (cutoff_date,))
            delete_count = self.cursor.fetchone()[0]
            
            if delete_count > 0:
                # Delete old invalid codes
                self.cursor.execute("""
                    DELETE FROM gift_codes 
                    WHERE validation_status = 'invalid' 
                    AND date < ?
                """, (cutoff_date,))
                
                # Also clean up any related user_giftcodes entries for deleted codes
                self.cursor.execute("""
                    DELETE FROM user_giftcodes 
                    WHERE giftcode NOT IN (SELECT giftcode FROM gift_codes)
                """)
                
                self.conn.commit()
                self.logger.info(f"Cleaned up {delete_count} invalid gift codes older than 7 days")
            else:
                self.logger.info("No old invalid gift codes found for cleanup")
                
        except Exception as e:
            self.logger.exception(f"Error during invalid codes cleanup: {e}")

    @tasks.loop(seconds=7200)
    async def periodic_validation_loop(self):
        """Periodically validate existing codes that are marked as 'valid' or 'pending'."""
        loop_start_time = datetime.now()
        self.logger.info(f"\nGiftOps: periodic_validation_loop running at {loop_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Check if we need to run daily cleanup (once per day)
            current_date = loop_start_time.date()
            if self._last_cleanup_date != current_date:
                self.logger.info("Running daily cleanup of old invalid gift codes...")
                await self.cleanup_old_invalid_codes()
                self._last_cleanup_date = current_date
            
            # Check if validation is already in progress to avoid conflicts
            async with self._validation_lock:
                # Get codes that need validation (pending or validated)
                self.cursor.execute("""
                    SELECT giftcode, validation_status 
                    FROM gift_codes 
                    WHERE validation_status IN ('pending', 'validated')
                """)
                codes_to_check = self.cursor.fetchall()
                
                if not codes_to_check:
                    self.logger.info("GiftOps: No codes need periodic validation.")
                    return
                
                self.logger.info(f"GiftOps: Found {len(codes_to_check)} codes to validate periodically.")
                
                # Get test ID for validation
                test_fid, fid_source = await self.get_validation_fid()
                self.logger.info(f"GiftOps: Using {fid_source} ID {test_fid} for periodic validation.")
                
                codes_checked = 0
                codes_invalidated = 0
                codes_still_valid = 0
                
                for giftcode, current_status in codes_to_check:
                    # Skip if we've checked too many codes (to prevent long-running loops)
                    if codes_checked >= 20:
                        self.logger.info("GiftOps: Reached periodic validation limit of 20 codes per run.")
                        break
                    
                    try:
                        self.logger.info(f"GiftOps: Periodically validating code '{giftcode}' (current status: {current_status})")
                        
                        # Check the code with test ID
                        status = await self.claim_giftcode_rewards_wos(test_fid, giftcode)
                        codes_checked += 1
                        
                        if status in ["TIME_ERROR", "CDK_NOT_FOUND", "USAGE_LIMIT"]: # Code is now invalid
                            self.logger.info(f"GiftOps: Code '{giftcode}' is now invalid (status: {status}). Updating database.")
                            
                            self.cursor.execute("UPDATE gift_codes SET validation_status = 'invalid' WHERE giftcode = ?", (giftcode,))
                            # Clear redemption status for the test fid
                            self.cursor.execute("DELETE FROM user_giftcodes WHERE giftcode = ? AND fid = ?", (giftcode, test_fid))
                            self.conn.commit()
                            
                            codes_invalidated += 1
                            
                            # Remove from API if present
                            if hasattr(self, 'api') and self.api:
                                asyncio.create_task(self.api.remove_giftcode(giftcode, from_validation=True))
                            
                            # Notify admins about invalidated code
                            self.settings_cursor.execute("SELECT id FROM admin WHERE is_initial = 1")
                            admin_ids = [row[0] for row in self.settings_cursor.fetchall()]
                            
                            for admin_id in admin_ids:
                                try:
                                    admin_user = await self.bot.fetch_user(admin_id)
                                    if admin_user:
                                        embed = discord.Embed(
                                            title=f"{theme.deniedIcon} Gift Code Invalidated",
                                            description=f"Code `{giftcode}` has been invalidated during periodic validation.\nStatus: {status}",
                                            color=theme.emColor2,
                                            timestamp=datetime.now()
                                        )
                                        await admin_user.send(embed=embed)
                                except Exception as e:
                                    self.logger.exception(f"Error notifying admin {admin_id}: {e}")
                        
                        elif status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE", "TOO_SMALL_SPEND_MORE", "TOO_POOR_SPEND_MORE"]:
                            codes_still_valid += 1

                            if current_status == 'pending':
                                self.logger.info(f"GiftOps: Code '{giftcode}' confirmed valid. Updating status to 'validated'.")
                                self.cursor.execute("UPDATE gift_codes SET validation_status = 'validated' WHERE giftcode = ? AND validation_status = 'pending'", (giftcode,))
                                self.conn.commit()

                                if hasattr(self, 'api') and self.api:
                                    asyncio.create_task(self.api.add_giftcode(giftcode))

                                try:
                                    await self._execute_with_retry(
                                        lambda: self.cursor.execute("SELECT alliance_id FROM giftcodecontrol WHERE status = 1 ORDER BY priority ASC, alliance_id ASC")
                                    )
                                    auto_alliances = self.cursor.fetchall() or []
                                except sqlite3.OperationalError as e:
                                    error_msg = f"Auto-alliance query failed after retries for code '{giftcode}': {e}"
                                    self.logger.error(error_msg)
                                    print(f"ERROR: {error_msg}")
                                    auto_alliances = []
                                except Exception as e:
                                    error_msg = f"Unexpected error in auto-alliance query for code '{giftcode}': {e}"
                                    self.logger.error(error_msg)
                                    print(f"ERROR: {error_msg}")
                                    auto_alliances = []

                                if auto_alliances:
                                    self.logger.info(f"GiftOps: Triggering delayed auto-redemption for code '{giftcode}' to {len(auto_alliances)} alliances")

                                    for alliance in auto_alliances:
                                        try:
                                            await self.add_to_validation_queue(
                                                giftcode=giftcode,
                                                source='periodic-auto',
                                                operation_type='redemption',
                                                alliance_id=alliance[0],
                                                interaction=None
                                            )
                                        except Exception as e:
                                            self.logger.exception(f"Error queueing delayed auto-redemption for code {giftcode} to alliance {alliance[0]}: {e}")

                                    self.settings_cursor.execute("SELECT id FROM admin WHERE is_initial = 1")
                                    admin_ids = [row[0] for row in self.settings_cursor.fetchall()]

                                    for admin_id in admin_ids:
                                        try:
                                            admin_user = await self.bot.fetch_user(admin_id)
                                            if admin_user:
                                                embed = discord.Embed(
                                                    title=f"{theme.verifiedIcon} Auto-Redemption Started",
                                                    description=f"Code `{giftcode}` has been validated and auto-redemption is now starting for {len(auto_alliances)} alliance(s).",
                                                    color=theme.emColor3,
                                                    timestamp=datetime.now()
                                                )
                                                await admin_user.send(embed=embed)
                                        except Exception as e:
                                            self.logger.exception(f"Error notifying admin {admin_id} about delayed auto-redemption: {e}")
                        
                        else:
                            self.logger.info(f"GiftOps: Code '{giftcode}' returned status '{status}' during periodic validation.")
                            
                            # Extra delay for CAPTCHA_TOO_FREQUENT errors
                            if status == "CAPTCHA_TOO_FREQUENT":
                                self.logger.info(f"GiftOps: Encountered CAPTCHA_TOO_FREQUENT, waiting 60-90 seconds before next validation")
                                await asyncio.sleep(random.uniform(60.0, 90.0))
                                continue
                        
                        # Wait between validations to avoid rate limiting
                        await asyncio.sleep(random.uniform(30.0, 60.0))
                        
                    except Exception as e:
                        self.logger.exception(f"Error validating code '{giftcode}' during periodic check: {e}")
                        await asyncio.sleep(5) # Longer wait on error
                
                self.logger.info(f"GiftOps: Periodic validation complete. Checked: {codes_checked}, Invalidated: {codes_invalidated}, Still valid: {codes_still_valid}")
            
            loop_end_time = datetime.now()
            self.logger.info(f"GiftOps: periodic_validation_loop finished at {loop_end_time.strftime('%Y-%m-%d %H:%M:%S')}. Duration: {loop_end_time - loop_start_time}\n")

        except Exception as e:
            self.logger.exception(f"GiftOps: Error in periodic_validation_loop: {str(e)}")
            # Wait before next attempt to avoid rapid error loops
            await asyncio.sleep(60)

    @periodic_validation_loop.before_loop
    async def before_periodic_validation_loop(self):
        self.logger.info("GiftOps: Waiting for bot to be ready before starting periodic_validation_loop...")
        await self.bot.wait_until_ready()
        self.logger.info("GiftOps: Bot is ready, periodic_validation_loop will start.")

    async def fetch_captcha(self, player_id, session=None):
        """Fetch a captcha image for a player ID."""
        if session is None:
            session = requests.Session()
            session.mount("https://", HTTPAdapter(max_retries=self.retry_config))
            
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": self.wos_giftcode_redemption_url,
        }
        
        data_to_encode = {
            "fid": player_id,
            "time": f"{int(datetime.now().timestamp() * 1000)}",
            "init": "0"
        }
        data = self.encode_data(data_to_encode)
        
        try:
            response = session.post(
                self.wos_captcha_url,
                headers=headers,
                data=data,
            )
            
            if response.status_code == 200:
                captcha_data = response.json()
                if captcha_data.get("code") == 1 and captcha_data.get("msg") == "CAPTCHA GET TOO FREQUENT.":
                    return None, "CAPTCHA_TOO_FREQUENT"
                    
                if "data" in captcha_data and "img" in captcha_data["data"]:
                    return captcha_data["data"]["img"], None
            
            return None, "CAPTCHA_FETCH_ERROR"
        except Exception as e:
            self.logger.exception(f"Error fetching captcha: {e}")
            return None, f"CAPTCHA_EXCEPTION: {str(e)}"

    async def show_ocr_settings(self, interaction: discord.Interaction):
            """Show OCR settings menu."""
            try:
                lang = _get_lang(interaction)
                self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
                admin_info = self.settings_cursor.fetchone()

                if not admin_info or admin_info[0] != 1:
                    error_msg = f"{theme.deniedIcon} {t('gift.ocr.admin_only', lang)}"
                    if interaction.response.is_done():
                        await interaction.followup.send(error_msg, ephemeral=True)
                    else:
                        await interaction.response.send_message(error_msg, ephemeral=True)
                    return

                self.settings_cursor.execute("SELECT enabled, save_images FROM ocr_settings ORDER BY id DESC LIMIT 1")
                ocr_settings = self.settings_cursor.fetchone()

                if not ocr_settings:
                    self.logger.warning("No OCR settings found in DB, inserting defaults.")
                    self.settings_cursor.execute("INSERT INTO ocr_settings (enabled, save_images) VALUES (1, 0)")
                    self.settings_conn.commit()
                    ocr_settings = (1, 0)

                enabled, save_images_setting = ocr_settings
                current_test_fid = self.get_test_fid()

                onnx_available = False
                solver_status_msg = t("gift.common.na", lang)
                if self.captcha_solver:
                    if self.captcha_solver.is_initialized:
                        onnx_available = True
                        solver_status_msg = t("gift.ocr.status.ready", lang)
                    elif hasattr(self.captcha_solver, 'is_initialized'):
                        onnx_available = True
                        solver_status_msg = t("gift.ocr.status.init_failed", lang)
                    else:
                        solver_status_msg = t("gift.ocr.status.instance_error", lang)
                else:
                    try:
                        # Suppress ONNX C++ GPU warning (writes to fd 2, not sys.stderr)
                        import sys, os as _os
                        _fd, _null = sys.stderr.fileno(), _os.open(_os.devnull, _os.O_WRONLY)
                        _bak = _os.dup(_fd); _os.dup2(_null, _fd); _os.close(_null)
                        import onnxruntime
                        _os.dup2(_bak, _fd); _os.close(_bak)
                        onnx_available = True
                        solver_status_msg = t("gift.ocr.status.disabled_or_failed", lang)
                    except ImportError:
                        onnx_available = False
                        solver_status_msg = t("gift.ocr.status.missing_lib", lang)

                save_options_text = {
                    0: f"{theme.deniedIcon} {t('gift.ocr.save.none', lang)}",
                    1: f"{theme.warnIcon} {t('gift.ocr.save.failed_only', lang)}",
                    2: f"{theme.verifiedIcon} {t('gift.ocr.save.success_only', lang)}",
                    3: f"{theme.saveIcon} {t('gift.ocr.save.all', lang)}"
                }
                save_images_display = save_options_text.get(
                    save_images_setting,
                    t("gift.ocr.save.unknown", lang, value=save_images_setting)
                )

                ocr_enabled_text = (
                    f"{theme.verifiedIcon} {t('gift.common.yes', lang)}"
                    if enabled == 1
                    else f"{theme.deniedIcon} {t('gift.common.no', lang)}"
                )
                onnx_runtime_text = (
                    f"{theme.verifiedIcon} {t('gift.ocr.onnx_found', lang)}"
                    if onnx_available
                    else f"{theme.deniedIcon} {t('gift.ocr.onnx_missing', lang)}"
                )

                embed = discord.Embed(
                    title=f"{theme.searchIcon} {t('gift.ocr.title', lang)}",
                    description=(
                        f"{t('gift.ocr.description', lang)}\n\n"
                        f"**{t('gift.ocr.current_settings', lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.robotIcon} **{t('gift.ocr.ocr_enabled', lang)}** {ocr_enabled_text}\n"
                        f"{theme.saveIcon} **{t('gift.ocr.save_images', lang)}** {save_images_display}\n"
                        f"{theme.fidIcon} **{t('gift.ocr.test_id', lang)}** `{current_test_fid}`\n"
                        f"{theme.giftIcon} **{t('gift.ocr.onnx_runtime', lang)}** {onnx_runtime_text}\n"
                        f"{theme.settingsIcon} **{t('gift.ocr.solver_status', lang)}** `{solver_status_msg}`\n"
                        f"{theme.lowerDivider}\n"
                    ),
                    color=theme.emColor1
                )

                if not onnx_available:
                    embed.add_field(
                        name=f"{theme.warnIcon} {t('gift.ocr.missing_library_title', lang)}",
                        value=t("gift.ocr.missing_library_body", lang),
                        inline=False
                    )

                stats_lines = []
                stats_lines.append(f"**{t('gift.ocr.stats.solver_title', lang)}**")
                ocr_calls = self.processing_stats['ocr_solver_calls']
                ocr_valid = self.processing_stats['ocr_valid_format']
                ocr_format_rate = (ocr_valid / ocr_calls * 100) if ocr_calls > 0 else 0
                stats_lines.append(t("gift.ocr.stats.solver_calls", lang, count=ocr_calls))
                stats_lines.append(t("gift.ocr.stats.valid_format", lang, count=ocr_valid, rate=f"{ocr_format_rate:.1f}"))

                stats_lines.append(f"\n**{t('gift.ocr.stats.redemption_title', lang)}**")
                submissions = self.processing_stats['captcha_submissions']
                server_success = self.processing_stats['server_validation_success']
                server_fail = self.processing_stats['server_validation_failure']
                total_server_val = server_success + server_fail
                server_pass_rate = (server_success / total_server_val * 100) if total_server_val > 0 else 0
                stats_lines.append(t("gift.ocr.stats.captcha_submissions", lang, count=submissions))
                stats_lines.append(t("gift.ocr.stats.server_success", lang, count=server_success))
                stats_lines.append(t("gift.ocr.stats.server_failure", lang, count=server_fail))
                stats_lines.append(t("gift.ocr.stats.server_pass_rate", lang, rate=f"{server_pass_rate:.1f}"))

                total_fids = self.processing_stats['total_fids_processed']
                total_time = self.processing_stats['total_processing_time']
                avg_time = (total_time / total_fids if total_fids > 0 else 0)
                stats_lines.append(t(
                    "gift.ocr.stats.avg_processing",
                    lang,
                    seconds=f"{avg_time:.2f}",
                    total=total_fids
                ))

                embed.add_field(
                    name=f"{theme.chartIcon} {t('gift.ocr.stats.title', lang)}",
                    value="\n".join(stats_lines),
                    inline=False
                )

                embed.add_field(
                    name=f"{theme.warnIcon} {t('gift.ocr.note_title', lang)}",
                    value=t("gift.ocr.note_body", lang),
                    inline=False
                )

                view = OCRSettingsView(self, ocr_settings, onnx_available, lang)

                if interaction.response.is_done():
                    try:
                        await interaction.edit_original_response(embed=embed, view=view)
                    except discord.NotFound:
                        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                    except Exception as e_edit:
                        self.logger.exception(f"Error editing original response in show_ocr_settings: {e_edit}")
                        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

            except sqlite3.Error as db_err:
                self.logger.exception(f"Database error in show_ocr_settings: {db_err}")
                error_message = f"{theme.deniedIcon} {t('gift.ocr.error.db', lang)}"
                if interaction.response.is_done(): await interaction.followup.send(error_message, ephemeral=True)
                else: await interaction.response.send_message(error_message, ephemeral=True)
            except Exception as e:
                self.logger.exception(f"Error showing OCR settings: {e}")
                traceback.print_exc()
                error_message = f"{theme.deniedIcon} {t('gift.ocr.error.unexpected', lang)}"
                if interaction.response.is_done():
                    await interaction.followup.send(error_message, ephemeral=True)
                else:
                    await interaction.response.send_message(error_message, ephemeral=True)

    async def update_ocr_settings(self, interaction, enabled=None, save_images=None, lang: str | None = None):
        """Update OCR settings in the database and reinitialize the solver if needed."""
        try:
            lang = lang or get_guild_language(None)
            self.settings_cursor.execute("SELECT enabled, save_images FROM ocr_settings ORDER BY id DESC LIMIT 1")
            current_settings = self.settings_cursor.fetchone()
            if not current_settings:
                current_settings = (1, 0)

            current_enabled, current_save_images = current_settings

            target_enabled = enabled if enabled is not None else current_enabled
            target_save_images = save_images if save_images is not None else current_save_images

            self.settings_cursor.execute("""
                UPDATE ocr_settings SET enabled = ?, save_images = ?
                WHERE id = (SELECT MAX(id) FROM ocr_settings)
                """, (target_enabled, target_save_images))
            if self.settings_cursor.rowcount == 0:
                self.settings_cursor.execute("""
                    INSERT INTO ocr_settings (enabled, save_images) VALUES (?, ?)
                    """, (target_enabled, target_save_images))
            self.settings_conn.commit()
            self.logger.info(f"GiftOps: Updated OCR settings in DB -> Enabled={target_enabled}, SaveImages={target_save_images}")

            message_suffix = t("gift.ocr.update.settings_updated", lang)
            reinitialize_solver = False

            if enabled is not None and enabled != current_enabled:
                reinitialize_solver = True
                message_suffix = t(
                    "gift.ocr.update.solver_enabled",
                    lang
                ) if target_enabled == 1 else t("gift.ocr.update.solver_disabled", lang)
            
            if save_images is not None and self.captcha_solver and self.captcha_solver.is_initialized:
                self.captcha_solver.save_images_mode = target_save_images
                self.logger.info(f"GiftOps: Updated live captcha_solver.save_images_mode to {target_save_images}")
                if not reinitialize_solver:
                    message_suffix = t("gift.ocr.update.image_saving_updated", lang)

            if reinitialize_solver:
                self.captcha_solver = None
                if target_enabled == 1:
                    self.logger.info("GiftOps: OCR is being enabled/reinitialized...")
                    try:
                        self.captcha_solver = GiftCaptchaSolver(save_images=target_save_images)
                        if self.captcha_solver.is_initialized:
                            self.logger.info("GiftOps: ONNX solver reinitialized successfully.")
                            message_suffix = f"{message_suffix} {t('gift.ocr.update.solver_reinitialized', lang)}"
                        else:
                            self.logger.error("GiftOps: ONNX solver FAILED to reinitialize.")
                            message_suffix = f"{message_suffix} {t('gift.ocr.update.solver_reinit_failed', lang)}"
                            self.captcha_solver = None
                            return False, t("gift.ocr.update.result", lang, detail=message_suffix)
                    except ImportError as imp_err:
                        self.logger.exception(f"GiftOps: ERROR - Reinitialization failed: Missing library {imp_err}")
                        message_suffix = f"{message_suffix} {t('gift.ocr.update.solver_init_missing_lib', lang, error=imp_err)}"
                        self.captcha_solver = None
                        return False, t("gift.ocr.update.result", lang, detail=message_suffix)
                    except Exception as e:
                        self.logger.exception(f"GiftOps: ERROR - Reinitialization failed: {e}")
                        message_suffix = f"{message_suffix} {t('gift.ocr.update.solver_init_failed', lang, error=e)}"
                        self.captcha_solver = None
                        return False, t("gift.ocr.update.result", lang, detail=message_suffix)
                else:
                    self.logger.info("GiftOps: OCR disabled, solver instance removed/kept None.")

            return True, t("gift.ocr.update.result", lang, detail=message_suffix)

        except sqlite3.Error as db_err:
            self.logger.exception(f"Database error updating OCR settings: {db_err}")
            return False, t("gift.ocr.update.db_error", lang, error=db_err)
        except Exception as e:
            self.logger.exception(f"Unexpected error updating OCR settings: {e}")
            return False, t("gift.ocr.update.unexpected_error", lang, error=e)

    async def show_redemption_priority(self, interaction: discord.Interaction):
        """Show the redemption priority management interface (global admin only)."""
        try:
            lang = _get_lang(interaction)
            # Check global admin permission
            self.settings_cursor.execute("SELECT is_initial FROM admin WHERE id = ?", (interaction.user.id,))
            admin_info = self.settings_cursor.fetchone()

            if not admin_info or admin_info[0] != 1:
                error_msg = f"{theme.deniedIcon} {t('gift.priority.global_only', lang)}"
                if interaction.response.is_done():
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await interaction.response.send_message(error_msg, ephemeral=True)
                return

            # Get all alliances with their priority info
            self.alliance_cursor.execute("SELECT alliance_id, name FROM alliance_list ORDER BY alliance_id")
            all_alliances = self.alliance_cursor.fetchall()

            if not all_alliances:
                error_msg = t("gift.priority.none_found", lang)
                if interaction.response.is_done():
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await interaction.response.send_message(error_msg, ephemeral=True)
                return

            # Get priority info for alliances
            alliance_ids = [a[0] for a in all_alliances]
            placeholders = ','.join('?' * len(alliance_ids))
            self.cursor.execute(f"""
                SELECT alliance_id, priority FROM giftcodecontrol
                WHERE alliance_id IN ({placeholders})
            """, alliance_ids)
            priority_data = {row[0]: row[1] for row in self.cursor.fetchall()}

            # Build alliance list with priorities
            alliances_with_priority = []
            for alliance_id, name in all_alliances:
                priority = priority_data.get(alliance_id, 0)
                alliances_with_priority.append((alliance_id, name, priority))

            # Sort by priority, then by alliance_id
            alliances_with_priority.sort(key=lambda x: (x[2], x[0]))

            # Create embed
            embed = discord.Embed(
                title=f"{theme.chartIcon} {t('gift.priority.title', lang)}",
                description=t("gift.priority.description", lang),
                color=theme.emColor1
            )

            # Build priority list
            priority_list = []
            for idx, (alliance_id, name, priority) in enumerate(alliances_with_priority, 1):
                priority_list.append(f"`{idx}.` **{name}**")

            embed.add_field(
                name=t("gift.priority.current_order", lang),
                value="\n".join(priority_list) if priority_list else t("gift.priority.none", lang),
                inline=False
            )

            view = RedemptionPriorityView(self, alliances_with_priority, lang)

            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            self.logger.exception(f"Error in show_redemption_priority: {e}")
            error_msg = f"{t('gift.error.generic', lang)}: {str(e)}"
            if interaction.response.is_done():
                await interaction.followup.send(error_msg, ephemeral=True)
            else:
                await interaction.response.send_message(error_msg, ephemeral=True)

    async def validate_gift_codes(self):
        try:
            lang = get_guild_language(None)
            self.cursor.execute("SELECT giftcode, validation_status FROM gift_codes WHERE validation_status != 'invalid'")
            all_codes = self.cursor.fetchall()
            
            self.settings_cursor.execute("SELECT id FROM admin WHERE is_initial = 1")
            admin_ids = [row[0] for row in self.settings_cursor.fetchall()]
            
            if not all_codes:
                self.logger.info("[validate_gift_codes] No codes found needing validation.")
                return

            for giftcode, current_db_status in all_codes:
                if current_db_status == 'invalid':
                    self.logger.info(f"[validate_gift_codes] Skipping already invalid code: {giftcode}")
                    continue

                self.logger.info(f"[validate_gift_codes] Validating code: {giftcode} (current DB status: {current_db_status})")
                test_fid = self.get_test_fid()
                status = await self.claim_giftcode_rewards_wos(test_fid, giftcode)

                if status in ["TIME_ERROR", "CDK_NOT_FOUND", "USAGE_LIMIT"]:
                    self.logger.info(f"[validate_gift_codes] Code {giftcode} found to be invalid with status: {status}. Updating DB.")
                    
                    self.cursor.execute("UPDATE gift_codes SET validation_status = 'invalid' WHERE giftcode = ?", (giftcode,))
                    test_fid = self.get_test_fid()
                    self.cursor.execute("DELETE FROM user_giftcodes WHERE giftcode = ? AND fid = ?", (giftcode, test_fid))
                    self.conn.commit()
                    
                    if hasattr(self, 'api') and self.api:
                        asyncio.create_task(self.api.remove_giftcode(giftcode, from_validation=True))

                    reason_map = {
                        "TIME_ERROR": t("gift.redeem.invalid_time_error", lang),
                        "CDK_NOT_FOUND": t("gift.redeem.invalid_cdk_not_found", lang),
                        "USAGE_LIMIT": t("gift.redeem.invalid_usage_limit", lang)
                    }
                    detailed_reason = reason_map.get(
                        status,
                        t("gift.redeem.invalid_generic", lang, status=status)
                    )

                    admin_embed = discord.Embed(
                        title=f"{theme.giftIcon} {t('gift.validation.invalidated_title', lang)}",
                        description=(
                            f"**{t('gift.common.details_title', lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                            f"{theme.deniedIcon} **{t('gift.common.status_label', lang)}** {detailed_reason}\n"
                            f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.redeem.invalid_action', lang)}\n"
                            f"{theme.timeIcon} **{t('gift.common.time_label', lang)}** <t:{int(datetime.now().timestamp())}:R>\n"
                            f"{theme.lowerDivider}\n"
                        ),
                        color=discord.Color.orange()
                    )
                    
                    for admin_id in admin_ids:
                        try:
                            admin_user = await self.bot.fetch_user(admin_id)
                            if admin_user:
                                await admin_user.send(embed=admin_embed)
                        except Exception as e:
                            self.logger.exception(f"Error sending message to admin {admin_id}: {str(e)}")
                
                elif status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE", "TOO_SMALL_SPEND_MORE", "TOO_POOR_SPEND_MORE"] and current_db_status == 'pending':
                    self.logger.info(f"[validate_gift_codes] Code {giftcode} confirmed valid. Updating status to 'validated'.")
                    self.cursor.execute("UPDATE gift_codes SET validation_status = 'validated' WHERE giftcode = ? AND validation_status = 'pending'", (giftcode,))
                    self.conn.commit()

                    if hasattr(self, 'api') and self.api:
                        asyncio.create_task(self.api.add_giftcode(giftcode))
                    
                await asyncio.sleep(60)
                
        except Exception as e:
            self.logger.exception(f"Error in validate_gift_codes: {str(e)}")

    async def handle_success(self, message, giftcode):
        lang = get_guild_language(message.guild.id if message.guild else None)
        test_fid = self.get_test_fid()
        status = await self.claim_giftcode_rewards_wos(test_fid, giftcode)
        
        if status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE"]:
            self.cursor.execute("SELECT 1 FROM gift_codes WHERE giftcode = ?", (giftcode,))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO gift_codes (giftcode, date) VALUES (?, ?)", (giftcode, datetime.now()))
                self.conn.commit()
                
                try:
                    asyncio.create_task(self.api.add_giftcode(giftcode))
                except:
                    pass
                
                await message.add_reaction(f"{theme.verifiedIcon}")
                await message.reply(t("gift.validation.added_reply", lang), mention_author=False)
        elif status == "TIME_ERROR":
            await message.add_reaction(f"{theme.deniedIcon}")
            await message.reply(t("gift.validation.expired_reply", lang), mention_author=False)
        elif status == "CDK_NOT_FOUND":
            await message.add_reaction(f"{theme.deniedIcon}")
            await message.reply(t("gift.validation.incorrect_reply", lang), mention_author=False)
        elif status == "USAGE_LIMIT":
            await message.add_reaction(f"{theme.deniedIcon}")
            await message.reply(t("gift.validation.usage_limit_reply", lang), mention_author=False)

    async def handle_already_received(self, message, giftcode):
        lang = get_guild_language(message.guild.id if message.guild else None)
        test_fid = self.get_test_fid()
        status = await self.claim_giftcode_rewards_wos(test_fid, giftcode)
        
        if status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE"]:
            self.cursor.execute("SELECT 1 FROM gift_codes WHERE giftcode = ?", (giftcode,))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO gift_codes (giftcode, date) VALUES (?, ?)", (giftcode, datetime.now()))
                self.conn.commit()
                
                try:
                    asyncio.create_task(self.api.add_giftcode(giftcode))
                except:
                    pass
                
                await message.add_reaction(f"{theme.verifiedIcon}")
                await message.reply(t("gift.validation.added_reply", lang), mention_author=False)
        elif status == "TIME_ERROR":
            await message.add_reaction(f"{theme.deniedIcon}")
            await message.reply(t("gift.validation.expired_reply", lang), mention_author=False)
        elif status == "CDK_NOT_FOUND":
            await message.add_reaction(f"{theme.deniedIcon}")
            await message.reply(t("gift.validation.incorrect_reply", lang), mention_author=False)
        elif status == "USAGE_LIMIT":
            await message.add_reaction(f"{theme.deniedIcon}")
            await message.reply(t("gift.validation.usage_limit_reply", lang), mention_author=False)

    async def get_admin_info(self, user_id):
        """Get admin info - delegates to centralized PermissionManager"""
        is_admin, is_global = PermissionManager.is_admin(user_id)
        if not is_admin:
            return None
        return (user_id, 1 if is_global else 0)

    async def get_alliance_names(self, user_id, is_global=False):
        if is_global:
            self.alliance_cursor.execute("SELECT name FROM alliance_list")
            return [row[0] for row in self.alliance_cursor.fetchall()]
        else:
            self.settings_cursor.execute("""
                SELECT alliances_id FROM adminserver WHERE admin = ?
            """, (user_id,))
            alliance_ids = [row[0] for row in self.settings_cursor.fetchall()]

            if alliance_ids:
                placeholders = ','.join('?' * len(alliance_ids))
                self.alliance_cursor.execute(f"""
                    SELECT name FROM alliance_list
                    WHERE alliance_id IN ({placeholders})
                """, alliance_ids)
                return [row[0] for row in self.alliance_cursor.fetchall()]
            return []

    async def get_available_alliances(self, interaction: discord.Interaction):
        """Get available alliances - delegates to centralized PermissionManager"""
        user_id = interaction.user.id
        guild_id = interaction.guild_id if interaction.guild else None

        alliances, _ = PermissionManager.get_admin_alliances(user_id, guild_id or 0)
        return alliances

    async def setup_gift_channel(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        admin_info = await self.get_admin_info(interaction.user.id)
        if not admin_info:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.channel.setup.not_authorized', lang)}",
                ephemeral=True
            )
            return

        available_alliances = await self.get_available_alliances(interaction)
        if not available_alliances:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.channel.setup.no_alliances_title', lang)}",
                    description=t("gift.channel.setup.no_alliances_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return

        alliances_with_counts = []
        for alliance_id, name in available_alliances:
            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                member_count = cursor.fetchone()[0]
                alliances_with_counts.append((alliance_id, name, member_count))

        self.cursor.execute("SELECT alliance_id, channel_id FROM giftcode_channel")
        current_channels = dict(self.cursor.fetchall())

        alliance_embed = discord.Embed(
            title=f"{theme.announceIcon} {t('gift.channel.setup.title', lang)}",
            description=(
                f"{t('gift.channel.setup.select_alliance', lang)}\n\n"
                f"**{t('gift.redeem.alliance_list', lang)}**\n"
                f"{theme.middleDivider}\n"
                f"{t('gift.channel.setup.select_alliance_hint', lang)}\n"
            ),
            color=theme.emColor1
        )

        view = AllianceSelectView(alliances_with_counts, self, context="giftcode")

        async def alliance_callback(select_interaction: discord.Interaction, alliance_id=None):
            try:
                if alliance_id is None:
                    alliance_id = int(view.current_select.values[0])

                channel_embed = discord.Embed(
                    title=f"{theme.announceIcon} {t('gift.channel.setup.title', lang)}",
                    description=(
                        f"**{t('gift.channel.setup.instructions', lang)}**\n"
                        f"{theme.middleDivider}\n"
                        f"{t('gift.channel.setup.select_channel', lang)}\n\n"
                        f"**{t('gift.channel.setup.page', lang)}** 1/1\n"
                        f"**{t('gift.channel.setup.total_channels', lang)}** {len(select_interaction.guild.text_channels)}"
                    ),
                    color=theme.emColor1
                )

                async def channel_select_callback(channel_interaction: discord.Interaction):
                    try:
                        channel_id = int(channel_interaction.data["values"][0])
                        
                        self.cursor.execute("""
                            INSERT OR REPLACE INTO giftcode_channel (alliance_id, channel_id)
                            VALUES (?, ?)
                        """, (alliance_id, channel_id))
                        self.conn.commit()

                        alliance_name = next(
                            (name for aid, name in available_alliances if aid == alliance_id),
                            t("gift.redeem.unknown", lang)
                        )

                        success_embed = discord.Embed(
                            title=f"{theme.verifiedIcon} {t('gift.channel.setup.success_title', lang)}",
                            description=(
                                f"{t('gift.channel.setup.success_desc', lang)}\n\n"
                                f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                                f"{theme.editListIcon} **{t('gift.channel.channel_label', lang)}** <#{channel_id}>\n\n"
                                f"{theme.verifiedIcon} {t('gift.channel.setup.configured_line', lang)}\n"
                                f"{t('gift.channel.setup.history_hint', lang)}\n"
                                f"{t('gift.channel.setup.tip', lang)}"
                            ),
                            color=theme.emColor3
                        )

                        await channel_interaction.response.edit_message(
                            embed=success_embed,
                            view=None
                        )

                    except Exception as e:
                        self.logger.exception(f"Error setting gift code channel: {e}")
                        await channel_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('gift.channel.setup.error', lang)}",
                            ephemeral=True
                        )

                channels = select_interaction.guild.text_channels
                channel_view = PaginatedChannelView(channels, channel_select_callback)

                if not select_interaction.response.is_done():
                    await select_interaction.response.edit_message(
                        embed=channel_embed,
                        view=channel_view
                    )
                else:
                    await select_interaction.message.edit(
                        embed=channel_embed,
                        view=channel_view
                    )

            except Exception as e:
                self.logger.exception(f"Error in alliance selection: {e}")
                if not select_interaction.response.is_done():
                    await select_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('gift.error.process_selection', _get_lang(select_interaction))}",
                        ephemeral=True
                    )
                else:
                    await select_interaction.followup.send(
                        f"{theme.deniedIcon} {t('gift.error.process_selection', _get_lang(select_interaction))}",
                        ephemeral=True
                    )

        view.callback = alliance_callback

        await interaction.response.send_message(
            embed=alliance_embed,
            view=view,
            ephemeral=True
        )

    async def show_gift_menu(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        gift_menu_embed = discord.Embed(
            title=f"{theme.giftIcon} {t('gift.menu.title', lang)}",
            description=(
                f"{t('gift.menu.intro', lang)}\n\n"
                f"{t('gift.menu.auto_fetch', lang)} "
                f"{t('gift.menu.auto_validate', lang)}\n\n"
                f"{t('gift.menu.getting_started', lang)}\n"
                f"- {t('gift.menu.tip_auto', lang)}\n"
                f"- {t('gift.menu.tip_channel', lang)}\n"
                f"- {t('gift.menu.tip_priority', lang)}\n\n"
                f"**{t('gift.menu.available', lang)}**\n"
                f"{theme.upperDivider}\n"
                f"{theme.giftIcon} **{t('gift.menu.add', lang)}**\n"
                f"└ {t('gift.menu.add_desc', lang)}\n\n"
                f"{theme.listIcon} **{t('gift.menu.list', lang)}**\n"
                f"└ {t('gift.menu.list_desc', lang)}\n\n"
                f"{theme.targetIcon} **{t('gift.menu.redeem', lang)}**\n"
                f"└ {t('gift.menu.redeem_desc', lang)}\n\n"
                f"{theme.settingsIcon} **{t('gift.menu.settings', lang)}**\n"
                f"└ {t('gift.menu.settings_desc', lang)}\n\n"
                f"{theme.deniedIcon} **{t('gift.menu.delete', lang)}**\n"
                f"└ {t('gift.menu.delete_desc', lang)}\n"
                f"{theme.lowerDivider}"
            ),
            color=discord.Color.gold()
        )

        view = GiftView(self, lang)
        try:
            await interaction.response.edit_message(embed=gift_menu_embed, view=view)
        except discord.InteractionResponded:
            pass
        except Exception:
            pass

    async def create_gift_code(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        self.settings_cursor.execute("SELECT 1 FROM admin WHERE id = ?", (interaction.user.id,))
        if not self.settings_cursor.fetchone():
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.create_not_authorized', lang)}",
                ephemeral=True
            )
            return

        modal = CreateGiftCodeModal(self, lang)
        try:
            await interaction.response.send_modal(modal)
        except Exception as e:
            self.logger.exception(f"Error showing modal: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('gift.error.create_form', lang)}",
                    ephemeral=True
                )

    async def list_gift_codes(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        self.cursor.execute("""
            SELECT 
                gc.giftcode,
                gc.date,
                COUNT(DISTINCT ugc.fid) as used_count
            FROM gift_codes gc
            LEFT JOIN user_giftcodes ugc ON gc.giftcode = ugc.giftcode
            WHERE gc.validation_status = 'validated'
            GROUP BY gc.giftcode
            ORDER BY gc.date DESC
        """)
        
        codes = self.cursor.fetchall()
        
        if not codes:
            await interaction.response.send_message(
                t("gift.list.none", lang),
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{theme.giftIcon} {t('gift.list.title', lang)}",
            description=t("gift.list.description", lang),
            color=theme.emColor1
        )

        for code, date, used_count in codes:
            embed.add_field(
                name=t("gift.list.code_label", lang, code=code),
                value=t("gift.list.code_value", lang, date=date, used=used_count),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def delete_gift_code(self, interaction: discord.Interaction):
        try:
            lang = _get_lang(interaction)
            settings_conn = sqlite3.connect('db/settings.sqlite')
            settings_cursor = settings_conn.cursor()
            
            settings_cursor.execute("""
                SELECT 1 FROM admin 
                WHERE id = ? AND is_initial = 1
            """, (interaction.user.id,))
            
            is_admin = settings_cursor.fetchone()
            settings_cursor.close()
            settings_conn.close()

            if not is_admin:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.delete.unauthorized_title', lang)}",
                        description=t("gift.delete.unauthorized_body", lang),
                        color=theme.emColor2
                    ),
                    ephemeral=True
                )
                return

            self.cursor.execute("""
                SELECT 
                    gc.giftcode,
                    gc.date,
                    gc.validation_status,
                    COUNT(DISTINCT ugc.fid) as used_count
                FROM gift_codes gc
                LEFT JOIN user_giftcodes ugc ON gc.giftcode = ugc.giftcode
                GROUP BY gc.giftcode, gc.date, gc.validation_status
                ORDER BY gc.date ASC
            """)
            
            codes = self.cursor.fetchall()
            
            if not codes:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.delete.none_title', lang)}",
                        description=t("gift.delete.none_body", lang),
                        color=theme.emColor2
                    ),
                    ephemeral=True
                )
                return

            # Discord limits Select menus to 25 options
            total_codes = len(codes)
            codes_to_show = codes[:25] if total_codes > 25 else codes
            
            select_options = []
            for code, date, validation_status, used_count in codes_to_show:
                if validation_status == 'validated':
                    status_display = f"{theme.verifiedIcon} {t('gift.delete.status_valid', lang)}"
                elif validation_status == 'invalid':
                    status_display = f"{theme.deniedIcon} {t('gift.delete.status_invalid', lang)}"
                elif validation_status == 'pending':
                    status_display = f"{theme.warnIcon} {t('gift.delete.status_pending', lang)}"
                else:
                    status_display = f"{theme.infoIcon} {t('gift.delete.status_unknown', lang)}"
                
                select_options.append(
                    discord.SelectOption(
                        label=f"Code: {code}",
                        description=t(
                            "gift.delete.option_desc",
                            lang,
                            status=status_display,
                            date=date,
                            used=used_count
                        ),
                        value=code
                    )
                )
            
            # Handling for 0 codes to avoid errors
            if not select_options:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.delete.none_title', lang)}",
                        description=t("gift.delete.none_body", lang),
                        color=theme.emColor2
                    ),
                    ephemeral=True
                )
                return
            
            select = discord.ui.Select(
                placeholder=t("gift.delete.select_placeholder", lang),
                options=select_options
            )

            async def select_callback(select_interaction):
                selected_code = select_interaction.data["values"][0]
                
                confirm = discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label=t("gift.delete.confirm_label", lang),
                    custom_id="confirm"
                )
                cancel = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label=t("gift.button.cancel", lang),
                    custom_id="cancel"
                )

                async def button_callback(button_interaction):
                    try:
                        if button_interaction.data.get('custom_id') == "confirm":
                            try:
                                self.cursor.execute("DELETE FROM gift_codes WHERE giftcode = ?", (selected_code,))
                                self.cursor.execute("DELETE FROM user_giftcodes WHERE giftcode = ?", (selected_code,))
                                self.conn.commit()
                                
                                success_embed = discord.Embed(
                                    title=f"{theme.verifiedIcon} {t('gift.delete.success_title', lang)}",
                                    description=(
                                        f"**{t('gift.delete.details', lang)}**\n"
                                        f"{theme.upperDivider}\n"
                                        f"{theme.giftIcon} **{t('gift.delete.code_label', lang)}** `{selected_code}`\n"
                                        f"{theme.userIcon} **{t('gift.delete.deleted_by', lang)}** {button_interaction.user.mention}\n"
                                        f"{theme.timeIcon} **{t('gift.delete.time', lang)}** <t:{int(datetime.now().timestamp())}:R>\n"
                                        f"{theme.lowerDivider}\n"
                                    ),
                                    color=theme.emColor3
                                )
                                
                                await button_interaction.response.edit_message(
                                    embed=success_embed,
                                    view=None
                                )
                                
                            except Exception as e:
                                await button_interaction.response.send_message(
                                    f"{theme.deniedIcon} {t('gift.delete.error_deleting', lang)}",
                                    ephemeral=True
                                )

                        else:
                            cancel_embed = discord.Embed(
                                title=f"{theme.deniedIcon} {t('gift.delete.cancelled_title', lang)}",
                                description=t("gift.delete.cancelled_body", lang),
                                color=theme.emColor2
                            )
                            await button_interaction.response.edit_message(
                                embed=cancel_embed,
                                view=None
                            )

                    except Exception as e:
                        self.logger.exception(f"Button callback error: {str(e)}")
                        try:
                            await button_interaction.response.send_message(
                                f"{theme.deniedIcon} {t('gift.error.process_request', lang)}",
                                ephemeral=True
                            )
                        except:
                            await button_interaction.followup.send(
                                f"{theme.deniedIcon} {t('gift.error.process_request', lang)}",
                                ephemeral=True
                            )

                confirm.callback = button_callback
                cancel.callback = button_callback

                confirm_view = discord.ui.View()
                confirm_view.add_item(confirm)
                confirm_view.add_item(cancel)

                confirmation_embed = discord.Embed(
                    title=f"{theme.warnIcon} {t('gift.delete.confirm_title', lang)}",
                    description=(
                        f"**{t('gift.delete.details', lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.giftIcon} **{t('gift.delete.selected_code', lang)}** `{selected_code}`\n"
                        f"{theme.warnIcon} **{t('gift.delete.warning', lang)}** {t('gift.delete.warning_body', lang)}\n"
                        f"{theme.lowerDivider}\n"
                    ),
                    color=discord.Color.yellow()
                )

                await select_interaction.response.edit_message(
                    embed=confirmation_embed,
                    view=confirm_view
                )

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)

            # Build description with truncation notice if needed
            description_text = (
                f"**{t('gift.delete.instructions', lang)}**\n"
                f"{theme.upperDivider}\n"
                f"{theme.num1Icon} {t('gift.delete.step1', lang)}\n"
                f"{theme.num2Icon} {t('gift.delete.step2', lang)}\n"
                f"{theme.num3Icon} {t('gift.delete.step3', lang)}\n"
                f"{theme.lowerDivider}\n"
            )
            
            if total_codes > 25:
                description_text += (
                    f"\n{theme.warnIcon} **{t('gift.delete.note', lang, total=total_codes)}**\n"
                    f"{t('gift.delete.note_oldest', lang)}\n"
                    f"{t('gift.delete.note_delete_order', lang)}"
                )
            
            initial_embed = discord.Embed(
                title=f"{theme.trashIcon} {t('gift.delete.title', lang)}",
                description=description_text,
                color=theme.emColor1
            )

            await interaction.response.send_message(
                embed=initial_embed,
                view=view,
                ephemeral=True
            )

        except Exception as e:
            self.logger.exception(f"Delete gift code error: {str(e)}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.process_request', _get_lang(interaction))}",
                ephemeral=True
            )

    async def delete_gift_channel(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        admin_info = await self.get_admin_info(interaction.user.id)
        if not admin_info:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.not_authorized', lang)}",
                ephemeral=True
            )
            return

        available_alliances = await self.get_available_alliances(interaction)
        if not available_alliances:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.error.no_alliances_title', lang)}",
                    description=t("gift.error.no_alliances_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return

        self.cursor.execute("SELECT alliance_id, channel_id FROM giftcode_channel")
        current_channels = dict(self.cursor.fetchall())

        alliances_with_counts = []
        for alliance_id, name in available_alliances:
            if alliance_id in current_channels:
                with sqlite3.connect('db/users.sqlite') as users_db:
                    cursor = users_db.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                    member_count = cursor.fetchone()[0]
                    alliances_with_counts.append((alliance_id, name, member_count))

        if not alliances_with_counts:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.channel.none_set_title', lang)}",
                    description=t("gift.channel.none_set_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return

        remove_embed = discord.Embed(
            title=f"{theme.trashIcon} {t('gift.channel.remove_title', lang)}",
            description=(
                f"{t('gift.channel.remove_select', lang)}\n\n"
                f"**{t('gift.channel.current_channels', lang)}**\n"
                f"{theme.upperDivider}\n"
                f"{t('gift.channel.select_from_list', lang)}\n"
            ),
            color=theme.emColor2
        )

        view = AllianceSelectView(alliances_with_counts, self, context="giftcode")

        async def alliance_callback(select_interaction: discord.Interaction, alliance_id=None):
            try:
                if alliance_id is None:
                    alliance_id = int(view.current_select.values[0])

                self.cursor.execute("SELECT channel_id FROM giftcode_channel WHERE alliance_id = ?", (alliance_id,))
                channel_id = self.cursor.fetchone()[0]
                
                alliance_name = next((name for aid, name in available_alliances if aid == alliance_id), "Unknown Alliance")
                if alliance_name == "Unknown Alliance":
                    alliance_name = t("gift.redeem.unknown", lang)
                
                confirm_embed = discord.Embed(
                    title=f"{theme.warnIcon} {t('gift.channel.confirm_remove_title', lang)}",
                    description=(
                        f"{t('gift.channel.confirm_remove_body', lang)}\n\n"
                        f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                        f"{theme.editListIcon} **{t('gift.channel.channel_label', lang)}** <#{channel_id}>\n\n"
                        f"{t('gift.channel.warning_body', lang)}"
                    ),
                    color=discord.Color.yellow()
                )

                confirm_view = discord.ui.View()
                
                async def confirm_callback(button_interaction: discord.Interaction):
                    try:
                        self.cursor.execute("DELETE FROM giftcode_channel WHERE alliance_id = ?", (alliance_id,))
                        self.conn.commit()

                        success_embed = discord.Embed(
                            title=f"{theme.verifiedIcon} {t('gift.channel.removed_title', lang)}",
                            description=(
                                f"{t('gift.channel.removed_body', lang)}\n\n"
                                f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                                f"{theme.editListIcon} **{t('gift.channel.channel_label', lang)}** <#{channel_id}>"
                            ),
                            color=theme.emColor3
                        )

                        await button_interaction.response.edit_message(
                            embed=success_embed,
                            view=None
                        )

                    except Exception as e:
                        self.logger.exception(f"Error removing gift code channel: {e}")
                        await button_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('gift.channel.remove_error', lang)}",
                            ephemeral=True
                        )

                async def cancel_callback(button_interaction: discord.Interaction):
                    cancel_embed = discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.channel.cancelled_title', lang)}",
                        description=t("gift.channel.cancelled_body", lang),
                        color=theme.emColor2
                    )
                    await button_interaction.response.edit_message(
                        embed=cancel_embed,
                        view=None
                    )

                confirm_button = discord.ui.Button(
                    label=t("gift.button.confirm", lang),
                    emoji=f"{theme.verifiedIcon}",
                    style=discord.ButtonStyle.danger,
                    custom_id="confirm_remove"
                )
                confirm_button.callback = confirm_callback

                cancel_button = discord.ui.Button(
                    label=t("gift.button.cancel", lang),
                    emoji=f"{theme.deniedIcon}",
                    style=discord.ButtonStyle.secondary,
                    custom_id="cancel_remove"
                )
                cancel_button.callback = cancel_callback

                confirm_view.add_item(confirm_button)
                confirm_view.add_item(cancel_button)

                if not select_interaction.response.is_done():
                    await select_interaction.response.edit_message(
                        embed=confirm_embed,
                        view=confirm_view
                    )
                else:
                    await select_interaction.message.edit(
                        embed=confirm_embed,
                        view=confirm_view
                    )

            except Exception as e:
                self.logger.exception(f"Error in alliance selection: {e}")
                if not select_interaction.response.is_done():
                    await select_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('gift.error.process_request', lang)}",
                        ephemeral=True
                    )
                else:
                    await select_interaction.followup.send(
                        f"{theme.deniedIcon} {t('gift.error.process_request', lang)}",
                        ephemeral=True
                    )

        view.callback = alliance_callback

        await interaction.response.send_message(
            embed=remove_embed,
            view=view,
            ephemeral=True
        )
    
    async def delete_gift_channel_for_alliance(self, interaction: discord.Interaction, alliance_id: int):
        """Remove gift code channel setting for a specific alliance"""
        try:
            lang = _get_lang(interaction)
            # Check if channel exists for this alliance
            self.cursor.execute("SELECT channel_id FROM giftcode_channel WHERE alliance_id = ?", (alliance_id,))
            result = self.cursor.fetchone()
            
            if not result:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('gift.channel.none_for_alliance', lang)}",
                    ephemeral=True
                )
                return
            
            channel_id = result[0]
            
            # Get alliance name
            available_alliances = await self.get_available_alliances(interaction)
            alliance_name = next((name for aid, name in available_alliances if aid == alliance_id), "Unknown Alliance")
            if alliance_name == "Unknown Alliance":
                alliance_name = t("gift.redeem.unknown", lang)
            
            # Create confirmation embed
            confirm_embed = discord.Embed(
                title=f"{theme.warnIcon} {t('gift.channel.confirm_remove_title', lang)}",
                description=(
                    f"{t('gift.channel.confirm_setting_body', lang)}\n\n"
                    f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                    f"{theme.editListIcon} **{t('gift.channel.current_channel_label', lang)}** <#{channel_id}>\n\n"
                    f"{t('gift.channel.warning_body', lang)}"
                ),
                color=discord.Color.yellow()
            )
            
            # Create confirmation buttons
            confirm_view = discord.ui.View()
            
            async def confirm_removal(button_interaction: discord.Interaction):
                try:
                    self.cursor.execute("DELETE FROM giftcode_channel WHERE alliance_id = ?", (alliance_id,))
                    self.conn.commit()
                    
                    success_embed = discord.Embed(
                        title=f"{theme.verifiedIcon} {t('gift.channel.setting_removed_title', lang)}",
                        description=(
                            f"{t('gift.channel.setting_removed_body', lang)}\n\n"
                            f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                            f"{theme.editListIcon} **{t('gift.channel.channel_label', lang)}** <#{channel_id}>\n\n"
                            f"{t('gift.channel.setting_removed_hint', lang)}"
                        ),
                        color=theme.emColor3
                    )
                    
                    await button_interaction.response.edit_message(
                        embed=success_embed,
                        view=None
                    )
                    
                except Exception as e:
                    self.logger.exception(f"Error removing gift code channel for alliance {alliance_id}: {e}")
                    await button_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('gift.channel.remove_error', lang)}",
                        ephemeral=True
                    )
            
            async def cancel_removal(button_interaction: discord.Interaction):
                cancel_embed = discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.channel.cancelled_title', lang)}",
                    description=t("gift.channel.cancelled_body", lang),
                    color=theme.emColor2
                )
                await button_interaction.response.edit_message(
                    embed=cancel_embed,
                    view=None
                )
            
            confirm_button = discord.ui.Button(
                label=t("gift.channel.remove_setting_button", lang),
                emoji=f"{theme.trashIcon}",
                style=discord.ButtonStyle.danger
            )
            confirm_button.callback = confirm_removal

            cancel_button = discord.ui.Button(
                label=t("gift.button.cancel", lang),
                emoji=f"{theme.deniedIcon}",
                style=discord.ButtonStyle.secondary
            )
            cancel_button.callback = cancel_removal
            
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)
            
            await interaction.response.send_message(
                embed=confirm_embed,
                view=confirm_view,
                ephemeral=True
            )
            
        except Exception as e:
            self.logger.exception(f"Error in delete_gift_channel_for_alliance: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.channel.remove_request_error', _get_lang(interaction))}",
                ephemeral=True
            )

    async def show_settings_menu(self, interaction: discord.Interaction):
        """Show unified settings menu with all configuration options."""
        lang = _get_lang(interaction)
        admin_info = await self.get_admin_info(interaction.user.id)
        if not admin_info:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.not_authorized', lang)}",
                ephemeral=True
            )
            return

        is_global = admin_info[1] == 1

        settings_embed = discord.Embed(
            title=f"{theme.settingsIcon} {t('gift.settings.title', lang)}",
            description=(
                f"{theme.upperDivider}\n"
                f"{theme.announceIcon} **{t('gift.settings.channel_mgmt', lang)}**\n"
                f"└ {t('gift.settings.channel_mgmt_desc', lang)}\n\n"
                f"{theme.giftIcon} **{t('gift.settings.auto_redemption', lang)}**\n"
                f"└ {t('gift.settings.auto_redemption_desc', lang)}\n\n"
                f"{theme.chartIcon} **{t('gift.settings.priority', lang)}**\n"
                f"└ {t('gift.settings.priority_desc', lang)}\n\n"
                f"{theme.searchIcon} **{t('gift.settings.history_scan', lang)}**\n"
                f"└ {t('gift.settings.history_scan_desc', lang)}\n\n"
                f"{theme.settingsIcon} **{t('gift.settings.captcha', lang)}**\n"
                f"└ {t('gift.settings.captcha_desc', lang)}\n"
                f"{theme.lowerDivider}"
            ),
            color=theme.emColor1
        )

        settings_view = SettingsMenuView(self, is_global, lang)

        await interaction.response.edit_message(
            embed=settings_embed,
            view=settings_view
        )
    
    async def manage_channel_settings(self, interaction: discord.Interaction):
        """Manage gift code channel settings including channel configuration and historical scanning."""
        lang = _get_lang(interaction)
        admin_info = await self.get_admin_info(interaction.user.id)
        if not admin_info:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.not_authorized', lang)}",
                ephemeral=True
            )
            return
        
        available_alliances = await self.get_available_alliances(interaction)
        if not available_alliances:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.error.no_alliances_title', lang)}",
                    description=t("gift.error.no_alliances_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return
        
        # Get alliances with configured channels
        self.cursor.execute("""
            SELECT alliance_id, channel_id 
            FROM giftcode_channel
            ORDER BY alliance_id
        """)
        channel_configs = self.cursor.fetchall()
        
        alliance_names = {aid: name for aid, name in available_alliances}
        main_embed = discord.Embed(
            title=f"{theme.settingsIcon} {t('gift.channel.manage_title', lang)}",
            description=t("gift.channel.manage_desc", lang),
            color=theme.emColor1
        )
        
        # Show configured channels
        if channel_configs:
            configured_text = ""
            for alliance_id, channel_id in channel_configs:
                if alliance_id in alliance_names:
                    alliance_name = alliance_names[alliance_id]
                    channel = self.bot.get_channel(channel_id)
                    # Avoid nested f-strings for Python 3.9+ compatibility
                    if channel:
                        channel_name = f"<#{channel_id}>"
                    else:
                        channel_name = f"Unknown Channel ({channel_id})"
                    configured_text += f"{theme.allianceIcon} **{alliance_name}**\n{theme.announceIcon} Channel: {channel_name}\n\n"
            
            if configured_text:
                main_embed.add_field(
                    name=f"{theme.listIcon} {t('gift.channel.current_configs', lang)}",
                    value=configured_text,
                    inline=False
                )
        else:
            main_embed.add_field(
                name=f"{theme.listIcon} {t('gift.channel.current_configs', lang)}",
                value=t("gift.channel.no_configs", lang),
                inline=False
            )
        
        main_view = discord.ui.View(timeout=300)
        
        # Configure/Change Channel button
        config_button = discord.ui.Button(
            label=t("gift.channel.configure_button", lang),
            style=discord.ButtonStyle.primary,
            emoji=f"{theme.announceIcon}"
        )
        
        async def config_callback(config_interaction: discord.Interaction):
            # Show alliance selection for configuration
            alliance_embed = discord.Embed(
                title=f"{theme.announceIcon} {t('gift.channel.select_config_title', lang)}",
                description=t("gift.channel.select_config_desc", lang),
                color=theme.emColor1
            )
            
            alliance_options = []
            for alliance_id, name in available_alliances:
                # Check if already configured
                current_channel_id = None
                for aid, cid in channel_configs:
                    if aid == alliance_id:
                        current_channel_id = cid
                        break
                
                if current_channel_id:
                    # Get the actual channel object to display the name
                    channel = self.bot.get_channel(current_channel_id)
                    if channel:
                        description = t("gift.channel.current_channel_named", lang, name=channel.name)
                    else:
                        description = t("gift.channel.current_channel_unknown", lang, channel_id=current_channel_id)
                else:
                    description = t("gift.channel.not_configured", lang)
                
                alliance_options.append(discord.SelectOption(
                    label=name,
                    value=str(alliance_id),
                    description=description,
                    emoji=theme.allianceIcon
                ))
            
            alliance_select = discord.ui.Select(
                placeholder=t("gift.channel.select_config_placeholder", lang),
                options=alliance_options,
                min_values=1,
                max_values=1
            )
            
            async def alliance_select_callback(alliance_interaction: discord.Interaction):
                alliance_id = int(alliance_select.values[0])
                alliance_name = alliance_names[alliance_id]
                
                channel_embed = discord.Embed(
                    title=f"{theme.announceIcon} {t('gift.channel.configure_for', lang, alliance=alliance_name)}",
                    description=t("gift.channel.select_channel", lang),
                    color=theme.emColor1
                )
                
                # Using PaginatedChannelView from alliance.py for channel selection
                from .alliance import PaginatedChannelView
                
                async def channel_callback(channel_interaction: discord.Interaction):
                    try:
                        channel_id = int(channel_interaction.data["values"][0])
                        
                        self.cursor.execute("""
                            INSERT OR REPLACE INTO giftcode_channel (alliance_id, channel_id)
                            VALUES (?, ?)
                        """, (alliance_id, channel_id))
                        self.conn.commit()
                        
                        success_embed = discord.Embed(
                            title=f"{theme.verifiedIcon} {t('gift.channel.configured_title', lang)}",
                            description=(
                                f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                                f"{theme.announceIcon} **{t('gift.channel.channel_label', lang)}** <#{channel_id}>\n\n"
                                f"{theme.verifiedIcon} {t('gift.channel.configured_body', lang)}"
                            ),
                            color=theme.emColor3
                        )
                        
                        await channel_interaction.response.edit_message(
                            embed=success_embed,
                            view=None
                        )
                        
                    except Exception as e:
                        self.logger.exception(f"Error configuring channel: {e}")
                        await channel_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('gift.channel.configure_error', lang)}",
                            ephemeral=True
                        )
                
                channel_view = PaginatedChannelView(
                    alliance_interaction.guild.text_channels,
                    channel_callback
                )
                
                await alliance_interaction.response.edit_message(
                    embed=channel_embed,
                    view=channel_view
                )
            
            alliance_select.callback = alliance_select_callback
            alliance_view = discord.ui.View(timeout=300)
            alliance_view.add_item(alliance_select)
            
            await config_interaction.response.edit_message(
                embed=alliance_embed,
                view=alliance_view
            )
        
        config_button.callback = config_callback
        main_view.add_item(config_button)
        
        
        # Remove Channel button (only show if there are configured channels)
        if channel_configs:
            remove_button = discord.ui.Button(
                label=t("gift.channel.remove_button", lang),
                style=discord.ButtonStyle.danger,
                emoji=f"{theme.trashIcon}"
            )
            
            async def remove_callback(remove_interaction: discord.Interaction):
                # Show alliance selection for removal
                remove_embed = discord.Embed(
                    title=f"{theme.trashIcon} {t('gift.channel.select_remove_title', lang)}",
                    description=t("gift.channel.select_remove_desc", lang),
                    color=theme.emColor2
                )
                
                remove_options = []
                for alliance_id, channel_id in channel_configs:
                    if alliance_id in alliance_names:
                        name = alliance_names[alliance_id]
                        remove_options.append(discord.SelectOption(
                            label=name,
                            value=str(alliance_id),
                            description=t("gift.channel.remove_option_desc", lang, channel_id=channel_id),
                            emoji=f"{theme.trashIcon}"
                        ))
                
                remove_select = discord.ui.Select(
                    placeholder=t("gift.channel.select_remove_placeholder", lang),
                    options=remove_options,
                    min_values=1,
                    max_values=1
                )
                
                async def remove_select_callback(remove_select_interaction: discord.Interaction):
                    alliance_id = int(remove_select.values[0])
                    alliance_name = alliance_names[alliance_id]
                    
                    # Get channel info for confirmation
                    self.cursor.execute("SELECT channel_id FROM giftcode_channel WHERE alliance_id = ?", (alliance_id,))
                    result = self.cursor.fetchone()
                    if not result:
                        await remove_select_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('gift.channel.config_not_found', lang)}",
                            ephemeral=True
                        )
                        return
                    
                    channel_id = result[0]
                    
                    # Confirmation embed
                    confirm_embed = discord.Embed(
                        title=f"{theme.warnIcon} {t('gift.channel.confirm_remove_title', lang)}",
                        description=(
                            f"{t('gift.channel.confirm_config_body', lang)}\n\n"
                            f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                            f"{theme.announceIcon} **{t('gift.channel.channel_label', lang)}** <#{channel_id}>\n\n"
                            f"{theme.warnIcon} **{t('gift.channel.warning', lang)}** {t('gift.channel.warning_stop', lang)}"
                        ),
                        color=theme.emColor2
                    )
                    
                    confirm_view = discord.ui.View(timeout=60)
                    
                    confirm_button = discord.ui.Button(
                        label=t("gift.channel.confirm_remove_button", lang),
                        style=discord.ButtonStyle.danger,
                        emoji=f"{theme.verifiedIcon}"
                    )
                    
                    cancel_button = discord.ui.Button(
                        label=t("gift.button.cancel", lang),
                        style=discord.ButtonStyle.secondary,
                        emoji=f"{theme.deniedIcon}"
                    )
                    
                    async def confirm_remove_callback(confirm_interaction: discord.Interaction):
                        try:
                            self.cursor.execute("DELETE FROM giftcode_channel WHERE alliance_id = ?", (alliance_id,))
                            self.conn.commit()
                            
                            success_embed = discord.Embed(
                                title=f"{theme.verifiedIcon} {t('gift.channel.config_removed_title', lang)}",
                                description=(
                                    f"{t('gift.channel.config_removed_body', lang)}\n\n"
                                    f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                                    f"{theme.announceIcon} **{t('gift.channel.channel_label', lang)}** <#{channel_id}>"
                                ),
                                color=theme.emColor3
                            )
                            
                            await confirm_interaction.response.edit_message(
                                embed=success_embed,
                                view=None
                            )
                            
                        except Exception as e:
                            self.logger.exception(f"Error removing channel configuration: {e}")
                            await confirm_interaction.response.send_message(
                                f"{theme.deniedIcon} {t('gift.channel.remove_error', lang)}: {str(e)}",
                                ephemeral=True
                            )
                    
                    async def cancel_remove_callback(cancel_interaction: discord.Interaction):
                        await self.manage_channel_settings(cancel_interaction)
                    
                    confirm_button.callback = confirm_remove_callback
                    cancel_button.callback = cancel_remove_callback
                    confirm_view.add_item(confirm_button)
                    confirm_view.add_item(cancel_button)
                    
                    await remove_select_interaction.response.edit_message(
                        embed=confirm_embed,
                        view=confirm_view
                    )
                
                remove_select.callback = remove_select_callback
                remove_view = discord.ui.View(timeout=300)
                remove_view.add_item(remove_select)
                
                await remove_interaction.response.edit_message(
                    embed=remove_embed,
                    view=remove_view
                )
            
            remove_button.callback = remove_callback
            main_view.add_item(remove_button)
        
        await interaction.response.send_message(
            embed=main_embed,
            view=main_view,
            ephemeral=True
        )

    async def channel_history_scan(self, interaction: discord.Interaction):
        """Perform on-demand historical scan of gift code channels."""
        lang = _get_lang(interaction)
        admin_info = await self.get_admin_info(interaction.user.id)
        if not admin_info:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.not_authorized', lang)}",
                ephemeral=True
            )
            return
        
        available_alliances = await self.get_available_alliances(interaction)
        if not available_alliances:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.error.no_alliances_title', lang)}",
                    description=t("gift.error.no_alliances_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return
        
        # Get alliances with configured channels
        self.cursor.execute("""
            SELECT alliance_id, channel_id 
            FROM giftcode_channel
            ORDER BY alliance_id
        """)
        channel_configs = self.cursor.fetchall()
        
        if not channel_configs:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.scan.no_channels_title', lang)}",
                    description=t("gift.scan.no_channels_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return
        
        alliance_names = {aid: name for aid, name in available_alliances}
        
        # Filter to only show alliances the user has access to
        available_alliance_ids = [aid for aid, _ in available_alliances]
        accessible_configs = []
        for alliance_id, channel_id in channel_configs:
            if alliance_id in available_alliance_ids:
                accessible_configs.append((alliance_id, channel_id))
        
        if not accessible_configs:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.scan.no_access_title', lang)}",
                    description=t("gift.scan.no_access_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return
        
        # Create alliance selection menu
        scan_embed = discord.Embed(
            title=f"{theme.searchIcon} {t('gift.scan.title', lang)}",
            description=t("gift.scan.select_alliance", lang),
            color=theme.emColor1
        )
        
        alliance_options = []
        for alliance_id, channel_id in accessible_configs:
            alliance_name = alliance_names[alliance_id]
            channel = self.bot.get_channel(channel_id)
            # Avoid nested f-strings for Python 3.9+ compatibility
            if channel:
                channel_display = f"#{channel.name}"
            else:
                channel_display = f"Unknown Channel ({channel_id})"

            alliance_options.append(discord.SelectOption(
                label=alliance_name,
                value=str(alliance_id),
                description=t("gift.scan.option_desc", lang, channel=channel_display),
                emoji=theme.searchIcon
            ))
        
        alliance_select = discord.ui.Select(
            placeholder=t("gift.scan.select_placeholder", lang),
            options=alliance_options,
            min_values=1,
            max_values=1
        )
        
        async def alliance_select_callback(select_interaction: discord.Interaction):
            alliance_id = int(alliance_select.values[0])
            alliance_name = alliance_names[alliance_id]
            
            # Get fresh channel info from database (in case it was recently changed)
            self.cursor.execute("""
                SELECT channel_id FROM giftcode_channel 
                WHERE alliance_id = ?
            """, (alliance_id,))
            result = self.cursor.fetchone()
            
            if not result:
                await select_interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.scan.no_channel_title', lang)}",
                        description=t("gift.scan.no_channel_body", lang, alliance=alliance_name),
                        color=theme.emColor2
                    ),
                    ephemeral=True
                )
                return
            
            channel_id = result[0]
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await select_interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.scan.channel_not_found_title', lang)}",
                        description=t("gift.scan.channel_not_found_body", lang),
                        color=theme.emColor2
                    ),
                    ephemeral=True
                )
                return
            
            # Create confirmation dialog
            confirm_embed = discord.Embed(
                title=f"{theme.searchIcon} {t('gift.scan.confirm_title', lang)}",
                description=(
                    f"**{t('gift.scan.details', lang)}**\n"
                    f"{theme.upperDivider}\n"
                    f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                    f"{theme.announceIcon} **{t('gift.channel.channel_label', lang)}** #{channel.name}\n"
                    f"{theme.chartIcon} **{t('gift.scan.limit', lang)}** {t('gift.scan.limit_value', lang)}\n\n"
                    f"{theme.warnIcon} **{t('gift.scan.note', lang)}** {t('gift.scan.note_body', lang)}\n\n"
                    f"{t('gift.scan.proceed', lang)}"
                ),
                color=discord.Color.yellow()
            )
            
            confirm_view = discord.ui.View(timeout=60)
            
            confirm_button = discord.ui.Button(
                label=t("gift.scan.start_button", lang),
                style=discord.ButtonStyle.success,
                emoji=f"{theme.verifiedIcon}"
            )
            
            cancel_button = discord.ui.Button(
                label=t("gift.button.cancel", lang),
                style=discord.ButtonStyle.secondary,
                emoji=f"{theme.deniedIcon}"
            )
            
            async def confirm_scan_callback(confirm_interaction: discord.Interaction):
                await confirm_interaction.response.defer()
                
                # Perform the historical scan
                scan_results = await self.scan_historical_messages(channel, alliance_id)
                
                # Build detailed results summary
                total_found = scan_results.get('total_codes_found', 0)
                messages_scanned = scan_results.get('messages_scanned', 0)
                
                # Count validation results
                new_valid = len([code for code, is_valid in scan_results.get('validation_results', {}).items() if is_valid])
                new_invalid = len([code for code, is_valid in scan_results.get('validation_results', {}).items() if not is_valid])
                existing_valid = len(scan_results.get('existing_valid', []))
                existing_invalid = len(scan_results.get('existing_invalid', []))
                existing_pending = len(scan_results.get('existing_pending', []))
                
                results_text = f"**Scan Complete**\n"
                results_text += f"{theme.upperDivider}\n"
                results_text += f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                results_text += f"{theme.announceIcon} **{t('gift.channel.channel_label', lang)}** #{channel.name}\n"
                results_text += f"{theme.chartIcon} **{t('gift.scan.messages_scanned', lang)}** {messages_scanned}\n"
                results_text += f"{theme.giftIcon} **{t('gift.scan.total_found', lang)}** {total_found}\n\n"
                
                if total_found > 0:
                    results_text += f"**{t('gift.scan.validation_results', lang)}**\n"
                    if new_valid > 0:
                        results_text += f"{theme.verifiedIcon} {t('gift.scan.new_valid', lang)} {new_valid}\n"
                    if new_invalid > 0:
                        results_text += f"{theme.deniedIcon} {t('gift.scan.new_invalid', lang)} {new_invalid}\n"
                    if existing_valid > 0:
                        results_text += f"{theme.verifiedIcon} {t('gift.scan.prev_valid', lang)} {existing_valid}\n"
                    if existing_invalid > 0:
                        results_text += f"{theme.deniedIcon} {t('gift.scan.prev_invalid', lang)} {existing_invalid}\n"
                    if existing_pending > 0:
                        results_text += f"{theme.warnIcon} {t('gift.scan.pending', lang)} {existing_pending}\n"
                    
                    results_text += f"\n{theme.editListIcon} **{t('gift.scan.note', lang)}** {t('gift.scan.summary_posted', lang, channel=channel.name)}"
                else:
                    results_text += t("gift.scan.none_found", lang)
                
                await confirm_interaction.edit_original_response(
                    embed=discord.Embed(
                        title=f"{theme.searchIcon} {t('gift.scan.complete_title', lang)}",
                        description=results_text,
                        color=theme.emColor3
                    ),
                    view=None
                )
            
            async def cancel_scan_callback(cancel_interaction: discord.Interaction):
                await cancel_interaction.response.edit_message(
                    embed=discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.scan.cancelled_title', lang)}",
                        description=t("gift.scan.cancelled_body", lang),
                        color=theme.emColor2
                    ),
                    view=None
                )
            
            confirm_button.callback = confirm_scan_callback
            cancel_button.callback = cancel_scan_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)
            
            await select_interaction.response.edit_message(
                embed=confirm_embed,
                view=confirm_view
            )
        
        alliance_select.callback = alliance_select_callback
        alliance_view = discord.ui.View(timeout=300)
        alliance_view.add_item(alliance_select)
        
        await interaction.response.send_message(
            embed=scan_embed,
            view=alliance_view,
            ephemeral=True
        )

    async def setup_giftcode_auto(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        admin_info = await self.get_admin_info(interaction.user.id)
        if not admin_info:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.not_authorized', lang)}",
                ephemeral=True
            )
            return

        available_alliances = await self.get_available_alliances(interaction)
        if not available_alliances:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.error.no_alliances_title', lang)}",
                    description=t("gift.error.no_alliances_body", lang),
                    color=theme.emColor2
                ),
                ephemeral=True
            )
            return

        self.cursor.execute("SELECT alliance_id, status FROM giftcodecontrol")
        current_status = dict(self.cursor.fetchall())

        alliances_with_counts = []
        for alliance_id, name in available_alliances:
            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                member_count = cursor.fetchone()[0]
                alliances_with_counts.append((alliance_id, name, member_count))

        auto_gift_embed = discord.Embed(
            title=f"{theme.settingsIcon} {t('gift.auto.title', lang)}",
            description=(
                f"{t('gift.auto.select_alliance', lang)}\n\n"
                f"**{t('gift.redeem.alliance_list', lang)}**\n"
                f"{theme.upperDivider}\n"
                f"{t('gift.redeem.select_alliance_hint', lang)}\n"
            ),
            color=theme.emColor1
        )

        view = AllianceSelectView(alliances_with_counts, self, context="giftcode")

        view.current_select.options.insert(0, discord.SelectOption(
            label=t("gift.auto.enable_all", lang),
            value="enable_all",
            description=t("gift.auto.enable_all_desc", lang),
            emoji=f"{theme.verifiedIcon}"
        ))

        view.current_select.options.insert(1, discord.SelectOption(
            label=t("gift.auto.disable_all", lang),
            value="disable_all",
            description=t("gift.auto.disable_all_desc", lang),
            emoji=f"{theme.deniedIcon}"
        ))

        async def alliance_callback(select_interaction: discord.Interaction, alliance_id=None):
            try:
                if alliance_id is not None:
                    selected_value = str(alliance_id)
                else:
                    selected_value = view.current_select.values[0]
                
                if selected_value in ["enable_all", "disable_all"]:
                    status = 1 if selected_value == "enable_all" else 0

                    for alliance_id, _, _ in alliances_with_counts:
                        if status == 1:
                            # When enabling, assign next available priority
                            self.cursor.execute("SELECT COALESCE(MAX(priority), 0) + 1 FROM giftcodecontrol")
                            next_priority = self.cursor.fetchone()[0]
                            self.cursor.execute(
                                """
                                INSERT INTO giftcodecontrol (alliance_id, status, priority)
                                VALUES (?, ?, ?)
                                ON CONFLICT(alliance_id)
                                DO UPDATE SET status = excluded.status,
                                    priority = CASE WHEN giftcodecontrol.priority = 0 THEN excluded.priority ELSE giftcodecontrol.priority END
                                """,
                                (alliance_id, status, next_priority)
                            )
                        else:
                            # When disabling, keep existing priority
                            self.cursor.execute(
                                """
                                INSERT INTO giftcodecontrol (alliance_id, status)
                                VALUES (?, ?)
                                ON CONFLICT(alliance_id)
                                DO UPDATE SET status = excluded.status
                                """,
                                (alliance_id, status)
                            )
                    self.conn.commit()

                    status_text = t("gift.auto.enabled", lang) if status == 1 else t("gift.auto.disabled", lang)
                    success_embed = discord.Embed(
                        title=f"{theme.verifiedIcon} {t('gift.auto.updated_title', lang)}",
                        description=(
                            f"**{t('gift.auto.details', lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.globeIcon} **{t('gift.auto.scope', lang)}** {t('gift.auto.scope_all', lang)}\n"
                            f"{theme.chartIcon} **{t('gift.auto.status', lang)}** {t('gift.auto.status_text', lang, status=status_text)}\n"
                            f"{theme.userIcon} **{t('gift.auto.updated_by', lang)}** {select_interaction.user.mention}\n"
                            f"{theme.lowerDivider}\n"
                        ),
                        color=theme.emColor3
                    )
                    
                    await select_interaction.response.edit_message(
                        embed=success_embed,
                        view=None
                    )
                    return

                alliance_id = int(selected_value)
                alliance_name = next((name for aid, name in available_alliances if aid == alliance_id), t("gift.redeem.unknown", lang))

                current_setting = t("gift.auto.enabled", lang) if current_status.get(alliance_id, 0) == 1 else t("gift.auto.disabled", lang)
                
                confirm_embed = discord.Embed(
                    title=f"{theme.settingsIcon} {t('gift.auto.config_title', lang)}",
                    description=(
                        f"**{t('gift.auto.alliance_details', lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                        f"{theme.chartIcon} **{t('gift.auto.current_status', lang)}** {t('gift.auto.current_status_text', lang, status=current_setting)}\n"
                        f"{theme.lowerDivider}\n\n"
                        f"{t('gift.auto.enable_disable_prompt', lang)}"
                    ),
                    color=discord.Color.yellow()
                )

                confirm_view = discord.ui.View()
                
                async def button_callback(button_interaction: discord.Interaction):
                    try:
                        status = 1 if button_interaction.data['custom_id'] == "confirm" else 0

                        if status == 1:
                            # When enabling, assign next available priority
                            self.cursor.execute("SELECT COALESCE(MAX(priority), 0) + 1 FROM giftcodecontrol")
                            next_priority = self.cursor.fetchone()[0]
                            self.cursor.execute(
                                """
                                INSERT INTO giftcodecontrol (alliance_id, status, priority)
                                VALUES (?, ?, ?)
                                ON CONFLICT(alliance_id)
                                DO UPDATE SET status = excluded.status,
                                    priority = CASE WHEN giftcodecontrol.priority = 0 THEN excluded.priority ELSE giftcodecontrol.priority END
                                """,
                                (alliance_id, status, next_priority)
                            )
                        else:
                            # When disabling, keep existing priority
                            self.cursor.execute(
                                """
                                INSERT INTO giftcodecontrol (alliance_id, status)
                                VALUES (?, ?)
                                ON CONFLICT(alliance_id)
                                DO UPDATE SET status = excluded.status
                                """,
                                (alliance_id, status)
                            )
                        self.conn.commit()

                        status_text = t("gift.auto.enabled", lang) if status == 1 else t("gift.auto.disabled", lang)
                        success_embed = discord.Embed(
                            title=f"{theme.verifiedIcon} {t('gift.auto.updated_title', lang)}",
                            description=(
                                f"**{t('gift.auto.details', lang)}**\n"
                                f"{theme.upperDivider}\n"
                                f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** {alliance_name}\n"
                                f"{theme.chartIcon} **{t('gift.auto.status', lang)}** {t('gift.auto.status_text', lang, status=status_text)}\n"
                                f"{theme.userIcon} **{t('gift.auto.updated_by', lang)}** {button_interaction.user.mention}\n"
                                f"{theme.lowerDivider}\n"
                            ),
                            color=theme.emColor3
                        )
                        
                        await button_interaction.response.edit_message(
                            embed=success_embed,
                            view=None
                        )

                    except Exception as e:
                        self.logger.exception(f"Button callback error: {str(e)}")
                        if not button_interaction.response.is_done():
                            await button_interaction.response.send_message(
                                f"{theme.deniedIcon} {t('gift.auto.update_error', lang)}",
                                ephemeral=True
                            )
                        else:
                            await button_interaction.followup.send(
                                f"{theme.deniedIcon} {t('gift.auto.update_error', lang)}",
                                ephemeral=True
                            )

                confirm_button = discord.ui.Button(
                    label=t("gift.auto.enable", lang),
                    emoji=f"{theme.verifiedIcon}",
                    style=discord.ButtonStyle.success,
                    custom_id="confirm"
                )
                confirm_button.callback = button_callback

                deny_button = discord.ui.Button(
                    label=t("gift.auto.disable", lang),
                    emoji=f"{theme.deniedIcon}",
                    style=discord.ButtonStyle.danger,
                    custom_id="deny"
                )
                deny_button.callback = button_callback

                confirm_view.add_item(confirm_button)
                confirm_view.add_item(deny_button)

                if not select_interaction.response.is_done():
                    await select_interaction.response.edit_message(
                        embed=confirm_embed,
                        view=confirm_view
                    )
                else:
                    await select_interaction.message.edit(
                        embed=confirm_embed,
                        view=confirm_view
                    )

            except Exception as e:
                self.logger.exception(f"Error in alliance selection: {e}")
                if not select_interaction.response.is_done():
                    await select_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('gift.error.process_request', lang)}",
                        ephemeral=True
                    )
                else:
                    await select_interaction.followup.send(
                        f"{theme.deniedIcon} {t('gift.error.process_request', lang)}",
                        ephemeral=True
                    )

        view.callback = alliance_callback

        await interaction.response.send_message(
            embed=auto_gift_embed,
            view=view,
            ephemeral=True
        )

    async def use_giftcode_for_alliance(self, alliance_id, giftcode):
        MEMBER_PROCESS_DELAY = 1.0
        API_RATE_LIMIT_COOLDOWN = 60.0
        CAPTCHA_CYCLE_COOLDOWN = 60.0
        MAX_RETRY_CYCLES = 10

        self.logger.info(f"\nGiftOps: Starting use_giftcode_for_alliance for Alliance {alliance_id}, Code {giftcode}")

        try:
            lang = get_guild_language(None)
            # Initialize error tracking for summary
            error_summary = {}
            
            # Initial Setup (Get channel, alliance name)
            self.alliance_cursor.execute("SELECT channel_id FROM alliancesettings WHERE alliance_id = ?", (alliance_id,))
            channel_result = self.alliance_cursor.fetchone()
            self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (alliance_id,))
            name_result = self.alliance_cursor.fetchone()

            if not channel_result or not name_result:
                self.logger.error(f"GiftOps: Could not find channel or name for alliance {alliance_id}.")
                return False
            
            channel_id, alliance_name = channel_result[0], name_result[0]
            channel = self.bot.get_channel(channel_id)

            if not channel:
                self.logger.error(f"GiftOps: Bot cannot access channel {channel_id} for alliance {alliance_name}.")
                return False

            lang = get_guild_language(channel.guild.id if channel.guild else None)

            # Check if OCR is enabled
            self.settings_cursor.execute("SELECT enabled FROM ocr_settings ORDER BY id DESC LIMIT 1")
            ocr_settings_row = self.settings_cursor.fetchone()
            ocr_enabled = ocr_settings_row[0] if ocr_settings_row else 0
            
            if not (ocr_enabled == 1 and self.captcha_solver):
                error_embed = discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.redeem.ocr_disabled_title', lang)}",
                    description=(
                        f"**{t('gift.common.details_title', lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                        f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** `{alliance_name}`\n"
                        f"{theme.lowerDivider}\n\n"
                        f"{theme.warnIcon} {t('gift.redeem.ocr_required', lang)}"
                    ),
                    color=theme.emColor2
                )
                await channel.send(embed=error_embed)
                self.logger.info(f"GiftOps: Skipping alliance {alliance_id} - OCR disabled or solver not ready")
                return False

            # Check if this code has been validated before
            self.cursor.execute("SELECT validation_status FROM gift_codes WHERE giftcode = ?", (giftcode,))
            master_code_status_row = self.cursor.fetchone()
            master_code_status = master_code_status_row[0] if master_code_status_row else None
            final_invalid_reason_for_embed = None

            if master_code_status == 'invalid':
                self.logger.info(f"GiftOps: Code {giftcode} is already marked as 'invalid' in the database.")
                final_invalid_reason_for_embed = t("gift.redeem.invalid_previously", lang)
            else:
                # If not marked 'invalid' in master table, check with test ID if status is 'pending' or for other cached issues
                test_fid = self.get_test_fid()
                self.cursor.execute("SELECT status FROM user_giftcodes WHERE fid = ? AND giftcode = ?", (test_fid, giftcode))
                validation_fid_status_row = self.cursor.fetchone()

                if validation_fid_status_row:
                    fid_status = validation_fid_status_row[0]
                    if fid_status in ["TIME_ERROR", "CDK_NOT_FOUND", "USAGE_LIMIT"]:
                        self.logger.info(f"GiftOps: Code {giftcode} known to be invalid via test ID (status: {fid_status}). Marking invalid.")
                        self.mark_code_invalid(giftcode)
                        if hasattr(self, 'api') and self.api:
                            asyncio.create_task(self.api.remove_giftcode(giftcode, from_validation=True))
                        
                        reason_map_fid = {
                            "TIME_ERROR": t("gift.redeem.invalid_time_error", lang),
                            "CDK_NOT_FOUND": t("gift.redeem.invalid_cdk_not_found", lang),
                            "USAGE_LIMIT": t("gift.redeem.invalid_usage_limit", lang)
                        }
                        final_invalid_reason_for_embed = reason_map_fid.get(
                            fid_status,
                            t("gift.redeem.invalid_generic", lang, status=fid_status)
                        )

            if final_invalid_reason_for_embed:
                error_embed = discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.redeem.invalid_title', lang)}",
                    description=(
                        f"**{t('gift.common.details_title', lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                        f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** `{alliance_name}`\n"
                        f"{theme.deniedIcon} **{t('gift.common.status_label', lang)}** {final_invalid_reason_for_embed}\n"
                        f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.redeem.invalid_action', lang)}\n"
                        f"{theme.timeIcon} **{t('gift.common.time_label', lang)}** <t:{int(datetime.now().timestamp())}:R>\n"
                        f"{theme.lowerDivider}\n"
                    ),
                    color=theme.emColor2
                )
                await channel.send(embed=error_embed)
                return False

            # Get Members
            with sqlite3.connect('db/users.sqlite') as users_conn:
                users_cursor = users_conn.cursor()
                users_cursor.execute("SELECT fid, nickname FROM users WHERE alliance = ?", (str(alliance_id),))
                members = users_cursor.fetchall()
            if not members:
                self.logger.info(f"GiftOps: No members found for alliance {alliance_id} ({alliance_name}).")
                return False

            total_members = len(members)
            self.logger.info(f"GiftOps: Found {total_members} members for {alliance_name}.")

            # Initialize State
            processed_count = 0
            success_count = 0
            received_count = 0
            failed_count = 0
            successful_users = []
            already_used_users = []
            failed_users_dict = {}

            retry_queue = []
            active_members_to_process = []
            
            # Batch Processing
            batch_results = []
            batch_size = 10

            # Check Cache & Populate Initial List
            member_ids = [m[0] for m in members]
            cached_member_statuses = self.batch_get_user_giftcode_status(giftcode, member_ids)

            for fid, nickname in members:
                if fid in cached_member_statuses:
                    status = cached_member_statuses[fid]
                    if status in ["SUCCESS", "RECEIVED", "SAME TYPE EXCHANGE"]:
                        received_count += 1
                        already_used_users.append(nickname)
                    processed_count += 1
                else:
                    active_members_to_process.append((fid, nickname, 0))
            self.logger.info(f"GiftOps: Pre-processed {len(cached_member_statuses)} members from cache. {len(active_members_to_process)} remaining.")

            # Progress Embed
            embed = discord.Embed(
                title=f"{theme.giftIcon} {t('gift.redeem.progress_title', lang, code=giftcode)}",
                color=theme.emColor1
            )
            def update_embed_description(include_errors=False):
                base_description = (
                    f"**{t('gift.redeem.progress_status_for', lang)}** `{alliance_name}`\n"
                    f"{theme.upperDivider}\n"
                    f"{theme.membersIcon} **{t('gift.common.total_members_label', lang)}** `{total_members}`\n"
                    f"{theme.verifiedIcon} **{t('gift.common.success_label', lang)}** `{success_count}`\n"
                    f"{theme.infoIcon} **{t('gift.common.already_redeemed_label', lang)}** `{received_count}`\n"
                    f"{theme.refreshIcon} **{t('gift.common.retrying_label', lang)}** `{len(retry_queue)}`\n"
                    f"{theme.deniedIcon} **{t('gift.common.failed_label', lang)}** `{failed_count}`\n"
                    f"{theme.hourglassIcon} **{t('gift.common.processed_label', lang)}** `{processed_count}/{total_members}`\n"
                    f"{theme.lowerDivider}\n"
                )
                
                if include_errors and failed_count > 0:
                    non_success_errors = {k: v for k, v in error_summary.items() if k != "SUCCESS"}
                    if non_success_errors:
                        # Define user-friendly messages for each error type
                        error_descriptions = {
                            "TOO_POOR_SPEND_MORE": ("gift.redeem.error_breakdown.too_poor_spend_more", theme.warnIcon),
                            "TOO_SMALL_SPEND_MORE": ("gift.redeem.error_breakdown.too_small_spend_more", theme.warnIcon),
                            "TIMEOUT_RETRY": ("gift.redeem.error_breakdown.timeout_retry", theme.timeIcon),
                            "LOGIN_EXPIRED_MID_PROCESS": ("gift.redeem.error_breakdown.login_expired_mid_process", theme.lockIcon),
                            "LOGIN_FAILED": ("gift.redeem.error_breakdown.login_failed", theme.lockIcon),
                            "CAPTCHA_SOLVING_FAILED": ("gift.redeem.error_breakdown.captcha_solving_failed", theme.robotIcon),
                            "CAPTCHA_SOLVER_ERROR": ("gift.redeem.error_breakdown.captcha_solver_error", theme.settingsIcon),
                            "OCR_DISABLED": ("gift.redeem.error_breakdown.ocr_disabled", theme.deniedIcon),
                            "SIGN_ERROR": ("gift.redeem.error_breakdown.sign_error", theme.lockIcon),
                            "ERROR": ("gift.redeem.error_breakdown.error", theme.deniedIcon),
                            "UNKNOWN_API_RESPONSE": ("gift.redeem.error_breakdown.unknown_api_response", theme.infoIcon),
                            "CONNECTION_ERROR": ("gift.redeem.error_breakdown.connection_error", theme.globeIcon)
                        }
                        
                        base_description += f"\n**{t('gift.redeem.error_breakdown_title', lang)}**\n"
                        
                        # Build message for each error type
                        for error_type, count in sorted(non_success_errors.items(), key=lambda x: x[1], reverse=True):
                            if error_type in error_descriptions:
                                key, icon = error_descriptions[error_type]
                                base_description += f"{icon} {t(key, lang, count=count)}\n"
                            else:
                                # Handle any unexpected error types
                                base_description += f"{theme.warnIcon} {t('gift.redeem.error_breakdown.unknown', lang, count=count, status=error_type)}\n"
                
                return base_description
            embed.description = update_embed_description()
            try: status_message = await channel.send(embed=embed)
            except Exception as e: self.logger.exception(f"GiftOps: Error sending initial status embed: {e}"); return False

            # Main Processing Loop
            last_embed_update = time.time()
            code_is_invalid = False

            while active_members_to_process or retry_queue:
                if code_is_invalid:
                    self.logger.info(f"GiftOps: Code {giftcode} detected as invalid, stopping redemption.")
                    break
                    
                current_time = time.time()

                # Dequeue Ready Retries
                ready_to_retry = []
                remaining_in_queue = []
                for item in retry_queue:
                    if current_time >= item[3]:
                        ready_to_retry.append(item[:3])
                    else:
                        remaining_in_queue.append(item)
                retry_queue = remaining_in_queue
                active_members_to_process.extend(ready_to_retry)

                if not active_members_to_process:
                    if retry_queue:
                        next_retry_ts = min(item[3] for item in retry_queue)
                        wait_time = max(0.1, next_retry_ts - current_time)
                        await asyncio.sleep(wait_time)
                    else:
                        break
                    continue

                # Process One Member
                fid, nickname, current_cycle_count = active_members_to_process.pop(0)

                self.logger.info(f"GiftOps: Processing ID {fid} ({nickname}), Cycle {current_cycle_count + 1}/{MAX_RETRY_CYCLES}")

                response_status = "ERROR"
                try:
                    await asyncio.sleep(random.uniform(MEMBER_PROCESS_DELAY * 0.7, MEMBER_PROCESS_DELAY * 1.3))
                    response_status = await self.claim_giftcode_rewards_wos(fid, giftcode)
                except Exception as claim_err:
                    self.logger.exception(f"GiftOps: Unexpected error during claim for {fid}: {claim_err}")
                    response_status = "ERROR"

                # Check if code is invalid
                if response_status in ["TIME_ERROR", "CDK_NOT_FOUND", "USAGE_LIMIT"]:
                    code_is_invalid = True
                    self.logger.info(f"GiftOps: Code {giftcode} became invalid (status: {response_status}) while processing {fid}. Marking as invalid in DB.")
                    
                    # Mark as invalid
                    self.mark_code_invalid(giftcode)
                    
                    if hasattr(self, 'api') and self.api:
                        asyncio.create_task(self.api.remove_giftcode(giftcode, from_validation=True))

                    reason_map_runtime = {
                        "TIME_ERROR": t("gift.redeem.invalid_time_error", lang),
                        "CDK_NOT_FOUND": t("gift.redeem.invalid_cdk_not_found", lang),
                        "USAGE_LIMIT": t("gift.redeem.invalid_usage_limit", lang)
                    }
                    status_reason_runtime = reason_map_runtime.get(
                        response_status,
                        t("gift.redeem.invalid_generic", lang, status=response_status)
                    )
                    
                    embed.title = f"{theme.deniedIcon} {t('gift.redeem.invalid_runtime_title', lang, code=giftcode)}"
                    embed.color = discord.Color.red()
                    embed.description = (
                        f"**{t('gift.redeem.halted_title', lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                        f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** `{alliance_name}`\n"
                        f"{theme.deniedIcon} **{t('gift.common.reason_label', lang)}** {status_reason_runtime}\n"
                        f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.redeem.invalid_action_halt', lang)}\n"
                        f"{theme.chartIcon} **{t('gift.common.processed_before_halt_label', lang)}** {processed_count}/{total_members}\n"
                        f"{theme.timeIcon} **{t('gift.common.time_label', lang)}** <t:{int(datetime.now().timestamp())}:R>\n"
                        f"{theme.lowerDivider}\n"
                    )
                    embed.clear_fields()

                    try:
                        await status_message.edit(embed=embed)
                    except Exception as embed_edit_err:
                        self.logger.warning(f"GiftOps: Failed to update progress embed to show code invalidation: {embed_edit_err}")
                    
                    if fid not in failed_users_dict:
                        processed_count +=1 
                        failed_count +=1
                        failed_users_dict[fid] = (nickname, f"Led to code invalidation ({response_status})", current_cycle_count + 1)
                    continue
                
                if response_status == "SIGN_ERROR":
                    self.logger.error(f"GiftOps: Sign error detected (likely wrong encrypt key). Stopping redemption for alliance {alliance_id}.")
                    
                    embed.title = f"{theme.settingsIcon} {t('gift.redeem.sign_error_title', lang, code=giftcode)}"
                    embed.color = discord.Color.red()
                    embed.description = (
                        f"**{t('gift.redeem.sign_error_heading', lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{giftcode}`\n"
                        f"{theme.allianceIcon} **{t('gift.channel.alliance_label', lang)}** `{alliance_name}`\n"
                        f"{theme.settingsIcon} **{t('gift.common.reason_label', lang)}** {t('gift.redeem.sign_error_reason', lang)}\n"
                        f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.redeem.sign_error_action', lang)}\n"
                        f"{theme.chartIcon} **{t('gift.common.processed_before_halt_label', lang)}** {processed_count}/{total_members}\n"
                        f"{theme.timeIcon} **{t('gift.common.time_label', lang)}** <t:{int(datetime.now().timestamp())}:R>\n"
                        f"{theme.lowerDivider}\n"
                    )
                    embed.clear_fields()
                    
                    try:
                        await status_message.edit(embed=embed)
                    except Exception as embed_edit_err:
                        self.logger.warning(f"GiftOps: Failed to update progress embed for sign error: {embed_edit_err}")

                    break

                # Handle Response
                mark_processed = False
                add_to_failed = False
                queue_for_retry = False
                retry_delay = 0

                if response_status == "SUCCESS":
                    success_count += 1
                    successful_users.append(nickname)
                    batch_results.append((fid, giftcode, response_status))
                    mark_processed = True
                elif response_status in ["RECEIVED", "SAME TYPE EXCHANGE"]:
                    received_count += 1
                    already_used_users.append(nickname)
                    batch_results.append((fid, giftcode, response_status))
                    mark_processed = True
                elif response_status == "OCR_DISABLED":
                    add_to_failed = True
                    mark_processed = True
                    fail_reason = "OCR Disabled"
                    error_summary["OCR_DISABLED"] = error_summary.get("OCR_DISABLED", 0) + 1
                elif response_status in ["SOLVER_ERROR", "CAPTCHA_FETCH_ERROR"]:
                    add_to_failed = True
                    mark_processed = True
                    fail_reason = f"Solver Error ({response_status})"
                    error_summary["CAPTCHA_SOLVER_ERROR"] = error_summary.get("CAPTCHA_SOLVER_ERROR", 0) + 1
                elif response_status in ["LOGIN_FAILED", "LOGIN_EXPIRED_MID_PROCESS", "ERROR", "UNKNOWN_API_RESPONSE"]:
                    add_to_failed = True
                    mark_processed = True
                    fail_reason = f"Processing Error ({response_status})"
                    error_summary[response_status] = error_summary.get(response_status, 0) + 1
                elif response_status == "TIMEOUT_RETRY":
                    queue_for_retry = True
                    retry_delay = API_RATE_LIMIT_COOLDOWN
                    fail_reason = "API Rate Limited"
                    if current_cycle_count + 1 >= MAX_RETRY_CYCLES: # Track as error if this is the final attempt
                        error_summary["TIMEOUT_RETRY"] = error_summary.get("TIMEOUT_RETRY", 0) + 1
                elif response_status == "TOO_POOR_SPEND_MORE":
                    add_to_failed = True
                    mark_processed = True
                    fail_reason = "VIP level too low"
                    error_summary["TOO_POOR_SPEND_MORE"] = error_summary.get("TOO_POOR_SPEND_MORE", 0) + 1
                elif response_status == "TOO_SMALL_SPEND_MORE":
                    add_to_failed = True
                    mark_processed = True
                    fail_reason = "Furnace level too low"
                    error_summary["TOO_SMALL_SPEND_MORE"] = error_summary.get("TOO_SMALL_SPEND_MORE", 0) + 1
                elif response_status == "CAPTCHA_TOO_FREQUENT":
                    # Queue for retry with rate limit delay (60s max)
                    queue_for_retry = True
                    retry_delay = 60.0
                    fail_reason = "Captcha API rate limited (too frequent)"
                    self.logger.info(f"GiftOps: ID {fid} hit CAPTCHA_TOO_FREQUENT. Queuing for retry in {retry_delay:.1f}s.")
                    if current_cycle_count + 1 >= MAX_RETRY_CYCLES:
                        error_summary["CAPTCHA_TOO_FREQUENT"] = error_summary.get("CAPTCHA_TOO_FREQUENT", 0) + 1
                elif response_status in ["CAPTCHA_INVALID", "MAX_CAPTCHA_ATTEMPTS_REACHED", "OCR_FAILED_ATTEMPT"]:
                    if current_cycle_count + 1 < MAX_RETRY_CYCLES:
                        queue_for_retry = True
                        retry_delay = CAPTCHA_CYCLE_COOLDOWN
                        fail_reason = "Captcha Cycle Failed"
                        self.logger.info(f"GiftOps: ID {fid} failed captcha cycle {current_cycle_count + 1}. Queuing for retry cycle {current_cycle_count + 2} in {retry_delay}s.")
                    else:
                        add_to_failed = True
                        mark_processed = True
                        fail_reason = f"Failed after {MAX_RETRY_CYCLES} captcha cycles (Last Status: {response_status})"
                        self.logger.info(f"GiftOps: Max ({MAX_RETRY_CYCLES}) retry cycles reached for ID {fid}. Marking as failed.")
                        # Track based on error type
                        if response_status in ["CAPTCHA_INVALID", "MAX_CAPTCHA_ATTEMPTS_REACHED"]:
                            error_summary["CAPTCHA_SOLVING_FAILED"] = error_summary.get("CAPTCHA_SOLVING_FAILED", 0) + 1
                        else:  # OCR_FAILED_ATTEMPT
                            error_summary["CAPTCHA_SOLVER_ERROR"] = error_summary.get("CAPTCHA_SOLVER_ERROR", 0) + 1
                else:
                    add_to_failed = True
                    mark_processed = True
                    fail_reason = f"Unhandled status: {response_status}"
                    error_summary[response_status] = error_summary.get(response_status, 0) + 1

                # Update State Based on Outcome
                if mark_processed:
                    processed_count += 1
                    if add_to_failed:
                        failed_count += 1
                        cycle_failed_on = current_cycle_count + 1 if response_status not in ["CAPTCHA_INVALID", "MAX_CAPTCHA_ATTEMPTS_REACHED", "OCR_FAILED_ATTEMPT"] or (current_cycle_count + 1 >= MAX_RETRY_CYCLES) else MAX_RETRY_CYCLES
                        failed_users_dict[fid] = (nickname, fail_reason, cycle_failed_on)
                
                if queue_for_retry:
                    retry_after_ts = time.time() + retry_delay
                    cycle_for_next_retry = current_cycle_count + 1 if response_status in ["CAPTCHA_INVALID", "MAX_CAPTCHA_ATTEMPTS_REACHED", "OCR_FAILED_ATTEMPT"] else current_cycle_count
                    retry_queue.append((fid, nickname, cycle_for_next_retry, retry_after_ts))
                
                # Batch process results when reaching batch size
                if len(batch_results) >= batch_size:
                    self.batch_process_alliance_results(batch_results)
                    batch_results = []

                # Update Embed Periodically
                current_time = time.time()
                if current_time - last_embed_update > 5 and not code_is_invalid:
                    embed.description = update_embed_description()
                    try:
                        await status_message.edit(embed=embed)
                        last_embed_update = current_time
                    except Exception as embed_edit_err:
                        self.logger.warning(f"GiftOps: WARN - Failed to edit progress embed: {embed_edit_err}")

            # Final Embed Update
            if not code_is_invalid:
                self.logger.info(f"GiftOps: Alliance {alliance_id} processing loop finished. Preparing final update.")
                final_title = f"{theme.giftIcon} {t('gift.redeem.complete_title_with_code', lang, code=giftcode)}"
                final_color = discord.Color.green() if failed_count == 0 and total_members > 0 else \
                              discord.Color.orange() if success_count > 0 or received_count > 0 else \
                              discord.Color.red()
                if total_members == 0:
                    final_title = f"{theme.infoIcon} {t('gift.redeem.no_members_title_with_code', lang, code=giftcode)}"
                    final_color = discord.Color.light_grey()

                embed.title = final_title
                embed.color = final_color
                embed.description = update_embed_description(include_errors=True)

                try:
                    await status_message.edit(embed=embed)
                    self.logger.info(f"GiftOps: Successfully edited final status embed for alliance {alliance_id}.")
                except discord.NotFound:
                    self.logger.warning(f"GiftOps: WARN - Failed to edit final progress embed for alliance {alliance_id}: Original message not found.")
                except discord.Forbidden:
                    self.logger.warning(f"GiftOps: WARN - Failed to edit final progress embed for alliance {alliance_id}: Missing permissions.")
                except Exception as final_embed_err:
                    self.logger.exception(f"GiftOps: WARN - Failed to edit final progress embed for alliance {alliance_id}: {final_embed_err}")

            summary_lines = [
                "\n",
                "--- Redemption Summary Start ---",
                f"Alliance: {alliance_name} ({alliance_id})",
                f"Gift Code: {giftcode}",
            ]
            try:
                master_status_log = self.cursor.execute("SELECT validation_status FROM gift_codes WHERE giftcode = ?", (giftcode,)).fetchone()
                summary_lines.append(f"Master Code Status at Log Time: {master_status_log[0] if master_status_log else 'NOT_FOUND_IN_DB'}")
            except Exception as e_log:
                summary_lines.append(f"Master Code Status at Log Time: Error fetching - {e_log}")

            summary_lines.extend([
                f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "------------------------",
                f"Total Members: {total_members}",
                f"Successful: {success_count}",
                f"Already Redeemed: {received_count}",
                f"Failed: {failed_count}",
                "------------------------",
            ])

            if successful_users:
                summary_lines.append(f"\nSuccessful Users ({len(successful_users)}):")
                summary_lines.extend(successful_users)

            if already_used_users:
                summary_lines.append(f"\nAlready Redeemed Users ({len(already_used_users)}):")
                summary_lines.extend(already_used_users)

            final_failed_log_details = []
            if code_is_invalid and retry_queue:
                 for f_fid, f_nick, f_cycle, _ in retry_queue:
                     if f_fid not in failed_users_dict:
                         final_failed_log_details.append(f"- {f_nick} ({f_fid}): Halted in retry (Next Cycle: {f_cycle})")
            
            for fid_failed, (nick_failed, reason_failed, cycles_attempted) in failed_users_dict.items():
                final_failed_log_details.append(f"- {nick_failed} ({fid_failed}): {reason_failed} (Cycles Attempted: {cycles_attempted})")
            
            if final_failed_log_details:
                summary_lines.append(f"\nFailed Users ({len(final_failed_log_details)}):")
                summary_lines.extend(final_failed_log_details)

            summary_lines.append("--- Redemption Summary End ---\n")
            summary_log_message = "\n".join(summary_lines)
            self.logger.info(summary_log_message)
            
            # Process any remaining batch results
            if batch_results:
                self.batch_process_alliance_results(batch_results)
                batch_results = []
            
            return True
        
        except Exception as e:
            self.logger.exception(f"GiftOps: UNEXPECTED ERROR in use_giftcode_for_alliance for {alliance_id}/{giftcode}: {str(e)}")
            self.logger.exception(f"Traceback: {traceback.format_exc()}")
            try:
                if 'channel' in locals() and channel:
                    await channel.send(
                        f"{theme.warnIcon} {t('gift.redeem.unexpected_error', lang, code=giftcode, alliance=alliance_name)}"
                    )
            except Exception: pass
            return False

class CreateGiftCodeModal(discord.ui.Modal):
    def __init__(self, cog, lang: str):
        super().__init__(title=t("gift.modal.create_title", lang))
        self.cog = cog
        self.lang = lang
        
        self.giftcode = discord.ui.TextInput(
            label=t("gift.modal.create_label", self.lang),
            placeholder=t("gift.modal.create_placeholder", self.lang),
            required=True,
            min_length=4,
            max_length=20
        )
        self.add_item(self.giftcode)
    
    async def on_submit(self, interaction: discord.Interaction):
        logger = self.cog.logger
        await interaction.response.defer(ephemeral=True)
        lang = self.lang

        code = self.cog.clean_gift_code(self.giftcode.value)
        logger.info(f"[CreateGiftCodeModal] Code entered: {code}")
        final_embed = discord.Embed(title=f"{theme.giftIcon} {t('gift.modal.create_result_title', lang)}")

        # Check if code already exists
        self.cog.cursor.execute("SELECT 1 FROM gift_codes WHERE giftcode = ?", (code,))
        if self.cog.cursor.fetchone():
            logger.info(f"[CreateGiftCodeModal] Code {code} already exists in DB.")
            final_embed.title = f"{theme.infoIcon} {t('gift.modal.exists_title', lang)}"
            final_embed.description = (
                f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
                f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{code}`\n"
                f"{theme.verifiedIcon} **{t('gift.common.status_label', lang)}** {t('gift.modal.exists_status', lang)}\n"
                f"{theme.lowerDivider}\n"
            )
            final_embed.color = discord.Color.blue()
        else: # Validate the code immediately
            logger.info(f"[CreateGiftCodeModal] Validating code {code} before adding to DB.")
            
            validation_embed = discord.Embed(
                title=f"{theme.refreshIcon} {t('gift.modal.validation_title', lang)}",
                description=t("gift.modal.validation_desc", lang, code=code),
                color=theme.emColor1
            )
            await interaction.edit_original_response(embed=validation_embed)
            
            is_valid, validation_msg = await self.cog.validate_gift_code_immediately(code, "button")
            
            if is_valid: # Valid code - send to API and add to DB
                logger.info(f"[CreateGiftCodeModal] Code '{code}' validated successfully.")
                
                if hasattr(self.cog, 'api') and self.cog.api:
                    asyncio.create_task(self.cog.api.add_giftcode(code))
                
                final_embed.title = f"{theme.verifiedIcon} {t('gift.modal.validated_title', lang)}"
                final_embed.description = (
                    f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
                    f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{code}`\n"
                    f"{theme.verifiedIcon} **{t('gift.common.status_label', lang)}** {validation_msg}\n"
                    f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.modal.action_added', lang)}\n"
                    f"{theme.lowerDivider}\n"
                )
                final_embed.color = discord.Color.green()
                
            elif is_valid is False: # Invalid code - do not add
                logger.warning(f"[CreateGiftCodeModal] Code '{code}' is invalid: {validation_msg}")
                
                final_embed.title = f"{theme.deniedIcon} {t('gift.modal.invalid_title', lang)}"
                final_embed.description = (
                    f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
                    f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{code}`\n"
                    f"{theme.deniedIcon} **{t('gift.common.status_label', lang)}** {validation_msg}\n"
                    f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.modal.action_not_added', lang)}\n"
                    f"{theme.lowerDivider}\n"
                )
                final_embed.color = discord.Color.red()
                
            else: # Validation inconclusive - add as pending
                logger.warning(f"[CreateGiftCodeModal] Code '{code}' validation inconclusive: {validation_msg}")
                
                try:
                    date = datetime.now().strftime("%Y-%m-%d")
                    self.cog.cursor.execute(
                        "INSERT INTO gift_codes (giftcode, date, validation_status) VALUES (?, ?, ?)",
                        (code, date, "pending")
                    )
                    self.cog.conn.commit()
                    
                    final_embed.title = f"{theme.warnIcon} {t('gift.modal.pending_title', lang)}"
                    final_embed.description = (
                        f"**{t('gift.common.details_title', lang)}**\n{theme.upperDivider}\n"
                        f"{theme.giftIcon} **{t('gift.common.gift_code_label', lang)}** `{code}`\n"
                        f"{theme.warnIcon} **{t('gift.common.status_label', lang)}** {validation_msg}\n"
                        f"{theme.editListIcon} **{t('gift.common.action_label', lang)}** {t('gift.modal.action_pending', lang)}\n"
                        f"{theme.lowerDivider}\n"
                    )
                    final_embed.color = discord.Color.yellow()
                    
                except sqlite3.Error as db_err:
                    logger.exception(f"[CreateGiftCodeModal] DB Error inserting code '{code}': {db_err}")
                    final_embed.title = f"{theme.deniedIcon} {t('gift.modal.db_error_title', lang)}"
                    final_embed.description = t("gift.modal.db_error_body", lang, code=code)
                    final_embed.color = discord.Color.red()

        try:
            await interaction.edit_original_response(embed=final_embed)
            logger.info(f"[CreateGiftCodeModal] Final result embed sent for code {code}.")
        except Exception as final_edit_err:
            logger.exception(f"[CreateGiftCodeModal] Failed to edit interaction with final result for {code}: {final_edit_err}")

class DeleteGiftCodeModal(discord.ui.Modal):
    def __init__(self, cog, lang: str):
        super().__init__(title=t("gift.modal.delete_title", lang))
        self.cog = cog
        self.lang = lang
        
        self.giftcode = discord.ui.TextInput(
            label=t("gift.modal.delete_label", self.lang),
            placeholder=t("gift.modal.delete_placeholder", self.lang),
            required=True
        )
        self.add_item(self.giftcode)
    
    async def on_submit(self, interaction: discord.Interaction):
        lang = self.lang
        code = self.giftcode.value
        
        self.cog.cursor.execute("SELECT 1 FROM gift_codes WHERE giftcode = ?", (code,))
        if not self.cog.cursor.fetchone():
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.modal.delete_not_found', lang)}",
                ephemeral=True
            )
            return
            
        self.cog.cursor.execute("DELETE FROM gift_codes WHERE giftcode = ?", (code,))
        self.cog.cursor.execute("DELETE FROM user_giftcodes WHERE giftcode = ?", (code,))
        self.cog.conn.commit()
        
        embed = discord.Embed(
            title=f"{theme.verifiedIcon} {t('gift.modal.delete_success_title', lang)}",
            description=t("gift.modal.delete_success_body", lang, code=code),
            color=theme.emColor3
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TestIDModal(discord.ui.Modal):
    def __init__(self, cog, lang: str):
        super().__init__(title=t("gift.ocr.test_id_title", lang))
        self.cog = cog
        self.lang = lang
        
        try:
            self.cog.settings_cursor.execute("SELECT test_fid FROM test_fid_settings ORDER BY id DESC LIMIT 1")
            result = self.cog.settings_cursor.fetchone()
            current_fid = result[0] if result else "244886619"
        except Exception:
            current_fid = "244886619"
        
        self.test_fid = discord.ui.TextInput(
            label=t("gift.ocr.test_id_label", self.lang),
            placeholder=t("gift.ocr.test_id_placeholder", self.lang),
            default=current_fid,
            required=True,
            min_length=1,
            max_length=20
        )
        self.add_item(self.test_fid)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Defer the response since we'll make an API call to validate
            await interaction.response.defer(ephemeral=True)
            
            new_fid = self.test_fid.value.strip()
            
            if not new_fid.isdigit():
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_id_invalid_format', self.lang)}",
                    ephemeral=True
                )
                return
            
            is_valid, message = await self.cog.verify_test_fid(new_fid)
            
            if is_valid:
                success = await self.cog.update_test_fid(new_fid)
                
                if success:
                    embed = discord.Embed(
                        title=f"{theme.verifiedIcon} {t('gift.ocr.test_id_updated_title', self.lang)}",
                        description=(
                            f"**{t('gift.ocr.test_id_config_title', self.lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.fidIcon} **ID:** `{new_fid}`\n"
                            f"{theme.verifiedIcon} **{t('gift.common.status_label', self.lang)}** {t('gift.ocr.test_id_status_validated', self.lang)}\n"
                            f"{theme.editListIcon} **{t('gift.common.action_label', self.lang)}** {t('gift.ocr.test_id_action_updated', self.lang)}\n"
                            f"{theme.lowerDivider}\n"
                        ),
                        color=theme.emColor3
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
                    await self.cog.show_ocr_settings(interaction)
                else:
                    await interaction.followup.send(
                        f"{theme.deniedIcon} {t('gift.ocr.test_id_update_failed', self.lang)}",
                        ephemeral=True
                    )
            else:
                embed = discord.Embed(
                    title=f"{theme.deniedIcon} {t('gift.ocr.test_id_invalid_title', self.lang)}",
                    description=(
                        f"**{t('gift.ocr.test_id_validation_title', self.lang)}**\n"
                        f"{theme.upperDivider}\n"
                        f"{theme.fidIcon} **ID:** `{new_fid}`\n"
                        f"{theme.deniedIcon} **{t('gift.common.status_label', self.lang)}** {t('gift.ocr.test_id_status_invalid', self.lang)}\n"
                        f"{theme.editListIcon} **{t('gift.common.reason_label', self.lang)}** {message}\n"
                        f"{theme.lowerDivider}\n"
                    ),
                    color=theme.emColor2
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            self.cog.logger.exception(f"Error updating test ID: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('gift.ocr.test_id_error', self.lang, error=str(e))}",
                ephemeral=True
            )

class GiftView(discord.ui.View):
    def __init__(self, cog, lang: str):
        super().__init__(timeout=7200)
        self.cog = cog
        self._apply_language(lang)

    def _apply_language(self, lang: str) -> None:
        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue
            if child.custom_id == "create_gift":
                child.label = t("gift.button.add", lang)
            elif child.custom_id == "list_gift":
                child.label = t("gift.button.list", lang)
            elif child.custom_id == "use_gift_alliance":
                child.label = t("gift.button.redeem", lang)
            elif child.custom_id == "gift_code_settings":
                child.label = t("gift.button.settings", lang)
            elif child.custom_id == "delete_gift":
                child.label = t("gift.button.delete", lang)
            elif child.custom_id == "main_menu":
                child.label = t("gift.button.main_menu", lang)

    @discord.ui.button(
        label="Add Gift Code",
        style=discord.ButtonStyle.green,
        custom_id="create_gift",
        emoji=f"{theme.giftIcon}",
        row=0
    )
    async def create_gift(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.create_gift_code(interaction)

    @discord.ui.button(
        label="List Gift Codes",
        style=discord.ButtonStyle.blurple,
        custom_id="list_gift",
        emoji=f"{theme.listIcon}",
        row=0
    )
    async def list_gift(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.list_gift_codes(interaction)

    @discord.ui.button(
        label="Redeem Gift Code",
        emoji=f"{theme.targetIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="use_gift_alliance",
        row=0
    )
    async def use_gift_alliance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lang = _get_lang(interaction)
            admin_info = await self.cog.get_admin_info(interaction.user.id)
            if not admin_info:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('gift.error.not_authorized', lang)}",
                    ephemeral=True
                )
                return

            available_alliances = await self.cog.get_available_alliances(interaction)
            if not available_alliances:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{theme.deniedIcon} {t('gift.error.no_alliances_title', lang)}",
                        description=t("gift.error.no_alliances_body", lang),
                        color=theme.emColor2
                    ),
                    ephemeral=True
                )
                return

            alliances_with_counts = []
            for alliance_id, name in available_alliances:
                with sqlite3.connect('db/users.sqlite') as users_db:
                    cursor = users_db.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                    member_count = cursor.fetchone()[0]
                    alliances_with_counts.append((alliance_id, name, member_count))

            alliance_embed = discord.Embed(
                title=f"{theme.targetIcon} {t('gift.redeem.title', lang)}",
                description=(
                    f"{t('gift.redeem.select_alliance', lang)}\n\n"
                    f"**{t('gift.redeem.alliance_list', lang)}**\n"
                    f"{theme.upperDivider}\n"
                    f"{t('gift.redeem.select_alliance_hint', lang)}\n"
                ),
                color=theme.emColor1
            )

            view = AllianceSelectView(alliances_with_counts, self.cog, context="giftcode")

            view.current_select.options.insert(0, discord.SelectOption(
                label=t("gift.redeem.all_alliances", lang),
                value="all",
                description=t("gift.redeem.all_alliances_desc", lang, count=len(alliances_with_counts)),
                emoji=theme.globeIcon
            ))

            async def alliance_callback(select_interaction: discord.Interaction, alliance_id=None):
                try:
                    # If alliance_id is provided (from ID search modal), use it directly
                    if alliance_id is not None:
                        selected_value = str(alliance_id)
                    else:
                        selected_value = view.current_select.values[0]

                    if selected_value == "all":
                        # Get alliances ordered by priority
                        alliance_ids = [aid for aid, _, _ in alliances_with_counts]
                        placeholders = ','.join('?' * len(alliance_ids))
                        self.cog.cursor.execute(f"""
                            SELECT alliance_id FROM giftcodecontrol
                            WHERE alliance_id IN ({placeholders})
                            ORDER BY priority ASC, alliance_id ASC
                        """, alliance_ids)
                        prioritized = [row[0] for row in self.cog.cursor.fetchall()]
                        # Add any alliances not in giftcodecontrol at the end, ordered by ID
                        remaining = sorted([aid for aid in alliance_ids if aid not in prioritized])
                        all_alliances = prioritized + remaining
                    else:
                        alliance_id = int(selected_value)
                        all_alliances = [alliance_id]
                    
                    self.cog.cursor.execute("""
                        SELECT giftcode, date FROM gift_codes
                        WHERE validation_status != 'invalid'
                        ORDER BY date DESC
                    """)
                    gift_codes = self.cog.cursor.fetchall()

                    if not gift_codes:
                        await select_interaction.response.edit_message(
                            content=t("gift.redeem.no_active_codes", lang),
                            embed=None,
                            view=None
                        )
                        return

                    giftcode_embed = discord.Embed(
                        title=f"{theme.giftIcon} {t('gift.redeem.select_code_title', lang)}",
                        description=(
                            f"{t('gift.redeem.select_code', lang)}\n\n"
                            f"**{t('gift.redeem.code_list', lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{t('gift.redeem.select_code_hint', lang)}\n"
                        ),
                        color=theme.emColor1
                    )

                    select_giftcode = discord.ui.Select(
                        placeholder=t("gift.redeem.select_code_placeholder", lang),
                        options=[
                            discord.SelectOption(
                                label=f"Code: {code}",
                                value=code,
                                description=t("gift.redeem.code_created", lang, date=date),
                                emoji=theme.giftIcon
                            ) for code, date in gift_codes
                        ]
                    )

                    # Add ALL CODES option at the beginning
                    select_giftcode.options.insert(0, discord.SelectOption(
                        label=t("gift.redeem.all_codes", lang),
                        value="all_codes",
                        description=t("gift.redeem.all_codes_desc", lang, count=len(gift_codes)),
                        emoji=theme.packageIcon
                    ))

                    async def giftcode_callback(giftcode_interaction: discord.Interaction):
                        try:
                            selected_code_value = giftcode_interaction.data["values"][0]

                            # Handle ALL CODES selection
                            if selected_code_value == "all_codes":
                                selected_codes = [code for code, date in gift_codes]
                                code_display = t("gift.redeem.code_all_display", lang, count=len(selected_codes))
                            else:
                                selected_codes = [selected_code_value]
                                code_display = f"`{selected_code_value}`"

                            alliance_display = t("gift.redeem.all", lang) if selected_value == 'all' else next((name for aid, name, _ in alliances_with_counts if aid == alliance_id), t("gift.redeem.unknown", lang))
                            total_redemptions = len(selected_codes) * len(all_alliances)

                            confirm_embed = discord.Embed(
                                title=f"{theme.warnIcon} {t('gift.redeem.confirm_title', lang)}",
                                description=(
                                    f"{t('gift.redeem.confirm_body_multi', lang) if len(selected_codes) > 1 else t('gift.redeem.confirm_body_single', lang)}\n\n"
                                    f"**{t('gift.redeem.details', lang)}**\n"
                                    f"{theme.upperDivider}\n"
                                    f"{theme.giftIcon} **{t('gift.redeem.codes_label', lang, plural='s' if len(selected_codes) > 1 else '')}** {code_display}\n"
                                    f"{theme.allianceIcon} **{t('gift.redeem.alliances_label', lang)}** {alliance_display} ({len(all_alliances)})\n"
                                    f"{theme.chartIcon} **{t('gift.redeem.total_redemptions', lang)}** {total_redemptions}\n"
                                    f"{theme.lowerDivider}\n"
                                ),
                                color=discord.Color.yellow()
                            )

                            confirm_view = discord.ui.View()
                            
                            async def confirm_callback(button_interaction: discord.Interaction):
                                try:
                                    # Defer first so followup.send works for batch progress
                                    await button_interaction.response.defer()

                                    await self.cog.add_manual_redemption_to_queue(
                                        selected_codes, all_alliances, button_interaction
                                    )

                                    queue_status = await self.cog.get_queue_status()

                                    alliance_names = []
                                    for aid in all_alliances[:3]:  # Show first 3 alliance names
                                        name = next((n for a_id, n, _ in alliances_with_counts if a_id == aid), 'Unknown')
                                        alliance_names.append(name)

                                    alliance_list = ", ".join(alliance_names)
                                    if len(all_alliances) > 3:
                                        alliance_list += f" {t('gift.redeem.and_more', lang, count=len(all_alliances) - 3)}"

                                    queue_summary = []
                                    your_position = None

                                    for code, items in queue_status['queue_by_code'].items():
                                        alliance_count = len([i for i in items if i.get('alliance_id')])

                                        if code in selected_codes and your_position is None:
                                            your_position = min(i['position'] for i in items)

                                        queue_summary.append(f"• `{code}` - {alliance_count} alliance{'s' if alliance_count != 1 else ''}")

                                    queue_info = "\n".join(queue_summary) if queue_summary else "Queue is empty"

                                    queue_embed = discord.Embed(
                                        title=f"{theme.verifiedIcon} {t('gift.redeem.queued_title', lang)}",
                                        description=(
                                            f"{t('gift.redeem.queued_body', lang)}\n\n"
                                            f"**{t('gift.redeem.your_redemption', lang)}**\n"
                                            f"{theme.upperDivider}\n"
                                            f"{theme.giftIcon} **{t('gift.redeem.codes_label', lang, plural='s' if len(selected_codes) > 1 else '')}** {code_display}\n"
                                            f"{theme.allianceIcon} **{t('gift.redeem.alliances_label', lang)}** {alliance_list}\n"
                                            f"{theme.chartIcon} **{t('gift.redeem.total_redemptions', lang)}** {len(selected_codes) * len(all_alliances)}\n"
                                            f"{theme.lowerDivider}\n\n"
                                            f"**{t('gift.redeem.queue_details', lang)}**\n"
                                            f"{queue_info}\n\n"
                                            f"{theme.chartIcon} **{t('gift.redeem.queue_total', lang)}** {queue_status['queue_length']}\n"
                                            f"{theme.pinIcon} **{t('gift.redeem.queue_position', lang)}** #{your_position if your_position else t('gift.redeem.queue_processing', lang)}\n\n"
                                            f"{theme.infoIcon} {t('gift.redeem.queue_notify', lang)}"
                                        ),
                                        color=theme.emColor3
                                    )
                                    queue_embed.set_footer(text=t("gift.redeem.queue_footer", lang))

                                    await button_interaction.edit_original_response(
                                        embed=queue_embed,
                                        view=None
                                    )

                                except Exception as e:
                                    self.logger.exception(f"Error queueing gift code redemptions: {e}")
                                    await button_interaction.followup.send(
                                        f"{theme.deniedIcon} {t('gift.error.queue_failed', lang)}",
                                        ephemeral=True
                                    )

                            async def cancel_callback(button_interaction: discord.Interaction):
                                cancel_embed = discord.Embed(
                                    title=f"{theme.deniedIcon} {t('gift.redeem.cancelled_title', lang)}",
                                    description=t("gift.redeem.cancelled_body", lang),
                                    color=theme.emColor2
                                )
                                await button_interaction.response.edit_message(
                                    embed=cancel_embed,
                                    view=None
                                )

                            confirm_button = discord.ui.Button(
                                label=t("gift.button.confirm", lang),
                                style=discord.ButtonStyle.success,
                                emoji=f"{theme.verifiedIcon}"
                            )
                            cancel_button = discord.ui.Button(
                                label=t("gift.button.cancel", lang),
                                style=discord.ButtonStyle.danger,
                                emoji=f"{theme.deniedIcon}"
                            )

                            confirm_button.callback = confirm_callback
                            cancel_button.callback = cancel_callback

                            confirm_view.add_item(confirm_button)
                            confirm_view.add_item(cancel_button)

                            await giftcode_interaction.response.edit_message(
                                embed=confirm_embed,
                                view=confirm_view
                            )
                        except Exception as e:
                            self.logger.exception(f"Gift code callback error: {e}")
                            await giftcode_interaction.response.send_message(
                                f"{theme.deniedIcon} {t('gift.error.process_gift', lang)}",
                                ephemeral=True
                            )

                    select_giftcode.callback = giftcode_callback
                    giftcode_view = discord.ui.View()
                    giftcode_view.add_item(select_giftcode)

                    await select_interaction.response.edit_message(
                        embed=giftcode_embed,
                        view=giftcode_view
                    )
                except Exception as e:
                    self.logger.exception(f"Alliance callback error: {e}")
                    await select_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('gift.error.process_alliance', lang)}",
                        ephemeral=True
                    )

            view.current_select.callback = alliance_callback
            await interaction.response.send_message(
                embed=alliance_embed,
                view=view,
                ephemeral=True
            )
        except Exception as e:
            self.logger.exception(f"Use gift alliance button error: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.process_request', _get_lang(interaction))}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Settings",
        style=discord.ButtonStyle.secondary,
        custom_id="gift_code_settings",
        emoji=f"{theme.settingsIcon}",
        row=1
    )
    async def gift_code_settings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.show_settings_menu(interaction)

    @discord.ui.button(
        label="Delete Gift Code",
        emoji=f"{theme.trashIcon}",
        style=discord.ButtonStyle.danger,
        custom_id="delete_gift",
        row=1
    )
    async def delete_gift_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.delete_gift_code(interaction)
        except Exception as e:
            self.logger.exception(f"Delete gift button error: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.error.delete_request', _get_lang(interaction))}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Main Menu",
        emoji=f"{theme.homeIcon}",
        style=discord.ButtonStyle.secondary,
        custom_id="main_menu",
        row=2
    )
    async def main_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            alliance_cog = self.cog.bot.get_cog("Alliance")
            if alliance_cog:
                try:
                    await interaction.message.edit(content=None, embed=None, view=None)
                except:
                    pass
                await alliance_cog.show_main_menu(interaction)
        except:
            pass

class SettingsMenuView(discord.ui.View):
    def __init__(self, cog, is_global: bool = False, lang: str = "en"):
        super().__init__(timeout=7200)
        self.cog = cog
        self.is_global = is_global
        self._apply_language(lang)

        # Disable global-admin-only buttons for non-global admins
        if not is_global:
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id in [
                    "redemption_priority", "captcha_settings"
                ]:
                    child.disabled = True

    def _apply_language(self, lang: str) -> None:
        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue
            if child.custom_id == "channel_management":
                child.label = t("gift.settings.channel_mgmt", lang)
            elif child.custom_id == "auto_gift_settings":
                child.label = t("gift.settings.auto_redemption", lang)
            elif child.custom_id == "redemption_priority":
                child.label = t("gift.settings.priority", lang)
            elif child.custom_id == "channel_history_scan":
                child.label = t("gift.settings.history_scan", lang)
            elif child.custom_id == "captcha_settings":
                child.label = t("gift.settings.captcha", lang)
            elif child.custom_id == "back_to_main":
                child.label = t("language.back", lang)

    @discord.ui.button(
        label="Channel Management",
        style=discord.ButtonStyle.green,
        custom_id="channel_management",
        emoji=f"{theme.announceIcon}",
        row=0
    )
    async def channel_management_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.manage_channel_settings(interaction)

    @discord.ui.button(
        label="Automatic Redemption",
        style=discord.ButtonStyle.primary,
        custom_id="auto_gift_settings",
        emoji=f"{theme.giftIcon}",
        row=0
    )
    async def auto_gift_settings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.setup_giftcode_auto(interaction)

    @discord.ui.button(
        label="Redemption Priority",
        style=discord.ButtonStyle.primary,
        custom_id="redemption_priority",
        emoji=f"{theme.chartIcon}",
        row=0
    )
    async def redemption_priority_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.show_redemption_priority(interaction)

    @discord.ui.button(
        label="Channel History Scan",
        style=discord.ButtonStyle.secondary,
        custom_id="channel_history_scan",
        emoji=f"{theme.searchIcon}",
        row=1
    )
    async def channel_history_scan_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.channel_history_scan(interaction)

    @discord.ui.button(
        label="CAPTCHA Settings",
        style=discord.ButtonStyle.secondary,
        custom_id="captcha_settings",
        emoji=f"{theme.settingsIcon}",
        row=1
    )
    async def captcha_settings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.show_ocr_settings(interaction)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        custom_id="back_to_main",
        emoji=f"{theme.backIcon}",
        row=2
    )
    async def back_to_main_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.show_gift_menu(interaction)

class RedemptionPriorityView(discord.ui.View):
    def __init__(self, cog, alliances_with_priority, lang: str):
        super().__init__(timeout=7200)
        self.cog = cog
        self.alliances = alliances_with_priority  # List of (alliance_id, name, priority)
        self.selected_alliance_id = None
        self.lang = lang

        # Alliance select menu
        options = [
            discord.SelectOption(
                label=f"{idx}. {name}",
                value=str(alliance_id),
                description=t("gift.priority.position", lang, position=idx)
            )
            for idx, (alliance_id, name, _) in enumerate(self.alliances, 1)
        ]

        if options:
            self.alliance_select = discord.ui.Select(
                placeholder=t("gift.priority.select_placeholder", lang),
                options=options[:25],  # Discord limit
                row=0
            )
            self.alliance_select.callback = self.alliance_select_callback
            self.add_item(self.alliance_select)

    async def alliance_select_callback(self, interaction: discord.Interaction):
        self.selected_alliance_id = int(self.alliance_select.values[0])

        # Update embed to show selected alliance with marker
        embed = discord.Embed(
            title=f"{theme.chartIcon} {t('gift.priority.title', self.lang)}",
            description=t("gift.priority.description", self.lang),
            color=theme.emColor1
        )

        priority_list = []
        for idx, (alliance_id, name, _) in enumerate(self.alliances, 1):
            marker = " ◀" if alliance_id == self.selected_alliance_id else ""
            priority_list.append(f"`{idx}.` **{name}**{marker}")

        embed.add_field(
            name=t("gift.priority.current_order", self.lang),
            value="\n".join(priority_list) if priority_list else t("gift.priority.none", self.lang),
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Move Up", style=discord.ButtonStyle.primary, emoji=f"{theme.upIcon}", row=1)
    async def move_up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_alliance_id:
            await interaction.response.send_message(t("gift.priority.select_first", self.lang), ephemeral=True)
            return

        # Find current position
        current_idx = next((i for i, (aid, _, _) in enumerate(self.alliances) if aid == self.selected_alliance_id), None)
        if current_idx is None or current_idx == 0:
            await interaction.response.send_message(t("gift.priority.already_top", self.lang), ephemeral=True)
            return

        # Swap with the alliance above
        await self._swap_priorities(current_idx, current_idx - 1)
        await self._refresh_view(interaction)

    @discord.ui.button(label="Move Down", style=discord.ButtonStyle.primary, emoji=f"{theme.downIcon}", row=1)
    async def move_down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_alliance_id:
            await interaction.response.send_message(t("gift.priority.select_first", self.lang), ephemeral=True)
            return

        # Find current position
        current_idx = next((i for i, (aid, _, _) in enumerate(self.alliances) if aid == self.selected_alliance_id), None)
        if current_idx is None or current_idx >= len(self.alliances) - 1:
            await interaction.response.send_message(t("gift.priority.already_bottom", self.lang), ephemeral=True)
            return

        # Swap with the alliance below
        await self._swap_priorities(current_idx, current_idx + 1)
        await self._refresh_view(interaction)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.secondary, emoji=f"{theme.verifiedIcon}", row=1)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{theme.chartIcon} {t('gift.priority.updated_title', self.lang)}",
                description=t("gift.priority.updated_body", self.lang),
                color=theme.emColor3
            ),
            view=None
        )

    async def _swap_priorities(self, idx1, idx2):
        """Swap the priorities of two alliances in the list and database."""
        alliance1_id, name1, priority1 = self.alliances[idx1]
        alliance2_id, name2, priority2 = self.alliances[idx2]

        # Assign new sequential priorities based on position
        new_priority1 = idx2 + 1
        new_priority2 = idx1 + 1

        # Update database
        self.cog.cursor.execute("""
            INSERT INTO giftcodecontrol (alliance_id, status, priority)
            VALUES (?, 0, ?)
            ON CONFLICT(alliance_id) DO UPDATE SET priority = excluded.priority
        """, (alliance1_id, new_priority1))

        self.cog.cursor.execute("""
            INSERT INTO giftcodecontrol (alliance_id, status, priority)
            VALUES (?, 0, ?)
            ON CONFLICT(alliance_id) DO UPDATE SET priority = excluded.priority
        """, (alliance2_id, new_priority2))

        self.cog.conn.commit()

        # Swap in local list
        self.alliances[idx1] = (alliance1_id, name1, new_priority1)
        self.alliances[idx2] = (alliance2_id, name2, new_priority2)
        self.alliances[idx1], self.alliances[idx2] = self.alliances[idx2], self.alliances[idx1]

    async def _refresh_view(self, interaction: discord.Interaction):
        """Refresh the embed and view after a priority change."""
        # Rebuild embed
        embed = discord.Embed(
            title=f"{theme.chartIcon} {t('gift.priority.title', self.lang)}",
            description=t("gift.priority.description", self.lang),
            color=theme.emColor1
        )

        priority_list = []
        for idx, (alliance_id, name, _) in enumerate(self.alliances, 1):
            marker = " ◀" if alliance_id == self.selected_alliance_id else ""
            priority_list.append(f"`{idx}.` **{name}**{marker}")

        embed.add_field(
            name=t("gift.priority.current_order", self.lang),
            value="\n".join(priority_list) if priority_list else t("gift.priority.none", self.lang),
            inline=False
        )

        # Rebuild select options
        options = [
            discord.SelectOption(
                label=f"{idx}. {name}",
                value=str(alliance_id),
                description=t("gift.priority.position", self.lang, position=idx)
            )
            for idx, (alliance_id, name, _) in enumerate(self.alliances, 1)
        ]

        if options:
            self.alliance_select.options = options[:25]

        await interaction.response.edit_message(embed=embed, view=self)

class ClearCacheConfirmView(discord.ui.View):
    def __init__(self, parent_cog, lang: str):
        super().__init__(timeout=60)
        self.parent_cog = parent_cog
        self.lang = lang
        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue
            if child.label == "Confirm":
                child.label = t("gift.ocr.cache_confirm_button", self.lang)
            elif child.label == "Cancel":
                child.label = t("gift.button.cancel", self.lang)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji=f"{theme.verifiedIcon}")
    async def confirm_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        try: # Clear the user_giftcodes table
            self.parent_cog.cursor.execute("DELETE FROM user_giftcodes")
            deleted_count = self.parent_cog.cursor.rowcount
            self.parent_cog.conn.commit()
            
            success_embed = discord.Embed(
                title=f"{theme.verifiedIcon} {t('gift.ocr.cache_cleared_title', self.lang)}",
                description=t("gift.ocr.cache_cleared_body", self.lang, count=f"{deleted_count:,}"),
                color=theme.emColor3
            )
            
            self.parent_cog.logger.info(f"Redemption cache cleared by user {interaction.user.id}: {deleted_count} records deleted")
            
            await interaction.response.edit_message(embed=success_embed, view=None)
            
        except Exception as e:
            self.parent_cog.logger.exception(f"Error clearing redemption cache: {e}")
            error_embed = discord.Embed(
                title=f"{theme.deniedIcon} {t('gift.ocr.cache_clear_error_title', self.lang)}",
                description=t("gift.ocr.cache_clear_error_body", self.lang, error=str(e)),
                color=theme.emColor2
            )
            try:
                await interaction.response.edit_message(embed=error_embed, view=None)
            except discord.InteractionResponded:
                await interaction.followup.edit_message(interaction.message.id, embed=error_embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji=f"{theme.deniedIcon}")
    async def cancel_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        cancel_embed = discord.Embed(
            title=f"{theme.deniedIcon} {t('gift.ocr.cache_cancelled_title', self.lang)}",
            description=t("gift.ocr.cache_cancelled_body", self.lang),
            color=theme.emColor1
        )
        await interaction.response.edit_message(embed=cancel_embed, view=None)

    async def on_timeout(self):
        """Handle timeout by disabling all buttons"""
        for item in self.children:
            item.disabled = True
        try:
            timeout_embed = discord.Embed(
                title=f"{theme.timeIcon} {t('gift.ocr.cache_timeout_title', self.lang)}",
                description=t("gift.ocr.cache_timeout_body", self.lang),
                color=discord.Color.orange()
            )
        except:
            pass

class OCRSettingsView(discord.ui.View):
    def __init__(self, cog, ocr_settings, onnx_available, lang: str):
        super().__init__(timeout=7200)
        self.cog = cog
        self.enabled = ocr_settings[0]
        self.save_images_setting = ocr_settings[1]
        self.onnx_available = onnx_available
        self.disable_controls = not onnx_available
        self.lang = lang

        # Row 0: Enable/Disable Button, Test Button
        self.enable_ocr_button_item = discord.ui.Button(
            emoji=f"{theme.verifiedIcon}" if self.enabled == 1 else "🚫",
            custom_id="enable_ocr", row=0,
            label=t("gift.ocr.button.disable_solver", self.lang) if self.enabled == 1 else t("gift.ocr.button.enable_solver", self.lang),
            style=discord.ButtonStyle.danger if self.enabled == 1 else discord.ButtonStyle.success,
            disabled=self.disable_controls
        )
        self.enable_ocr_button_item.callback = self.enable_ocr_button
        self.add_item(self.enable_ocr_button_item)

        self.test_ocr_button_item = discord.ui.Button(
            label=t("gift.ocr.button.test_solver", self.lang), style=discord.ButtonStyle.secondary, emoji=f"{theme.testIcon}",
            custom_id="test_ocr", row=0,
            disabled=self.disable_controls
        )
        self.test_ocr_button_item.callback = self.test_ocr_button
        self.add_item(self.test_ocr_button_item)

        # Add the Change Test ID Button
        self.change_test_fid_button_item = discord.ui.Button(
            label=t("gift.ocr.button.change_test_id", self.lang), style=discord.ButtonStyle.primary, emoji=f"{theme.refreshIcon}",
            custom_id="change_test_fid", row=0,
            disabled=self.disable_controls
        )
        self.change_test_fid_button_item.callback = self.change_test_fid_button
        self.add_item(self.change_test_fid_button_item)

        # Add the Clear Redemption Cache Button
        self.clear_cache_button_item = discord.ui.Button(
            label=t("gift.ocr.button.clear_cache", self.lang), style=discord.ButtonStyle.danger, emoji=f"{theme.trashIcon}",
            custom_id="clear_redemption_cache", row=1,
            disabled=self.disable_controls
        )
        self.clear_cache_button_item.callback = self.clear_redemption_cache_button
        self.add_item(self.clear_cache_button_item)

        # Row 2: Image Save Select Menu
        self.image_save_select_item = discord.ui.Select(
            placeholder=t("gift.ocr.select.placeholder", self.lang),
            min_values=1, max_values=1, row=2, custom_id="image_save_select",
            options=[
                discord.SelectOption(
                    label=t("gift.ocr.select.none", self.lang),
                    value="0",
                    description=t("gift.ocr.select.none_desc", self.lang)
                ),
                discord.SelectOption(
                    label=t("gift.ocr.select.failed", self.lang),
                    value="1",
                    description=t("gift.ocr.select.failed_desc", self.lang)
                ),
                discord.SelectOption(
                    label=t("gift.ocr.select.success", self.lang),
                    value="2",
                    description=t("gift.ocr.select.success_desc", self.lang)
                ),
                discord.SelectOption(
                    label=t("gift.ocr.select.all", self.lang),
                    value="3",
                    description=t("gift.ocr.select.all_desc", self.lang)
                )
            ],
            disabled=self.disable_controls
        )
        for option in self.image_save_select_item.options:
            option.default = (str(self.save_images_setting) == option.value)
        self.image_save_select_item.callback = self.image_save_select_callback
        self.add_item(self.image_save_select_item)

    async def change_test_fid_button(self, interaction: discord.Interaction):
        """Handle the change test ID button click."""
        if not self.onnx_available:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.ocr.error.onnx_missing', self.lang)}",
                ephemeral=True
            )
            return
        await interaction.response.send_modal(TestIDModal(self.cog, self.lang))

    async def enable_ocr_button(self, interaction: discord.Interaction):
        if not self.onnx_available:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.ocr.error.onnx_missing', self.lang)}",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        new_enabled = 1 if self.enabled == 0 else 0
        success, message = await self.cog.update_ocr_settings(interaction, enabled=new_enabled, lang=self.lang)
        await self.cog.show_ocr_settings(interaction)

    async def test_ocr_button(self, interaction: discord.Interaction):
        logger = self.cog.logger
        user_id = interaction.user.id
        current_time = time.time()

        if not self.onnx_available:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.ocr.error.onnx_missing', self.lang)}",
                ephemeral=True
            )
            return
        if not self.cog.captcha_solver or not self.cog.captcha_solver.is_initialized:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.ocr.error.solver_not_ready', self.lang)}",
                ephemeral=True
            )
            return

        last_test_time = self.cog.test_captcha_cooldowns.get(user_id, 0)
        if current_time - last_test_time < self.cog.test_captcha_delay:
            remaining_time = int(self.cog.test_captcha_delay - (current_time - last_test_time))
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.ocr.error.test_cooldown', self.lang, seconds=remaining_time)}",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        logger.info(f"[Test Button] User {user_id} triggered test.")
        self.cog.test_captcha_cooldowns[user_id] = current_time

        captcha_image_base64 = None
        image_bytes = None
        error = None
        captcha_code = None
        success = False
        method = "N/A"
        confidence = 0.0
        solve_duration = 0.0
        test_fid = self.cog.get_test_fid()

        try:
            logger.info(f"[Test Button] First logging in with test ID {test_fid}...")
            session, response_stove_info = self.cog.get_stove_info_wos(player_id=test_fid)
            
            try:
                player_info_json = response_stove_info.json()
                if player_info_json.get("msg") != "success":
                    logger.error(f"[Test Button] Login failed for test ID {test_fid}: {player_info_json.get('msg')}")
                    await interaction.followup.send(
                        f"{theme.deniedIcon} {t('gift.ocr.test_login_failed', self.lang, test_id=test_fid)}",
                        ephemeral=True
                    )
                    return
                logger.info(f"[Test Button] Successfully logged in with test ID {test_fid}")
            except Exception as json_err:
                logger.error(f"[Test Button] Error parsing login response: {json_err}")
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_login_parse_error', self.lang)}",
                    ephemeral=True
                )
                return
            
            logger.info(f"[Test Button] Fetching captcha for test ID {test_fid} using established session...")
            captcha_image_base64, error = await self.cog.fetch_captcha(test_fid, session=session)
            logger.info(f"[Test Button] Captcha fetch result: Error='{error}', HasImage={captcha_image_base64 is not None}")

            if error:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_fetch_error', self.lang, error=error)}",
                    ephemeral=True
                )
                return

            if captcha_image_base64:
                try:
                    if captcha_image_base64.startswith("data:image"):
                        img_b64_data = captcha_image_base64.split(",", 1)[1]
                    else:
                        img_b64_data = captcha_image_base64
                    image_bytes = base64.b64decode(img_b64_data)
                    logger.info("[Test Button] Successfully decoded base64 image.")
                except Exception as decode_err:
                    logger.error(f"[Test Button] Failed to decode base64 image: {decode_err}")
                    await interaction.followup.send(
                        f"{theme.deniedIcon} {t('gift.ocr.test_decode_error', self.lang)}",
                        ephemeral=True
                    )
                    return
            else:
                logger.error("[Test Button] Captcha fetch returned no image data.")
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_no_image', self.lang)}",
                    ephemeral=True
                )
                return

            if image_bytes:
                logger.info("[Test Button] Solving fetched captcha...")
                start_solve_time = time.time()
                captcha_code, success, method, confidence, _ = await self.cog.captcha_solver.solve_captcha(
                    image_bytes, fid=f"test-{user_id}", attempt=0
                )
                solve_duration = time.time() - start_solve_time
                log_confidence_str = f'{confidence:.2f}' if isinstance(confidence, float) else 'N/A'
                logger.info(f"[Test Button] Solve result: Success={success}, Code='{captcha_code}', Method='{method}', Conf={log_confidence_str}. Duration: {solve_duration:.2f}s")
            else:
                 logger.error("[Test Button] Logic error: image_bytes is None before solving.")
                 await interaction.followup.send(
                     f"{theme.deniedIcon} {t('gift.ocr.test_internal_error', self.lang)}",
                     ephemeral=True
                 )
                 return

            confidence_str = f'{confidence:.2f}' if isinstance(confidence, float) else 'N/A'
            ocr_success_text = (
                f"{theme.verifiedIcon} {t('gift.common.yes', self.lang)}"
                if success
                else f"{theme.deniedIcon} {t('gift.common.no', self.lang)}"
            )
            embed = discord.Embed(
                title=f"{theme.searchIcon} {t('gift.ocr.test_results_title', self.lang)}",
                description=(
                    f"**{t('gift.ocr.test_summary', self.lang)}**\n{theme.upperDivider}\n"
                    f"{theme.robotIcon} **{t('gift.ocr.test_ocr_success', self.lang)}** {ocr_success_text}\n"
                    f"{theme.searchIcon} **{t('gift.ocr.test_code', self.lang)}** `{captcha_code if success and captcha_code else t('gift.common.na', self.lang)}`\n"
                    f"{theme.chartIcon} **{t('gift.ocr.test_confidence', self.lang)}** `{confidence_str}`\n"
                    f"{theme.timeIcon} **{t('gift.ocr.test_solve_time', self.lang)}** `{solve_duration:.2f}s`\n"
                    f"{theme.lowerDivider}\n"
                ), color=theme.emColor3 if success else discord.Color.red()
            )

            save_path_str = None
            save_error_str = None
            try:
                self.cog.settings_cursor.execute("SELECT save_images FROM ocr_settings ORDER BY id DESC LIMIT 1")
                save_setting_row = self.cog.settings_cursor.fetchone()
                current_save_mode = save_setting_row[0] if save_setting_row else 0

                should_save_img = False
                save_tag = "UNKNOWN"
                if success and current_save_mode in [2, 3]:
                    should_save_img = True
                    save_tag = captcha_code if captcha_code else "SUCCESS_NOCDE"
                elif not success and current_save_mode in [1, 3]:
                    should_save_img = True
                    save_tag = "FAILED"

                if should_save_img and image_bytes:
                    logger.info(f"[Test Button] Attempting to save image based on mode {current_save_mode}. Status success={success}, tag='{save_tag}'")
                    captcha_dir = self.cog.captcha_solver.captcha_dir
                    safe_tag = re.sub(r'[\\/*?:"<>|]', '_', save_tag)
                    timestamp = int(time.time())

                    if success:
                         base_filename = f"{safe_tag}.png"
                    else:
                         base_filename = f"FAIL_{safe_tag}_{timestamp}.png"

                    test_path = os.path.join(captcha_dir, base_filename)

                    counter = 1
                    orig_path = test_path
                    while os.path.exists(test_path) and counter <= 100:
                        name, ext = os.path.splitext(orig_path)
                        test_path = f"{name}_{counter}{ext}"
                        counter += 1

                    if counter > 100:
                        save_error_str = t(
                            "gift.ocr.test_save_name_error",
                            self.lang,
                            filename=base_filename
                        )
                        logger.warning(f"[Test Button] {save_error_str}")
                    else:
                        os.makedirs(captcha_dir, exist_ok=True)
                        with open(test_path, "wb") as f:
                            f.write(image_bytes)
                        save_path_str = os.path.basename(test_path)
                        logger.info(f"[Test Button] Saved test captcha image to {test_path}")

            except Exception as img_save_err:
                logger.exception(f"[Test Button] Error saving test image: {img_save_err}")
                save_error_str = t("gift.ocr.test_save_error", self.lang, error=img_save_err)

            if save_path_str:
                embed.add_field(
                    name=f"{theme.saveIcon} {t('gift.ocr.test_image_saved_title', self.lang)}",
                    value=t(
                        "gift.ocr.test_image_saved_body",
                        self.lang,
                        filename=save_path_str,
                        directory=os.path.relpath(self.cog.captcha_solver.captcha_dir)
                    ),
                    inline=False
                )
            elif save_error_str:
                embed.add_field(
                    name=f"{theme.warnIcon} {t('gift.ocr.test_image_save_error_title', self.lang)}",
                    value=save_error_str,
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"[Test Button] Test completed for user {user_id}.")

        except requests.exceptions.ConnectionError:
            logger.warning(f"[Test Button] Connection error for user {user_id}. WOS API may be unavailable.")
            try:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_connection_error', self.lang)}",
                    ephemeral=True
                )
            except Exception:
                pass
        except requests.exceptions.Timeout:
            logger.warning(f"[Test Button] Timeout for user {user_id}. WOS API may be slow.")
            try:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_timeout', self.lang)}",
                    ephemeral=True
                )
            except Exception:
                pass
        except requests.exceptions.RequestException as e:
            logger.warning(f"[Test Button] Request error for user {user_id}: {type(e).__name__}")
            try:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_request_error', self.lang, error=type(e).__name__)}",
                    ephemeral=True
                )
            except Exception:
                pass
        except Exception as e:
            logger.exception(f"[Test Button] UNEXPECTED Error during test for user {user_id}: {e}")
            try:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('gift.ocr.test_unexpected_error', self.lang, error=e)}",
                    ephemeral=True
                )
            except Exception as followup_err:
                logger.error(f"[Test Button] Failed to send final error followup to user {user_id}: {followup_err}")

    async def clear_redemption_cache_button(self, interaction: discord.Interaction):
        """Handle the clear redemption cache button click."""
        if not self.onnx_available:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.ocr.error.onnx_missing', self.lang)}",
                ephemeral=True
            )
            return

        # Create confirmation embed
        embed = discord.Embed(
            title=f"{theme.warnIcon} {t('gift.ocr.cache_clear_title', self.lang)}",
            description=(
                f"{t('gift.ocr.cache_clear_desc', self.lang)}"
            ),
            color=discord.Color.orange()
        )

        # Get current count for display
        try:
            self.cog.cursor.execute("SELECT COUNT(*) FROM user_giftcodes")
            current_count = self.cog.cursor.fetchone()[0]
            embed.add_field(
                name=f"{theme.chartIcon} {t('gift.ocr.cache_current_records', self.lang)}",
                value=t("gift.ocr.cache_current_records_value", self.lang, count=f"{current_count:,}"),
                inline=False
            )
        except Exception as e:
            self.cog.logger.error(f"Error getting user_giftcodes count: {e}")
            embed.add_field(
                name=f"{theme.chartIcon} {t('gift.ocr.cache_current_records', self.lang)}",
                value=t("gift.ocr.cache_current_records_error", self.lang),
                inline=False
            )

        # Create confirmation view
        confirm_view = ClearCacheConfirmView(self.cog, self.lang)
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

    async def image_save_select_callback(self, interaction: discord.Interaction):
        if not self.onnx_available:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('gift.ocr.error.onnx_missing', self.lang)}",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True) 
        
        try:
            selected_value = int(interaction.data["values"][0])
        
            success, message = await self.cog.update_ocr_settings(
                interaction=interaction,
                save_images=selected_value,
                lang=self.lang
            )

            if success:
                self.save_images_setting = selected_value
                for option in self.image_save_select_item.options:
                    option.default = (str(self.save_images_setting) == option.value)
            else:
                await interaction.followup.send(f"{theme.deniedIcon} {message}", ephemeral=True)

        except ValueError:
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('gift.ocr.select_invalid', self.lang)}",
                ephemeral=True
            )
        except Exception as e:
            self.cog.logger.exception("Error processing image save selection in OCRSettingsView.")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('gift.ocr.select_update_error', self.lang)}",
                ephemeral=True
            )
        
        async def update_task(save_images_value):
            self.cog.logger.info(f"Task started: Updating OCR save_images to {save_images_value}")
            _success, _message = await self.cog.update_ocr_settings(
                interaction=None,
                save_images=save_images_value,
                lang=self.lang
            )
            self.cog.logger.info(f"Task finished: update_ocr_settings returned success={_success}, message='{_message}'")
            return _success, _message

        update_job = asyncio.create_task(update_task(selected_value))
        initial_followup_message = f"{theme.hourglassIcon} {t('gift.ocr.update_in_progress', self.lang)}"
        try:
            progress_message = await interaction.followup.send(initial_followup_message, ephemeral=True)
        except discord.HTTPException as e:
            self.cog.logger.error(f"Failed to send initial followup for image save: {e}")
            return

        try:
            success, message_from_task = await asyncio.wait_for(update_job, timeout=60.0)
        except asyncio.TimeoutError:
            self.cog.logger.error("Timeout waiting for OCR settings update task to complete.")
            await progress_message.edit(content=f"{t('gift.ocr.update_timeout', self.lang)}")
            return
        except Exception as e_task:
            self.cog.logger.exception(f"Exception in OCR settings update task: {e_task}")
            await progress_message.edit(
                content=f"{theme.deniedIcon} {t('gift.ocr.update_error', self.lang, error=e_task)}"
            )
            return

        if success:
            self.cog.logger.info(f"OCR settings update successful: {message_from_task}")
            self.cog.settings_cursor.execute("SELECT enabled, save_images FROM ocr_settings ORDER BY id DESC LIMIT 1")
            ocr_settings_new = self.cog.settings_cursor.fetchone()
            if ocr_settings_new:
                self.save_images_setting = ocr_settings_new[1]
                for option in self.image_save_select_item.options:
                    option.default = (str(self.save_images_setting) == option.value)
            
            try:
                new_embed = interaction.message.embeds[0] if interaction.message.embeds else None

                await interaction.edit_original_response(
                    content=None,
                    embed=new_embed, 
                    view=self
                )
                await progress_message.edit(content=f"{theme.verifiedIcon} {message_from_task}")
            except discord.NotFound:
                 self.cog.logger.warning("Original message or progress message for OCR settings not found for final update.")
            except Exception as e_edit_final:
                 self.cog.logger.exception(f"Error editing messages after successful OCR settings update: {e_edit_final}")
                 await progress_message.edit(
                     content=f"{theme.verifiedIcon} {message_from_task}\n{theme.warnIcon} {t('gift.ocr.update_refresh_warn', self.lang)}"
                 )

        else:
            self.cog.logger.error(f"OCR settings update failed: {message_from_task}")
            await progress_message.edit(content=f"{theme.deniedIcon} {message_from_task}")

async def setup(bot):
    await bot.add_cog(GiftOperations(bot))