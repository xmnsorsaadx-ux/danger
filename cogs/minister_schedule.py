import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import sqlite3
import aiohttp
import hashlib
from aiohttp_socks import ProxyConnector
import time
import re
from datetime import datetime
import json
from .pimp_my_bot import theme
from i18n import get_guild_language, t

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

SECRET = 'tB87#kPtkxqOS2'


def _get_lang(interaction: discord.Interaction | None) -> str:
    guild_id = interaction.guild.id if interaction and interaction.guild else None
    return get_guild_language(guild_id)

class ChannelSelectView(discord.ui.View):
    def __init__(self, bot, context: str, lang: str):
        super().__init__(timeout=None)
        self.add_item(ChannelSelect(bot, context, lang))

class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, context: str, lang: str):
        self.bot = bot
        self.context = context

        super().__init__(
            placeholder=t("minister.channel.select_placeholder", lang),
            channel_types=[
                discord.ChannelType.text,
                discord.ChannelType.private,
                discord.ChannelType.news,
                discord.ChannelType.forum,
                discord.ChannelType.news_thread,
                discord.ChannelType.public_thread,
                discord.ChannelType.private_thread,
                discord.ChannelType.stage_voice
            ],
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        selected_channel = self.values[0]
        channel_id = selected_channel.id

        try:
            svs_conn = sqlite3.connect("db/svs.sqlite")
            svs_cursor = svs_conn.cursor()
            
            # Check if we're updating a minister channel
            if self.context.endswith("channel"):
                # Get the activity name from the context (e.g., "Construction Day channel" -> "Construction Day")
                activity_name = self.context.replace(" channel", "")
                
                # Check if this is one of the minister activity channels
                if activity_name in ["Construction Day", "Research Day", "Troops Training Day"]:
                    # Get the old channel ID if it exists
                    svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", (self.context,))
                    old_channel_row = svs_cursor.fetchone()
                    
                    if old_channel_row:
                        old_channel_id = int(old_channel_row[0])
                        # Get the message ID for this activity
                        svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", (activity_name,))
                        message_row = svs_cursor.fetchone()
                        
                        if message_row and old_channel_id != channel_id:
                            # Delete the old message if channel has changed
                            message_id = int(message_row[0])
                            guild = interaction.guild
                            if guild:
                                old_channel = guild.get_channel(old_channel_id)
                                if old_channel:
                                    try:
                                        old_message = await old_channel.fetch_message(message_id)
                                        await old_message.delete()
                                    except:
                                        pass  # Message might already be deleted
                            
                            # Remove the message reference so it will be recreated in the new channel
                            svs_cursor.execute("DELETE FROM reference WHERE context=?", (activity_name,))
            
            # Update the channel reference
            svs_cursor.execute("""
                INSERT INTO reference (context, context_id)
                VALUES (?, ?)
                ON CONFLICT(context) DO UPDATE SET context_id = excluded.context_id;
            """, (self.context, channel_id))
            svs_conn.commit()
            
            # Trigger message update in the new channel
            if self.context.endswith("channel"):
                activity_name = self.context.replace(" channel", "")
                if activity_name in ["Construction Day", "Research Day", "Troops Training Day"]:
                    minister_menu_cog = self.bot.get_cog("MinisterMenu")
                    if minister_menu_cog:
                        await minister_menu_cog.update_channel_message(activity_name)
            
            svs_conn.close()

            # Check if this is being called from the minister menu system
            minister_menu_cog = self.bot.get_cog("MinisterMenu")
            if minister_menu_cog and self.context.endswith("channel"):
                # Return to channel configuration menu with confirmation
                embed = discord.Embed(
                    title=f"{theme.editListIcon} {t('minister.channel.setup_title', lang)}",
                    description=t(
                        "minister.channel.setup_desc",
                        lang,
                        context=self.context,
                        channel_id=channel_id,
                        settings_icon=theme.settingsIcon,
                        search_icon=theme.searchIcon,
                        alliance_icon=theme.allianceIcon,
                        document_icon=theme.documentIcon,
                    ),
                    color=theme.emColor3
                )

                # Get the ChannelConfigurationView from minister_menu
                import sys
                minister_menu_module = minister_menu_cog.__class__.__module__
                ChannelConfigurationView = getattr(sys.modules[minister_menu_module], 'ChannelConfigurationView')
                
                view = ChannelConfigurationView(self.bot, minister_menu_cog)
                
                await interaction.response.edit_message(
                    content=None, # Clear the "Select a channel for..." content
                    embed=embed,
                    view=view
                )
            else:
                # Fallback for other contexts
                await interaction.response.edit_message(
                    content=t(
                        "minister.channel.set_success",
                        lang,
                        context=self.context,
                        channel_id=channel_id,
                        icon=theme.verifiedIcon
                    ),
                    view=None
                )

        except Exception as e:
            try:
                await interaction.response.send_message(
                    t("minister.channel.update_failed", lang, error=str(e), icon=theme.deniedIcon),
                    ephemeral=True
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    t("minister.channel.update_failed", lang, error=str(e), icon=theme.deniedIcon),
                    ephemeral=True
                )

class MinisterSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users_conn = sqlite3.connect('db/users.sqlite')
        self.users_cursor = self.users_conn.cursor()
        self.settings_conn = sqlite3.connect('db/settings.sqlite')
        self.settings_cursor = self.settings_conn.cursor()
        self.alliance_conn = sqlite3.connect('db/alliance.sqlite')
        self.alliance_cursor = self.alliance_conn.cursor()
        self.svs_conn = sqlite3.connect("db/svs.sqlite")
        self.svs_cursor = self.svs_conn.cursor()

        self.svs_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS appointments (
                        fid INTEGER,
                        appointment_type TEXT,
                        time TEXT,
                        alliance INTEGER,
                        PRIMARY KEY (fid, appointment_type)
                    );
                """)
        self.svs_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reference (
                        context TEXT PRIMARY KEY,
                        context_id INTEGER
                    );
                """)
        self.svs_cursor.execute("""
            INSERT OR IGNORE INTO reference (context, context_id)
            VALUES ('list type', 1);
        """)
        self.svs_cursor.execute("""
            INSERT OR IGNORE INTO reference (context, context_id)
            VALUES ('slot_mode', 0);
        """)

        self.svs_conn.commit()

    async def fetch_user_data(self, fid, proxy=None):
        url = 'https://wos-giftcode-api.centurygame.com/api/player'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        current_time = int(time.time() * 1000)
        form = f"fid={fid}&time={current_time}"
        sign = hashlib.md5((form + SECRET).encode('utf-8')).hexdigest()
        form = f"sign={sign}&{form}"

        try:
            connector = ProxyConnector.from_url(proxy) if proxy else None
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, data=form, ssl=False) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return response.status
        except Exception as e:
            return None

    async def send_embed_to_channel(self, embed):
        """Sends the embed message to a specific channel."""
        log_channel_id = await self.get_channel_id("minister log channel")
        log_channel = self.bot.get_channel(log_channel_id)

        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print(f"Error: Could not find the log channel please change it to a valid channel")

    async def is_admin(self, user_id: int) -> bool:
        if user_id == self.bot.owner_id:
            return True
        self.settings_cursor.execute("SELECT 1 FROM admin WHERE id=?", (user_id,))
        return self.settings_cursor.fetchone() is not None

    async def log_change(self, action_type: str, user, appointment_type: str = None, fid: int = None,
                        nickname: str = None, old_time: str = None, new_time: str = None,
                        alliance_name: str = None, additional_data: str = None, archive_id: int = None):
        """
        Log a change to the minister change history table.

        Args:
            action_type: Type of action (add, remove, reschedule, clear_all, time_slot_mode_change, archive_created)
            user: Discord user object who made the change
            appointment_type: Type of appointment (Construction Day, Research Day, etc.)
            fid: User FID
            nickname: User nickname
            old_time: Previous time slot (for reschedule)
            new_time: New time slot (for add/reschedule)
            alliance_name: Alliance name
            additional_data: JSON string with extra context
            archive_id: Archive ID if this change is associated with an archive
        """
        try:
            timestamp = datetime.now().isoformat()
            discord_user_id = user.id
            discord_username = user.display_name

            self.svs_cursor.execute("""
                INSERT INTO minister_change_history
                (archive_id, timestamp, discord_user_id, discord_username, action_type,
                 appointment_type, fid, nickname, old_time, new_time, alliance_name, additional_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (archive_id, timestamp, discord_user_id, discord_username, action_type,
                  appointment_type, fid, nickname, old_time, new_time, alliance_name, additional_data))

            self.svs_conn.commit()
        except Exception as e:
            print(f"Error logging change: {e}")

    def fix_arabic(self, text):
        """
        Fix Arabic text rendering by reshaping and applying bidirectional algorithm.
        """
        if not text or not ARABIC_SUPPORT:
            return text

        # Check if text contains Arabic characters
        if re.search(r'[\u0600-\u06FF]', text):
            try:
                reshaped = arabic_reshaper.reshape(text)
                return get_display(reshaped)
            except Exception:
                return text
        return text

    def get_time_slots(self, slot_mode: int):
        """
        Generate time slots based on the slot mode.

        Mode 0 (Standard): 00:00, 00:30, 01:00, ..., 23:30 (48 slots × 30min)
        Mode 1 (Offset): 00:00 (15min), 00:15, 00:45, 01:15, ..., 23:45 (15min to midnight)

        Returns: List of time strings in HH:MM format
        """
        time_slots = []

        if slot_mode == 0:
            # Standard mode: 30-minute intervals starting at 00:00
            for hour in range(24):
                for minute in (0, 30):
                    time_slots.append(f"{hour:02}:{minute:02}")
        else:
            # Offset mode: First slot at 00:00 (15min), then 30min slots at :15 and :45
            time_slots.append("00:00")  # First slot: 00:00-00:15
            for hour in range(24):
                for minute in (15, 45):
                    if hour == 23 and minute == 45:
                        time_slots.append("23:45")  # Last slot: 23:45-00:00
                        break
                    time_slots.append(f"{hour:02}:{minute:02}")

        return time_slots

    async def show_minister_channel_menu(self, interaction: discord.Interaction):
        # Redirect to the MinisterMenu cog
        minister_cog = self.bot.get_cog("MinisterMenu")
        if minister_cog:
            await minister_cog.show_minister_channel_menu(interaction)
        else:
            await interaction.response.send_message(
                f"{theme.deniedIcon} Minister Menu module not found.",
                ephemeral=True
            )

    # Autocomplete handler for appointment type
    async def appointment_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            choices = [
                discord.app_commands.Choice(name="Construction Day", value="Construction Day"),
                discord.app_commands.Choice(name="Research Day", value="Research Day"),
                discord.app_commands.Choice(name="Troops Training Day", value="Troops Training Day")
            ]
            if current:
                filtered_choices = [choice for choice in choices if current.lower() in choice.name.lower()]
            else:
                filtered_choices = choices

            return filtered_choices
        except Exception as e:
            print(f"Error in appointment type autocomplete: {e}")
            return []

    # Autocomplete handler for names
    async def fid_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            # Fetch selected appointment type from interaction
            appointment_type = next(
                (option["value"] for option in interaction.data.get("options", []) if option["name"] == "appointment_type"),
                None
            )

            if not appointment_type:
                return []  # If no appointment type is selected, return an empty list

            # Fetch all registered users
            self.users_cursor.execute("SELECT fid, nickname FROM users")
            users = self.users_cursor.fetchall()

            # Fetch users already booked for the selected appointment type
            self.svs_cursor.execute("SELECT fid FROM appointments WHERE appointment_type=?", (appointment_type,))
            booked_fids = {row[0] for row in self.svs_cursor.fetchall()}  # Convert to a set for quick lookup

            # Filter out booked users
            available_choices = [
                discord.app_commands.Choice(name=f"{nickname} ({fid})", value=str(fid))
                for fid, nickname in users if fid not in booked_fids
            ]

            # Apply search filtering if the user is typing
            if current:
                filtered_choices = [choice for choice in available_choices if current.lower() in choice.name.lower()][:25]
            else:
                filtered_choices = available_choices[:25]

            return filtered_choices
        except Exception as e:
            print(f"Autocomplete for fid failed: {e}")
            return []

    # Autocomplete handler for registered names
    async def registered_fid_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            # Fetch selected appointment type from interaction
            appointment_type = next(
                (option["value"] for option in interaction.data.get("options", []) if option["name"] == "appointment_type"),
                None
            )

            if not appointment_type:
                return []

            # Fetch users already booked for the selected appointment type
            self.svs_cursor.execute("SELECT fid FROM appointments WHERE appointment_type = ?", (appointment_type,))
            fids = [row[0] for row in self.svs_cursor.fetchall()]
            if not fids:
                return []

            placeholders = ",".join("?" for _ in fids)
            query = f"SELECT fid, nickname FROM users WHERE fid IN ({placeholders})"
            self.users_cursor.execute(query, fids)

            registered_users = self.users_cursor.fetchall()

            # Create choices list
            choices = [
                discord.app_commands.Choice(name=f"{nickname} ({fid})", value=str(fid))
                for fid, nickname in registered_users
            ]

            # Apply search filtering if the user is typing
            if current:
                filtered_choices = [choice for choice in choices if current.lower() in choice.name.lower()][:25]
            else:
                filtered_choices = choices[:25]

            return filtered_choices
        except Exception as e:
            print(f"Autocomplete for registered fid failed: {e}")
            return []

    # Autocomplete handler for time
    async def time_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            appointment_type = next(
                (option["value"] for option in interaction.data.get("options", []) if option["name"] == "appointment_type"),
                None
            )

            if not appointment_type:
                return []

            # Get current slot mode
            self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", ("slot_mode",))
            row = self.svs_cursor.fetchone()
            slot_mode = int(row[0]) if row else 0

            # Get booked times
            self.svs_cursor.execute("SELECT time FROM appointments WHERE appointment_type=?", (appointment_type,))
            booked_times = {row[0] for row in self.svs_cursor.fetchall()}

            # Generate time slots based on mode
            time_slots = self.get_time_slots(slot_mode)
            available_times = [time_slot for time_slot in time_slots if time_slot not in booked_times]

            # Ensure user input is properly formatted (normalize input)
            if current:
                # Normalize single-digit hours (e.g., "1:00" -> "01:00")
                parts = current.split(":")
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    formatted_input = f"{int(parts[0]):02}:{int(parts[1]):02}"
                else:
                    return []  # Invalid format

                # Ensure input is valid for current slot mode
                valid_times = set(time_slots)
                if formatted_input not in valid_times:
                    return []

                # Filter choices based on input
                filtered_choices = [
                    discord.app_commands.Choice(name=time, value=time)
                    for time in available_times if formatted_input in time
                ][:25]
            else:
                filtered_choices = [
                    discord.app_commands.Choice(name=time, value=time)
                    for time in available_times
                ][:25]

            return filtered_choices
        except Exception as e:
            print(f"Error in time autocomplete: {e}")
            return []

    # Autocomplete handler for choices of what to show
    async def choice_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            choices = [
                discord.app_commands.Choice(name="Show full minister list", value="all"),
                discord.app_commands.Choice(name="Show available slots only", value="available only")
            ]

            if current:
                filtered_choices = [choice for choice in choices if current.lower() in choice.name.lower()]
            else:
                filtered_choices = choices

            return filtered_choices
        except Exception as e:
            print(f"Error in all_or_available autocomplete: {e}")
            return []

    # handler for looping through all times and updating fids to current nickname
    async def update_time_list(self, booked_times, progress_callback=None):
        """
        Generates a list of time slots with their booking details, fetching nicknames from the API.
        Implements rate limit handling and batch processing.
        """
        time_list = []
        booked_fids = {}

        fids_to_fetch = {fid for fid, _ in booked_times.values() if fid}
        fetched_data = {}  # Cache API responses

        # Get current slot mode
        self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", ("slot_mode",))
        row = self.svs_cursor.fetchone()
        slot_mode = int(row[0]) if row else 0

        # Generate time slots based on mode
        time_slots = self.get_time_slots(slot_mode)

        for time_slot in time_slots:
            booked_fid, booked_alliance = booked_times.get(time_slot, ("", ""))

            booked_nickname = "Unknown"
            if booked_fid:
                # Check cache first
                if booked_fid not in fetched_data:
                    while True:
                        if progress_callback:
                            await progress_callback(len(fetched_data), len(fids_to_fetch), waiting=False)

                        data = await self.fetch_user_data(booked_fid)
                        if isinstance(data, dict) and "data" in data:
                            fetched_data[booked_fid] = data["data"].get("nickname", "Unknown")
                            if progress_callback: # Immediate progress update after successful fetch
                                await progress_callback(len(fetched_data), len(fids_to_fetch), waiting=False)
                            break
                        elif data == 429:
                            if progress_callback:
                                await progress_callback(len(fetched_data), len(fids_to_fetch), waiting=True)
                            await asyncio.sleep(60) # Rate limit, wait and retry
                        else:
                            fetched_data[booked_fid] = "Unknown"
                            if progress_callback: # Immediate progress update even for failed fetch
                                await progress_callback(len(fetched_data), len(fids_to_fetch), waiting=False)
                            break

                booked_nickname = fetched_data.get(booked_fid, "Unknown")

                # Fetch alliance name
                self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id=?", (booked_alliance,))
                alliance_data = self.alliance_cursor.fetchone()
                booked_alliance_name = alliance_data[0] if alliance_data else "Unknown"

                # Wrap nickname in LTR embedding to prevent line reversal
                time_list.append(f"`{time_slot}` - [{booked_alliance_name}]\u202a{booked_nickname}\u202c - {booked_fid}")
            else:
                time_list.append(f"`{time_slot}` - ")

            booked_fids[time_slot] = booked_fid

            # Update progress after processing each time slot
            if progress_callback:
                await progress_callback(len(fetched_data), len(fids_to_fetch), waiting=False)

        return time_list, booked_fids

    # handler for looping through all times without updating fids
    def generate_time_list(self, booked_times):
        """
        Generates a list of time slots with their booking details.
        """
        time_list = []
        booked_fids = {}

        # Get current slot mode
        self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", ("slot_mode",))
        row = self.svs_cursor.fetchone()
        slot_mode = int(row[0]) if row else 0

        # Generate time slots based on mode
        time_slots = self.get_time_slots(slot_mode)

        for time_slot in time_slots:
            booked_fid, booked_alliance = booked_times.get(time_slot, ("", ""))
            booked_nickname = ""
            if booked_fid:
                self.users_cursor.execute("SELECT nickname FROM users WHERE fid=?", (booked_fid,))
                user = self.users_cursor.fetchone()
                booked_nickname = user[0] if user else f"ID: {booked_fid}"

                self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id=?", (booked_alliance,))
                alliance_data = self.alliance_cursor.fetchone()
                booked_alliance_name = alliance_data[0] if alliance_data else "Unknown"

                # Wrap nickname in LTR embedding to prevent line reversal
                time_list.append(f"`{time_slot}` - [{booked_alliance_name}]\u202a{booked_nickname}\u202c - {booked_fid}")
            else:
                time_list.append(f"`{time_slot}` - ")
            booked_fids[time_slot] = booked_fid

        return time_list, booked_fids

    # handler for looping through available times
    def generate_available_time_list(self, booked_times):
        """
        Generates a list of only available (non-booked) time slots.
        """
        time_list = []

        # Get current slot mode
        self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", ("slot_mode",))
        row = self.svs_cursor.fetchone()
        slot_mode = int(row[0]) if row else 0

        # Generate time slots based on mode
        time_slots = self.get_time_slots(slot_mode)

        for time_slot in time_slots:
            if time_slot not in booked_times:  # Only add unbooked slots
                time_list.append(f"`{time_slot}` - ")

        return time_list
    
    # handler for looping through unavailable times
    def generate_booked_time_list(self, booked_times):
        """
        Generates a list of only booked time slots with their details.
        """
        time_list = []

        # Get current slot mode
        self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", ("slot_mode",))
        row = self.svs_cursor.fetchone()
        slot_mode = int(row[0]) if row else 0

        # Generate time slots based on mode
        time_slots = self.get_time_slots(slot_mode)

        for time_slot in time_slots:
            if time_slot in booked_times:
                booked_fid, booked_alliance = booked_times[time_slot]
                booked_nickname = ""
                if booked_fid:
                    self.users_cursor.execute("SELECT nickname FROM users WHERE fid=?", (booked_fid,))
                    user = self.users_cursor.fetchone()
                    booked_nickname = user[0] if user else f"ID: {booked_fid}"

                    self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id=?", (booked_alliance,))
                    alliance_data = self.alliance_cursor.fetchone()
                    booked_alliance_name = alliance_data[0] if alliance_data else "Unknown"

                    # Wrap nickname in LTR embedding to prevent line reversal
                    time_list.append(f"`{time_slot}` - [{booked_alliance_name}]\u202a{booked_nickname}\u202c - {booked_fid}")

        return time_list

    def split_message_content(self, header: str, time_list: list, max_length: int = 1900) -> list:
        """
        Splits message content into chunks that fit within Discord's character limit.
        Returns a list of message strings.
        """
        if not time_list:
            return [header]

        messages = []
        current_lines = []
        current_length = len(header) + 1  # for newline after header

        for line in time_list:
            line_length = len(line) + 1
            if current_length + line_length > max_length:
                # Save current chunk
                if current_lines:
                    messages.append(header + "\n" + "\n".join(current_lines))
                else:
                    messages.append(header)
                current_lines = [line]
                current_length = len(header) + 1 + line_length
            else:
                current_lines.append(line)
                current_length += line_length

        # Add remaining lines
        if current_lines:
            messages.append(header + "\n" + "\n".join(current_lines))
        elif not messages:
            messages.append(header)

        return messages

    # handler to get minister channel
    async def get_channel_id(self, context: str):
        self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", (context,))
        row = self.svs_cursor.fetchone()
        return int(row[0]) if row else None

    # handler to get minister message from channel to edit it
    async def get_or_create_message(self, context: str, message_content: str, channel: discord.TextChannel):
        # Check if content exceeds Discord's 2000 character limit
        if len(message_content) > 1900:
            truncated_content = message_content[:1850] + "\n\n*... (list truncated due to length)*"
            message_content = truncated_content

        self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", (context,))
        row = self.svs_cursor.fetchone()

        if row:
            message_id = int(row[0])
            try:
                message = await channel.fetch_message(message_id)
                await message.edit(content=message_content)
                return message
            except discord.NotFound:
                pass

        # Send a new message if none found
        new_message = await channel.send(message_content)
        self.svs_cursor.execute(
            "REPLACE INTO reference (context, context_id) VALUES (?, ?)",
            (context, new_message.id)
        )
        self.svs_conn.commit()
        return new_message

    # handler to get guild id
    async def get_log_guild(self, log_guild: discord.Guild) -> discord.Guild | None:
        self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", ("minister guild id",))
        row = self.svs_cursor.fetchone()

        if not row:
            # Save the current guild as main guild if not found
            if log_guild:
                self.svs_cursor.execute(
                    "INSERT INTO reference (context, context_id) VALUES (?, ?)",
                    ("minister guild id", log_guild.id)
                )
                self.svs_conn.commit()
                return log_guild
            else:
                return None
        else:
            guild_id = int(row[0])
            guild = self.bot.get_guild(guild_id)
            if guild:
                return guild
            else:
                return None

    @discord.app_commands.command(name='minister_add', description='Book an appointment slot for a user.')
    @app_commands.autocomplete(appointment_type=appointment_autocomplete, fid=fid_autocomplete, time=time_autocomplete)
    async def minister_add(self, interaction: discord.Interaction, appointment_type: str, fid: str, time: str):
        lang = _get_lang(interaction)
        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message(t("minister.error.no_permission", lang), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            log_guild = await self.get_log_guild(interaction.guild)

            if not log_guild:
                await interaction.followup.send(
                    t("minister.error.log_guild_missing", lang)
                )
                return

            # Check minister and log channels
            context = f"{appointment_type}"
            channel_context = f"{appointment_type} channel"
            log_context = "minister log channel"
            list_type = await self.get_channel_id("list type")

            channel_id = await self.get_channel_id(channel_context)
            log_channel_id = await self.get_channel_id(log_context)

            channel = log_guild.get_channel(channel_id)
            log_channel = log_guild.get_channel(log_channel_id)

            if (not channel or not log_channel) and interaction.guild.id != log_guild.id:
                await interaction.followup.send(
                    t("minister.error.channels_missing", lang, guild=log_guild)
                )
                return

            if not channel:
                try:
                    await interaction.followup.send(
                        content=t("minister.channel.select_for_type", lang, appointment_type=appointment_type),
                        view=ChannelSelectView(self.bot, channel_context, _get_lang(interaction))
                    )
                    return
                except Exception as e:
                    print(f"Failed to select channel: {e}")
                    await interaction.followup.send(t("minister.channel.select_failed", lang, error=str(e)))
                    return

            if not log_channel:
                try:
                    await interaction.followup.send(
                        content=t("minister.channel.select_log", lang),
                        view=ChannelSelectView(self.bot, log_context, _get_lang(interaction))
                    )
                    return
                except Exception as e:
                    print(f"Failed to select channel: {e}")
                    await interaction.followup.send(t("minister.channel.select_failed", lang, error=str(e)))
                    return

            # Get current slot mode
            slot_mode_row = await self.get_channel_id("slot_mode")
            slot_mode = slot_mode_row if slot_mode_row else 0

            # Normalize time input to always be HH:MM format
            try:
                hours, minutes = map(int, time.split(":"))
                normalized_time = f"{hours:02}:{minutes:02}"
            except ValueError:
                await interaction.followup.send(t("minister.time.invalid_format", lang))
                return

            # Validate time based on slot mode
            if slot_mode == 0:
                # Standard mode: only 0 and 30 minutes
                if minutes not in {0, 30}:
                    await interaction.followup.send(t("minister.time.invalid_standard", lang))
                    return
            else:
                # Offset mode: 0, 15, and 45 minutes
                if minutes not in {0, 15, 45}:
                    await interaction.followup.send(t("minister.time.invalid_offset", lang))
                    return

            # Validate time is in valid slot list for current mode
            valid_slots = self.get_time_slots(slot_mode)
            if normalized_time not in valid_slots:
                await interaction.followup.send(t("minister.time.invalid_slot", lang, time=normalized_time))
                return

            # Retrieve alliance_id based on fid
            self.users_cursor.execute("SELECT alliance, nickname FROM users WHERE fid=?", (fid,))
            user_data = self.users_cursor.fetchone()

            if not user_data:
                await interaction.followup.send(t("minister.user.not_registered", lang, fid=fid))
                return

            alliance_id, nickname = user_data

            # Retrieve alliance name from alliance_list
            self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id=?", (alliance_id,))
            alliance_result = self.alliance_cursor.fetchone()

            if not alliance_result:
                await interaction.followup.send(t("minister.user.alliance_not_found", lang))
                return

            alliance_name = alliance_result[0]

            # Check if the user is already booked for the same appointment type
            self.svs_cursor.execute("SELECT time FROM appointments WHERE fid=? AND appointment_type=?", (fid, appointment_type))
            existing_booking = self.svs_cursor.fetchone()
            if existing_booking:
                await interaction.followup.send(
                    t(
                        "minister.booking.already",
                        lang,
                        nickname=nickname,
                        appointment_type=appointment_type,
                        time=existing_booking[0]
                    )
                )
                return

            # Check if the time is already booked for this appointment type
            self.svs_cursor.execute("SELECT fid FROM appointments WHERE appointment_type=? AND time=?", (appointment_type, normalized_time))
            conflicting_booking = self.svs_cursor.fetchone()
            if conflicting_booking:
                booked_fid = conflicting_booking[0]
                self.users_cursor.execute("SELECT nickname FROM users WHERE fid=?", (booked_fid,))
                booked_user = self.users_cursor.fetchone()
                booked_nickname = booked_user[0] if booked_user else "Unknown"
                await interaction.followup.send(
                    t(
                        "minister.booking.taken",
                        lang,
                        time=normalized_time,
                        appointment_type=appointment_type,
                        nickname=booked_nickname
                    )
                )
                return

            # Book the slot with the retrieved alliance info
            self.svs_cursor.execute("INSERT INTO appointments (fid, appointment_type, time, alliance) VALUES (?, ?, ?, ?)",
                                      (fid, appointment_type, normalized_time, alliance_id))
            self.svs_conn.commit()

            # Log the change
            await self.log_change(
                action_type="add",
                user=interaction.user,
                appointment_type=appointment_type,
                fid=int(fid),
                nickname=nickname,
                old_time=None,
                new_time=normalized_time,
                alliance_name=alliance_name
            )

            # Try to get the avatar image
            try:
                data = await self.fetch_user_data(fid)

                if isinstance(data, int) and data == 429:
                    # Rate limit hit
                    avatar_image = "https://gof-formal-avatar.akamaized.net/avatar-dev/2023/07/17/1001.png"
                elif data and "data" in data and "avatar_image" in data["data"]:
                    avatar_image = data["data"]["avatar_image"]
                else:
                    avatar_image = "https://gof-formal-avatar.akamaized.net/avatar-dev/2023/07/17/1001.png"

            except Exception as e:
                avatar_image = "https://gof-formal-avatar.akamaized.net/avatar-dev/2023/07/17/1001.png"

            # Send embed confirmation to log channel
            embed = discord.Embed(
                title=t("minister.embed.add_title", lang, appointment_type=appointment_type),
                description=t(
                    "minister.embed.add_description",
                    lang,
                    nickname=nickname,
                    fid=fid,
                    alliance_name=alliance_name,
                    time=normalized_time
                ),
                color=theme.emColor3
            )
            embed.set_thumbnail(url=avatar_image)
            embed.set_author(
                name=t("minister.embed.add_author", lang, user=interaction.user.display_name),
                icon_url=interaction.user.avatar.url
            )

            await self.send_embed_to_channel(embed)
            await interaction.followup.send(
                t("minister.booking.added_short", lang, nickname=nickname, time=time)
            )

            # Update the appointment list
            self.svs_cursor.execute("SELECT time, fid, alliance FROM appointments WHERE appointment_type=?", (appointment_type,))
            booked_times = {row[0]: (row[1], row[2]) for row in self.svs_cursor.fetchall()}

            if list_type == 3:
                time_list, _ = self.generate_time_list(booked_times)
                message_content = t("minister.list.slots", lang, appointment_type=appointment_type) + "\n" + "\n".join(
                    time_list
                )
            elif list_type == 2:
                time_list = self.generate_booked_time_list(booked_times)
                message_content = t("minister.list.booked", lang, appointment_type=appointment_type) + "\n" + "\n".join(
                    time_list
                )
            else:
                time_list = self.generate_available_time_list(booked_times)
                available_slots = len(time_list) > 0
                message_content = (
                    t("minister.list.available", lang, appointment_type=appointment_type) + "\n" + "\n".join(time_list)
                ) if available_slots else t("minister.list.full", lang, appointment_type=appointment_type)

            # Update existing message or send a new one in the selected channel
            await self.get_or_create_message(context, message_content, channel)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            await interaction.followup.send(t("minister.error.unexpected", lang, error=str(e)))

    @discord.app_commands.command(name='minister_remove', description='Cancel an appointment slot for a user.')
    @app_commands.autocomplete(appointment_type=appointment_autocomplete, fid=registered_fid_autocomplete)
    async def minister_remove(self, interaction: discord.Interaction, appointment_type: str, fid: str):
        lang = _get_lang(interaction)
        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message(t("minister.error.no_permission", lang), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        try:
            log_guild = await self.get_log_guild(interaction.guild)

            if not log_guild:
                await interaction.followup.send(t("minister.error.log_guild_missing", lang))
                return

            # Check minister and log channels
            context = f"{appointment_type}"
            channel_context = f"{appointment_type} channel"
            log_context = "minister log channel"
            list_type = await self.get_channel_id("list type")

            channel_id = await self.get_channel_id(channel_context)
            log_channel_id = await self.get_channel_id(log_context)

            channel = log_guild.get_channel(channel_id)
            log_channel = log_guild.get_channel(log_channel_id)

            if (not channel or not log_channel) and interaction.guild.id != log_guild.id:
                await interaction.followup.send(t("minister.error.channels_missing", lang, guild=log_guild))
                return

            if not channel:
                try:
                    await interaction.followup.send(
                        content=t("minister.channel.select_for_type", lang, appointment_type=appointment_type),
                        view=ChannelSelectView(self.bot, channel_context, _get_lang(interaction))
                    )
                    return
                except Exception as e:
                    print(f"Failed to select channel: {e}")
                    await interaction.followup.send(t("minister.channel.select_failed", lang, error=str(e)))
                    return

            if not log_channel:
                try:
                    await interaction.followup.send(
                        content=t("minister.channel.select_log", lang),
                        view=ChannelSelectView(self.bot, log_context, _get_lang(interaction))
                    )
                    return
                except Exception as e:
                    print(f"Failed to select channel: {e}")
                    await interaction.followup.send(t("minister.channel.select_failed", lang, error=str(e)))
                    return

            # Check if the user is booked for the appointment type
            self.svs_cursor.execute("SELECT * FROM appointments WHERE fid=? AND appointment_type=?", (fid, appointment_type))
            booking = self.svs_cursor.fetchone()

            # Fetch nickname and alliance for the user
            self.users_cursor.execute("SELECT nickname, alliance FROM users WHERE fid=?", (fid,))
            user = self.users_cursor.fetchone()
            nickname = user[0] if user else "Unknown"
            alliance_id = user[1] if user else None

            if not booking:
                await interaction.followup.send(
                    t("minister.booking.not_listed", lang, nickname=nickname, appointment_type=appointment_type)
                )
                return

            # Get alliance name for logging
            alliance_name = None
            if alliance_id:
                self.alliance_cursor.execute("SELECT name FROM alliance_list WHERE alliance_id=?", (alliance_id,))
                alliance_result = self.alliance_cursor.fetchone()
                alliance_name = alliance_result[0] if alliance_result else None

            # Remove the appointment
            self.svs_cursor.execute("DELETE FROM appointments WHERE fid=? AND appointment_type=?", (fid, appointment_type))
            self.svs_conn.commit()

            # Log the change
            await self.log_change(
                action_type="remove",
                user=interaction.user,
                appointment_type=appointment_type,
                fid=int(fid),
                nickname=nickname,
                old_time=None,
                new_time=None,
                alliance_name=alliance_name
            )

            # Try to get the avatar image
            try:
                data = await self.fetch_user_data(fid)

                if isinstance(data, int) and data == 429:
                    # Rate limit hit
                    avatar_image = "https://gof-formal-avatar.akamaized.net/avatar-dev/2023/07/17/1001.png"
                elif data and "data" in data and "avatar_image" in data["data"]:
                    avatar_image = data["data"]["avatar_image"]
                else:
                    avatar_image = "https://gof-formal-avatar.akamaized.net/avatar-dev/2023/07/17/1001.png"

            except Exception as e:
                avatar_image = "https://gof-formal-avatar.akamaized.net/avatar-dev/2023/07/17/1001.png"

            # Send embed confirmation to log channel
            embed = discord.Embed(
                title=t("minister.embed.remove_title", lang, appointment_type=appointment_type),
                description=t("minister.embed.remove_description", lang, nickname=nickname, fid=fid),
                color=theme.emColor2
            )
            embed.set_thumbnail(url=avatar_image)
            embed.set_author(
                name=t("minister.embed.remove_author", lang, user=interaction.user.display_name),
                icon_url=interaction.user.avatar.url
            )

            await self.send_embed_to_channel(embed)
            await interaction.followup.send(t("minister.booking.removed_short", lang, nickname=nickname))

            # Send the list of times for the selected appointment type
            self.svs_cursor.execute("SELECT time, fid, alliance FROM appointments WHERE appointment_type=?", (appointment_type,))
            booked_times = {row[0]: (row[1], row[2]) for row in self.svs_cursor.fetchall()}

            if list_type == 3:
                time_list, _ = self.generate_time_list(booked_times)
                message_content = t("minister.list.slots", lang, appointment_type=appointment_type) + "\n" + "\n".join(
                    time_list
                )
            elif list_type == 2:
                time_list = self.generate_booked_time_list(booked_times)
                message_content = t("minister.list.booked", lang, appointment_type=appointment_type) + "\n" + "\n".join(
                    time_list
                )
            else:
                time_list = self.generate_available_time_list(booked_times)
                message_content = t("minister.list.available", lang, appointment_type=appointment_type) + "\n" + "\n".join(
                    time_list
                )

            # Update existing message or send a new one in the selected channel
            await self.get_or_create_message(context, message_content, channel)

        except Exception as e:
            print(f"An error occurred: {e}")
            await interaction.followup.send(t("minister.error.cancel_failed", lang, error=str(e)))

    @discord.app_commands.command(name='minister_clear_all', description='Cancel all appointments for a selected appointment type.')
    @app_commands.autocomplete(appointment_type=appointment_autocomplete)
    async def minister_clear_all(self, interaction: discord.Interaction, appointment_type: str):
        lang = _get_lang(interaction)
        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message(t("minister.error.no_permission", lang), ephemeral=True)
            return
        await interaction.response.defer()

        log_guild = await self.get_log_guild(interaction.guild)

        # Check minister log channels
        context = f"{appointment_type}"
        channel_context = f"{appointment_type} channel"

        log_context = "minister log channel"
        log_channel_id = await self.get_channel_id(log_context)
        log_channel = log_guild.get_channel(log_channel_id)

        if not log_channel:
            await interaction.followup.send(
                t("minister.clear.log_channel_missing", lang)
            )
            return

        try:
            # Send a confirmation prompt
            embed = discord.Embed(
                title=t("minister.clear.confirm_title", lang, appointment_type=appointment_type, icon=theme.warnIcon),
                description=t(
                    "minister.clear.confirm_desc",
                    lang,
                    appointment_type=appointment_type,
                    icon=theme.warnIcon
                ),
                color=discord.Color.orange()
            )
            confirmation_message = await interaction.followup.send(embed=embed)

            # Wait for user confirmation
            def check(message):
                return message.author == interaction.user and message.channel == interaction.channel

            try:
                response = await self.bot.wait_for('message', check=check, timeout=10.0)

                if response.content.lower() == "yes":
                    # Retrieve booked times before deletion
                    self.svs_cursor.execute("SELECT time, fid, alliance FROM appointments WHERE appointment_type=?", (appointment_type,))
                    booked_times = {row[0]: (row[1], row[2]) for row in self.svs_cursor.fetchall()}

                    # Generate available times list
                    time_list, _ = self.generate_time_list(booked_times)

                    # Split into chunks if too long for embed description (4096 char limit)
                    header = t("minister.clear.previous_header", lang, appointment_type=appointment_type)
                    message_chunks = self.split_message_content(header, time_list, max_length=4000)

                    for i, chunk in enumerate(message_chunks):
                        title = (
                            t("minister.clear.cleared_title", lang, appointment_type=appointment_type)
                            if i == 0
                            else t("minister.clear.cleared_title_continued", lang, appointment_type=appointment_type)
                        )
                        clear_list_embed = discord.Embed(
                            title=title,
                            description=chunk,
                            color=discord.Color.orange()
                        )
                        await self.send_embed_to_channel(clear_list_embed)

                    # Regenerate empty list of available times
                    booked_times = {}
                    time_list = self.generate_available_time_list(booked_times)

                    message_content = t("minister.list.available", lang, appointment_type=appointment_type) + "\n" + "\n".join(time_list)

                    # Get the channel to update
                    self.svs_cursor.execute("SELECT context_id FROM reference WHERE context=?", (channel_context,))
                    channel_row = self.svs_cursor.fetchone()

                    if channel_row:
                        channel_id = int(channel_row[0])
                        channel = log_guild.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
                        await self.get_or_create_message(context, message_content, channel)
                    else:
                        await confirmation_message.reply(
                            t("minister.clear.message_missing", lang, appointment_type=appointment_type)
                        )

                    self.svs_cursor.execute("DELETE FROM appointments WHERE appointment_type=?", (appointment_type,))
                    self.svs_conn.commit()

                    # Log the change
                    await self.log_change(
                        action_type="clear_all",
                        user=interaction.user,
                        appointment_type=appointment_type,
                        fid=None,
                        nickname=None,
                        old_time=None,
                        new_time=None,
                        alliance_name=None
                    )

                    embed = discord.Embed(
                        title=t("minister.clear.success_title", lang, appointment_type=appointment_type),
                        description=t("minister.clear.success_desc", lang, appointment_type=appointment_type),
                        color=theme.emColor2
                    )
                    embed.set_author(
                        name=t("minister.clear.success_author", lang, user=interaction.user.display_name),
                        icon_url=interaction.user.avatar.url
                    )

                    await self.send_embed_to_channel(embed)
                    await interaction.followup.send(
                        t("minister.clear.success_message", lang, appointment_type=appointment_type, icon=theme.verifiedIcon)
                    )
                else:
                    await confirmation_message.reply(
                        t("minister.clear.cancelled", lang, appointment_type=appointment_type)
                    )

            except asyncio.TimeoutError:
                await interaction.followup.send(t("minister.clear.timeout", lang), ephemeral=True)
                await confirmation_message.reply(
                    t("minister.clear.timeout_user", lang, user_id=interaction.user.id)
                )

        except Exception as e:
            print(f"An error occurred: {e}")
            await interaction.followup.send(
                t("minister.clear.error", lang, error=str(e)),
                ephemeral=True
            )
        
    @discord.app_commands.command(name='minister_list', description='View the schedule for an appointment type.')
    @app_commands.autocomplete(appointment_type=appointment_autocomplete, all_or_available=choice_autocomplete)
    @app_commands.describe(
        appointment_type="The type of minister appointment to view.",
        all_or_available="Show full schedule or only available slots.", 
        update="Default: False. Whether to update names via API or not. Will take some time if enabled."
    )
    async def minister_list(self, interaction: discord.Interaction, appointment_type: str, all_or_available: str, update: bool = False):
        lang = _get_lang(interaction)
        try:
            await interaction.response.defer()

            # Fetch the booked times for the specific appointment type
            self.svs_cursor.execute("SELECT time, fid, alliance FROM appointments WHERE appointment_type=?", (appointment_type,))
            booked_times = {row[0]: (row[1], row[2]) for row in self.svs_cursor.fetchall()}

            if all_or_available == "all":
                if update:
                    async def update_progress(checked, total, waiting):
                        if checked % 1 == 0:
                            color = discord.Color.orange() if waiting else discord.Color.green()
                            title = (
                                t("minister.list.waiting", lang)
                                if waiting
                                else t("minister.list.updating", lang)
                            )
                            embed = discord.Embed(
                                title=title,
                                description=t("minister.list.progress", lang, checked=checked, total=total),
                                color=color
                            )
                            try:
                                await interaction.edit_original_response(embed=embed)
                            except discord.NotFound:
                                print("Interaction expired before progress update.")

                    # Fetch updated data via API
                    time_list, _ = await self.update_time_list(booked_times, update_progress)
                else:
                    # Use database method
                    time_list, _ = self.generate_time_list(booked_times)

                # Format the time list for the embed
                time_list = "\n".join(time_list)

                if time_list:
                    embed = discord.Embed(
                        title=t("minister.list.schedule_title", lang, appointment_type=appointment_type),
                        description=time_list,
                        color=theme.emColor1
                    )
                    try:
                        await interaction.edit_original_response(embed=embed)
                    except discord.NotFound:
                        print("Interaction expired before final update.")

            elif all_or_available == "available only":
                available_slots = self.generate_available_time_list(booked_times)
                if available_slots:
                    time_list = "\n".join(available_slots)
                    await interaction.followup.send(
                        t("minister.list.available_plain", lang, appointment_type=appointment_type, time_list=time_list)
                    )
                else:
                    await interaction.followup.send(t("minister.list.full", lang, appointment_type=appointment_type))

        except Exception as e:
            print(f"An error occurred: {e}")
            await interaction.followup.send(t("minister.list.error", lang, error=str(e)))

    @discord.app_commands.command(name='minister_archive_save', description='Save current minister schedule to an archive (Global Admin only)')
    @app_commands.describe(name="Optional name for the archive (defaults to current date)")
    async def minister_archive_save(self, interaction: discord.Interaction, name: str = None):
        lang = _get_lang(interaction)
        # Check if user is global admin
        minister_menu_cog = self.bot.get_cog("MinisterMenu")
        if not minister_menu_cog:
            await interaction.response.send_message(
                t("minister.archive.menu_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        is_admin, is_global_admin, _ = await minister_menu_cog.get_admin_permissions(interaction.user.id)
        if not is_global_admin:
            await interaction.response.send_message(
                t("minister.archive.save_forbidden", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        # Get archive cog
        archive_cog = self.bot.get_cog("MinisterArchive")
        if not archive_cog:
            await interaction.response.send_message(
                t("minister.archive.module_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        # Generate name if not provided
        if not name:
            name = datetime.now().strftime("SvS %Y-%m-%d")

        # Save the current schedule
        await archive_cog.save_current_schedule(interaction, name)

    @discord.app_commands.command(name='minister_archive_list', description='View all saved minister archives (Global Admin only)')
    async def minister_archive_list(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        # Check if user is global admin
        minister_menu_cog = self.bot.get_cog("MinisterMenu")
        if not minister_menu_cog:
            await interaction.response.send_message(
                t("minister.archive.menu_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        is_admin, is_global_admin, _ = await minister_menu_cog.get_admin_permissions(interaction.user.id)
        if not is_global_admin:
            await interaction.response.send_message(
                t("minister.archive.list_forbidden", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        # Get archive cog
        archive_cog = self.bot.get_cog("MinisterArchive")
        if not archive_cog:
            await interaction.response.send_message(
                t("minister.archive.module_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        # Show archive list
        await archive_cog.show_archive_list(interaction)

    async def archive_id_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for archive IDs"""
        try:
            # Get all archives
            self.svs_cursor.execute("""
                SELECT archive_id, archive_name, created_at
                FROM minister_archives
                ORDER BY created_at DESC
                LIMIT 25
            """)
            archives = self.svs_cursor.fetchall()

            choices = []
            for archive_id, archive_name, created_at in archives:
                created_date = datetime.fromisoformat(created_at).strftime("%Y-%m-%d")
                label = f"{archive_name} ({created_date})"

                if current and current.lower() not in label.lower():
                    continue

                choices.append(discord.app_commands.Choice(name=label[:100], value=archive_id))

            return choices[:25]
        except Exception as e:
            print(f"Error in archive autocomplete: {e}")
            return []

    @discord.app_commands.command(name='minister_archive_history', description='View change history for minister appointments (Global Admin only)')
    @app_commands.describe(
        archive_id="Optional: Select an archive to view its change history (leave empty for current changes)",
        appointment_type="Optional: Filter by appointment type (Construction/Research/Training Day)",
        discord_user="Optional: Filter by specific Discord user who made changes"
    )
    @app_commands.autocomplete(archive_id=archive_id_autocomplete, appointment_type=appointment_autocomplete)
    async def minister_archive_history(
        self,
        interaction: discord.Interaction,
        archive_id: int = None,
        appointment_type: str = None,
        discord_user: discord.User = None
    ):
        lang = _get_lang(interaction)
        # Check if user is global admin
        minister_menu_cog = self.bot.get_cog("MinisterMenu")
        if not minister_menu_cog:
            await interaction.response.send_message(
                t("minister.archive.menu_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        is_admin, is_global_admin, _ = await minister_menu_cog.get_admin_permissions(interaction.user.id)
        if not is_global_admin:
            await interaction.response.send_message(
                t("minister.archive.history_forbidden", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        # Get archive cog
        archive_cog = self.bot.get_cog("MinisterArchive")
        if not archive_cog:
            await interaction.response.send_message(
                t("minister.archive.module_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        # Build query based on filters
        query = """
            SELECT
                timestamp, discord_username, action_type, appointment_type,
                fid, nickname, old_time, new_time, alliance_name, additional_data
            FROM minister_change_history
            WHERE 1=1
        """
        params = []

        if archive_id is not None:
            query += " AND archive_id = ?"
            params.append(archive_id)
        else:
            query += " AND archive_id IS NULL"

        if appointment_type:
            query += " AND appointment_type = ?"
            params.append(appointment_type)

        if discord_user:
            query += " AND discord_user_id = ?"
            params.append(discord_user.id)

        query += " ORDER BY timestamp DESC"

        self.svs_cursor.execute(query, params)
        history_records = self.svs_cursor.fetchall()

        if not history_records:
            await interaction.response.send_message(t("minister.archive.history_empty", lang), ephemeral=True)
            return

        # Show history via archive cog
        from .minister_archive import ChangeHistoryView
        view = ChangeHistoryView(self.bot, archive_cog, history_records, page=0, archive_id=archive_id)
        await archive_cog.update_history_embed(interaction, history_records, 0, archive_id, view)

async def setup(bot):
    await bot.add_cog(MinisterSchedule(bot))
