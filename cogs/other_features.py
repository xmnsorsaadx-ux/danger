import discord
from discord.ext import commands
import sqlite3
from .permission_handler import PermissionManager
from .pimp_my_bot import theme
from i18n import get_guild_language, t

def _get_lang(interaction: discord.Interaction | None) -> str:
    guild_id = interaction.guild.id if interaction and interaction.guild else None
    return get_guild_language(guild_id)

class OtherFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def show_other_features_menu(self, interaction: discord.Interaction):
        try:
            _, is_global = PermissionManager.is_admin(interaction.user.id)
            lang = _get_lang(interaction)

            embed = discord.Embed(
                title=f"{theme.settingsIcon} {t('other.features.title', lang)}",
                description=(
                    f"{t('other.features.description', lang)}\n\n"
                    f"**{t('other.features.available', lang)}**\n"
                    f"{theme.upperDivider}\n"
                    f"{theme.announceIcon} **{t('other.features.notification.title', lang)}**\n"
                    f"└ {t('other.features.notification.desc1', lang)}\n"
                    f"└ {t('other.features.notification.desc2', lang)}\n"
                    f"   {t('other.features.notification.desc3', lang)}\n"
                    f"└ {t('other.features.notification.desc4', lang)}\n\n"
                    f"{theme.fidIcon} **{t('other.features.id_channel.title', lang)}**\n"
                    f"└ {t('other.features.id_channel.desc1', lang)}\n"
                    f"└ {t('other.features.id_channel.desc2', lang)}\n"
                    f"└ {t('other.features.id_channel.desc3', lang)}\n\n"
                    f"{theme.editListIcon} **{t('other.features.registration.title', lang)}**\n"
                    f"└ {t('other.features.registration.desc1', lang)}\n"
                    f"└ {t('other.features.registration.desc2', lang)}\n\n"
                    f"{theme.listIcon} **{t('other.features.attendance.title', lang)}**\n"
                    f"└ {t('other.features.attendance.desc1', lang)}\n"
                    f"└ {t('other.features.attendance.desc2', lang)}\n"
                    f"└ {t('other.features.attendance.desc3', lang)}\n\n"
                    f"{theme.ministerIcon} **{t('other.features.minister.title', lang)}**\n"
                    f"└ {t('other.features.minister.desc1', lang)}\n"
                    f"└ {t('other.features.minister.desc2', lang)}\n"
                    f"└ {t('other.features.minister.desc3', lang)}\n\n"
                    f"{theme.saveIcon} **{t('other.features.backup.title', lang)}**\n"
                    f"└ {t('other.features.backup.desc1', lang)}\n"
                    f"└ {t('other.features.backup.desc2', lang)}\n"
                    f"└ {t('other.features.backup.desc3', lang)}\n"
                    f"{theme.lowerDivider}"
                ),
                color=theme.emColor1
            )

            view = OtherFeaturesView(self, is_global, lang)

            try:
                await interaction.response.edit_message(embed=embed, view=view)
            except discord.InteractionResponded:
                pass

        except Exception as e:
            print(f"Error in show_other_features_menu: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('other.features.error.generic', _get_lang(interaction))}",
                    ephemeral=True
                )

class OtherFeaturesView(discord.ui.View):
    def __init__(self, cog, is_global: bool = False, lang: str = "en"):
        super().__init__(timeout=None)
        self.cog = cog
        self.is_global = is_global
        self._apply_language(lang)

        # Disable global-admin-only buttons for non-global admins
        if not is_global:
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id in [
                    "backup_system", "registration_system"
                ]:
                    child.disabled = True

    def _apply_language(self, lang: str) -> None:
        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue
            if child.custom_id == "bear_trap":
                child.label = t("other.features.notification.title", lang)
            elif child.custom_id == "id_channel":
                child.label = t("other.features.id_channel.title", lang)
            elif child.custom_id == "minister_channels":
                child.label = t("other.features.minister.title", lang)
            elif child.custom_id == "backup_system":
                child.label = t("other.features.backup.title", lang)
            elif child.custom_id == "registration_system":
                child.label = t("other.features.registration.title", lang)
            elif child.custom_id == "attendance_system":
                child.label = t("other.features.attendance.title", lang)
            elif child.custom_id == "main_menu":
                child.label = t("other.features.main_menu", lang)

    @discord.ui.button(
        label="Notification System",
        emoji=f"{theme.announceIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="bear_trap",
        row=0
    )
    async def bear_trap_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lang = _get_lang(interaction)
            bear_trap_cog = self.cog.bot.get_cog("BearTrap")
            if bear_trap_cog:
                await bear_trap_cog.show_bear_trap_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('other.features.error.module_not_found', lang, module=t('other.features.module.notification', lang))}",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error loading Bear Trap menu: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('other.features.error.loading', lang, module=t('other.features.module.notification', lang))}",
                ephemeral=True
            )

    @discord.ui.button(
        label="ID Channel",
        emoji=f"{theme.fidIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="id_channel",
        row=0
    )
    async def id_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lang = _get_lang(interaction)
            id_channel_cog = self.cog.bot.get_cog("IDChannel")
            if id_channel_cog:
                await id_channel_cog.show_id_channel_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('other.features.error.module_not_found', lang, module=t('other.features.module.id_channel', lang))}",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error loading ID Channel menu: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('other.features.error.loading', lang, module=t('other.features.module.id_channel', lang))}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Minister Scheduling",
        emoji=f"{theme.ministerIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="minister_channels",
        row=1
    )
    async def minister_channels_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lang = _get_lang(interaction)
            minister_menu_cog = self.cog.bot.get_cog("MinisterMenu")
            if minister_menu_cog:
                await minister_menu_cog.show_minister_channel_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('other.features.error.module_not_found', lang, module=t('other.features.module.minister', lang))}",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error loading Minister Scheduling menu: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('other.features.error.loading', lang, module=t('other.features.module.minister', lang))}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Backup System",
        emoji=f"{theme.saveIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="backup_system",
        row=2
    )
    async def backup_system_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lang = _get_lang(interaction)
            backup_cog = self.cog.bot.get_cog("BackupOperations")
            if backup_cog:
                await backup_cog.show_backup_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('other.features.error.module_not_found', lang, module=t('other.features.module.backup', lang))}",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error loading Backup System menu: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('other.features.error.loading', lang, module=t('other.features.module.backup', lang))}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Registration System",
        emoji=f"{theme.editListIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="registration_system",
        row=0
    )
    async def registration_system_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lang = _get_lang(interaction)
            register_cog = self.cog.bot.get_cog("Register")
            if register_cog:
                await register_cog.show_settings_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('other.features.error.module_not_found', lang, module=t('other.features.module.registration', lang))}",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error loading Registration System menu: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('other.features.error.loading', lang, module=t('other.features.module.registration', lang))}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Attendance System",
        emoji=f"{theme.listIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="attendance_system",
        row=1
    )
    async def attendance_system_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lang = _get_lang(interaction)
            attendance_cog = self.cog.bot.get_cog("Attendance")
            if attendance_cog:
                await attendance_cog.show_attendance_menu(interaction)
            else:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('other.features.error.module_not_found', lang, module=t('other.features.module.attendance', lang))}",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error loading Attendance System menu: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('other.features.error.loading', lang, module=t('other.features.module.attendance', lang))}",
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
                await alliance_cog.show_main_menu(interaction)
        except Exception as e:
            print(f"Error returning to main menu: {e}")
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('other.features.error.main_menu', _get_lang(interaction))}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(OtherFeatures(bot))