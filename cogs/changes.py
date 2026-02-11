import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
from .alliance_member_operations import AllianceSelectView
from .permission_handler import PermissionManager
from .pimp_my_bot import theme
from i18n import get_guild_language, t

class Changes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn_settings = sqlite3.connect('db/settings.sqlite')
        self.c_settings = self.conn_settings.cursor()
        self.conn = sqlite3.connect('db/changes.sqlite')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _get_lang(self, interaction: discord.Interaction | None) -> str:
        guild_id = interaction.guild.id if interaction and interaction.guild else None
        return get_guild_language(guild_id)
        
        self.level_mapping = {
            31: "30-1", 32: "30-2", 33: "30-3", 34: "30-4",
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

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS furnace_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fid INTEGER,
                old_value INTEGER,
                new_value INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def cog_unload(self):
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()

    async def show_alliance_history_menu(self, interaction: discord.Interaction):
        try:
            lang = self._get_lang(interaction)
            embed = discord.Embed(
                title=f"{theme.listIcon} {t('changes.menu.title', lang)}",
                description=(
                    f"**{t('changes.menu.available', lang)}**\n"
                    f"{theme.upperDivider}\n"
                    f"{theme.stoveIcon} **{t('changes.menu.furnace', lang)}**\n"
                    f"└ {t('changes.menu.furnace_desc', lang)}\n\n"
                    f"{theme.editListIcon} **{t('changes.menu.nickname', lang)}**\n"
                    f"└ {t('changes.menu.nickname_desc', lang)}\n"
                    f"{theme.lowerDivider}"
                ),
                color=theme.emColor1
            )

            view = HistoryView(self, lang)
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            if not any(error_code in str(e) for error_code in ["10062", "40060"]):
                print(f"Show alliance history menu error: {e}")

    async def show_furnace_history(self, interaction: discord.Interaction, fid: int):
        try:
            lang = self._get_lang(interaction)
            self.cursor.execute("""
                SELECT old_furnace_lv, new_furnace_lv, change_date 
                FROM furnace_changes 
                WHERE fid = ? 
                ORDER BY change_date DESC
            """, (fid,))
            
            changes = self.cursor.fetchall()
            
            if not changes:
                await interaction.followup.send(
                    t("changes.furnace.no_changes", lang),
                    ephemeral=True
                )
                return

            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("SELECT nickname, furnace_lv FROM users WHERE fid = ?", (fid,))
                user_info = cursor.fetchone()
                nickname = user_info[0] if user_info else t("changes.common.unknown", lang)
                current_level = user_info[1] if user_info else 0

            embed = discord.Embed(
                title=f"{theme.levelIcon} {t('changes.furnace.title', lang)}",
                description=(
                    f"**{t('changes.common.player', lang)}** `{nickname}`\n"
                    f"**{t('changes.common.id', lang)}** `{fid}`\n"
                    f"**{t('changes.common.current_level', lang)}** `{self.level_mapping.get(current_level, str(current_level))}`\n"
                    f"{theme.upperDivider}\n"
                ),
                color=theme.emColor1
            )

            for old_level, new_level, change_date in changes:
                old_level_str = self.level_mapping.get(int(old_level), str(old_level))
                new_level_str = self.level_mapping.get(int(new_level), str(new_level))
                embed.add_field(
                    name=t("changes.furnace.change_at", lang, date=change_date),
                    value=f"{theme.stoveOldIcon} `{old_level_str}` ➜ {theme.stoveIcon} `{new_level_str}`",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in show_furnace_history: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('changes.furnace.error', lang)}",
                ephemeral=True
            )

    async def show_nickname_history(self, interaction: discord.Interaction, fid: int):
        try:
            lang = self._get_lang(interaction)
            self.cursor.execute("""
                SELECT old_nickname, new_nickname, change_date 
                FROM nickname_changes 
                WHERE fid = ? 
                ORDER BY change_date DESC
            """, (fid,))
            
            changes = self.cursor.fetchall()
            
            if not changes:
                await interaction.followup.send(
                    t("changes.nickname.no_changes", lang),
                    ephemeral=True
                )
                return

            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("SELECT nickname, furnace_lv FROM users WHERE fid = ?", (fid,))
                user_info = cursor.fetchone()
                nickname = user_info[0] if user_info else t("changes.common.unknown", lang)
                current_level = user_info[1] if user_info else 0

            embed = discord.Embed(
                title=f"{theme.editListIcon} {t('changes.nickname.title', lang)}",
                description=(
                    f"**{t('changes.common.player', lang)}** `{nickname}`\n"
                    f"**{t('changes.common.id', lang)}** `{fid}`\n"
                    f"**{t('changes.common.current_level', lang)}** `{self.level_mapping.get(current_level, str(current_level))}`\n"
                    f"{theme.upperDivider}\n"
                ),
                color=theme.emColor1
            )

            for old_name, new_name, change_date in changes:
                embed.add_field(
                    name=t("changes.nickname.change_at", lang, date=change_date),
                    value=f"{theme.avatarOldIcon} `{old_name}` ➜ {theme.avatarIcon} `{new_name}`",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in show_nickname_history: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('changes.nickname.error', lang)}",
                ephemeral=True
            )

    async def show_member_list_nickname(self, interaction: discord.Interaction, alliance_id: int):
        try:
            lang = self._get_lang(interaction)
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
                    f"{theme.deniedIcon} {t('changes.common.no_members', lang)}",
                    ephemeral=True
                )
                return

            embed = discord.Embed(
                title=t("changes.member_list.title", lang, icon=theme.editListIcon, alliance=alliance_name),
                description=(
                    f"{t('changes.nickname.select_prompt', lang)}\n"
                    f"{theme.upperDivider}\n"
                    f"{t('changes.common.total_members', lang)} {len(members)}\n"
                    f"{t('changes.common.current_page', lang)} 1/{(len(members) + 24) // 25}\n"
                    f"{theme.lowerDivider}"
                ),
                color=theme.emColor1
            )

            view = MemberListViewNickname(self, members, alliance_name, lang)
            
            await interaction.response.edit_message(
                embed=embed,
                view=view
            )

        except Exception as e:
            print(f"Error in show_member_list_nickname: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.common.member_list_error', lang)}",
                ephemeral=True
            )

    async def show_recent_changes(self, interaction: discord.Interaction, alliance_name: str, hours: int):
        try:
            lang = self._get_lang(interaction)
            with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                cursor = alliance_db.cursor()
                cursor.execute("SELECT alliance_id FROM alliance_list WHERE name = ?", (alliance_name,))
                alliance_id = cursor.fetchone()[0]

            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("""
                    SELECT fid, nickname 
                    FROM users 
                    WHERE alliance = ?
                """, (alliance_id,))
                members = {fid: name for fid, name in cursor.fetchall()}

            self.cursor.execute("""
                SELECT fid, old_furnace_lv, new_furnace_lv, change_date 
                FROM furnace_changes 
                WHERE fid IN ({})
                AND change_date >= datetime('now', '-{} hours')
                ORDER BY change_date DESC
            """.format(','.join('?' * len(members)), hours), tuple(members.keys()))
            
            changes = self.cursor.fetchall()

            if not changes:
                await interaction.followup.send(
                    t("changes.recent.none_furnace", lang, hours=hours, alliance=alliance_name),
                    ephemeral=True
                )
                return

            chunks = [changes[i:i + 25] for i in range(0, len(changes), 25)]
            
            view = RecentChangesView(chunks, members, self.level_mapping, alliance_name, hours, lang)
            await interaction.followup.send(embed=view.get_embed(), view=view)

        except Exception as e:
            print(f"Error in show_recent_changes: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('changes.recent.error', lang)}",
                ephemeral=True
            )

    async def show_recent_nickname_changes(self, interaction: discord.Interaction, alliance_name: str, hours: int):
        try:
            lang = self._get_lang(interaction)
            with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                cursor = alliance_db.cursor()
                cursor.execute("SELECT alliance_id FROM alliance_list WHERE name = ?", (alliance_name,))
                alliance_id = cursor.fetchone()[0]

            with sqlite3.connect('db/users.sqlite') as users_db:
                cursor = users_db.cursor()
                cursor.execute("""
                    SELECT fid, nickname 
                    FROM users 
                    WHERE alliance = ?
                """, (alliance_id,))
                members = {fid: name for fid, name in cursor.fetchall()}

            self.cursor.execute("""
                SELECT fid, old_nickname, new_nickname, change_date 
                FROM nickname_changes 
                WHERE fid IN ({})
                AND change_date >= datetime('now', '-{} hours')
                ORDER BY change_date DESC
            """.format(','.join('?' * len(members)), hours), tuple(members.keys()))
            
            changes = self.cursor.fetchall()

            if not changes:
                await interaction.followup.send(
                    t("changes.recent.none_nickname", lang, hours=hours, alliance=alliance_name),
                    ephemeral=True
                )
                return

            chunks = [changes[i:i + 25] for i in range(0, len(changes), 25)]
            
            view = RecentNicknameChangesView(chunks, members, alliance_name, hours, lang)
            await interaction.followup.send(embed=view.get_embed(), view=view)

        except Exception as e:
            print(f"Error in show_recent_nickname_changes: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('changes.recent.error', lang)}",
                ephemeral=True
            )

class HistoryView(discord.ui.View):
    def __init__(self, cog, lang: str):
        super().__init__()
        self.cog = cog
        self.lang = lang
        self.current_page = 0
        self.members_per_page = 25
        self.level_mapping = cog.level_mapping
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.custom_id == "furnace_changes":
                item.label = t("changes.menu.furnace", self.lang)
            elif item.custom_id == "nickname_changes":
                item.label = t("changes.menu.nickname", self.lang)
            elif item.custom_id == "main_menu":
                item.label = t("changes.common.main_menu", self.lang)

    @discord.ui.button(
        label="Furnace Changes",
        emoji=f"{theme.stoveIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="furnace_changes",
        row=0
    )
    async def furnace_changes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            alliances, is_global = PermissionManager.get_admin_alliances(
                interaction.user.id,
                interaction.guild_id
            )

            if not alliances:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.permissions.none', self.lang)}",
                    ephemeral=True
                )
                return

            alliances_with_counts = []
            for alliance_id, name in alliances:
                with sqlite3.connect('db/users.sqlite') as users_db:
                    cursor = users_db.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                    member_count = cursor.fetchone()[0]
                    alliances_with_counts.append((alliance_id, name, member_count))

            select_embed = discord.Embed(
                title=f"{theme.stoveIcon} {t('changes.furnace.select_title', self.lang)}",
                description=(
                    f"{t('changes.furnace.select_prompt', self.lang)}\n\n"
                    f"**{t('changes.permissions.title', self.lang)}**\n"
                    f"{theme.upperDivider}\n"
                    f"{theme.userIcon} **{t('changes.permissions.access_level', self.lang)}** `{t('changes.permissions.global_admin', self.lang) if is_global else t('changes.permissions.alliance_admin', self.lang)}`\n"
                    f"{theme.searchIcon} **{t('changes.permissions.access_type', self.lang)}** `{t('changes.permissions.all_alliances', self.lang) if is_global else t('changes.permissions.assigned_alliances', self.lang)}`\n"
                    f"{theme.chartIcon} **{t('changes.permissions.available_alliances', self.lang)}** `{len(alliances)}`\n"
                    f"{theme.lowerDivider}"
                ),
                color=theme.emColor1
            )

            view = AllianceSelectView(alliances_with_counts, self.cog, page=0, context="furnace_history", lang=self.lang)

            async def alliance_callback(select_interaction: discord.Interaction):
                try:
                    alliance_id = int(view.current_select.values[0])
                    await self.member_callback(select_interaction, alliance_id)
                except Exception as e:
                    print(f"Error in alliance selection: {e}")
                    if not select_interaction.response.is_done():
                        await select_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('changes.common.selection_error', self.lang)}",
                            ephemeral=True
                        )
                    else:
                        await select_interaction.followup.send(
                            f"{theme.deniedIcon} {t('changes.common.selection_error', self.lang)}",
                            ephemeral=True
                        )

            view.callback = alliance_callback
            
            await interaction.response.send_message(
                embed=select_embed,
                view=view,
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in furnace_changes_button: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.common.request_error', self.lang)}",
                ephemeral=True
            )

    async def member_callback(self, interaction: discord.Interaction, alliance_id: int):
        try:
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
                    f"{theme.deniedIcon} {t('changes.common.no_members', self.lang)}",
                    ephemeral=True
                )
                return

            with sqlite3.connect('db/alliance.sqlite') as alliance_db:
                cursor = alliance_db.cursor()
                cursor.execute("SELECT name FROM alliance_list WHERE alliance_id = ?", (alliance_id,))
                alliance_name = cursor.fetchone()[0]

            view = MemberListView(self.cog, members, alliance_name, self.lang)
            
            embed = discord.Embed(
                title=t("changes.member_list.title", self.lang, icon=theme.levelIcon, alliance=alliance_name),
                description=(
                    f"{t('changes.furnace.select_member_prompt', self.lang)}\n"
                    f"{theme.upperDivider}\n"
                    f"{t('changes.common.total_members', self.lang)} {len(members)}\n"
                    f"{t('changes.common.current_page', self.lang)} 1/{view.total_pages}\n"
                    f"{theme.lowerDivider}"
                ),
                color=theme.emColor1
            )

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"Error in member_callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.common.member_list_error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.common.member_list_error', self.lang)}",
                    ephemeral=True
                )

    @discord.ui.button(
        label="Nickname Changes",
        emoji=f"{theme.editListIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="nickname_changes",
        row=0
    )
    async def nickname_changes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            alliances, is_global = PermissionManager.get_admin_alliances(
                interaction.user.id,
                interaction.guild_id
            )

            if not alliances:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.permissions.none', self.lang)}",
                    ephemeral=True
                )
                return

            alliances_with_counts = []
            for alliance_id, name in alliances:
                with sqlite3.connect('db/users.sqlite') as users_db:
                    cursor = users_db.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users WHERE alliance = ?", (alliance_id,))
                    member_count = cursor.fetchone()[0]
                    alliances_with_counts.append((alliance_id, name, member_count))

            select_embed = discord.Embed(
                title=f"{theme.editListIcon} {t('changes.nickname.select_title', self.lang)}",
                description=(
                    f"{t('changes.nickname.select_prompt', self.lang)}\n\n"
                    f"**{t('changes.permissions.title', self.lang)}**\n"
                    f"{theme.upperDivider}\n"
                    f"{theme.userIcon} **{t('changes.permissions.access_level', self.lang)}** `{t('changes.permissions.global_admin', self.lang) if is_global else t('changes.permissions.alliance_admin', self.lang)}`\n"
                    f"{theme.searchIcon} **{t('changes.permissions.access_type', self.lang)}** `{t('changes.permissions.all_alliances', self.lang) if is_global else t('changes.permissions.assigned_alliances', self.lang)}`\n"
                    f"{theme.chartIcon} **{t('changes.permissions.available_alliances', self.lang)}** `{len(alliances)}`\n"
                    f"{theme.lowerDivider}"
                ),
                color=theme.emColor1
            )

            view = AllianceSelectView(alliances_with_counts, self.cog, page=0, context="nickname_history", lang=self.lang)

            async def alliance_callback(select_interaction: discord.Interaction):
                try:
                    alliance_id = int(view.current_select.values[0])
                    await self.cog.show_member_list_nickname(select_interaction, alliance_id)
                except Exception as e:
                    print(f"Error in alliance selection: {e}")
                    if not select_interaction.response.is_done():
                        await select_interaction.response.send_message(
                            f"{theme.deniedIcon} {t('changes.common.selection_error', self.lang)}",
                            ephemeral=True
                        )
                    else:
                        await select_interaction.followup.send(
                            f"{theme.deniedIcon} {t('changes.common.selection_error', self.lang)}",
                            ephemeral=True
                        )

            view.callback = alliance_callback
            
            await interaction.response.send_message(
                embed=select_embed,
                view=view,
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in nickname_changes_button: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.common.request_error', self.lang)}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Main Menu",
        emoji=f"{theme.homeIcon}",
        style=discord.ButtonStyle.secondary,
        custom_id="main_menu",
        row=1
    )
    async def main_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_main_menu(interaction)

    async def show_main_menu(self, interaction: discord.Interaction):
        try:
            alliance_cog = self.cog.bot.get_cog("Alliance")
            if alliance_cog:
                await alliance_cog.show_main_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.common.main_menu_error', self.lang)}",
                    ephemeral=True
                )
        except Exception as e:
            print(f"[ERROR] Main Menu error in changes: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    t("changes.common.main_menu_error", self.lang),
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    t("changes.common.main_menu_error", self.lang),
                    ephemeral=True
                )

    async def last_hour_callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
            await self.cog.show_recent_changes(interaction, self.alliance_name, hours=1)
        except Exception as e:
            print(f"Error in last_hour_callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )

    async def last_day_callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
            await self.cog.show_recent_changes(interaction, self.alliance_name, hours=24)
        except Exception as e:
            print(f"Error in last_day_callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )

    async def custom_time_callback(self, interaction: discord.Interaction):
        try:
            modal = CustomTimeModal(self.cog, self.alliance_name, self.lang)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Error in custom_time_callback: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('changes.custom_time.error_open', self.lang)}",
                ephemeral=True
            )

class MemberListView(discord.ui.View):
    def __init__(self, cog, members, alliance_name, lang: str):
        super().__init__()
        self.cog = cog
        self.members = members
        self.alliance_name = alliance_name
        self.lang = lang
        self.current_page = 0
        self.total_pages = (len(members) + 24) // 25
        self.update_view()

    def update_view(self):
        self.clear_items()
        
        start_idx = self.current_page * 25
        end_idx = min(start_idx + 25, len(self.members))
        current_members = self.members[start_idx:end_idx]

        select = discord.ui.Select(
            placeholder=t(
                "changes.member_list.select_placeholder",
                self.lang,
                current=self.current_page + 1,
                total=self.total_pages
            ),
            options=[
                discord.SelectOption(
                    label=f"{name}",
                    value=str(fid),
                    description=t(
                        "changes.member_list.option_desc",
                        self.lang,
                        fid=fid,
                        level=self.cog.level_mapping.get(furnace_lv, str(furnace_lv))
                    )
                ) for fid, name, furnace_lv in current_members
            ],
            row=0
        )

        async def member_callback(interaction):
            try:
                fid = int(select.values[0])
                await interaction.response.defer()
                await self.cog.show_furnace_history(interaction, fid)
            except Exception as e:
                print(f"Error in member_callback: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                            f"{theme.deniedIcon} {t('changes.furnace.error', self.lang)}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                            f"{theme.deniedIcon} {t('changes.furnace.error', self.lang)}",
                        ephemeral=True
                    )

        select.callback = member_callback
        self.add_item(select)

        last_hour_button = discord.ui.Button(
            label=t("changes.recent.last_hour", self.lang),
            emoji=f"{theme.timeIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="last_hour",
            row=1
        )
        last_hour_button.callback = self.last_hour_callback
        self.add_item(last_hour_button)

        last_day_button = discord.ui.Button(
            label=t("changes.recent.last_24h", self.lang),
            emoji=f"{theme.calendarIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="last_day",
            row=1
        )
        last_day_button.callback = self.last_day_callback
        self.add_item(last_day_button)

        custom_time_button = discord.ui.Button(
            label=t("changes.recent.custom_time", self.lang),
            emoji=f"{theme.settingsIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="custom_time",
            row=1
        )
        custom_time_button.callback = self.custom_time_callback
        self.add_item(custom_time_button)

        if self.total_pages > 1:
            previous_button = discord.ui.Button(
                label=t("changes.common.previous", self.lang),
                emoji=f"{theme.backIcon}",
                style=discord.ButtonStyle.secondary,
                custom_id="previous",
                disabled=self.current_page == 0,
                row=2
            )
            previous_button.callback = self.previous_callback
            self.add_item(previous_button)

            next_button = discord.ui.Button(
                label=t("changes.common.next", self.lang),
                emoji=f"{theme.forwardIcon}",
                style=discord.ButtonStyle.secondary,
                custom_id="next",
                disabled=self.current_page == self.total_pages - 1,
                row=2
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)

        search_button = discord.ui.Button(
            label=t("changes.common.search_by_id", self.lang),
            emoji=f"{theme.searchIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="search_fid",
            row=2
        )
        search_button.callback = self.search_callback
        self.add_item(search_button)

    async def last_hour_callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
            await self.cog.show_recent_changes(interaction, self.alliance_name, hours=1)
        except Exception as e:
            print(f"Error in last_hour_callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )

    async def last_day_callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
            await self.cog.show_recent_changes(interaction, self.alliance_name, hours=24)
        except Exception as e:
            print(f"Error in last_day_callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )

    async def custom_time_callback(self, interaction: discord.Interaction):
        try:
            modal = CustomTimeModal(self.cog, self.alliance_name, self.lang)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Error in custom_time_callback: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('changes.custom_time.error_open', self.lang)}",
                ephemeral=True
            )

    async def previous_callback(self, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        await self.update_page(interaction)

    async def next_callback(self, interaction: discord.Interaction):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self.update_page(interaction)

    async def search_callback(self, interaction: discord.Interaction):
        modal = FurnaceHistoryIDSearchModal(self.cog, self.lang)
        await interaction.response.send_modal(modal)

    async def update_page(self, interaction: discord.Interaction):
        self.update_view()
        
        embed = discord.Embed(
            title=t("changes.member_list.title", self.lang, icon=theme.levelIcon, alliance=self.alliance_name),
            description=(
                f"{t('changes.furnace.select_member_prompt', self.lang)}\n"
                f"{theme.upperDivider}\n"
                f"{t('changes.common.total_members', self.lang)} {len(self.members)}\n"
                f"{t('changes.common.current_page', self.lang)} {self.current_page + 1}/{self.total_pages}\n"
                f"{theme.lowerDivider}"
            ),
            color=theme.emColor1
        )

        await interaction.response.edit_message(embed=embed, view=self)

class FurnaceHistoryIDSearchModal(discord.ui.Modal):
    def __init__(self, cog, lang: str):
        super().__init__(title=t("changes.common.search_title", lang))
        self.cog = cog
        self.lang = lang
        self.fid = discord.ui.TextInput(
            label=t("changes.common.id", self.lang),
            placeholder=t("changes.common.id_placeholder", self.lang),
            required=True,
            min_length=1,
            max_length=20
        )
        self.add_item(self.fid)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            fid = int(self.fid.value)
            await interaction.response.defer()
            await self.cog.show_furnace_history(interaction, fid)
                
        except ValueError:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.common.invalid_id', self.lang)}",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in FurnaceHistoryIDSearchModal on_submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.common.search_error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.common.search_error', self.lang)}",
                    ephemeral=True
                )

class MemberListViewNickname(discord.ui.View):
    def __init__(self, cog, members, alliance_name, lang: str):
        super().__init__()
        self.cog = cog
        self.members = members
        self.alliance_name = alliance_name
        self.lang = lang
        self.current_page = 0
        self.total_pages = (len(members) + 24) // 25
        self.update_view()

    def update_view(self):
        self.clear_items()
        
        start_idx = self.current_page * 25
        end_idx = min(start_idx + 25, len(self.members))
        current_members = self.members[start_idx:end_idx]

        select = discord.ui.Select(
            placeholder=t(
                "changes.member_list.select_placeholder",
                self.lang,
                current=self.current_page + 1,
                total=self.total_pages
            ),
            options=[
                discord.SelectOption(
                    label=f"{name}",
                    value=str(fid),
                    description=t(
                        "changes.member_list.option_desc",
                        self.lang,
                        fid=fid,
                        level=self.cog.level_mapping.get(furnace_lv, str(furnace_lv))
                    )
                ) for fid, name, furnace_lv in current_members
            ],
            row=0
        )

        async def member_callback(interaction):
            try:
                fid = int(select.values[0])
                await interaction.response.defer()
                await self.cog.show_nickname_history(interaction, fid)
            except Exception as e:
                print(f"Error in member_callback: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                            f"{theme.deniedIcon} {t('changes.nickname.error', self.lang)}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                            f"{theme.deniedIcon} {t('changes.nickname.error', self.lang)}",
                        ephemeral=True
                    )

        select.callback = member_callback
        self.add_item(select)

        last_hour_button = discord.ui.Button(
            label=t("changes.recent.last_hour", self.lang),
            emoji=f"{theme.timeIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="last_hour_nick",
            row=1
        )
        last_hour_button.callback = self.last_hour_callback
        self.add_item(last_hour_button)

        last_day_button = discord.ui.Button(
            label=t("changes.recent.last_24h", self.lang),
            emoji=f"{theme.calendarIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="last_day_nick",
            row=1
        )
        last_day_button.callback = self.last_day_callback
        self.add_item(last_day_button)

        custom_time_button = discord.ui.Button(
            label=t("changes.recent.custom_time", self.lang),
            emoji=f"{theme.settingsIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="custom_time_nick",
            row=1
        )
        custom_time_button.callback = self.custom_time_callback
        self.add_item(custom_time_button)

        if self.total_pages > 1:
            previous_button = discord.ui.Button(
                label=t("changes.common.previous", self.lang),
                emoji=f"{theme.backIcon}",
                style=discord.ButtonStyle.secondary,
                custom_id="previous_nick",
                disabled=self.current_page == 0,
                row=2
            )
            previous_button.callback = self.previous_callback
            self.add_item(previous_button)

            next_button = discord.ui.Button(
                label=t("changes.common.next", self.lang),
                emoji=f"{theme.forwardIcon}",
                style=discord.ButtonStyle.secondary,
                custom_id="next_nick",
                disabled=self.current_page == self.total_pages - 1,
                row=2
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)

        search_button = discord.ui.Button(
            label=t("changes.common.search_by_id", self.lang),
            emoji=f"{theme.searchIcon}",
            style=discord.ButtonStyle.primary,
            custom_id="search_fid_nick",
            row=2
        )
        search_button.callback = self.search_callback
        self.add_item(search_button)

    async def last_hour_callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
            await self.cog.show_recent_nickname_changes(interaction, self.alliance_name, hours=1)
        except Exception as e:
            print(f"Error in last_hour_callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )

    async def last_day_callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
            await self.cog.show_recent_nickname_changes(interaction, self.alliance_name, hours=24)
        except Exception as e:
            print(f"Error in last_day_callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.recent.error', self.lang)}",
                    ephemeral=True
                )

    async def custom_time_callback(self, interaction: discord.Interaction):
        try:
            modal = CustomTimeModalNickname(self.cog, self.alliance_name, self.lang)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Error in custom_time_callback: {e}")
            await interaction.followup.send(
                f"{theme.deniedIcon} {t('changes.custom_time.error_open', self.lang)}",
                ephemeral=True
            )

    async def previous_callback(self, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        await self.update_page(interaction)

    async def next_callback(self, interaction: discord.Interaction):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self.update_page(interaction)

    async def search_callback(self, interaction: discord.Interaction):
        modal = NicknameHistoryIDSearchModal(self.cog, self.lang)
        await interaction.response.send_modal(modal)

    async def update_page(self, interaction: discord.Interaction):
        self.update_view()
        
        embed = discord.Embed(
            title=t("changes.member_list.title", self.lang, icon=theme.editListIcon, alliance=self.alliance_name),
            description=(
                f"{t('changes.nickname.select_member_prompt', self.lang)}\n"
                f"{theme.upperDivider}\n"
                f"{t('changes.common.total_members', self.lang)} {len(self.members)}\n"
                f"{t('changes.common.current_page', self.lang)} {self.current_page + 1}/{self.total_pages}\n"
                f"{theme.lowerDivider}"
            ),
            color=theme.emColor1
        )

        await interaction.response.edit_message(embed=embed, view=self)

class NicknameHistoryIDSearchModal(discord.ui.Modal):
    def __init__(self, cog, lang: str):
        super().__init__(title=t("changes.common.search_title", lang))
        self.cog = cog
        self.lang = lang
        self.fid = discord.ui.TextInput(
            label=t("changes.common.id", self.lang),
            placeholder=t("changes.common.id_placeholder", self.lang),
            required=True,
            min_length=1,
            max_length=20
        )
        self.add_item(self.fid)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            fid = int(self.fid.value)
            await interaction.response.defer()
            await self.cog.show_nickname_history(interaction, fid)
                
        except ValueError:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.common.invalid_id', self.lang)}",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in NicknameHistoryIDSearchModal on_submit: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.common.search_error', self.lang)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"{theme.deniedIcon} {t('changes.common.search_error', self.lang)}",
                    ephemeral=True
                )

class CustomTimeModal(discord.ui.Modal):
    def __init__(self, cog, alliance_name, lang: str):
        super().__init__(title=t("changes.custom_time.title", lang))
        self.cog = cog
        self.alliance_name = alliance_name
        self.lang = lang
        self.hours = discord.ui.TextInput(
            label=t("changes.custom_time.label", self.lang),
            placeholder=t("changes.custom_time.placeholder", self.lang),
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.hours)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            hours = int(self.hours.value)
            if hours < 1 or hours > 24:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.custom_time.range_error', self.lang)}",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            await self.cog.show_recent_changes(interaction, self.alliance_name, hours)
                
        except ValueError:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.custom_time.invalid_number', self.lang)}",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in CustomTimeModal on_submit: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.common.request_error', self.lang)}",
                ephemeral=True
            )

class RecentChangesView(discord.ui.View):
    def __init__(self, chunks, members, level_mapping, alliance_name, hours, lang: str):
        super().__init__()
        self.chunks = chunks
        self.members = members
        self.level_mapping = level_mapping
        self.alliance_name = alliance_name
        self.hours = hours
        self.lang = lang
        self.current_page = 0
        self.total_pages = len(chunks)
        
        self.update_buttons()
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.custom_id == "previous":
                item.label = t("changes.common.previous", self.lang)
            elif item.custom_id == "next":
                item.label = t("changes.common.next", self.lang)

    def get_embed(self):
        embed = discord.Embed(
            title=t("changes.recent.furnace_title", self.lang, alliance=self.alliance_name, icon=theme.levelIcon),
            description=(
                f"{t('changes.recent.showing', self.lang, hours=self.hours)}\n"
                f"{theme.upperDivider}\n"
                f"{t('changes.recent.total_changes', self.lang)} {sum(len(chunk) for chunk in self.chunks)}\n"
                f"{t('changes.common.page', self.lang)} {self.current_page + 1}/{self.total_pages}\n"
                f"{theme.lowerDivider}\n"
            ),
            color=theme.emColor1
        )

        for fid, old_value, new_value, timestamp in self.chunks[self.current_page]:
            old_level = self.level_mapping.get(int(old_value), str(old_value))
            new_level = self.level_mapping.get(int(new_value), str(new_value))
            embed.add_field(
                name=t("changes.recent.member_line", self.lang, name=self.members[fid], fid=fid),
                value=f"{theme.stoveOldIcon} `{old_level}` ➜ {theme.stoveIcon} `{new_level}`\n{theme.timeIcon} {timestamp}",
                inline=False
            )

        if self.total_pages > 1:
            embed.set_footer(text=t("changes.common.page_of", self.lang, current=self.current_page + 1, total=self.total_pages))

        return embed

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1

    @discord.ui.button(label="Previous", emoji=f"{theme.prevIcon}", style=discord.ButtonStyle.secondary, custom_id="previous")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next", emoji=f"{theme.nextIcon}", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class RecentNicknameChangesView(discord.ui.View):
    def __init__(self, chunks, members, alliance_name, hours, lang: str):
        super().__init__()
        self.chunks = chunks
        self.members = members
        self.alliance_name = alliance_name
        self.hours = hours
        self.lang = lang
        self.current_page = 0
        self.total_pages = len(chunks)
        
        self.update_buttons()
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.custom_id == "previous_nick_recent":
                item.label = t("changes.common.previous", self.lang)
            elif item.custom_id == "next_nick_recent":
                item.label = t("changes.common.next", self.lang)

    def get_embed(self):
        embed = discord.Embed(
            title=t("changes.recent.nickname_title", self.lang, alliance=self.alliance_name, icon=theme.editListIcon),
            description=(
                f"{t('changes.recent.showing', self.lang, hours=self.hours)}\n"
                f"{theme.upperDivider}\n"
                f"{t('changes.recent.total_changes', self.lang)} {sum(len(chunk) for chunk in self.chunks)}\n"
                f"{t('changes.common.page', self.lang)} {self.current_page + 1}/{self.total_pages}\n"
                f"{theme.lowerDivider}\n"
            ),
            color=theme.emColor1
        )

        for fid, old_name, new_name, timestamp in self.chunks[self.current_page]:
            embed.add_field(
                name=t("changes.recent.member_line", self.lang, name=self.members[fid], fid=fid),
                value=f"{theme.avatarOldIcon} `{old_name}` ➜ {theme.avatarIcon} `{new_name}`\n{theme.timeIcon} {timestamp}",
                inline=False
            )

        if self.total_pages > 1:
            embed.set_footer(text=t("changes.common.page_of", self.lang, current=self.current_page + 1, total=self.total_pages))

        return embed

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1

    @discord.ui.button(label="Previous", emoji=f"{theme.prevIcon}", style=discord.ButtonStyle.secondary, custom_id="previous_nick_recent")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next", emoji=f"{theme.nextIcon}", style=discord.ButtonStyle.secondary, custom_id="next_nick_recent")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class CustomTimeModalNickname(discord.ui.Modal):
    def __init__(self, cog, alliance_name, lang: str):
        super().__init__(title=t("changes.custom_time.title", lang))
        self.cog = cog
        self.alliance_name = alliance_name
        self.lang = lang
        self.hours = discord.ui.TextInput(
            label=t("changes.custom_time.label", self.lang),
            placeholder=t("changes.custom_time.placeholder", self.lang),
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.hours)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            hours = int(self.hours.value)
            if hours < 1 or hours > 24:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('changes.custom_time.range_error', self.lang)}",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            await self.cog.show_recent_nickname_changes(interaction, self.alliance_name, hours)
                
        except ValueError:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.custom_time.invalid_number', self.lang)}",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in CustomTimeModalNickname on_submit: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('changes.common.request_error', self.lang)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Changes(bot)) 