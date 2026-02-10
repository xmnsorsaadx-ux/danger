import discord
from discord.ext import commands
from .pimp_my_bot import theme
from i18n import get_guild_language, t

class SupportOperations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def show_support_menu(self, interaction: discord.Interaction):
        lang = get_guild_language(interaction.guild.id if interaction.guild else None)
        support_menu_embed = discord.Embed(
            title=f"{theme.targetIcon} {t('support.menu.title', lang)}",
            description=(
                f"{t('support.menu.prompt', lang)}\n\n"
                f"**{t('support.menu.available', lang)}**\n"
                f"{theme.upperDivider}\n"
                f"{theme.editListIcon} **{t('support.menu.request', lang)}**\n"
                f"└ {t('support.menu.request_desc', lang)}\n\n"
                f"{theme.infoIcon} **{t('support.menu.about', lang)}**\n"
                f"└ {t('support.menu.about_desc', lang)}\n"
                f"{theme.lowerDivider}"
            ),
            color=theme.emColor1
        )

        view = SupportView(self, lang)
        
        try:
            await interaction.response.edit_message(embed=support_menu_embed, view=view)
        except discord.errors.InteractionResponded:
            await interaction.message.edit(embed=support_menu_embed, view=view)

    async def show_support_info(self, interaction: discord.Interaction):
        lang = get_guild_language(interaction.guild.id if interaction.guild else None)
        support_embed = discord.Embed(
            title=f"{theme.robotIcon} {t('support.info.title', lang)}",
            description=t('support.info.body', lang),
            color=theme.emColor1
        )
        
        try:
            await interaction.response.send_message(embed=support_embed, ephemeral=True)
            try:
                await interaction.user.send(embed=support_embed)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"{theme.deniedIcon} Could not send DM because your DMs are closed!",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error sending support info: {e}")

class SupportView(discord.ui.View):
    def __init__(self, cog, lang: str):
        super().__init__()
        self.cog = cog
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "request_support":
                    item.label = t("support.menu.request", lang)
                elif item.custom_id == "about_project":
                    item.label = t("support.menu.about", lang)
                elif item.custom_id == "main_menu":
                    item.label = t("button.main_menu", lang)

    @discord.ui.button(
        label="Request Support",
        emoji=f"{theme.editListIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="request_support"
    )
    async def support_request_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.show_support_info(interaction)

    @discord.ui.button(
        label="About Project",
        emoji=f"{theme.infoIcon}",
        style=discord.ButtonStyle.primary,
        custom_id="about_project"
    )
    async def about_project_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = get_guild_language(interaction.guild.id if interaction.guild else None)
        about_embed = discord.Embed(
            title=f"{theme.infoIcon} {t('support.about.title', lang)}",
            description=(
                f"**{t('support.about.open_source', lang)}**\n"
                f"{theme.upperDivider}\n"
                f"{t('support.about.body', lang)}\n\n"
                f"**{t('support.about.features', lang)}**\n"
                f"{theme.middleDivider}\n"
                f"• Alliance member management\n"
                f"• Gift code operations\n"
                f"• Automated member tracking\n"
                f"• Bear trap notifications\n"
                f"• ID channel verification\n"
                f"• and more...\n\n"
                f"**{t('support.about.contributing', lang)}**\n"
                f"{theme.middleDivider}\n"
                f"{t('support.about.contributing_body', lang)}"
            ),
            color=discord.Color.green()
        )

        about_embed.set_footer(text=t("support.about.footer", lang, heart=theme.heartIcon))
        
        try:
            await interaction.response.send_message(embed=about_embed, ephemeral=True)
            try:
                await interaction.user.send(embed=about_embed)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"{theme.deniedIcon} Could not send DM because your DMs are closed!",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error sending project info: {e}")

    @discord.ui.button(
        label="Main Menu",
        emoji=f"{theme.homeIcon}",
        style=discord.ButtonStyle.secondary,
        custom_id="main_menu"
    )
    async def main_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        alliance_cog = self.cog.bot.get_cog("Alliance")
        if alliance_cog:
            try:
                await interaction.message.edit(content=None, embed=None, view=None)
                await alliance_cog.show_main_menu(interaction)
            except discord.errors.InteractionResponded:
                await interaction.message.edit(content=None, embed=None, view=None)
                await alliance_cog.show_main_menu(interaction)

async def setup(bot):
    await bot.add_cog(SupportOperations(bot))