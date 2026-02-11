import discord
from discord.ext import commands
import hashlib
import sqlite3
import aiohttp
import time
import ssl
from .permission_handler import PermissionManager
from .pimp_my_bot import theme
from i18n import get_guild_language, t


def _get_lang(interaction: discord.Interaction | None) -> str:
    guild_id = interaction.guild.id if interaction and interaction.guild else None
    return get_guild_language(guild_id)

class RegisterSettingsView(discord.ui.View):
    def __init__(self, cog, lang: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.lang = lang
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.custom_id == "enable_register":
                item.label = t("registration.settings.enable", self.lang)
            elif item.custom_id == "disable_register":
                item.label = t("registration.settings.disable", self.lang)
        
    def change_settings(self, enabled: bool):
        try:
            conn = sqlite3.connect("db/settings.sqlite")
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='register_settings'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                cursor.execute("CREATE TABLE register_settings (enabled BOOLEAN)")
                cursor.execute("INSERT INTO register_settings VALUES (?)", (enabled,))
            else:
                cursor.execute("UPDATE register_settings SET enabled = ? WHERE rowid = 1", (enabled,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating register settings: {e}")

    @discord.ui.button(
        label="Enable",
        emoji=f"{theme.verifiedIcon}",
        style=discord.ButtonStyle.success,
        custom_id="enable_register",
        row=0
    )
    async def enable_register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.change_settings(True)
            await interaction.response.send_message(
                f"{theme.verifiedIcon} {t('registration.settings.enabled', _get_lang(interaction))}",
                ephemeral=True
            )
        except Exception as _:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('registration.settings.enable_error', _get_lang(interaction))}",
                ephemeral=True
            )
            
    @discord.ui.button(
        label="Disable",
        emoji=f"{theme.deniedIcon}",
        style=discord.ButtonStyle.danger,
        custom_id="disable_register",
        row=0
    )
    async def disable_register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.change_settings(False)
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('registration.settings.disabled', _get_lang(interaction))}",
                ephemeral=True
            )
        except Exception as _:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('registration.settings.disable_error', _get_lang(interaction))}",
                ephemeral=True
            )

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.conn_alliance = sqlite3.connect("db/alliance.sqlite")
        self.c_alliance = self.conn_alliance.cursor()
        
        self.conn_users = sqlite3.connect("db/users.sqlite")
        self.c_users = self.conn_users.cursor()
    
    def cog_unload(self):
        self.conn_alliance.close()
        self.conn_users.close()

    async def show_settings_menu(self, interaction: discord.Interaction):
        lang = _get_lang(interaction)
        is_admin, is_global = PermissionManager.is_admin(interaction.user.id)
        if not is_admin or not is_global:
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('registration.settings.no_permission', lang)}",
                ephemeral=True
            )
            return

        view = RegisterSettingsView(self, lang)
        
        await interaction.response.send_message(
            t("registration.settings.prompt", lang),
            view=view,
            ephemeral=True
        )
        
    def is_already_in_users(self, fid: int) -> bool:
        """Check if a user with the given fid is already registered."""
        self.c_users.execute("SELECT 1 FROM users WHERE fid = ?", (fid,))
        return self.c_users.fetchone() is not None
        
    def is_registration_enabled(self) -> bool:
        """Check if registration is enabled in the settings database."""
        try:
            conn = sqlite3.connect("db/settings.sqlite")
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='register_settings'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                conn.close()
                return False
            
            cursor.execute("SELECT enabled FROM register_settings WHERE rowid = 1")
            result = cursor.fetchone()
            
            conn.close()
            
            return bool(result[0]) if result else False
            
        except Exception as e:
            print(f"Error checking registration status: {e}")
            return False
        
    async def alliance_autocomplete(self, interaction: discord.Interaction, current: str):
        self.c_alliance.execute("SELECT alliance_id, name FROM alliance_list")
        alliances = self.c_alliance.fetchall()
        
        return [
            discord.app_commands.Choice(name=name, value=alliance_id)
            for alliance_id, name in alliances if current.lower() in name.lower()
        ][:25]
        
    async def fetch_user(self, fid: int):
        URL = "https://wos-giftcode-api.centurygame.com/api/player"
        HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
        
        ssl_context = ssl.create_default_context()
        session = aiohttp.ClientSession()
        
        data_nosign = f"fid={fid}&time={time.time_ns()}"
        sign = hashlib.md5((data_nosign + "tB87#kPtkxqOS2").encode()).hexdigest()
        data = f"sign={sign}&{data_nosign}"

        try:
            async with session.post(
                url=URL,
                data=data,
                headers=HEADERS,
                ssl=ssl_context
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise Exception("RATE_LIMITED")
                else:
                    raise Exception(f"Failed to fetch user data: {response.status}")
        finally:
            await session.close()
         
    @discord.app_commands.command(
        name="register",
        description=t("registration.command.desc", "en"),
    )
    @discord.app_commands.describe(
        fid=t("registration.command.fid", "en"),
        alliance=t("registration.command.alliance", "en")
    )
    @discord.app_commands.autocomplete(alliance=alliance_autocomplete)
    async def register(self, interaction: discord.Interaction, fid: int, alliance: int):
        lang = _get_lang(interaction)
        if not self.is_registration_enabled():
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('registration.disabled', lang)}",
                ephemeral=True
            )
            return
        
        if self.is_already_in_users(fid):
            await interaction.response.send_message(
                f"{theme.deniedIcon} {t('registration.already_registered', lang)}",
                ephemeral=True
            )
            return
        
        try:
            api_response = await self.fetch_user(fid)
            
            if api_response.get("msg") != "success":
                error_msg = api_response.get("msg", "Unknown error")
                
                if "role not exist" in error_msg.lower():
                    display_msg = f"{theme.deniedIcon} {t('registration.invalid_id', lang)}"
                else:
                    display_msg = f"{theme.deniedIcon} {t('registration.invalid_id_detail', lang, error=error_msg)}"
                
                await interaction.response.send_message(
                    display_msg,
                    ephemeral=True
                )
                return
            
            if "data" not in api_response:
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('registration.invalid_response', lang)}",
                    ephemeral=True
                )
                return
                
            user_data = api_response["data"]
            
        except Exception as e:
            if str(e) == "RATE_LIMITED":
                await interaction.response.send_message(
                    t("registration.rate_limited", lang),
                    ephemeral=True
                )
            else:
                print(f"Error fetching user data for FID {fid}: {e}")
                await interaction.response.send_message(
                    f"{theme.deniedIcon} {t('registration.fetch_error', lang)}",
                    ephemeral=True
                )
            return

        nickname = user_data["nickname"]
        furnace_lv = user_data["stove_lv"]
        kid = user_data["kid"]
        stove_lv_content = user_data.get("stove_lv_content")

        self.c_users.execute(
            "INSERT INTO users (fid, nickname, furnace_lv, kid, stove_lv_content, alliance) VALUES (?, ?, ?, ?, ?, ?)", 
            (fid, nickname, furnace_lv, kid, stove_lv_content, alliance)
        )
        
        self.conn_users.commit()    
        
        await interaction.response.send_message(
            t("registration.success", lang),
            ephemeral=True
        )
        
async def setup(bot):
    await bot.add_cog(Register(bot))