import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
import time
from typing import List
from datetime import datetime
import os
import csv
import io
from .login_handler import LoginHandler
from .permission_handler import PermissionManager
from .pimp_my_bot import theme
from i18n import get_guild_language, t

def _get_lang(interaction: discord.Interaction | None) -> str:
    guild_id = interaction.guild.id if interaction and interaction.guild else None
    return get_guild_language(guild_id)

class PaginationView(discord.ui.View):
    def __init__(self, chunks: List[discord.Embed], author_id: int, lang: str):
        super().__init__(timeout=7200)
        self.chunks = chunks
        self.current_page = 0
        self.message = None
        self.author_id = author_id
        self.lang = lang
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                t("pagination.not_allowed", self.lang),
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(emoji=theme.importIcon, style=discord.ButtonStyle.blurple, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_page_change(interaction, -1)

    @discord.ui.button(emoji=theme.exportIcon, style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_page_change(interaction, 1)

    async def _handle_page_change(self, interaction: discord.Interaction, change: int):
        self.current_page = max(0, min(self.current_page + change, len(self.chunks) - 1))
        self.update_buttons()
        await self.update_page(interaction)

    def update_buttons(self):
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.chunks) - 1

    async def update_page(self, interaction: discord.Interaction):
        embed = self.chunks[self.current_page]
        embed.set_footer(
            text=t(
                "pagination.page",
                self.lang,
                current=self.current_page + 1,
                total=len(self.chunks)
            )
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

def fix_rtl(text):
    return f"\u202B{text}\u202C"

class AllianceMemberOperations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn_alliance = sqlite3.connect('db/alliance.sqlite')
        self.c_alliance = self.conn_alliance.cursor()
        
        self.conn_users = sqlite3.connect('db/users.sqlite')
        self.c_users = self.conn_users.cursor()
        
        self.level_mapping = {
            31: "F30 - 1", 32: "F30 - 2", 33: "F30 - 3", 34: "F30 - 4",
            35: "FC 1", 36: "FC 1 - 1", 37: "FC 1 - 2", 38: "FC 1 - 3", 39: "FC 1 - 4",
            40: "FC 2", 41: "FC 2 - 1", 42: "FC 2 - 2", 43: "FC 2 - 3", 44: "FC 2 - 4",
            45: "FC 3", 46: "FC 3 - 1", 47: "FC 3 - 2", 48: "FC 3 - 3", 49: "FC 3 - 4",
            50: "FC 4", 51: "FC 4 - 1", 52: "FC 4 - 2", 53: "FC 4 - 3", 54: "FC 4 - 4",
            55: "FC 5", 56: "FC 5 - 1", 57: "FC 5 - 2", 58: "FC 5 - 3", 59: "FC 5 - 4",
            60: "FC 6", 61: "FC 6 - 1", 62: "FC 6 - 2", 63: "FC 6 - 3", 64: "FC 6 - 4",
            65: "FC 7", 66: "FC 7 - 1", 67: "FC 7 - 2", 68: "FC 7 - 3", 69: "FC 7 - 4",
            70: "FC 8", 71: "FC 8 - 1", 72: "FC 8 - 2", 73: "FC 8 - 3", 74: "FC 8 - 4",
            75: "FC 9", 76: "FC 9 - 1", 77: "FC 9 - 2", 78: "FC 9 - 3", 79: "FC 9 - 4",
            80: "FC 10", 81: "FC 10 - 1", 82: "FC 10 - 2", 83: "FC 10 - 3", 84: "FC 10 - 4"
        }

        self.fl_emojis = {
            range(35, 40): "<:fc1:1326751863764156528>",
            range(40, 45): "<:fc2:1326751886954594315>",
            range(45, 50): "<:fc3:1326751903912034375>",
            range(50, 55): "<:fc4:1326751938674692106>",
            range(55, 60): "<:fc5:1326751952750776331>",
            range(60, 65): "<:fc6:1326751966184869981>",
            range(65, 70): "<:fc7:1326751983939489812>",
            range(70, 75): "<:fc8:1326751996707082240>",
            range(75, 80): "<:fc9:1326752008505528331>",
            range(80, 85): "<:fc10:1326752023001174066>"
        }

        self.log_directory = 'log'
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
        self.log_file = os.path.join(self.log_directory, 'alliance_memberlog.txt')
        
        # Initialize login handler for centralized API management
        self.login_handler = LoginHandler()

    def log_message(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def get_fl_emoji(self, fl_level: int) -> str:
        for level_range, emoji in self.fl_emojis.items():
            if fl_level in level_range:
                return emoji
        return f"{theme.levelIcon}"

    async def handle_member_operations(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        embed = discord.Embed(
            title=f"{theme.userIcon} {t('alliance.member.menu.title', lang)}",
            description=(
                f"{t('alliance.member.menu.prompt', lang)}\n\n"
                f"**{t('alliance.member.menu.available', lang)}**\n"
                f"{theme.newIcon} `{t('alliance.member.button.add', lang)}` - {t('alliance.member.menu.add_desc', lang)}\n"
                f"{theme.refreshIcon} `{t('alliance.member.button.transfer', lang)}` - {t('alliance.member.menu.transfer_desc', lang)}\n"
                f"{theme.minusIcon} `{t('alliance.member.button.remove', lang)}` - {t('alliance.member.menu.remove_desc', lang)}\n"
                f"{theme.userIcon} `{t('alliance.member.button.view', lang)}` - {t('alliance.member.menu.view_desc', lang)}\n"
                f"{theme.chartIcon} `{t('alliance.member.button.export', lang)}` - {t('alliance.member.menu.export_desc', lang)}\n"
                f"{theme.homeIcon} `{t('alliance.member.button.main_menu', lang)}` - {t('alliance.member.menu.main_menu_desc', lang)}"
            ),
            color=theme.emColor1
        )
        
        embed.set_footer(text=t("alliance.member.menu.footer", lang))

        class MemberOperationsView(discord.ui.View):
            def __init__(self, cog, lang: str):
                super().__init__()
                self.cog = cog
                self.bot = cog.bot
                self.lang = lang
                self._apply_language()

            def _apply_language(self):
                self.add_member_button.label = t("alliance.member.button.add", self.lang)
                self.remove_member_button.label = t("alliance.member.button.remove", self.lang)
                self.view_members_button.label = t("alliance.member.button.view", self.lang)
                self.export_members_button.label = t("alliance.member.button.export", self.lang)
                self.main_menu_button.label = t("alliance.member.button.main_menu", self.lang)
                self.transfer_member_button.label = t("alliance.member.button.transfer", self.lang)

            @discord.ui.button(
                label="Add Members",
                emoji=theme.addIcon,
                style=discord.ButtonStyle.success,
                custom_id="add_member",
                row=0
            )
            async def add_member_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    alliances, is_global = PermissionManager.get_admin_alliances(
                        button_interaction.user.id,
                        button_interaction.guild_id
                    )

                    if not alliances:
                        await button_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('alliance.member.error.no_alliances', self.lang)}",
                            ephemeral=True
                        )
                        return

                    select_embed = discord.Embed(
                        title=f"{theme.listIcon} {t('alliance.member.select_alliance_title', self.lang)}",
                        description=(
                            f"{t('alliance.member.select_add_prompt', self.lang)}\n\n"
                            f"**{t('alliance.member.permissions.title', self.lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.userIcon} **{t('alliance.member.permissions.access_level', self.lang)}** `{t('alliance.member.permissions.global_admin', self.lang) if is_global else t('alliance.member.permissions.alliance_admin', self.lang)}`\n"
                            f"{theme.searchIcon} **{t('alliance.member.permissions.access_type', self.lang)}** `{t('alliance.member.permissions.all_alliances', self.lang) if is_global else t('alliance.member.permissions.assigned_alliances', self.lang)}`\n"
                            f"{theme.chartIcon} **{t('alliance.member.permissions.available_alliances', self.lang)}** `{len(alliances)}`\n"
                            f"{theme.lowerDivider}"
                        ),
                        color=theme.emColor3
                    )

                    alliances_with_counts = []
                    for alliance_id, name in alliances:
                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                            member_count = cursor.fetchone()[0]
                            alliances_with_counts.append((alliance_id, name, member_count))

                    view = AllianceSelectView(alliances_with_counts, self.cog, lang=self.lang)
                    
                    async def select_callback(interaction: discord.Interaction):
                        alliance_id = int(view.current_select.values[0])
                        await interaction.response.send_modal(AddMemberModal(alliance_id, self.lang))

                    view.callback = select_callback
                    await button_interaction.response.send_message(
                        embed=select_embed,
                        view=view,
                        ephemeral=True
                    )

                except Exception as e:
                    self.log_message(f"Error in add_member_button: {e}")
                    await button_interaction.response.send_message(
                        t("alliance.member.error.request", self.lang),
                        ephemeral=True
                    )

            @discord.ui.button(
                label="Remove Members",
                emoji=theme.minusIcon,
                style=discord.ButtonStyle.danger,
                custom_id="remove_member",
                row=0
            )
            async def remove_member_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    alliances, is_global = PermissionManager.get_admin_alliances(
                        button_interaction.user.id,
                        button_interaction.guild_id
                    )

                    if not alliances:
                        await button_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('alliance.member.error.no_authorized_alliance', self.lang)}",
                            ephemeral=True
                        )
                        return

                    select_embed = discord.Embed(
                        title=f"{theme.trashIcon} {t('alliance.member.remove.select_title', self.lang)}",
                        description=(
                            f"{t('alliance.member.remove.select_prompt', self.lang)}\n\n"
                            f"**{t('alliance.member.permissions.title', self.lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.userIcon} **{t('alliance.member.permissions.access_level', self.lang)}** `{t('alliance.member.permissions.global_admin', self.lang) if is_global else t('alliance.member.permissions.alliance_admin', self.lang)}`\n"
                            f"{theme.searchIcon} **{t('alliance.member.permissions.access_type', self.lang)}** `{t('alliance.member.permissions.all_alliances', self.lang) if is_global else t('alliance.member.permissions.assigned_alliances', self.lang)}`\n"
                            f"{theme.chartIcon} **{t('alliance.member.permissions.available_alliances', self.lang)}** `{len(alliances)}`\n"
                            f"{theme.lowerDivider}"
                        ),
                        color=theme.emColor2
                    )

                    alliances_with_counts = []
                    for alliance_id, name in alliances:
                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                            member_count = cursor.fetchone()[0]
                            alliances_with_counts.append((alliance_id, name, member_count))

                    view = AllianceSelectView(alliances_with_counts, self.cog, lang=self.lang)
                    
                    async def select_callback(interaction: discord.Interaction):
                        alliance_id = int(view.current_select.values[0])
                        
                        with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                            cursor = alliance_db.cursor()
                            cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (alliance_id,))
                            alliance_name = cursor.fetchone()[0]
                        
                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute("""
                                SELECT fid, nickname, furnace_lv 
                                FROM users 
                                WHERE alliance = ? 
                                ORDER BY furnace_lv DESC, nickname
                            """, (alliance_id,))
                            members = cursor.fetchall()
                            
                        if not members:
                            await interaction.response.send_message(
                                f"{theme.deniedIcon} {t('alliance.member.error.no_members', self.lang)}",
                                ephemeral=True
                            )
                            return

                        max_fl = max(member[2] for member in members)
                        avg_fl = sum(member[2] for member in members) / len(members)

                        member_embed = discord.Embed(
                            title=f"{theme.userIcon} {t('alliance.member.remove.selection_title', self.lang, alliance=alliance_name)}",
                            description=(
                                "```ml\n"
                                f"{t('alliance.member.stats.title', self.lang)}\n"
                                "══════════════════════════\n"
                                f"{theme.chartIcon} {t('alliance.member.stats.total_members', self.lang)} {len(members)}\n"
                                f"{theme.levelIcon} {t('alliance.member.stats.highest_level', self.lang)} {self.cog.level_mapping.get(max_fl, str(max_fl))}\n"
                                f"{theme.chartIcon} {t('alliance.member.stats.avg_level', self.lang)} {self.cog.level_mapping.get(int(avg_fl), str(int(avg_fl)))}\n"
                                "══════════════════════════\n"
                                "```\n"
                                f"{t('alliance.member.remove.select_member', self.lang)}"
                            ),
                            color=theme.emColor2
                        )

                        member_view = MemberSelectView(
                            members,
                            alliance_name,
                            self.cog,
                            is_remove_operation=True,
                            alliance_id=alliance_id,
                            alliances=alliances_with_counts,
                            lang=self.lang
                        )

                        async def member_callback(member_interaction: discord.Interaction, selected_fids=None, delete_all=False):
                            # Handle multi-select or delete all
                            if delete_all or (selected_fids and len(selected_fids) == len(members)):
                                # Delete all members
                                selected_value = "all"
                                confirm_embed = discord.Embed(
                                    title=f"{theme.warnIcon} {t('alliance.member.remove.confirm_title', self.lang)}",
                                    description=t('alliance.member.remove.confirm_body', self.lang, count=len(members)),
                                    color=theme.emColor2
                                )
                                
                                confirm_view = discord.ui.View()
                                confirm_button = discord.ui.Button(
                                    label=f"{theme.verifiedIcon} {t('alliance.member.common.confirm', self.lang)}", 
                                    style=discord.ButtonStyle.danger, 
                                    custom_id="confirm_all"
                                )
                                cancel_button = discord.ui.Button(
                                    label=f"{theme.deniedIcon} {t('alliance.member.common.cancel', self.lang)}", 
                                    style=discord.ButtonStyle.secondary, 
                                    custom_id="cancel_all"
                                )
                                
                                confirm_view.add_item(confirm_button)
                                confirm_view.add_item(cancel_button)

                                async def confirm_callback(confirm_interaction: discord.Interaction):
                                    if confirm_interaction.data["custom_id"] == "confirm_all":
                                        with sqlite3.connect('db/users.sqlite') as users_db:
                                            cursor = users_db.cursor()
                                            cursor.execute("SELECT fid, nickname FROM users WHERE alliance = ?", (alliance_id,))
                                            removed_members = cursor.fetchall()
                                            cursor.execute("DELETE FROM users WHERE alliance = ?", (alliance_id,))
                                            users_db.commit()
                                        
                                        try:
                                            with sqlite3.connect('db/settings.sqlite') as settings_db:
                                                cursor = settings_db.cursor()
                                                cursor.execute("""
                                                    SELECT channel_id 
                                                    FROM alliance_logs 
                                                    WHERE alliance_id = ?
                                                """, (alliance_id,))
                                                alliance_log_result = cursor.fetchone()
                                                
                                                if alliance_log_result and alliance_log_result[0]:
                                                    log_embed = discord.Embed(
                                                        title=f"{theme.trashIcon} {t('alliance.member.remove.log_mass_title', self.lang)}",
                                                        description=(
                                                            f"**{t('alliance.member.common.alliance_label', self.lang)}** {alliance_name}\n"
                                                            f"**{t('alliance.member.common.admin_label', self.lang)}** {confirm_interaction.user.name} (`{confirm_interaction.user.id}`)\n"
                                                            f"**{t('alliance.member.common.date_label', self.lang)}** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                                            f"**{t('alliance.member.remove.log_total', self.lang)}** {len(removed_members)}\n\n"
                                                            f"**{t('alliance.member.remove.log_removed', self.lang)}**\n"
                                                            "```\n" + 
                                                            "\n".join([
                                                                t(
                                                                    "alliance.member.remove.log_entry_id",
                                                                    self.lang,
                                                                    index=idx + 1,
                                                                    fid=fid
                                                                )
                                                                for idx, (fid, _) in enumerate(removed_members[:20])
                                                            ]) +
                                                            (t('alliance.member.remove.log_more', self.lang, count=len(removed_members) - 20) if len(removed_members) > 20 else "") +
                                                            "\n```"
                                                        ),
                                                        color=theme.emColor2
                                                    )
                                                    
                                                    try:
                                                        alliance_channel_id = int(alliance_log_result[0])
                                                        alliance_log_channel = self.bot.get_channel(alliance_channel_id)
                                                        if alliance_log_channel:
                                                            await alliance_log_channel.send(embed=log_embed)
                                                    except Exception as e:
                                                        self.log_message(f"Alliance Log Sending Error: {e}")
                                        except Exception as e:
                                            self.log_message(f"Log record error: {e}")
                                        
                                        success_embed = discord.Embed(
                                            title=f"{theme.verifiedIcon} {t('alliance.member.remove.success_title', self.lang)}",
                                            description=t('alliance.member.remove.success_body', self.lang, count=len(removed_members)),
                                            color=theme.emColor3
                                        )
                                        await confirm_interaction.response.edit_message(embed=success_embed, view=None)
                                    else:
                                        cancel_embed = discord.Embed(
                                            title=f"{theme.deniedIcon} {t('alliance.member.common.cancelled_title', self.lang)}",
                                            description=t('alliance.member.remove.cancelled_body', self.lang),
                                            color=theme.emColor4
                                        )
                                        await confirm_interaction.response.edit_message(embed=cancel_embed, view=None)

                                confirm_button.callback = confirm_callback
                                cancel_button.callback = confirm_callback
                                
                                await member_interaction.response.edit_message(
                                    embed=confirm_embed,
                                    view=confirm_view
                                )
                            
                            elif selected_fids:
                                # Bulk delete selected members
                                try:
                                    with sqlite3.connect('db/users.sqlite') as users_db:
                                        cursor = users_db.cursor()
                                        placeholders = ','.join('?' * len(selected_fids))
                                        cursor.execute(f"SELECT fid, nickname FROM users WHERE fid IN ({placeholders})", selected_fids)
                                        removed_members = cursor.fetchall()

                                        cursor.execute(f"DELETE FROM users WHERE fid IN ({placeholders})", selected_fids)
                                        users_db.commit()

                                    try:
                                        with sqlite3.connect('db/settings.sqlite') as settings_db:
                                            cursor = settings_db.cursor()
                                            cursor.execute("""
                                                SELECT channel_id
                                                FROM alliance_logs
                                                WHERE alliance_id = ?
                                            """, (alliance_id,))
                                            alliance_log_result = cursor.fetchone()

                                            if alliance_log_result and alliance_log_result[0]:
                                                log_embed = discord.Embed(
                                                    title=f"{theme.trashIcon} {t('alliance.member.remove.log_bulk_title', self.lang)}",
                                                    description=(
                                                        f"**{t('alliance.member.common.alliance_label', self.lang)}** {alliance_name}\n"
                                                        f"**{t('alliance.member.common.admin_label', self.lang)}** {member_interaction.user.name} (`{member_interaction.user.id}`)\n"
                                                        f"**{t('alliance.member.common.date_label', self.lang)}** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                                        f"**{t('alliance.member.remove.log_total', self.lang)}** {len(removed_members)}\n\n"
                                                        f"**{t('alliance.member.remove.log_removed', self.lang)}**\n"
                                                        "```\n" +
                                                        "\n".join([
                                                            t(
                                                                "alliance.member.remove.log_entry_id_name",
                                                                self.lang,
                                                                index=idx + 1,
                                                                fid=fid,
                                                                name=nickname
                                                            )
                                                            for idx, (fid, nickname) in enumerate(removed_members[:20])
                                                        ]) +
                                                        (t('alliance.member.remove.log_more', self.lang, count=len(removed_members) - 20) if len(removed_members) > 20 else "") +
                                                        "\n```"
                                                    ),
                                                    color=theme.emColor2
                                                )

                                                try:
                                                    alliance_channel_id = int(alliance_log_result[0])
                                                    alliance_log_channel = self.bot.get_channel(alliance_channel_id)
                                                    if alliance_log_channel:
                                                        await alliance_log_channel.send(embed=log_embed)
                                                except Exception as e:
                                                    self.log_message(f"Alliance Log Sending Error: {e}")
                                    except Exception as e:
                                        self.log_message(f"Log record error: {e}")

                                    success_embed = discord.Embed(
                                        title=f"{theme.verifiedIcon} {t('alliance.member.remove.success_title', self.lang)}",
                                        description=t('alliance.member.remove.success_body', self.lang, count=len(removed_members)),
                                        color=theme.emColor3
                                    )
                                    try:
                                        await member_interaction.response.edit_message(embed=success_embed, view=None)
                                    except:
                                        await member_interaction.edit_original_response(embed=success_embed, view=None)

                                except Exception as e:
                                    self.log_message(f"Error in bulk member removal: {e}")
                                    error_embed = discord.Embed(
                                        title=f"{theme.deniedIcon} {t('alliance.member.common.error_title', self.lang)}",
                                        description=t('alliance.member.remove.error_body', self.lang),
                                        color=theme.emColor2
                                    )
                                    try:
                                        await member_interaction.response.send_message(embed=error_embed, ephemeral=True)
                                    except:
                                        await member_interaction.followup.send(embed=error_embed, ephemeral=True)

                        member_view.callback = member_callback
                        await interaction.response.edit_message(
                            embed=member_embed,
                            view=member_view
                        )

                    view.callback = select_callback
                    await button_interaction.response.send_message(
                        embed=select_embed,
                        view=view,
                        ephemeral=True
                    )

                except Exception as e:
                    self.log_message(f"Error in remove_member_button: {e}")
                    await button_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('alliance.member.remove.error_process', self.lang)}",
                        ephemeral=True
                    )

            @discord.ui.button(
                label="View Members",
                emoji=theme.membersIcon,
                style=discord.ButtonStyle.primary,
                custom_id="view_members",
                row=1
            )
            async def view_members_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    alliances, is_global = PermissionManager.get_admin_alliances(
                        button_interaction.user.id,
                        button_interaction.guild_id
                    )

                    if not alliances:
                        await button_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('alliance.member.error.no_authorized_alliance', self.lang)}",
                            ephemeral=True
                        )
                        return

                    select_embed = discord.Embed(
                        title=f"{theme.userIcon} {t('alliance.member.select_alliance_title', self.lang)}",
                        description=(
                            f"{t('alliance.member.view.select_prompt', self.lang)}\n\n"
                            f"**{t('alliance.member.permissions.title', self.lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.userIcon} **{t('alliance.member.permissions.access_level', self.lang)}** `{t('alliance.member.permissions.global_admin', self.lang) if is_global else t('alliance.member.permissions.alliance_admin', self.lang)}`\n"
                            f"{theme.searchIcon} **{t('alliance.member.permissions.access_type', self.lang)}** `{t('alliance.member.permissions.all_alliances', self.lang) if is_global else t('alliance.member.permissions.assigned_alliances', self.lang)}`\n"
                            f"{theme.chartIcon} **{t('alliance.member.permissions.available_alliances', self.lang)}** `{len(alliances)}`\n"
                            f"{theme.lowerDivider}"
                        ),
                        color=theme.emColor1
                    )

                    alliances_with_counts = []
                    for alliance_id, name in alliances:
                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                            member_count = cursor.fetchone()[0]
                            alliances_with_counts.append((alliance_id, name, member_count))

                    view = AllianceSelectView(alliances_with_counts, self.cog, lang=self.lang)
                    
                    async def select_callback(interaction: discord.Interaction):
                        alliance_id = int(view.current_select.values[0])
                        
                        with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                            cursor = alliance_db.cursor()
                            cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (alliance_id,))
                            alliance_name = cursor.fetchone()[0]
                        
                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute("""
                                SELECT fid, nickname, furnace_lv, kid
                                FROM users 
                                WHERE alliance = ? 
                                ORDER BY furnace_lv DESC, nickname
                            """, (alliance_id,))
                            members = cursor.fetchall()
                        
                        if not members:
                            await interaction.response.send_message(
                                f"{theme.deniedIcon} {t('alliance.member.error.no_members', self.lang)}",
                                ephemeral=True
                            )
                            return

                        max_fl = max(member[2] for member in members)
                        avg_fl = sum(member[2] for member in members) / len(members)

                        public_embed = discord.Embed(
                            title=f"{theme.userIcon} {t('alliance.member.view.list_title', self.lang, alliance=alliance_name)}",
                            description=(
                                f"```ml\n"
                                f"{t('alliance.member.stats.title', self.lang)}\n"
                                f"══════════════════════════\n"
                                f"{theme.chartIcon} {t('alliance.member.stats.total_members', self.lang)} {len(members)}\n"
                                f"{theme.levelIcon} {t('alliance.member.stats.highest_level', self.lang)} {self.cog.level_mapping.get(max_fl, str(max_fl))}\n"
                                f"{theme.chartIcon} {t('alliance.member.stats.avg_level', self.lang)} {self.cog.level_mapping.get(int(avg_fl), str(int(avg_fl)))}\n"
                                f"══════════════════════════\n"
                                f"```\n"
                                f"**{t('alliance.member.view.list_header', self.lang)}**\n"
                                f"{theme.middleDivider}\n"
                            ),
                            color=theme.emColor1
                        )

                        members_per_page = 15
                        member_chunks = [members[i:i + members_per_page] for i in range(0, len(members), members_per_page)]
                        embeds = []

                        for page, chunk in enumerate(member_chunks):
                            embed = public_embed.copy()
                            
                            member_list = ""
                            for idx, (fid, nickname, furnace_lv, kid) in enumerate(chunk, start=page * members_per_page + 1):
                                level = self.cog.level_mapping.get(furnace_lv, str(furnace_lv))
                                member_list += (
                                    f"{theme.userIcon} {nickname}\n"
                                    f"└ {theme.levelIcon} {level}\n"
                                    f"└ {theme.fidIcon} {t('alliance.member.common.id_label', self.lang)} {fid}\n"
                                    f"└ {theme.globeIcon} {t('alliance.member.common.state_label', self.lang)} {kid}\n\n"
                                )

                            embed.description += member_list
                            
                            if len(member_chunks) > 1:
                                embed.set_footer(
                                    text=t(
                                        "pagination.page",
                                        self.lang,
                                        current=page + 1,
                                        total=len(member_chunks)
                                    )
                                )
                            
                            embeds.append(embed)

                        pagination_view = PaginationView(embeds, interaction.user.id, self.lang)
                        
                        await interaction.response.edit_message(
                            content=f"{theme.verifiedIcon} {t('alliance.member.view.list_posted', self.lang)}",
                            embed=None,
                            view=None
                        )
                        
                        message = await interaction.channel.send(
                            embed=embeds[0],
                            view=pagination_view if len(embeds) > 1 else None
                        )
                        
                        if pagination_view:
                            pagination_view.message = message

                    view.callback = select_callback
                    await button_interaction.response.send_message(
                        embed=select_embed,
                        view=view,
                        ephemeral=True
                    )

                except Exception as e:
                    self.log_message(f"Error in view_members_button: {e}")
                    if not button_interaction.response.is_done():
                        await button_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('alliance.member.view.error_display', self.lang)}",
                            ephemeral=True
                        )

            @discord.ui.button(
                label="Export Members",
                emoji=theme.chartIcon,
                style=discord.ButtonStyle.primary,
                custom_id="export_members",
                row=1
            )
            async def export_members_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    alliances, is_global = PermissionManager.get_admin_alliances(
                        button_interaction.user.id,
                        button_interaction.guild_id
                    )

                    if not alliances:
                        await button_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('alliance.member.error.no_authorized_alliance', self.lang)}",
                            ephemeral=True
                        )
                        return

                    select_embed = discord.Embed(
                        title=f"{theme.chartIcon} {t('alliance.member.export.select_title', self.lang)}",
                        description=(
                            f"{t('alliance.member.export.select_prompt', self.lang)}\n\n"
                            f"**{t('alliance.member.permissions.title', self.lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.userIcon} **{t('alliance.member.permissions.access_level', self.lang)}** `{t('alliance.member.permissions.global_admin', self.lang) if is_global else t('alliance.member.permissions.alliance_admin', self.lang)}`\n"
                            f"{theme.searchIcon} **{t('alliance.member.permissions.access_type', self.lang)}** `{t('alliance.member.permissions.all_alliances', self.lang) if is_global else t('alliance.member.permissions.assigned_alliances', self.lang)}`\n"
                            f"{theme.chartIcon} **{t('alliance.member.permissions.available_alliances', self.lang)}** `{len(alliances)}`\n"
                            f"{theme.lowerDivider}"
                        ),
                        color=theme.emColor1
                    )

                    # Get member counts for alliances
                    alliances_with_counts = []
                    for alliance_id, name in alliances:
                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                            member_count = cursor.fetchone()[0]
                            alliances_with_counts.append((alliance_id, name, member_count))

                    # Create view for alliance selection with ALL option
                    view = AllianceSelectViewWithAll(alliances_with_counts, self.cog, self.lang)
                    
                    async def select_callback(interaction: discord.Interaction):
                        selected_value = view.current_select.values[0]
                        
                        if selected_value == "all":
                            alliance_id = "all"
                            alliance_name = t("alliance.member.export.all_alliances", self.lang)
                            
                            # Show column selection with alliance name column
                            column_embed = discord.Embed(
                                title=f"{theme.chartIcon} {t('alliance.member.export.columns_title', self.lang)}",
                                description=(
                                    f"**{t('alliance.member.export.type_label', self.lang)}** {t('alliance.member.export.all_alliances', self.lang)}\n"
                                    f"**{t('alliance.member.export.total_alliances', self.lang)}** {len(alliances_with_counts)}\n\n"
                                    f"{t('alliance.member.export.columns_instructions', self.lang)}\n"
                                    f"{t('alliance.member.export.columns_default', self.lang)}\n\n"
                                    f"**{t('alliance.member.export.columns_available', self.lang)}**\n"
                                    f"• **{t('alliance.member.export.column_alliance', self.lang)}** - {t('alliance.member.export.column_alliance_desc', self.lang)}\n"
                                    f"• **{t('alliance.member.export.column_id', self.lang)}** - {t('alliance.member.export.column_id_desc', self.lang)}\n"
                                    f"• **{t('alliance.member.export.column_name', self.lang)}** - {t('alliance.member.export.column_name_desc', self.lang)}\n"
                                    f"• **{t('alliance.member.export.column_fc', self.lang)}** - {t('alliance.member.export.column_fc_desc', self.lang)}\n"
                                    f"• **{t('alliance.member.export.column_state', self.lang)}** - {t('alliance.member.export.column_state_desc', self.lang)}"
                                ),
                                color=theme.emColor1
                            )
                            
                            column_view = ExportColumnSelectView(alliance_id, alliance_name, self.cog, include_alliance=True)
                        else:
                            alliance_id = int(selected_value)
                            # Get alliance name
                            alliance_name = next(
                                (name for aid, name, _ in alliances_with_counts if aid == alliance_id),
                                t("alliance.member.common.unknown", self.lang)
                            )
                            
                            # Show column selection view for single alliance
                            column_embed = discord.Embed(
                                title=f"{theme.chartIcon} {t('alliance.member.export.columns_title', self.lang)}",
                                description=(
                                    f"**{t('alliance.member.common.alliance_label', self.lang)}** {alliance_name}\n\n"
                                    f"{t('alliance.member.export.columns_instructions', self.lang)}\n"
                                    f"{t('alliance.member.export.columns_default', self.lang)}\n\n"
                                    f"**{t('alliance.member.export.columns_available', self.lang)}**\n"
                                    f"• **{t('alliance.member.export.column_id', self.lang)}** - {t('alliance.member.export.column_id_desc', self.lang)}\n"
                                    f"• **{t('alliance.member.export.column_name', self.lang)}** - {t('alliance.member.export.column_name_desc', self.lang)}\n"
                                    f"• **{t('alliance.member.export.column_fc', self.lang)}** - {t('alliance.member.export.column_fc_desc', self.lang)}\n"
                                    f"• **{t('alliance.member.export.column_state', self.lang)}** - {t('alliance.member.export.column_state_desc', self.lang)}"
                                ),
                                color=theme.emColor1
                            )
                            
                            column_view = ExportColumnSelectView(alliance_id, alliance_name, self.cog, include_alliance=False)
                        
                        await interaction.response.edit_message(embed=column_embed, view=column_view)

                    view.callback = select_callback
                    await button_interaction.response.send_message(
                        embed=select_embed,
                        view=view,
                        ephemeral=True
                    )

                except Exception as e:
                    self.cog.log_message(f"Error in export_members_button: {e}")
                    await button_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('alliance.member.export.error_process', self.lang)}",
                        ephemeral=True
                    )
            
            @discord.ui.button(
                label="Main Menu", 
                emoji=theme.homeIcon, 
                style=discord.ButtonStyle.secondary,
                row=2
            )
            async def main_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.cog.show_main_menu(interaction)

            @discord.ui.button(label="Transfer Members", emoji=theme.retryIcon, style=discord.ButtonStyle.primary, row=0)
            async def transfer_member_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    alliances, is_global = PermissionManager.get_admin_alliances(
                        button_interaction.user.id,
                        button_interaction.guild_id
                    )

                    if not alliances:
                        await button_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('alliance.member.error.no_authorized_alliance', self.lang)}",
                            ephemeral=True
                        )
                        return

                    select_embed = discord.Embed(
                        title=f"{theme.refreshIcon} {t('alliance.member.transfer.select_title', self.lang)}",
                        description=(
                            f"{t('alliance.member.transfer.select_prompt', self.lang)}\n\n"
                            f"**{t('alliance.member.permissions.title', self.lang)}**\n"
                            f"{theme.upperDivider}\n"
                            f"{theme.userIcon} **{t('alliance.member.permissions.access_level', self.lang)}** `{t('alliance.member.permissions.global_admin', self.lang) if is_global else t('alliance.member.permissions.alliance_admin', self.lang)}`\n"
                            f"{theme.searchIcon} **{t('alliance.member.permissions.access_type', self.lang)}** `{t('alliance.member.permissions.all_alliances', self.lang) if is_global else t('alliance.member.permissions.assigned_alliances', self.lang)}`\n"
                            f"{theme.chartIcon} **{t('alliance.member.permissions.available_alliances', self.lang)}** `{len(alliances)}`\n"
                            f"{theme.lowerDivider}"
                        ),
                        color=theme.emColor1
                    )

                    alliances_with_counts = []
                    for alliance_id, name in alliances:
                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                            member_count = cursor.fetchone()[0]
                            alliances_with_counts.append((alliance_id, name, member_count))

                    view = AllianceSelectView(alliances_with_counts, self.cog, lang=self.lang)
                    
                    async def source_callback(interaction: discord.Interaction):
                        try:
                            source_alliance_id = int(view.current_select.values[0])
                            
                            with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                                cursor = alliance_db.cursor()
                                cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (source_alliance_id,))
                                source_alliance_name = cursor.fetchone()[0]
                            
                            with sqlite3.connect('db/users.sqlite') as users_db:
                                cursor = users_db.cursor()
                                cursor.execute("""
                                    SELECT fid, nickname, furnace_lv 
                                    FROM users 
                                    WHERE alliance = ? 
                                    ORDER BY furnace_lv DESC, nickname
                                """, (source_alliance_id,))
                                members = cursor.fetchall()

                            if not members:
                                await interaction.response.send_message(
                                    f"{theme.deniedIcon} {t('alliance.member.error.no_members', self.lang)}",
                                    ephemeral=True
                                )
                                return

                            max_fl = max(member[2] for member in members)
                            avg_fl = sum(member[2] for member in members) / len(members)

                            
                            member_embed = discord.Embed(
                                title=f"{theme.userIcon} {t('alliance.member.transfer.selection_title', self.lang, alliance=source_alliance_name)}",
                                description=(
                                    f"```ml\n"
                                    f"{t('alliance.member.stats.title', self.lang)}\n"
                                    f"══════════════════════════\n"
                                    f"{theme.chartIcon} {t('alliance.member.stats.total_members', self.lang)} {len(members)}\n"
                                    f"{theme.levelIcon} {t('alliance.member.stats.highest_level', self.lang)} {self.cog.level_mapping.get(max_fl, str(max_fl))}\n"
                                    f"{theme.chartIcon} {t('alliance.member.stats.avg_level', self.lang)} {self.cog.level_mapping.get(int(avg_fl), str(int(avg_fl)))}\n"
                                    f"══════════════════════════\n"
                                    f"```\n"
                                    f"{t('alliance.member.transfer.select_member', self.lang)}\n\n"
                                    f"**{t('alliance.member.transfer.methods_title', self.lang)}**\n"
                                    f"{theme.num1Icon} {t('alliance.member.transfer.method_menu', self.lang)}\n"
                                    f"{theme.num2Icon} {t('alliance.member.transfer.method_id', self.lang)}\n"
                                    f"{theme.middleDivider}"
                                ),
                                color=theme.emColor1
                            )

                            member_view = MemberSelectView(
                                members,
                                source_alliance_name,
                                self.cog,
                                is_remove_operation=False,
                                alliance_id=source_alliance_id,
                                alliances=alliances_with_counts,
                                lang=self.lang
                            )

                            async def member_callback(member_interaction: discord.Interaction, selected_fids=None):
                                if not selected_fids:
                                    await member_interaction.response.send_message(
                                        t("alliance.member.transfer.no_members_selected", self.lang),
                                        ephemeral=True
                                    )
                                    return

                                # Get member names for confirmation
                                with sqlite3.connect('db/users.sqlite') as users_db:
                                    cursor = users_db.cursor()
                                    placeholders = ','.join('?' * len(selected_fids))
                                    cursor.execute(f"SELECT fid, nickname FROM users WHERE fid IN ({placeholders})", selected_fids)
                                    selected_members = cursor.fetchall()

                                member_list = "\n".join([f"• {nickname} (ID: {fid})" for fid, nickname in selected_members[:10]])
                                if len(selected_members) > 10:
                                    member_list += t(
                                        "alliance.member.transfer.more_members",
                                        self.lang,
                                        count=len(selected_members) - 10
                                    )

                                target_embed = discord.Embed(
                                    title=f"{theme.pinIcon} {t('alliance.member.transfer.target_title', self.lang)}",
                                    description=(
                                        f"**{t('alliance.member.transfer.transferring', self.lang, count=len(selected_fids))}**\n"
                                        f"{member_list}\n\n"
                                        f"{t('alliance.member.transfer.target_prompt', self.lang)}"
                                    ),
                                    color=theme.emColor1
                                )

                                target_options = [
                                    discord.SelectOption(
                                        label=f"{name[:50]}",
                                        value=str(alliance_id),
                                        description=t(
                                            "alliance.member.transfer.target_option",
                                            self.lang,
                                            alliance_id=alliance_id,
                                            count=count
                                        ),
                                        emoji=theme.allianceIcon
                                    ) for alliance_id, name, count in alliances_with_counts
                                    if alliance_id != source_alliance_id
                                ]

                                target_select = discord.ui.Select(
                                    placeholder=f"{theme.pinIcon} {t('alliance.member.transfer.target_placeholder', self.lang)}",
                                    options=target_options
                                )
                                
                                target_view = discord.ui.View()
                                target_view.add_item(target_select)

                                async def target_callback(target_interaction: discord.Interaction):
                                    target_alliance_id = int(target_select.values[0])

                                    try:
                                        with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                                            cursor = alliance_db.cursor()
                                            cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (target_alliance_id,))
                                            target_alliance_name = cursor.fetchone()[0]

                                        # Bulk transfer
                                        with sqlite3.connect('db/users.sqlite') as users_db:
                                            cursor = users_db.cursor()
                                            placeholders = ','.join('?' * len(selected_fids))
                                            cursor.execute(
                                                f"UPDATE users SET alliance = ? WHERE fid IN ({placeholders})",
                                                [target_alliance_id] + selected_fids
                                            )
                                            users_db.commit()

                                        success_embed = discord.Embed(
                                            title=f"{theme.verifiedIcon} {t('alliance.member.transfer.success_title', self.lang)}",
                                            description=(
                                                f"**{t('alliance.member.transfer.transferred_count', self.lang)}** {len(selected_fids)}\n"
                                                f"{theme.allianceOldIcon} **{t('alliance.member.transfer.source_label', self.lang)}** {source_alliance_name}\n"
                                                f"{theme.allianceIcon} **{t('alliance.member.transfer.target_label', self.lang)}** {target_alliance_name}\n\n"
                                                f"**{t('alliance.member.transfer.transferred_members', self.lang)}**\n{member_list}"
                                            ),
                                            color=theme.emColor3
                                        )

                                        await target_interaction.response.edit_message(
                                            embed=success_embed,
                                            view=None
                                        )

                                        # Log the bulk transfer
                                        self.cog.log_message(
                                            f"Bulk transfer: {len(selected_fids)} members from {source_alliance_name} to {target_alliance_name}"
                                        )

                                    except Exception as e:
                                        print(f"Transfer error: {e}")
                                        self.cog.log_message(f"Bulk transfer error: {e}")
                                        error_embed = discord.Embed(
                                            title=f"{theme.deniedIcon} {t('alliance.member.common.error_title', self.lang)}",
                                            description=t('alliance.member.transfer.error_body', self.lang),
                                            color=theme.emColor2
                                        )
                                        await target_interaction.response.edit_message(
                                            embed=error_embed,
                                            view=None
                                        )

                                target_select.callback = target_callback
                                try:
                                    await member_interaction.response.edit_message(
                                        embed=target_embed,
                                        view=target_view
                                    )
                                except:
                                    await member_interaction.edit_original_response(
                                        embed=target_embed,
                                        view=target_view
                                    )

                            member_view.callback = member_callback
                            await interaction.response.edit_message(
                                embed=member_embed,
                                view=member_view
                            )

                        except Exception as e:
                            self.log_message(f"Source callback error: {e}")
                            await interaction.response.send_message(
                                f"{theme.deniedIcon} {t('alliance.member.common.try_again', self.lang)}",
                                ephemeral=True
                            )

                    view.callback = source_callback
                    await button_interaction.response.send_message(
                        embed=select_embed,
                        view=view,
                        ephemeral=True
                    )

                except Exception as e:
                    self.log_message(f"Error in transfer_member_button: {e}")
                    await button_interaction.response.send_message(
                        f"{theme.deniedIcon} {t('alliance.member.transfer.error_body', self.lang)}",
                        ephemeral=True
                    )

        view = MemberOperationsView(self, lang)
        await interaction.response.edit_message(embed=embed, view=view)

    async def add_user(self, interaction: discord.Interaction, alliance_id: str, ids: str):
        lang = _get_lang(interaction)
        self.c_alliance.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (alliance_id,))
        alliance_name = self.c_alliance.fetchone()
        if alliance_name:
            alliance_name = alliance_name[0]
        else:
            await interaction.response.send_message(
                t("alliance.member.add.alliance_not_found", lang),
                ephemeral=True
            )
            return

        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message(
                t("alliance.member.add.no_permission", lang),
                ephemeral=True
            )
            return
        
        # Always add to queue to ensure proper ordering
        queue_position = await self.login_handler.queue_operation({
            'type': 'member_addition',
            'callback': lambda: self._process_add_user(interaction, alliance_id, alliance_name, ids),
            'description': f"Add members to {alliance_name}",
            'alliance_id': alliance_id,
            'interaction': interaction
        })
        
        # Check if we need to show queue message
        queue_info = self.login_handler.get_queue_info()
        # Calculate member count
        member_count = len(ids.split(',') if ',' in ids else ids.split('\n'))
        
        if queue_position > 1:  # Not the first in queue
            queue_embed = discord.Embed(
                title=f"{theme.timeIcon} {t('alliance.member.add.queued_title', lang)}",
                description=(
                    f"{t('alliance.member.add.queue_in_progress', lang)}\n\n"
                    f"**{t('alliance.member.add.queue_details', lang)}**\n"
                    f"{theme.pinIcon} {t('alliance.member.add.queue_position', lang)} `{queue_position}`\n"
                    f"{theme.allianceIcon} {t('alliance.member.common.alliance_label', lang)} {alliance_name}\n"
                    f"{theme.userIcon} {t('alliance.member.add.members_to_add', lang)} {member_count}\n\n"
                    f"{t('alliance.member.add.queue_notify', lang)}"
                ),
                color=theme.emColor4
            )
            await interaction.response.send_message(embed=queue_embed, ephemeral=True)
        else:
            # First in queue - will start immediately
            total_count = member_count
            embed = discord.Embed(
                title=f"{theme.userIcon} {t('alliance.member.add.progress_title', lang)}", 
                description=t(
                    "alliance.member.add.progress_desc",
                    lang,
                    count=total_count,
                    alliance=alliance_name,
                    current=0,
                    total=total_count
                ),
                color=theme.emColor1
            )
            embed.add_field(
                name=t("alliance.member.add.added_field", lang, current=0, total=total_count),
                value=t("alliance.member.common.none", lang),
                inline=False
            )
            embed.add_field(
                name=t("alliance.member.add.failed_field", lang, current=0, total=total_count),
                value=t("alliance.member.common.none", lang),
                inline=False
            )
            embed.add_field(
                name=t("alliance.member.add.exists_field", lang, current=0, total=total_count),
                value=t("alliance.member.common.none", lang),
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _process_add_user(self, interaction: discord.Interaction, alliance_id: str, alliance_name: str, ids: str):
        """Process the actual user addition operation"""
        lang = _get_lang(interaction)
        ids_list = []
        
        # Check if this is CSV/TSV data with headers
        lines = [line.strip() for line in ids.split('\n') if line.strip()]
        if lines and any(delimiter in lines[0] for delimiter in [',', '\t']):
            # Detect delimiter
            delimiter = '\t' if '\t' in lines[0] else ','
            
            # Try to parse as CSV/TSV
            try:
                reader = csv.reader(io.StringIO(ids), delimiter=delimiter)
                rows = list(reader)
                
                if rows and len(rows) > 1:
                    # Get headers
                    headers = [h.strip().lower() for h in rows[0]]
                    
                    # Find ID column - look for 'id', 'fid'
                    id_col_index = None
                    for i, header in enumerate(headers):
                        if header in ['id', 'fid']:
                            id_col_index = i
                            break
                    
                    if id_col_index is not None:
                        # Extract IDs from data rows
                        for row in rows[1:]:
                            if len(row) > id_col_index and row[id_col_index].strip():
                                # Clean the ID
                                fid = ''.join(c for c in row[id_col_index] if c.isdigit())
                                if fid:
                                    ids_list.append(fid)
                        
                        if ids_list:
                            self.log_message(f"Parsed CSV/TSV import: Found {len(ids_list)} IDs from {len(rows)-1} rows")
                    else:
                        # No header found, treat first row as data if it looks like IDs
                        if rows[0] and rows[0][0].strip().isdigit():
                            for row in rows:
                                if row and row[0].strip():
                                    fid = ''.join(c for c in row[0] if c.isdigit())
                                    if fid:
                                        ids_list.append(fid)
            except Exception as e:
                self.log_message(f"CSV/TSV parsing failed, falling back to simple parsing: {e}")
        
        # If CSV/TSV parsing didn't work or wasn't applicable, use simple parsing
        if not ids_list:
            if '\n' in ids:
                ids_list = [fid.strip() for fid in ids.split('\n') if fid.strip()]
            else:
                ids_list = [fid.strip() for fid in ids.split(",") if fid.strip()]

        # Pre-check which IDs already exist in the database
        already_in_db = []
        fids_to_process = []
        
        for fid in ids_list:
            self.c_users.execute("SELECT nickname FROM users WHERE fid=?", (fid,))
            existing = self.c_users.fetchone()
            if existing:
                # Member already exists in database
                already_in_db.append((fid, existing[0]))
            else:
                # Member doesn't exist at all
                fids_to_process.append(fid)
        
        total_users = len(ids_list)
        self.log_message(f"Pre-check complete: {len(already_in_db)} already exist, {len(fids_to_process)} to process")
        
        # For queued operations, we need to send a new progress embed
        if interaction.response.is_done():
            embed = discord.Embed(
                title=f"{theme.userIcon} {t('alliance.member.add.progress_title', lang)}", 
                description=t(
                    "alliance.member.add.progress_desc_short",
                    lang,
                    count=total_users,
                    current=0,
                    total=total_users
                ),
                color=theme.emColor1
            )
            embed.add_field(
                name=t("alliance.member.add.added_field", lang, current=0, total=total_users),
                value=t("alliance.member.common.none", lang),
                inline=False
            )
            embed.add_field(
                name=t("alliance.member.add.failed_field", lang, current=0, total=total_users),
                value=t("alliance.member.common.none", lang),
                inline=False
            )
            embed.add_field(
                name=t("alliance.member.add.exists_field", lang, current=0, total=total_users),
                value=t("alliance.member.common.none", lang),
                inline=False
            )
            message = await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # For immediate operations, the progress embed is already sent
            message = await interaction.original_response()
            # Get the embed from the existing message
            embed = (await interaction.original_response()).embeds[0]
        
        # Reset rate limit tracking for this operation
        self.login_handler.api1_requests = []
        self.login_handler.api2_requests = []
        
        # Check API availability before starting
        embed.description = f"{theme.searchIcon} {t('alliance.member.add.checking_api', lang)}"
        await message.edit(embed=embed)
        
        await self.login_handler.check_apis_availability()
        
        if not self.login_handler.available_apis:
            # No APIs available
            embed.description = f"{theme.deniedIcon} {t('alliance.member.add.no_api', lang)}"
            embed.color = discord.Color.red()
            await message.edit(embed=embed)
            return
        
        # Get processing rate from login handler
        rate_text = self.login_handler.get_processing_rate()
        
        # Update embed with rate information
        queue_info = (
            f"\n{theme.listIcon} **{t('alliance.member.add.queue_size', lang)}** {self.login_handler.get_queue_info()['queue_size']}"
            if self.login_handler.get_queue_info()['queue_size'] > 0
            else ""
        )
        embed.description = t(
            "alliance.member.add.progress_desc_rate",
            lang,
            count=total_users,
            rate=rate_text,
            queue_info=queue_info,
            current=0,
            total=total_users
        )
        embed.color = discord.Color.blue()
        await message.edit(embed=embed)

        added_count = 0
        error_count = 0 
        already_exists_count = len(already_in_db)
        added_users = []
        error_users = []
        already_exists_users = already_in_db.copy()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file_path = os.path.join(self.log_directory, 'add_memberlog.txt')
        
        # Determine input format
        input_format = "Simple IDs"
        if '\t' in ids and ',' not in ids.split('\n')[0] if '\n' in ids else ids:
            input_format = "TSV Format"
        elif ',' in ids and len(ids.split(',')[0]) > 10:
            input_format = "CSV Format"
        
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n{'='*50}\n")
                log_file.write(f"Date: {timestamp}\n")
                log_file.write(f"Administrator: {interaction.user.name} (ID: {interaction.user.id})\n")
                log_file.write(f"Alliance: {alliance_name} (ID: {alliance_id})\n")
                log_file.write(f"Input Format: {input_format}\n")
                # Avoid nested f-strings for Python 3.9+ compatibility
                if len(ids_list) <= 20:
                    ids_display = ', '.join(ids_list)
                else:
                    ids_display = f"{', '.join(ids_list[:20])}... ({len(ids_list)} total)"
                log_file.write(f"IDs to Process: {ids_display}\n")
                log_file.write(f"Total Members to Process: {total_users}\n")
                log_file.write(f"API Mode: {self.login_handler.get_mode_text()}\n")
                log_file.write(f"Available APIs: {self.login_handler.available_apis}\n")
                log_file.write(f"Operations in Queue: {self.login_handler.get_queue_info()['queue_size']}\n")
                log_file.write('-'*50 + '\n')

            # Update initial display with pre-existing members
            if already_exists_count > 0:
                embed.set_field_at(
                    2,
                    name=t("alliance.member.add.exists_field", lang, current=already_exists_count, total=total_users),
                    value=t("alliance.member.add.list_too_long", lang) if len(already_exists_users) > 70 
                    else ", ".join([n for _, n in already_exists_users]) or "-",
                    inline=False
                )
                await message.edit(embed=embed)
            
            index = 0
            while index < len(fids_to_process):
                fid = fids_to_process[index]
                try:
                    # Update progress
                    queue_info = (
                        f"\n{theme.listIcon} **{t('alliance.member.add.queue_size', lang)}** {self.login_handler.get_queue_info()['queue_size']}"
                        if self.login_handler.get_queue_info()['queue_size'] > 0
                        else ""
                    )
                    current_progress = already_exists_count + index + 1
                    embed.description = t(
                        "alliance.member.add.progress_desc_rate",
                        lang,
                        count=total_users,
                        rate=rate_text,
                        queue_info=queue_info,
                        current=current_progress,
                        total=total_users
                    )
                    await message.edit(embed=embed)
                    
                    # Fetch player data using login handler
                    result = await self.login_handler.fetch_player_data(fid)
                    
                    with open(log_file_path, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"\nAPI Response for ID {fid}:\n")
                        log_file.write(f"Status: {result['status']}\n")
                        if result.get('api_used'):
                            log_file.write(f"API Used: {result['api_used']}\n")
                    
                    if result['status'] == 'rate_limited':
                        # Handle rate limiting with countdown
                        wait_time = result.get('wait_time', 60)
                        countdown_start = time.time()
                        remaining_time = wait_time
                        
                        with open(log_file_path, 'a', encoding='utf-8') as log_file:
                            log_file.write(f"Rate limit reached - Total wait time: {wait_time:.1f} seconds\n")
                        
                        # Update display with countdown
                        while remaining_time > 0:
                            queue_info = (
                                f"\n{theme.listIcon} **{t('alliance.member.add.queue_size', lang)}** {self.login_handler.get_queue_info()['queue_size']}"
                                if self.login_handler.get_queue_info()['queue_size'] > 0
                                else ""
                            )
                            embed.description = t(
                                "alliance.member.add.rate_limit_wait",
                                lang,
                                seconds=f"{remaining_time:.0f}",
                                queue_info=queue_info
                            )
                            embed.color = discord.Color.orange()
                            await message.edit(embed=embed)
                            
                            # Wait for up to 5 seconds before updating
                            await asyncio.sleep(min(5, remaining_time))
                            elapsed = time.time() - countdown_start
                            remaining_time = max(0, wait_time - elapsed)
                        
                        embed.color = discord.Color.blue()
                        continue  # Retry this request
                    
                    if result['status'] == 'success':
                        data = result['data']
                        with open(log_file_path, 'a', encoding='utf-8') as log_file:
                            log_file.write(f"API Response Data: {str(data)}\n")
                        
                        nickname = data.get('nickname')
                        furnace_lv = data.get('stove_lv', 0)
                        stove_lv_content = data.get('stove_lv_content', None)
                        kid = data.get('kid', None)

                        if nickname:
                            try: # Since we pre-filtered, this ID should not exist in database
                                self.c_users.execute("""
                                    INSERT INTO users (fid, nickname, furnace_lv, kid, stove_lv_content, alliance)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (fid, nickname, furnace_lv, kid, stove_lv_content, alliance_id))
                                self.conn_users.commit()
                                
                                with open(self.log_file, 'a', encoding='utf-8') as f:
                                    f.write(f"[{timestamp}] Successfully added member - ID: {fid}, Nickname: {nickname}, Level: {furnace_lv}\n")
                                
                                added_count += 1
                                added_users.append((fid, nickname))
                                
                                embed.set_field_at(
                                    0,
                                    name=t("alliance.member.add.added_field", lang, current=added_count, total=total_users),
                                    value=t("alliance.member.add.list_too_long", lang) if len(added_users) > 70 
                                    else ", ".join([n for _, n in added_users]) or "-",
                                    inline=False
                                )
                                await message.edit(embed=embed)
                                
                            except sqlite3.IntegrityError as e:
                                # This shouldn't happen since we pre-filtered, but handle it just in case
                                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                                    log_file.write(f"ERROR: Member already exists (race condition?) - ID {fid}: {str(e)}\n")
                                already_exists_count += 1
                                already_exists_users.append((fid, nickname))
                                
                                embed.set_field_at(
                                    2,
                                    name=t("alliance.member.add.exists_field", lang, current=already_exists_count, total=total_users),
                                    value=t("alliance.member.add.list_too_long", lang) if len(already_exists_users) > 70 
                                    else ", ".join([n for _, n in already_exists_users]) or "-",
                                    inline=False
                                )
                                await message.edit(embed=embed)
                                
                            except Exception as e:
                                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                                    log_file.write(f"ERROR: Database error for ID {fid}: {str(e)}\n")
                                error_count += 1
                                error_users.append(fid)
                                
                                embed.set_field_at(
                                    1,
                                    name=t("alliance.member.add.failed_field", lang, current=error_count, total=total_users),
                                    value=t("alliance.member.add.list_too_long", lang) if len(error_users) > 70 
                                    else ", ".join(error_users) or "-",
                                    inline=False
                                )
                                await message.edit(embed=embed)
                        else:
                            # No nickname in API response
                            error_count += 1
                            error_users.append(fid)
                    else:
                            # Handle other error statuses
                            error_msg = result.get('error_message', 'Unknown error')
                            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                                log_file.write(f"ERROR: {error_msg} for ID {fid}\n")
                            error_count += 1
                            if fid not in error_users:
                                error_users.append(fid)
                            embed.set_field_at(
                                1,
                                name=t("alliance.member.add.failed_field", lang, current=error_count, total=total_users),
                                value=t("alliance.member.add.list_too_long", lang) if len(error_users) > 70 
                                else ", ".join(error_users) or "-",
                                inline=False
                            )
                            await message.edit(embed=embed)
                    
                    index += 1

                except Exception as e:
                    with open(log_file_path, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"ERROR: Request failed for ID {fid}: {str(e)}\n")
                        error_count += 1
                        error_users.append(fid)
                        await message.edit(embed=embed)
                        index += 1

            embed.set_field_at(
                0,
                name=f"{theme.verifiedIcon} {t('alliance.member.add.added_field', lang, current=added_count, total=total_users)}",
                value=t("alliance.member.add.list_too_long", lang) if len(added_users) > 70 
                else ", ".join([nickname for _, nickname in added_users]) or "-",
                inline=False
            )
            
            embed.set_field_at(1, name=t("alliance.member.add.failed_field", lang, current=error_count, total=total_users),
                value=t("alliance.member.add.list_too_long", lang) if len(error_users) > 70 
                else ", ".join(error_users) or "-",
                inline=False
            )
            
            embed.set_field_at(2, name=t("alliance.member.add.exists_field", lang, current=already_exists_count, total=total_users),
                value=t("alliance.member.add.list_too_long", lang) if len(already_exists_users) > 70 
                else ", ".join([nickname for _, nickname in already_exists_users]) or "-",
                inline=False
            )

            await message.edit(embed=embed)

            try:
                with sqlite3.connect('db/settings.sqlite') as settings_db:
                    cursor = settings_db.cursor()
                    cursor.execute("""
                        SELECT channel_id 
                        FROM alliance_logs 
                        WHERE alliance_id = ?
                    """, (alliance_id,))
                    alliance_log_result = cursor.fetchone()
                    
                    if alliance_log_result and alliance_log_result[0]:
                        log_embed = discord.Embed(
                            title=f"{theme.userIcon} {t('alliance.member.add.log_title', lang)}",
                            description=(
                                f"**{t('alliance.member.common.alliance_label', lang)}** {alliance_name}\n"
                                f"**{t('alliance.member.common.admin_label', lang)}** {interaction.user.name} (`{interaction.user.id}`)\n"
                                f"**{t('alliance.member.common.date_label', lang)}** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                f"**{t('alliance.member.add.results_title', lang)}**\n"
                                f"{theme.verifiedIcon} {t('alliance.member.add.results_added', lang)} {added_count}\n"
                                f"{theme.deniedIcon} {t('alliance.member.add.results_failed', lang)} {error_count}\n"
                                f"{theme.warnIcon} {t('alliance.member.add.results_exists', lang)} {already_exists_count}\n\n"
                                f"**{t('alliance.member.add.ids_title', lang)}**\n"
                                f"```\n{', '.join(ids_list)}\n```"
                            ),
                            color=theme.emColor3
                        )

                        try:
                            alliance_channel_id = int(alliance_log_result[0])
                            alliance_log_channel = self.bot.get_channel(alliance_channel_id)
                            if alliance_log_channel:
                                await alliance_log_channel.send(embed=log_embed)
                        except Exception as e:
                            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                                log_file.write(f"ERROR: Alliance Log Sending Error: {str(e)}\n")

            except Exception as e:
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"ERROR: Log record error: {str(e)}\n")

            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"\nFinal Results:\n")
                log_file.write(f"Successfully Added: {added_count}\n")
                log_file.write(f"Failed: {error_count}\n")
                log_file.write(f"Already Exists: {already_exists_count}\n")
                log_file.write(f"API Mode: {self.login_handler.get_mode_text()}\n")
                log_file.write(f"API1 Requests: {len(self.login_handler.api1_requests)}\n")
                log_file.write(f"API2 Requests: {len(self.login_handler.api2_requests)}\n")
                log_file.write(f"{'='*50}\n")

        except Exception as e:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"CRITICAL ERROR: {str(e)}\n")
                log_file.write(f"{'='*50}\n")

        # Calculate total processing time
        end_time = datetime.now()
        start_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        processing_time = (end_time - start_time).total_seconds()
        
        queue_info = (
            f"{theme.listIcon} **{t('alliance.member.add.queue_still', lang)}** {self.login_handler.get_queue_info()['queue_size']}"
            if self.login_handler.get_queue_info()['queue_size'] > 0
            else ""
        )
        
        embed.title = f"{theme.verifiedIcon} {t('alliance.member.add.completed_title', lang)}"
        embed.description = (
            f"{t('alliance.member.add.completed_body', lang, count=total_users)}\n"
            f"**{t('alliance.member.add.processing_time', lang)}** {processing_time:.1f} {t('alliance.member.common.seconds', lang)}{queue_info}\n\n"
        )
        embed.color = discord.Color.green()
        await message.edit(embed=embed)

    async def is_admin(self, user_id):
        try:
            with sqlite3.connect('db/settings.sqlite') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM admin WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                is_admin = result is not None
                return is_admin
        except Exception as e:
            self.log_message(f"Error in admin check: {str(e)}")
            self.log_message(f"Error details: {str(e.__class__.__name__)}")
            return False

    def cog_unload(self):
        self.conn_users.close()
        self.conn_alliance.close()

    async def get_admin_alliances(self, user_id: int, guild_id: int):
        """Get alliances for admin from centralized PermissionManager"""
        return PermissionManager.get_admin_alliances(user_id, guild_id)

    async def handle_button_interaction(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        
        if custom_id == "main_menu":
            await self.show_main_menu(interaction)
    
    async def process_member_export(self, interaction: discord.Interaction, alliance_id, alliance_name: str, selected_columns: list, export_format: str):
        """Process the member export with selected columns and format"""
        try:
            lang = _get_lang(interaction)
            # Update the message to show processing
            processing_embed = discord.Embed(
                title=f"{theme.timeIcon} {t('alliance.member.export.processing_title', lang)}",
                description=t("alliance.member.export.processing_body", lang),
                color=theme.emColor1
            )
            await interaction.response.edit_message(embed=processing_embed, view=None)
            
            # Build the SQL query based on selected columns
            db_columns = [col[0] for col in selected_columns]
            headers = [col[1] for col in selected_columns]
            
            # Check if exporting all alliances
            if alliance_id == "all":
                # Need to join with alliance table to get alliance names
                with sqlite3.connect('db/users.sqlite') as users_db:
                    # Attach the alliance database to get alliance names
                    cursor = users_db.cursor()
                    cursor.execute("ATTACH DATABASE 'db/alliance.sqlite' AS alliance_db")
                    
                    # Build query columns
                    query_columns = []
                    for db_col, _ in selected_columns:
                        if db_col == 'alliance_name':
                            query_columns.append('a.name AS alliance_name')
                        else:
                            query_columns.append(f'u.{db_col}')
                    
                    # Query with join
                    query = f"""
                        SELECT {', '.join(query_columns)}
                        FROM users u
                        JOIN alliance_db.alliance_list a ON u.alliance = a.alliance_id
                        ORDER BY a.name, u.furnace_lv DESC, u.nickname
                    """
                    cursor.execute(query)
                    members = cursor.fetchall()
                    cursor.execute("DETACH DATABASE alliance_db")
            else:
                # Single alliance export
                with sqlite3.connect('db/users.sqlite') as users_db:
                    cursor = users_db.cursor()
                    # Filter out alliance_name if it's in the columns (not applicable for single alliance)
                    filtered_columns = [col for col in selected_columns if col[0] != 'alliance_name']
                    db_columns = [col[0] for col in filtered_columns]
                    headers = [col[1] for col in filtered_columns]
                    
                    query = f"SELECT {', '.join(db_columns)} FROM users WHERE alliance = ? ORDER BY furnace_lv DESC, nickname"
                    cursor.execute(query, (alliance_id,))
                    members = cursor.fetchall()
            
            if not members:
                error_embed = discord.Embed(
                    title=f"{theme.deniedIcon} {t('alliance.member.export.no_members_title', lang)}",
                    description=t("alliance.member.export.no_members_body", lang),
                    color=theme.emColor2
                )
                await interaction.edit_original_response(embed=error_embed)
                return
            
            # Create the export file in memory
            output = io.StringIO()
            delimiter = '\t' if export_format == 'tsv' else ','
            writer = csv.writer(output, delimiter=delimiter)
            
            # Write headers
            writer.writerow(headers)
            
            # Process and write member data
            for member in members:
                row = []
                # Use the appropriate columns list based on whether it's a single or all export
                columns_to_use = selected_columns if alliance_id == "all" else filtered_columns
                for i, (db_col, header) in enumerate(columns_to_use):
                    value = member[i]
                    
                    # Special formatting for FC Level
                    if db_col == 'furnace_lv' and value is not None:
                        value = self.level_mapping.get(value, str(value))
                    
                    # Handle None values
                    if value is None:
                        value = ''
                    
                    row.append(value)
                
                writer.writerow(row)
            
            # Get the CSV/TSV content
            output.seek(0)
            file_content = output.getvalue()
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{alliance_name.replace(' ', '_')}_members_{timestamp}.{export_format}"
            
            # Create Discord file
            file = discord.File(io.BytesIO(file_content.encode('utf-8')), filename=filename)
            
            # Create summary embed
            summary_embed = discord.Embed(
                title=f"{theme.chartIcon} {t('alliance.member.export.ready_title', lang)}",
                description=(
                    f"**{t('alliance.member.common.alliance_label', lang)}** {alliance_name}\n"
                    f"**{t('alliance.member.export.total_members', lang)}** {len(members)}\n"
                    f"**{t('alliance.member.export.format_label', lang)}** {export_format.upper()}\n"
                    f"**{t('alliance.member.export.columns_included', lang)}** {', '.join(headers)}\n\n"
                    f"{t('alliance.member.export.dm_attempt', lang)}"
                ),
                color=theme.emColor3
            )
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"{theme.chartIcon} {t('alliance.member.export.dm_title', lang)}",
                    description=(
                        f"**{t('alliance.member.common.alliance_label', lang)}** {alliance_name}\n"
                        f"**{t('alliance.member.export.date_label', lang)}** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"**{t('alliance.member.export.total_members', lang)}** {len(members)}\n"
                        f"**{t('alliance.member.export.format_label', lang)}** {export_format.upper()}\n"
                        f"**{t('alliance.member.export.columns_label', lang)}** {', '.join(headers)}\n"
                    ),
                    color=theme.emColor1
                )
                
                # Add statistics
                if 'furnace_lv' in db_columns:
                    fc_index = db_columns.index('furnace_lv')
                    fc_levels = [m[fc_index] for m in members if m[fc_index] is not None]
                    if fc_levels:
                        max_fc = max(fc_levels)
                        avg_fc = sum(fc_levels) / len(fc_levels)
                        dm_embed.add_field(
                            name=f"{theme.chartIcon} {t('alliance.member.export.stats_title', lang)}",
                            value=(
                                f"**{t('alliance.member.export.stats_highest', lang)}** {self.level_mapping.get(max_fc, str(max_fc))}\n"
                                f"**{t('alliance.member.export.stats_average', lang)}** {self.level_mapping.get(int(avg_fc), str(int(avg_fc)))}"
                            ),
                            inline=False
                        )
                
                # Send DM with file
                await interaction.user.send(embed=dm_embed, file=file)
                
                # Update summary embed with success
                summary_embed.description += f"\n\n{theme.verifiedIcon} **{t('alliance.member.export.dm_success', lang)}**"
                summary_embed.color = discord.Color.green()
                
                # Log the export
                self.log_message(
                    f"Export completed - User: {interaction.user.name} ({interaction.user.id}), "
                    f"Alliance: {alliance_name} ({alliance_id}), Members: {len(members)}, "
                    f"Format: {export_format}, Columns: {', '.join(headers)}"
                )
                
            except discord.Forbidden:
                # DM failed, provide alternative
                summary_embed.description += (
                    f"\n\n{theme.deniedIcon} **{t('alliance.member.export.dm_failed', lang)}**\n"
                    f"{t('alliance.member.export.dm_fallback', lang)}"
                )
                summary_embed.color = discord.Color.orange()
                
                # Since DM failed, edit the original message with the file
                await interaction.edit_original_response(embed=summary_embed)
                # Send file as a follow-up
                await interaction.followup.send(file=file, ephemeral=True)
                return
            
            await interaction.edit_original_response(embed=summary_embed)
            
        except Exception as e:
            self.log_message(f"Error in process_member_export: {e}")
            error_embed = discord.Embed(
                title=f"{theme.deniedIcon} {t('alliance.member.export.failed_title', lang)}",
                description=t("alliance.member.export.failed_body", lang, error=str(e)),
                color=theme.emColor2
            )
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=error_embed)
            else:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)

    async def show_main_menu(self, interaction: discord.Interaction):
        try:
            alliance_cog = self.bot.get_cog("Alliance")
            if alliance_cog:
                await alliance_cog.show_main_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('alliance.member.common.main_menu_error', _get_lang(interaction))}",
                    ephemeral=True
                )
        except Exception as e:
            self.log_message(f"[ERROR] Main Menu error in member operations: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('alliance.member.common.main_menu_error', _get_lang(interaction))}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('alliance.member.common.main_menu_error', _get_lang(interaction))}",
                    ephemeral=True
                )

class AddMemberModal(discord.ui.Modal):
    def __init__(self, alliance_id, lang: str):
        super().__init__(title=t("alliance.member.add.modal_title", lang))
        self.alliance_id = alliance_id
        self.lang = lang
        self.add_item(discord.ui.TextInput(
            label=t("alliance.member.add.modal_label", self.lang),
            placeholder=t("alliance.member.add.modal_placeholder", self.lang),
            style=discord.TextStyle.paragraph
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ids = self.children[0].value
            await interaction.client.get_cog("AllianceMemberOperations").add_user(
                interaction, 
                self.alliance_id, 
                ids
            )
        except Exception as e:
            print(f"ERROR: Modal submit error - {str(e)}")
            await interaction.response.send_message(
                t("alliance.member.common.try_again", self.lang),
                ephemeral=True
            )

class AllianceSelectView(discord.ui.View):
    def __init__(self, alliances_with_counts, cog=None, page=0, context="transfer", lang: str | None = None):
        super().__init__(timeout=7200)
        self.alliances = alliances_with_counts
        self.cog = cog
        self.page = page
        self.max_page = (len(alliances_with_counts) - 1) // 25 if alliances_with_counts else 0
        self.current_select = None
        self.callback = None
        self.member_dict = {}
        self.selected_alliance_id = None
        self.context = context  # "transfer", "furnace_history", or "nickname_history"
        self.lang = lang or get_guild_language(None)
        self.update_select_menu()
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == "Filter by ID":
                item.label = t("alliance.member.select.filter_id", self.lang)

    def update_select_menu(self):
        for item in self.children[:]:
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)

        start_idx = self.page * 25
        end_idx = min(start_idx + 25, len(self.alliances))
        current_alliances = self.alliances[start_idx:end_idx]

        options = []
        for alliance_data in current_alliances:
            # Handle both 3-tuple and 4-tuple formats
            if len(alliance_data) == 4:
                alliance_id, name, count, is_assigned = alliance_data
                assigned_label = t("alliance.member.select.assigned", self.lang) if is_assigned else ""
                label = f"{name[:45]} {assigned_label}"[:50]
                description = t(
                    "alliance.member.select.option_desc_assigned",
                    self.lang,
                    alliance_id=alliance_id,
                    count=count,
                    assigned=assigned_label
                )[:100]
            else:
                alliance_id, name, count = alliance_data
                label = f"{name[:50]}"
                description = t(
                    "alliance.member.select.option_desc",
                    self.lang,
                    alliance_id=alliance_id,
                    count=count
                )

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(alliance_id),
                    description=description,
                    emoji=theme.verifiedIcon if len(alliance_data) == 4 and alliance_data[3] else theme.allianceIcon
                )
            )

        select = discord.ui.Select(
            placeholder=f"{theme.allianceIcon} {t('alliance.member.select.placeholder', self.lang, current=self.page + 1, total=self.max_page + 1)}",
            options=options
        )
        
        async def select_callback(interaction: discord.Interaction):
            self.current_select = select
            if self.callback:
                await self.callback(interaction)
        
        select.callback = select_callback
        self.add_item(select)
        self.current_select = select

        if hasattr(self, 'prev_button'):
            self.prev_button.disabled = self.page == 0
        if hasattr(self, 'next_button'):
            self.next_button.disabled = self.page == self.max_page

    @discord.ui.button(label="", emoji=f"{theme.prevIcon}", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self.update_select_menu()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", emoji=f"{theme.nextIcon}", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.max_page, self.page + 1)
        self.update_select_menu()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Filter by ID", emoji=theme.searchIcon, style=discord.ButtonStyle.secondary)
    async def fid_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.current_select and self.current_select.values:
                self.selected_alliance_id = self.current_select.values[0]
            
            modal = IDSearchModal(
                selected_alliance_id=self.selected_alliance_id,
                alliances=self.alliances,
                callback=self.callback,
                context=self.context,
                cog=self.cog,
                lang=self.lang
            )
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"ID button error: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('alliance.member.common.try_again', self.lang)}",
                ephemeral=True
            )

class IDSearchModal(discord.ui.Modal):
    def __init__(self, selected_alliance_id=None, alliances=None, callback=None, context="transfer", cog=None, lang: str | None = None):
        self.lang = lang or get_guild_language(None)
        super().__init__(title=t("alliance.member.id_search.title", self.lang))
        self.selected_alliance_id = selected_alliance_id
        self.alliances = alliances
        self.callback = callback
        self.context = context
        self.cog = cog

        self.add_item(discord.ui.TextInput(
            label=t("alliance.member.id_search.label", self.lang),
            placeholder=t("alliance.member.id_search.placeholder", self.lang),
            min_length=1,
            max_length=20,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            fid = self.children[0].value.strip()
            
            # Validate ID input
            if not fid:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('alliance.member.id_search.invalid_id', self.lang)}",
                    ephemeral=True
                )
                return
            
            # Check if we're in a history context
            if self.context in ["furnace_history", "nickname_history"]:
                # Get the Changes cog
                changes_cog = self.cog.bot.get_cog("Changes") if self.cog else interaction.client.get_cog("Changes")
                if changes_cog:
                    await interaction.response.defer()
                    if self.context == "furnace_history":
                        await changes_cog.show_furnace_history(interaction, int(fid))
                    else:
                        await changes_cog.show_nickname_history(interaction, int(fid))
                else:
                    await interaction.response.send_message(
                        f"{theme.deniedIcon} {t('alliance.member.id_search.history_unavailable', self.lang)}",
                        ephemeral=True
                    )
                return

            # Get member information
            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("""
                    SELECT fid, nickname, furnace_lv, alliance
                    FROM users
                    WHERE fid = ?
                """, (fid,))
                user_result = cursor.fetchone()

                if not user_result:
                    await interaction.response.send_message(
                        f"{theme.deniedIcon} {t('alliance.member.id_search.not_found', self.lang)}",
                        ephemeral=True
                    )
                    return

                fid, nickname, furnace_lv, current_alliance_id = user_result

                with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                    cursor = alliance_db.cursor()
                    cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (current_alliance_id,))
                    current_alliance_name = cursor.fetchone()[0]

                # Handle remove context
                if self.context == "remove":
                    embed = discord.Embed(
                        title=f"{theme.verifiedIcon} {t('alliance.member.id_search.remove_title', self.lang)}",
                        description=(
                            f"**{t('alliance.member.id_search.member_info', self.lang)}**\n"
                            f"{theme.userIcon} **{t('alliance.member.common.name_label', self.lang)}** {nickname}\n"
                            f"{theme.fidIcon} **{t('alliance.member.common.id_label', self.lang)}** {fid}\n"
                            f"{theme.levelIcon} **{t('alliance.member.common.level_label', self.lang)}** {self.cog.level_mapping.get(furnace_lv, str(furnace_lv))}\n"
                            f"{theme.allianceIcon} **{t('alliance.member.common.current_alliance_label', self.lang)}** {current_alliance_name}\n\n"
                            f"{theme.warnIcon} **{t('alliance.member.id_search.remove_confirm', self.lang)}**"
                        ),
                        color=theme.emColor2
                    )

                    view = discord.ui.View()
                    confirm_button = discord.ui.Button(
                        label=f"{theme.verifiedIcon} {t('alliance.member.common.confirm_delete', self.lang)}",
                        style=discord.ButtonStyle.danger
                    )
                    cancel_button = discord.ui.Button(
                        label=f"{theme.deniedIcon} {t('alliance.member.common.cancel', self.lang)}",
                        style=discord.ButtonStyle.secondary
                    )

                    async def confirm_callback(confirm_interaction: discord.Interaction):
                        try:
                            with sqlite3.connect('db/users.sqlite') as users_db:
                                cursor = users_db.cursor()
                                cursor.execute("DELETE FROM users WHERE fid = ?", (fid,))
                                users_db.commit()

                            success_embed = discord.Embed(
                                title=f"{theme.verifiedIcon} {t('alliance.member.id_search.deleted_title', self.lang)}",
                                description=(
                                    f"{theme.userIcon} **{t('alliance.member.common.member_label', self.lang)}** {nickname}\n"
                                    f"{theme.fidIcon} **{t('alliance.member.common.id_label', self.lang)}** {fid}\n"
                                    f"{theme.allianceIcon} **{t('alliance.member.common.alliance_label', self.lang)}** {current_alliance_name}"
                                ),
                                color=theme.emColor3
                            )

                            await confirm_interaction.response.edit_message(
                                embed=success_embed,
                                view=None
                            )

                            # Log the deletion
                            self.cog.log_message(f"Member deleted via ID search: {nickname} (ID: {fid}) from {current_alliance_name}")

                        except Exception as e:
                            print(f"Delete error: {e}")
                            error_embed = discord.Embed(
                                title=f"{theme.deniedIcon} {t('alliance.member.common.error_title', self.lang)}",
                                description=t("alliance.member.id_search.delete_error", self.lang),
                                color=theme.emColor2
                            )
                            await confirm_interaction.response.edit_message(
                                embed=error_embed,
                                view=None
                            )

                    async def cancel_callback(cancel_interaction: discord.Interaction):
                        cancel_embed = discord.Embed(
                            title=f"{theme.deniedIcon} {t('alliance.member.id_search.delete_cancel_title', self.lang)}",
                            description=t("alliance.member.id_search.delete_cancel_body", self.lang),
                            color=theme.emColor4
                        )
                        await cancel_interaction.response.edit_message(
                            embed=cancel_embed,
                            view=None
                        )

                    confirm_button.callback = confirm_callback
                    cancel_button.callback = cancel_callback
                    view.add_item(confirm_button)
                    view.add_item(cancel_button)

                    await interaction.response.send_message(
                        embed=embed,
                        view=view,
                        ephemeral=True
                    )
                    return

                # Handle giftcode context - validate permission and invoke callback with alliance
                if self.context == "giftcode":
                    # Check if user has permission to manage this alliance
                    has_permission = any(aid == current_alliance_id for aid, _, _ in self.alliances)
                    if not has_permission:
                        await interaction.response.send_message(
                            f"{theme.deniedIcon} {t('alliance.member.id_search.no_permission', self.lang)}",
                            ephemeral=True
                        )
                        return

                    # Invoke callback with the alliance ID
                    if self.callback:
                        await self.callback(interaction, alliance_id=current_alliance_id)
                    return

                # Transfer logic
                embed = discord.Embed(
                    title=f"{theme.verifiedIcon} {t('alliance.member.id_search.transfer_title', self.lang)}",
                    description=(
                        f"**{t('alliance.member.id_search.member_info', self.lang)}**\n"
                        f"{theme.userIcon} **{t('alliance.member.common.name_label', self.lang)}** {nickname}\n"
                        f"{theme.fidIcon} **{t('alliance.member.common.id_label', self.lang)}** {fid}\n"
                        f"{theme.levelIcon} **{t('alliance.member.common.level_label', self.lang)}** {self.cog.level_mapping.get(furnace_lv, str(furnace_lv))}\n"
                        f"{theme.allianceIcon} **{t('alliance.member.common.current_alliance_label', self.lang)}** {current_alliance_name}\n\n"
                        f"**{t('alliance.member.id_search.transfer_process', self.lang)}**\n"
                        f"{t('alliance.member.id_search.transfer_prompt', self.lang)}"
                    ),
                    color=theme.emColor1
                )

                select = discord.ui.Select(
                    placeholder=f"{theme.pinIcon} {t('alliance.member.transfer.target_placeholder', self.lang)}",
                    options=[
                        discord.SelectOption(
                            label=f"{name[:50]}",
                            value=str(alliance_id),
                            description=t(
                                "alliance.member.select.option_desc_id",
                                self.lang,
                                alliance_id=alliance_id
                            ),
                            emoji=theme.allianceIcon
                        ) for alliance_id, name, _ in self.alliances
                        if alliance_id != current_alliance_id
                    ]
                )

                view = discord.ui.View()
                view.add_item(select)

                async def select_callback(select_interaction: discord.Interaction):
                    target_alliance_id = int(select.values[0])

                    try:
                        with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                            cursor = alliance_db.cursor()
                            cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (target_alliance_id,))
                            target_alliance_name = cursor.fetchone()[0]


                        with sqlite3.connect('db/users.sqlite') as users_db:
                            cursor = users_db.cursor()
                            cursor.execute(
                                "UPDATE users SET alliance = ? WHERE fid = ?",
                                (target_alliance_id, fid)
                            )
                            users_db.commit()


                        success_embed = discord.Embed(
                            title=f"{theme.verifiedIcon} {t('alliance.member.transfer.success_title', self.lang)}",
                            description=(
                                f"{theme.userIcon} **{t('alliance.member.common.member_label', self.lang)}** {nickname}\n"
                                f"{theme.fidIcon} **{t('alliance.member.common.id_label', self.lang)}** {fid}\n"
                                f"{theme.allianceOldIcon} **{t('alliance.member.transfer.source_label', self.lang)}** {current_alliance_name}\n"
                                f"{theme.allianceIcon} **{t('alliance.member.transfer.target_label', self.lang)}** {target_alliance_name}"
                            ),
                            color=theme.emColor3
                        )

                        await select_interaction.response.edit_message(
                            embed=success_embed,
                            view=None
                        )

                    except Exception as e:
                        print(f"Transfer error: {e}")
                        error_embed = discord.Embed(
                            title=f"{theme.deniedIcon} {t('alliance.member.common.error_title', self.lang)}",
                            description=t("alliance.member.transfer.error_body", self.lang),
                            color=theme.emColor2
                        )
                        await select_interaction.response.edit_message(
                            embed=error_embed,
                            view=None
                        )

                select.callback = select_callback
                await interaction.response.send_message(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

        except Exception as e:
            print(f"Error details: {str(e.__class__.__name__)}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('alliance.member.common.try_again', self.lang)}",
                    ephemeral=True
                )

class AllianceSelectViewWithAll(discord.ui.View):
    def __init__(self, alliances_with_counts, cog, lang: str | None = None):
        super().__init__(timeout=300)
        self.alliances = alliances_with_counts
        self.cog = cog
        self.lang = lang or get_guild_language(None)
        self.current_select = None
        self.callback = None
        
        # Calculate total members across all alliances
        total_members = sum(count for _, _, count in alliances_with_counts)
        
        # Create select menu with ALL option
        options = [
            discord.SelectOption(
                label=t("alliance.member.export.all_alliances", self.lang),
                value="all",
                description=t(
                    "alliance.member.export.all_alliances_desc",
                    self.lang,
                    total_members=total_members,
                    total_alliances=len(alliances_with_counts)
                ),
                emoji=theme.stateIcon
            )
        ]
        
        # Add individual alliance options
        for alliance_id, name, count in alliances_with_counts[:24]:  # Discord limit is 25 options
            options.append(
                discord.SelectOption(
                    label=f"{name[:50]}",
                    value=str(alliance_id),
                    description=t(
                        "alliance.member.select.option_desc",
                        self.lang,
                        alliance_id=alliance_id,
                        count=count
                    ),
                    emoji=theme.allianceIcon
                )
            )
        
        select = discord.ui.Select(
            placeholder=f"{theme.allianceIcon} {t('alliance.member.export.select_placeholder', self.lang)}",
            options=options
        )
        
        async def select_callback(interaction: discord.Interaction):
            self.current_select = select
            if self.callback:
                await self.callback(interaction)
        
        select.callback = select_callback
        self.add_item(select)
        self.current_select = select

class ExportColumnSelectView(discord.ui.View):
    def __init__(self, alliance_id, alliance_name, cog, include_alliance=False, lang: str | None = None):
        super().__init__(timeout=300)
        self.alliance_id = alliance_id
        self.alliance_name = alliance_name
        self.cog = cog
        self.include_alliance = include_alliance
        self.lang = lang or get_guild_language(None)
        
        # Track selected columns (all selected by default)
        self.selected_columns = {
            'id': True,
            'name': True,
            'fc_level': True,
            'state': True
        }
        
        # Add alliance column if needed
        if include_alliance:
            self.selected_columns['alliance'] = True
            alliance_btn = discord.ui.Button(
                label=f"{theme.verifiedIcon} {t('alliance.member.export.column_alliance', self.lang)}", 
                style=discord.ButtonStyle.primary, 
                custom_id="toggle_alliance", 
                row=0
            )
            alliance_btn.callback = self.toggle_alliance_button
            self.add_item(alliance_btn)
        
        # Add other column buttons
        id_btn = discord.ui.Button(
            label=f"{theme.verifiedIcon} {t('alliance.member.export.column_id', self.lang)}",
            style=discord.ButtonStyle.primary,
            custom_id="toggle_id",
            row=0
        )
        id_btn.callback = self.toggle_id_button
        self.add_item(id_btn)
        
        name_btn = discord.ui.Button(
            label=f"{theme.verifiedIcon} {t('alliance.member.export.column_name', self.lang)}",
            style=discord.ButtonStyle.primary,
            custom_id="toggle_name",
            row=0
        )
        name_btn.callback = self.toggle_name_button
        self.add_item(name_btn)
        
        fc_btn = discord.ui.Button(
            label=f"{theme.verifiedIcon} {t('alliance.member.export.column_fc', self.lang)}",
            style=discord.ButtonStyle.primary,
            custom_id="toggle_fc",
            row=0 if not include_alliance else 1
        )
        fc_btn.callback = self.toggle_fc_button
        self.add_item(fc_btn)
        
        state_btn = discord.ui.Button(
            label=f"{theme.verifiedIcon} {t('alliance.member.export.column_state', self.lang)}",
            style=discord.ButtonStyle.primary,
            custom_id="toggle_state",
            row=0 if not include_alliance else 1
        )
        state_btn.callback = self.toggle_state_button
        self.add_item(state_btn)
        
        next_btn = discord.ui.Button(
            label=t("alliance.member.common.next", self.lang),
            emoji=theme.forwardIcon,
            style=discord.ButtonStyle.success,
            custom_id="next_step",
            row=1 if not include_alliance else 2
        )
        next_btn.callback = self.next_button
        self.add_item(next_btn)
        
        cancel_btn = discord.ui.Button(
            label=t("alliance.member.common.cancel", self.lang),
            style=discord.ButtonStyle.danger,
            custom_id="cancel",
            row=1 if not include_alliance else 2
        )
        cancel_btn.callback = self.cancel_button
        self.add_item(cancel_btn)
        
        self.update_buttons()
    
    def update_buttons(self):
        # Update button styles based on selection state
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == 'toggle_alliance' and self.include_alliance:
                    item.style = discord.ButtonStyle.primary if self.selected_columns.get('alliance', False) else discord.ButtonStyle.secondary
                    item.label = (
                        f"{theme.verifiedIcon} {t('alliance.member.export.column_alliance', self.lang)}"
                        if self.selected_columns.get('alliance', False)
                        else f"{theme.deniedIcon} {t('alliance.member.export.column_alliance', self.lang)}"
                    )
                elif item.custom_id == 'toggle_id':
                    item.style = discord.ButtonStyle.primary if self.selected_columns['id'] else discord.ButtonStyle.secondary
                    item.label = (
                        f"{theme.verifiedIcon} {t('alliance.member.export.column_id', self.lang)}"
                        if self.selected_columns['id']
                        else f"{theme.deniedIcon} {t('alliance.member.export.column_id', self.lang)}"
                    )
                elif item.custom_id == 'toggle_name':
                    item.style = discord.ButtonStyle.primary if self.selected_columns['name'] else discord.ButtonStyle.secondary
                    item.label = (
                        f"{theme.verifiedIcon} {t('alliance.member.export.column_name', self.lang)}"
                        if self.selected_columns['name']
                        else f"{theme.deniedIcon} {t('alliance.member.export.column_name', self.lang)}"
                    )
                elif item.custom_id == 'toggle_fc':
                    item.style = discord.ButtonStyle.primary if self.selected_columns['fc_level'] else discord.ButtonStyle.secondary
                    item.label = (
                        f"{theme.verifiedIcon} {t('alliance.member.export.column_fc', self.lang)}"
                        if self.selected_columns['fc_level']
                        else f"{theme.deniedIcon} {t('alliance.member.export.column_fc', self.lang)}"
                    )
                elif item.custom_id == 'toggle_state':
                    item.style = discord.ButtonStyle.primary if self.selected_columns['state'] else discord.ButtonStyle.secondary
                    item.label = (
                        f"{theme.verifiedIcon} {t('alliance.member.export.column_state', self.lang)}"
                        if self.selected_columns['state']
                        else f"{theme.deniedIcon} {t('alliance.member.export.column_state', self.lang)}"
                    )

    async def toggle_alliance_button(self, interaction: discord.Interaction):
        if self.include_alliance:
            self.selected_columns['alliance'] = not self.selected_columns.get('alliance', True)
            self.update_buttons()
            
            if not any(self.selected_columns.values()):
                self.selected_columns['alliance'] = True
                self.update_buttons()
                await interaction.response.edit_message(
                    content=f"{theme.warnIcon} {t('alliance.member.export.columns_required', self.lang)}",
                    view=self
                )
            else:
                await interaction.response.edit_message(view=self)
    
    async def toggle_id_button(self, interaction: discord.Interaction):
        self.selected_columns['id'] = not self.selected_columns['id']
        self.update_buttons()
        
        if not any(self.selected_columns.values()):
            self.selected_columns['id'] = True
            self.update_buttons()
            await interaction.response.edit_message(
                content=f"{theme.warnIcon} {t('alliance.member.export.columns_required', self.lang)}",
                view=self
            )
        else:
            await interaction.response.edit_message(view=self)
    
    async def toggle_name_button(self, interaction: discord.Interaction):
        self.selected_columns['name'] = not self.selected_columns['name']
        self.update_buttons()
        
        if not any(self.selected_columns.values()):
            self.selected_columns['name'] = True
            self.update_buttons()
            await interaction.response.edit_message(
                content=f"{theme.warnIcon} {t('alliance.member.export.columns_required', self.lang)}",
                view=self
            )
        else:
            await interaction.response.edit_message(view=self)
    
    async def toggle_fc_button(self, interaction: discord.Interaction):
        self.selected_columns['fc_level'] = not self.selected_columns['fc_level']
        self.update_buttons()
        
        if not any(self.selected_columns.values()):
            self.selected_columns['fc_level'] = True
            self.update_buttons()
            await interaction.response.edit_message(
                content=f"{theme.warnIcon} {t('alliance.member.export.columns_required', self.lang)}",
                view=self
            )
        else:
            await interaction.response.edit_message(view=self)
    
    async def toggle_state_button(self, interaction: discord.Interaction):
        self.selected_columns['state'] = not self.selected_columns['state']
        self.update_buttons()
        
        if not any(self.selected_columns.values()):
            self.selected_columns['state'] = True
            self.update_buttons()
            await interaction.response.edit_message(
                content=f"{theme.warnIcon} {t('alliance.member.export.columns_required', self.lang)}",
                view=self
            )
        else:
            await interaction.response.edit_message(view=self)
    
    async def next_button(self, interaction: discord.Interaction):
        # Build selected columns list
        columns = []
        if self.include_alliance and self.selected_columns.get('alliance', False):
            columns.append(('alliance_name', t('alliance.member.export.column_alliance', self.lang)))
        if self.selected_columns['id']:
            columns.append(('fid', t('alliance.member.export.column_id', self.lang)))
        if self.selected_columns['name']:
            columns.append(('nickname', t('alliance.member.export.column_name', self.lang)))
        if self.selected_columns['fc_level']:
            columns.append(('furnace_lv', t('alliance.member.export.column_fc', self.lang)))
        if self.selected_columns['state']:
            columns.append(('kid', t('alliance.member.export.column_state', self.lang)))
        
        # Show format selection
        format_embed = discord.Embed(
            title=f"{theme.exportIcon} {t('alliance.member.export.format_title', self.lang)}",
            description=(
                f"**{t('alliance.member.common.alliance_label', self.lang)}** {self.alliance_name}\n"
                f"**{t('alliance.member.export.columns_selected', self.lang)}** {', '.join([col[1] for col in columns])}\n\n"
                f"{t('alliance.member.export.format_prompt', self.lang)}"
            ),
            color=theme.emColor1
        )
        
        format_view = ExportFormatSelectView(self.alliance_id, self.alliance_name, columns, self.cog, self.lang)
        await interaction.response.edit_message(embed=format_embed, view=format_view, content=None)
    
    async def cancel_button(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"{theme.deniedIcon} {t('alliance.member.export.cancelled', self.lang)}",
            embed=None,
            view=None
        )

class ExportFormatSelectView(discord.ui.View):
    def __init__(self, alliance_id, alliance_name, selected_columns, cog, lang: str | None = None):
        super().__init__(timeout=300)
        self.alliance_id = alliance_id
        self.alliance_name = alliance_name
        self.selected_columns = selected_columns
        self.cog = cog
        self.lang = lang or get_guild_language(None)
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.custom_id == "csv":
                item.label = t("alliance.member.export.format_csv", self.lang)
            elif item.custom_id == "tsv":
                item.label = t("alliance.member.export.format_tsv", self.lang)
            elif item.custom_id == "back":
                item.label = t("alliance.member.common.back", self.lang)
            elif item.custom_id == "cancel":
                item.label = t("alliance.member.common.cancel", self.lang)
    
    @discord.ui.button(label="CSV (Comma-separated)", emoji=theme.averageIcon, style=discord.ButtonStyle.primary, custom_id="csv")
    async def csv_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_member_export(
            interaction,
            self.alliance_id,
            self.alliance_name,
            self.selected_columns,
            'csv'
        )
    
    @discord.ui.button(label="TSV (Tab-separated)", emoji=theme.listIcon, style=discord.ButtonStyle.primary, custom_id="tsv")
    async def tsv_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_member_export(
            interaction,
            self.alliance_id,
            self.alliance_name,
            self.selected_columns,
            'tsv'
        )
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        column_embed = discord.Embed(
            title=f"{theme.chartIcon} {t('alliance.member.export.columns_title', self.lang)}",
            description=(
                f"**{t('alliance.member.common.alliance_label', self.lang)}** {self.alliance_name}\n\n"
                f"{t('alliance.member.export.columns_instructions', self.lang)}\n"
                f"{t('alliance.member.export.columns_default', self.lang)}\n\n"
                f"**{t('alliance.member.export.columns_available', self.lang)}**\n"
                f"• **{t('alliance.member.export.column_id', self.lang)}** - {t('alliance.member.export.column_id_desc', self.lang)}\n"
                f"• **{t('alliance.member.export.column_name', self.lang)}** - {t('alliance.member.export.column_name_desc', self.lang)}\n"
                f"• **{t('alliance.member.export.column_fc', self.lang)}** - {t('alliance.member.export.column_fc_desc', self.lang)}\n"
                f"• **{t('alliance.member.export.column_state', self.lang)}** - {t('alliance.member.export.column_state_desc', self.lang)}"
            ),
            color=theme.emColor1
        )
        
        # Check if it's an all-alliance export by checking the alliance_id
        include_alliance = self.alliance_id == "all"
        if include_alliance:
            column_embed.description = (
                f"**{t('alliance.member.export.type_label', self.lang)}** {t('alliance.member.export.all_alliances', self.lang)}\n\n"
                f"{t('alliance.member.export.columns_instructions', self.lang)}\n"
                f"{t('alliance.member.export.columns_default', self.lang)}\n\n"
                f"**{t('alliance.member.export.columns_available', self.lang)}**\n"
                f"• **{t('alliance.member.export.column_alliance', self.lang)}** - {t('alliance.member.export.column_alliance_desc', self.lang)}\n"
                f"• **{t('alliance.member.export.column_id', self.lang)}** - {t('alliance.member.export.column_id_desc', self.lang)}\n"
                f"• **{t('alliance.member.export.column_name', self.lang)}** - {t('alliance.member.export.column_name_desc', self.lang)}\n"
                f"• **{t('alliance.member.export.column_fc', self.lang)}** - {t('alliance.member.export.column_fc_desc', self.lang)}\n"
                f"• **{t('alliance.member.export.column_state', self.lang)}** - {t('alliance.member.export.column_state_desc', self.lang)}"
            )
        
        column_view = ExportColumnSelectView(self.alliance_id, self.alliance_name, self.cog, include_alliance, self.lang)
        await interaction.response.edit_message(embed=column_embed, view=column_view)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content=f"{theme.deniedIcon} {t('alliance.member.export.cancelled', self.lang)}",
            embed=None,
            view=None
        )

class MemberSelectView(discord.ui.View):
    def __init__(self, members, source_alliance_name, cog, page=0, is_remove_operation=False, alliance_id=None, alliances=None, lang: str | None = None):
        super().__init__(timeout=7200)
        self.members = members
        self.source_alliance_name = source_alliance_name
        self.cog = cog
        self.page = page
        self.max_page = (len(members) - 1) // 25
        self.current_select = None
        self.callback = None
        self.member_dict = {str(fid): nickname for fid, nickname, _ in members}
        self.selected_alliance_id = alliance_id
        self.alliances = alliances
        self.is_remove_operation = is_remove_operation
        self.context = "remove" if is_remove_operation else "transfer"
        self.pending_selections = set()  # Track selected FIDs across pages
        self.lang = lang or get_guild_language(None)

        # Remove "Delete All" button if not in remove operation mode
        if not is_remove_operation:
            self.remove_item(self._delete_all_button)

        self.update_select_menu()
        self.update_action_buttons()
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.label == "Select by ID":
                item.label = t("alliance.member.common.select_by_id", self.lang)
            elif item.label == "Process Selected":
                item.label = t("alliance.member.common.process_selected", self.lang)
            elif item.label == "Clear Selection":
                item.label = t("alliance.member.common.clear_selection", self.lang)
            elif item.label == "Delete All":
                item.label = t("alliance.member.remove.delete_all", self.lang)

    def update_select_menu(self):
        for item in self.children[:]:
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)

        start_idx = self.page * 25
        end_idx = min(start_idx + 25, len(self.members))
        current_members = self.members[start_idx:end_idx]

        options = []

        # Build member options
        for fid, nickname, furnace_lv in current_members:
            # Mark as default if already selected
            is_selected = int(fid) in self.pending_selections
            options.append(discord.SelectOption(
                label=f"{nickname[:50]}",
                value=str(fid),
                description=t(
                    "alliance.member.select.member_option_desc",
                    self.lang,
                    fid=fid,
                    level=self.cog.level_mapping.get(furnace_lv, str(furnace_lv))
                ),
                emoji=theme.verifiedIcon if is_selected else theme.userIcon,
                default=is_selected
            ))

        # Determine placeholder based on context (remove vs transfer)
        if self.is_remove_operation:
            placeholder_text = (
                f"{theme.membersIcon} "
                f"{t('alliance.member.remove.select_placeholder', self.lang, current=self.page + 1, total=self.max_page + 1)}"
            )
        else:
            placeholder_text = (
                f"{theme.membersIcon} "
                f"{t('alliance.member.transfer.select_placeholder', self.lang, current=self.page + 1, total=self.max_page + 1)}"
            )

        # Multi-select dropdown
        max_vals = min(len(options), 25)
        select = discord.ui.Select(
            placeholder=placeholder_text,
            options=options,
            max_values=max_vals,
            min_values=0
        )

        async def select_callback(interaction: discord.Interaction):
            try:
                self.current_select = select

                # Get FIDs on current page
                current_page_fids = {int(fid) for fid, _, _ in current_members}

                # Remove old selections from this page
                self.pending_selections -= current_page_fids

                # Add new selections
                for val in select.values:
                    self.pending_selections.add(int(val))

                # Update UI
                self.update_select_menu()
                self.update_action_buttons()
                await self.update_main_embed(interaction)

            except Exception as e:
                print(f"Select callback error: {e}")
                error_embed = discord.Embed(
                    title=f"{theme.deniedIcon} {t('alliance.member.common.error_title', self.lang)}",
                    description=t("alliance.member.common.select_error", self.lang),
                    color=theme.emColor2
                )
                try:
                    await interaction.response.edit_message(embed=error_embed, view=self)
                except:
                    await interaction.followup.send(embed=error_embed, ephemeral=True)

        select.callback = select_callback
        self.add_item(select)
        self.current_select = select

        # Update navigation button states
        if hasattr(self, '_prev_button'):
            self._prev_button.disabled = self.page == 0
        if hasattr(self, '_next_button'):
            self._next_button.disabled = self.page == self.max_page

    async def update_main_embed(self, interaction: discord.Interaction):
        """Update the main embed with current selection count"""
        max_fl = max(member[2] for member in self.members)
        avg_fl = sum(member[2] for member in self.members) / len(self.members)

        selection_text = ""
        if self.pending_selections:
            selection_text = (
                f"\n\n**{theme.pinIcon} "
                f"{t('alliance.member.common.selected_count', self.lang, count=len(self.pending_selections))}**"
            )

        embed = discord.Embed(
            title=f"{theme.membersIcon} {t('alliance.member.common.selection_title', self.lang, alliance=self.source_alliance_name)}",
            description=(
                "```ml\n"
                f"{t('alliance.member.stats.title', self.lang)}\n"
                "══════════════════════════\n"
                f"{theme.chartIcon} {t('alliance.member.stats.total_members', self.lang)} {len(self.members)}\n"
                f"{theme.levelIcon} {t('alliance.member.stats.highest_level', self.lang)} {self.cog.level_mapping.get(max_fl, str(max_fl))}\n"
                f"{theme.chartIcon} {t('alliance.member.stats.avg_level', self.lang)} {self.cog.level_mapping.get(int(avg_fl), str(int(avg_fl)))}\n"
                "══════════════════════════\n"
                "```"
                f"{selection_text}\n"
                f"{t('alliance.member.common.select_prompt', self.lang)}"
            ),
            color=theme.emColor2 if self.is_remove_operation else discord.Color.blue()
        )

        # For dropdown interactions, we need to defer first, then edit
        if not interaction.response.is_done():
            await interaction.response.defer()

        await interaction.edit_original_response(embed=embed, view=self)

    def update_action_buttons(self):
        """Update the state of action buttons based on selections"""
        has_selections = len(self.pending_selections) > 0

        if hasattr(self, '_process_button'):
            self._process_button.disabled = not has_selections
        if hasattr(self, '_clear_button'):
            self._clear_button.disabled = not has_selections

    @discord.ui.button(label="", emoji=f"{theme.prevIcon}", style=discord.ButtonStyle.secondary, row=1)
    async def _prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self.update_select_menu()
        await self.update_main_embed(interaction)

    @discord.ui.button(label="", emoji=f"{theme.nextIcon}", style=discord.ButtonStyle.secondary, row=1)
    async def _next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.max_page, self.page + 1)
        self.update_select_menu()
        await self.update_main_embed(interaction)

    @discord.ui.button(label="Select by ID", emoji=theme.searchIcon, style=discord.ButtonStyle.secondary, row=1)
    async def fid_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            
            if self.current_select and self.current_select.values:
                self.selected_alliance_id = self.current_select.values[0]
            
            modal = IDSearchModal(
                selected_alliance_id=self.selected_alliance_id,
                alliances=self.alliances,
                callback=self.callback,
                context=self.context,
                cog=self.cog,
                lang=self.lang
            )
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"ID button error: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('alliance.member.common.try_again', self.lang)}",
                ephemeral=True
            )

    @discord.ui.button(label="Process Selected", emoji=theme.verifiedIcon, style=discord.ButtonStyle.success, row=2, disabled=True)
    async def _process_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Process selected members (delete or transfer)"""
        if not self.pending_selections:
            await interaction.response.send_message(
                t("alliance.member.common.no_members_selected", self.lang),
                ephemeral=True
            )
            return

        if self.callback:
            await self.callback(interaction, list(self.pending_selections))

    @discord.ui.button(label="Clear Selection", emoji=theme.trashIcon, style=discord.ButtonStyle.secondary, row=2, disabled=True)
    async def _clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Clear all selected members"""
        self.pending_selections.clear()
        self.update_select_menu()
        self.update_action_buttons()
        await self.update_main_embed(interaction)

    @discord.ui.button(label="Delete All", emoji=theme.warnIcon, style=discord.ButtonStyle.danger, row=2)
    async def _delete_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete all members in the alliance (only shown for remove operations)"""
        if not self.is_remove_operation:
            return

        await interaction.response.send_message(
            f"{theme.warnIcon} {t('alliance.member.remove.delete_all_confirm', self.lang, count=len(self.members), alliance=self.source_alliance_name)}",
            view=DeleteAllConfirmView(self, self.lang),
            ephemeral=True
        )

class DeleteAllConfirmView(discord.ui.View):
    def __init__(self, parent_view, lang: str):
        super().__init__(timeout=60)
        self.parent_view = parent_view
        self.lang = lang
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.label == "Confirm":
                item.label = t("alliance.member.common.confirm", self.lang)
            elif item.label == "Cancel":
                item.label = t("alliance.member.common.cancel", self.lang)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Call the parent's delete all callback
        if self.parent_view.callback:
            all_fids = [fid for fid, _, _ in self.parent_view.members]
            await self.parent_view.callback(interaction, all_fids, delete_all=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cancel_embed = discord.Embed(
            title=f"{theme.deniedIcon} {t('alliance.member.common.cancelled_title', self.lang)}",
            description=t("alliance.member.remove.delete_all_cancelled", self.lang),
            color=theme.emColor4
        )
        await interaction.response.edit_message(embed=cancel_embed, view=None)

async def setup(bot):
    await bot.add_cog(AllianceMemberOperations(bot))