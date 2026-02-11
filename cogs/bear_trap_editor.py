import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
import re
from .bear_event_types import get_event_icon
from .permission_handler import PermissionManager
from .pimp_my_bot import theme
from i18n import get_guild_language, t


def _get_lang(interaction: discord.Interaction | None) -> str:
    guild_id = interaction.guild.id if interaction and interaction.guild else None
    return get_guild_language(guild_id)

def check_mention_placeholder_misuse(text: str, is_embed: bool = False, lang: str = "en") -> str | None:
    """
    Check if user typed a literal @mention instead of {tag} or @tag.
    Returns a warning message if misuse detected, None otherwise.

    Args:
        text: The message text to check
        is_embed: If True, warn on ALL @ mentions (including @everyone/@here)
                  since they don't work in embed fields
    """
    # Skip if {tag} or @tag is already used correctly
    if "{tag}" in text or "@tag" in text:
        return None

    if is_embed:
        # In embeds, NO @ mentions work - warn on everything
        pattern = r'@(\w+)'
    else:
        # In plain messages, @everyone/@here work - only warn on usernames/roles
        pattern = r'@(?!everyone|here)(\w+)'

    matches = re.findall(pattern, text)

    if matches:
        examples = ", ".join(f"@{m}" for m in matches[:3])
        if is_embed:
            return t(
                "bear.editor.warn_embed_mention",
                lang,
                icon=theme.warnIcon,
                examples=examples
            )
        else:
            return t(
                "bear.editor.warn_plain_mention",
                lang,
                icon=theme.warnIcon,
                examples=examples
            )
    return None

def format_repeat_interval(repeat_minutes, notification_id=None, lang: str = "en") -> str:
    if repeat_minutes == 0:
        return t("bear.editor.repeat.none", lang, icon=theme.deniedIcon)

    if repeat_minutes == -1:
        if notification_id is None:
            return t("bear.editor.repeat.custom_days", lang)

        conn = sqlite3.connect("db/beartime.sqlite")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT weekday FROM notification_days
            WHERE notification_id = ?
        """, (notification_id,))
        rows = cursor.fetchall()
        conn.close()

        weekday_names = [
            t("bear.editor.weekday.monday", lang),
            t("bear.editor.weekday.tuesday", lang),
            t("bear.editor.weekday.wednesday", lang),
            t("bear.editor.weekday.thursday", lang),
            t("bear.editor.weekday.friday", lang),
            t("bear.editor.weekday.saturday", lang),
            t("bear.editor.weekday.sunday", lang),
        ]
        day_set = set()

        for row in rows:
            for part in row[0].split('|'):
                if part.strip().isdigit():
                    day_set.add(int(part))

        if not day_set:
            return t("bear.editor.repeat.no_days", lang, icon=theme.deniedIcon)

        sorted_days = sorted(day_set)
        day_list = [weekday_names[day] for day in sorted_days]

        if len(day_list) == 1:
            return t("bear.editor.repeat.every", lang, days=day_list[0])

        and_word = t("bear.editor.and", lang)
        return t("bear.editor.repeat.every", lang, days=", ".join(day_list[:-1]) + f" {and_word} " + day_list[-1])

    try:
        minutes = int(repeat_minutes)
    except ValueError:
        return t("bear.editor.repeat.invalid", lang)

    time_units = [
        ("month", 43200),
        ("week", 10080),
        ("day", 1440),
        ("hour", 60),
        ("minute", 1),
    ]

    result = []
    for name, unit in time_units:
        value = minutes // unit
        if value > 0:
            unit_key = f"bear.editor.unit.{name}_plural" if value > 1 else f"bear.editor.unit.{name}_single"
            result.append(f"{value} {t(unit_key, lang)}")
            minutes %= unit

    and_word = t("bear.editor.and", lang)
    return f" {and_word} ".join(result)

def format_mention(mention: str, lang: str = "en") -> str:
    """Formats mention strings into Discord mention syntax."""
    if mention.startswith("role_"):
        role_id = mention.split("_")[1]
        return f"<@&{role_id}>"
    elif mention.startswith("member_"):
        user_id = mention.split("_")[1]
        return f"<@{user_id}>"
    elif mention == "everyone":
        return "@everyone"
    else:
        return t("bear.editor.mention.none", lang)

def format_notification_type(notification_type: int, lang: str = "en") -> str:
    """Returns a formatted string for the given notification type."""
    notification_types = {
        1: t("bear.editor.notify_type.1", lang),
        2: t("bear.editor.notify_type.2", lang),
        3: t("bear.editor.notify_type.3", lang),
        4: t("bear.editor.notify_type.4", lang),
        5: t("bear.editor.notify_type.5", lang),
        6: t("bear.editor.notify_type.6", lang),
    }
    return notification_types.get(notification_type, t("bear.editor.notify_type.unknown", lang))

class EmbedFieldModal(discord.ui.Modal):
    def __init__(self, parent_view, field_name, label, placeholder, default="", style=discord.TextStyle.short,
                 max_length=1024, required=False, lang: str = "en"):
        super().__init__(title=t("bear.editor.modal.edit_field", lang, field=field_name))

        self.parent_view = parent_view
        self.field_name = field_name
        self.lang = lang

        self.input_field = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            default=default,
            style=style,
            max_length=max_length,
            required=required,
        )
        self.add_item(self.input_field)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Check for @ mention misuse in embed text fields and show warning
        text_fields = ("title", "embed_description", "footer", "author", "mention_message")
        if self.field_name in text_fields:
            warning = check_mention_placeholder_misuse(self.input_field.value, is_embed=True, lang=self.lang)
            if warning:
                await interaction.followup.send(warning, ephemeral=True)

        try:
            value = self.input_field.value
            if self.field_name == "color":
                if value.startswith("#"):
                    value = value[1:]
                try:
                    int_color = int(value, 16)
                except ValueError:
                    await interaction.response.send_message(
                        t("bear.editor.color_invalid", self.lang),
                        ephemeral=True
                    )
                    return

                self.parent_view.color = int_color
            else:
                setattr(self.parent_view, self.field_name, value)

            await self.parent_view.cog.update_embed_notification(self.parent_view)
            await self.parent_view.update_embed_view(interaction)
        except Exception as e:
            print(f"Error in modal for {self.field_name}: {e}")
            await interaction.followup.send(
                t("bear.editor.modal_error", self.lang, error=str(e)),
                ephemeral=True
            )

class EmbedDataView(discord.ui.View):
    def __init__(self, cog, notification_id, title, description, color, image_url, thumbnail_url, footer, author,
                 mention_message, event_type=None, hour=0, minute=0, next_notification=None, lang: str = "en"):
        super().__init__(timeout=None)
        self.cog = cog
        self.notification_id = notification_id
        self.title = title
        self.embed_description = description
        self.color = color
        self.image_url = image_url
        self.thumbnail_url = thumbnail_url
        self.footer = footer
        self.author = author
        self.mention_message = mention_message
        self.message = None
        self.event_type = event_type
        self.hour = hour
        self.minute = minute
        self.next_notification = next_notification
        self.lang = lang

        self.edit_title.label = t("bear.editor.button.title", self.lang)
        self.edit_description.label = t("bear.editor.button.description", self.lang)
        self.edit_color.label = t("bear.editor.button.color", self.lang)
        self.edit_mention_message.label = t("bear.editor.button.mention_message", self.lang)
        self.edit_footer.label = t("bear.editor.button.footer", self.lang)
        self.edit_author.label = t("bear.editor.button.author", self.lang)
        self.edit_image_url.label = t("bear.editor.button.image", self.lang)
        self.edit_thumbnail_url.label = t("bear.editor.button.thumbnail", self.lang)
        self.notification_setting.label = t("bear.editor.button.settings", self.lang)

    def _replace_variables(self, text):
        """Replace notification variables with sample values for preview."""
        if not text:
            return text

        example_time = t("bear.editor.preview.time", self.lang)
        example_name = self.event_type if self.event_type else t("bear.editor.preview.event", self.lang)
        example_emoji = get_event_icon(self.event_type) if self.event_type else theme.calendarIcon
        example_event_time = f"{self.hour:02d}:{self.minute:02d}"

        # Get date from next_notification if available
        if self.next_notification:
            try:
                next_dt = datetime.fromisoformat(self.next_notification.replace("+00:00", ""))
                example_date = next_dt.strftime("%b %d")
            except:
                example_date = t("bear.editor.preview.date_fallback", self.lang)
        else:
            example_date = t("bear.editor.preview.date_fallback", self.lang)

        return (text
            .replace("%t", example_time)
            .replace("{time}", example_time)
            .replace("%n", example_name)
            .replace("%e", example_event_time)
            .replace("%d", example_date)
            .replace("%i", example_emoji))

    async def update_embed_view(self, interaction: discord.Interaction):
        """Update the embed message when changes are made."""
        embed = discord.Embed(
            title=self._replace_variables(self.title),
            description=self._replace_variables(self.embed_description),
            color=self.color,
        )
        if self.footer:
            embed.set_footer(text=self._replace_variables(self.footer))
        if self.author:
            embed.set_author(name=self._replace_variables(self.author))
        if self.image_url:
            embed.set_image(url=self.image_url)
        if self.thumbnail_url:
            embed.set_thumbnail(url=self.thumbnail_url)

        mention_preview = self._replace_variables(self.mention_message) if self.mention_message else ""
        await self.message.edit(content=mention_preview, embed=embed, view=self)

    @discord.ui.button(label="Title", style=discord.ButtonStyle.primary)
    async def edit_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="title",
                label=t("bear.editor.label.embed_title", self.lang),
                placeholder=t("bear.editor.placeholder.title", self.lang),
                default=self.title or "",
                max_length=256,
                required=True,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Description", style=discord.ButtonStyle.primary)
    async def edit_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="embed_description",
                label=t("bear.editor.label.embed_description", self.lang),
                placeholder=t("bear.editor.placeholder.description", self.lang),
                default=self.embed_description or "",
                max_length=4000,
                style=discord.TextStyle.paragraph,
                required=True,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Color", style=discord.ButtonStyle.success)
    async def edit_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        default_hex = ""
        if self.color:
            default_hex = f"#{hex(self.color)[2:].zfill(6)}"

        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="color",
                label=t("bear.editor.label.color", self.lang),
                placeholder=t("bear.editor.placeholder.color", self.lang),
                default=default_hex,
                max_length=7,
                required=True,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Mention message", style=discord.ButtonStyle.secondary)
    async def edit_mention_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="mention_message",
                label=t("bear.editor.label.mention_message", self.lang),
                placeholder=t("bear.editor.placeholder.mention_message", self.lang),
                default=self.mention_message or "",
                required=False,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Footer", style=discord.ButtonStyle.secondary)
    async def edit_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="footer",
                label=t("bear.editor.label.footer", self.lang),
                placeholder=t("bear.editor.placeholder.footer", self.lang),
                default=self.footer or "",
                max_length=2048,
                required=False,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Author", style=discord.ButtonStyle.secondary)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="author",
                label=t("bear.editor.label.author", self.lang),
                placeholder=t("bear.editor.placeholder.author", self.lang),
                default=self.author or "",
                max_length=256,
                required=False,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Add Image", style=discord.ButtonStyle.secondary)
    async def edit_image_url(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="image_url",
                label=t("bear.editor.label.image", self.lang),
                placeholder=t("bear.editor.placeholder.image", self.lang),
                default=self.image_url or "",
                required=False,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Add Thumbnail", style=discord.ButtonStyle.secondary)
    async def edit_thumbnail_url(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedFieldModal(
                parent_view=self,
                field_name="thumbnail_url",
                label=t("bear.editor.label.thumbnail", self.lang),
                placeholder=t("bear.editor.placeholder.thumbnail", self.lang),
                default=self.thumbnail_url or "",
                required=False,
                lang=self.lang
            )
        )

    @discord.ui.button(label="Edit Notification settings", style=discord.ButtonStyle.primary, emoji=f"{theme.settingsIcon}")
    async def notification_setting(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        lang = _get_lang(interaction)

        conn = sqlite3.connect("db/beartime.sqlite")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT channel_id, hour, minute, description, mention_type, repeat_minutes, next_notification, timezone, notification_type FROM bear_notifications WHERE id = ?",
            (self.notification_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            await interaction.followup.send(
                t("bear.editor.notification_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        channel_id, hours, minutes, description, mention, repeat, next_notification, timezone, notification_type = result

        new_view = PlainEditorView(
            cog=self.cog,
            notification_id=self.notification_id,
            channel_id=channel_id,
            hours=hours,
            minutes=minutes,
            description=description,
            mention=mention,
            repeat=repeat,
            next_notification=next_notification,
            timezone=timezone,
            notification_type=notification_type,
            lang=lang
        )
        new_view.message = self.message

        next_notification_date = datetime.fromisoformat(next_notification).strftime("%d/%m/%Y")
        formatted_repeat = format_repeat_interval(repeat, self.notification_id, lang=lang)
        formatted_mention = format_mention(mention, lang=lang)
        formatted_type = format_notification_type(notification_type, lang=lang)

        embed = discord.Embed(
            title=t("bear.editor.edit_title", lang),
            description=t(
                "bear.editor.edit_desc",
                lang,
                calendar=theme.calendarIcon,
                time_icon=theme.timeIcon,
                announce=theme.announceIcon,
                edit_icon=theme.editListIcon,
                settings_icon=theme.settingsIcon,
                members_icon=theme.membersIcon,
                retry_icon=theme.retryIcon,
                next_date=next_notification_date,
                time=f"{hours:02d}:{minutes:02d}",
                timezone=timezone,
                channel_id=channel_id,
                description=description,
                notification_type=formatted_type,
                mention=formatted_mention,
                repeat=formatted_repeat
            ),
            color=theme.emColor1,
        )

        await self.message.edit(content=None, embed=embed, view=new_view)

class PlainEditorView(discord.ui.View):
    def __init__(self, cog, notification_id, channel_id, hours, minutes, description, mention, repeat,
                 next_notification, timezone, notification_type, lang: str = "en"):
        super().__init__(timeout=None)
        self.cog = cog
        self.notification_id = notification_id
        self.channel_id = channel_id
        self.hours = hours
        self.minutes = minutes
        self.description = description
        self.mention = mention
        self.repeat = repeat
        self.next_notification = next_notification
        self.timezone = timezone
        self.notification_type = notification_type
        self.message = None
        self.lang = lang

        self.description_button.label = t("bear.editor.button.description", self.lang)
        self.edit_channel.label = t("bear.editor.button.channel", self.lang)
        self.edit_time.label = t("bear.editor.button.time", self.lang)
        self.edit_repeat.label = t("bear.editor.button.repeat", self.lang)
        self.edit_mention.label = t("bear.editor.button.mention", self.lang)
        self.edit_notification_ping.label = t("bear.editor.button.notification_ping", self.lang)

        if self.repeat == -1:
            try:
                conn = sqlite3.connect("db/beartime.sqlite")
                cursor = conn.cursor()
                cursor.execute("SELECT weekday FROM notification_days WHERE notification_id = ?", (self.notification_id,))
                weekday_value = cursor.fetchone()
                if weekday_value:
                    self.weekdays = weekday_value[0]
                conn.close()
            except Exception as e:
                print(f"Failed to load weekdays: {e}")

        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "description_button":
                if "EMBED_MESSAGE" in self.description:
                    child.label = t("bear.editor.button.edit_embed", self.lang)
                    child.emoji = theme.editListIcon
                elif "PLAIN_MESSAGE" in self.description:
                    child.label = t("bear.editor.button.description", self.lang)
                else:
                    child.label = t("bear.editor.button.description", self.lang)

    async def update_embed(self, interaction: discord.Interaction):
        """Update the embed message when changes are made."""
        next_notification_date = datetime.fromisoformat(self.next_notification).strftime("%d/%m/%Y")
        formatted_repeat = format_repeat_interval(self.repeat, self.notification_id, lang=self.lang)
        formatted_mention = format_mention(self.mention, lang=self.lang)
        formatted_type = format_notification_type(self.notification_type, lang=self.lang)
        embed = discord.Embed(
            title=t("bear.editor.edit_title", self.lang),
            description=t(
                "bear.editor.edit_desc",
                self.lang,
                calendar=theme.calendarIcon,
                time_icon=theme.timeIcon,
                announce=theme.announceIcon,
                edit_icon=theme.editListIcon,
                settings_icon=theme.settingsIcon,
                members_icon=theme.membersIcon,
                retry_icon=theme.retryIcon,
                next_date=next_notification_date,
                time=f"{self.hours:02d}:{self.minutes:02d}",
                timezone=self.timezone,
                channel_id=self.channel_id,
                description=self.description,
                notification_type=formatted_type,
                mention=formatted_mention,
                repeat=formatted_repeat
            ),
            color=theme.emColor1,
        )
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Description", style=discord.ButtonStyle.primary, custom_id="description_button")
    async def description_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "EMBED_MESSAGE" in self.description:
            button.label = t("bear.editor.button.edit_embed", self.lang)
            button.emoji = theme.editListIcon
            # await interaction.response.defer()
            try:
                await self.cog.start_edit_process(interaction, self.notification_id, original_message=self.message)
            except Exception as e:
                print(f"error: {e}")
        elif "PLAIN_MESSAGE" in self.description:
            button.label = t("bear.editor.button.description", self.lang)

            class DescriptionModal(discord.ui.Modal, title="Edit Description"):
                def __init__(self, parent_view):
                    super().__init__(title=t("bear.editor.modal.edit_description", parent_view.lang))
                    self.parent_view = parent_view

                    # Extract the existing PLAIN_MESSAGE part if it exists
                    parts = parent_view.description.split("|")
                    plain_message_part = next((p for p in parts if p.startswith("PLAIN_MESSAGE:")), "PLAIN_MESSAGE:")
                    saved_description = plain_message_part.replace("PLAIN_MESSAGE:", "")

                    self.description = discord.ui.TextInput(
                        label=t("bear.editor.label.message", parent_view.lang),
                        placeholder=t("bear.editor.placeholder.message", parent_view.lang),
                        style=discord.TextStyle.paragraph,
                        required=True,
                        default=saved_description,
                        max_length=2000
                    )
                    self.add_item(self.description)

                async def on_submit(self, modal_interaction: discord.Interaction):
                    await modal_interaction.response.defer()

                    # Check for potential @mention misuse and show warning
                    warning = check_mention_placeholder_misuse(self.description.value, lang=self.parent_view.lang)
                    if warning:
                        await modal_interaction.followup.send(warning, ephemeral=True)

                    try:
                        # Preserve CUSTOM_TIMES if it exists
                        parts = self.parent_view.description.split("|")
                        updated_parts = [p for p in parts if not p.startswith("PLAIN_MESSAGE:")]
                        updated_parts.append(
                            f"PLAIN_MESSAGE:{self.description.value}")  # Update only the PLAIN_MESSAGE part

                        self.parent_view.description = "|".join(updated_parts)  # Reassemble

                        await self.parent_view.cog.update_notification(self.parent_view)
                        await self.parent_view.update_embed(modal_interaction)
                    except Exception as e:
                        print(f"Error in DescriptionModal: {e}")
                        await modal_interaction.followup.send(
                            t("bear.editor.modal_error_generic", self.parent_view.lang, icon=theme.deniedIcon),
                            ephemeral=True
                        )

            await interaction.response.send_modal(DescriptionModal(self))

    @discord.ui.button(label="Channel", style=discord.ButtonStyle.primary)
    async def edit_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_select = discord.ui.ChannelSelect(
            placeholder=t("bear.editor.placeholder.channel", self.lang),
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
            min_values=1,
            max_values=1
        )

        async def channel_select_callback(select_interaction: discord.Interaction):
            await select_interaction.response.defer()
            selected_channel_id = select_interaction.data["values"][0]
            self.channel_id = int(selected_channel_id)

            await self.cog.update_notification(self)
            await self.update_embed(select_interaction)

        channel_select.callback = channel_select_callback
        view = discord.ui.View()
        view.add_item(channel_select)

        await interaction.response.send_message(
            t("bear.editor.channel_select", self.lang),
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Time", style=discord.ButtonStyle.primary)
    async def edit_time(self, interaction: discord.Interaction, button: discord.ui.Button):

        class TimeModal(discord.ui.Modal, title="Edit Notification Time"):
            def __init__(self, parent_view):
                super().__init__(title=t("bear.editor.modal.edit_time", parent_view.lang))
                self.parent_view = parent_view
                next_notification_str = parent_view.next_notification.replace("+00:00", "")
                current_dt = datetime.strptime(next_notification_str, "%Y-%m-%dT%H:%M:%S")
                saved_date = current_dt.strftime("%d/%m/%Y")
                saved_hour = str(current_dt.hour)
                saved_minute = str(current_dt.minute)

                self.date = discord.ui.TextInput(
                    label=t("bear.editor.label.date", parent_view.lang),
                    required=True,
                    default=saved_date
                )
                self.hour = discord.ui.TextInput(
                    label=t("bear.editor.label.hour", parent_view.lang),
                    required=True,
                    default=saved_hour
                )
                self.minute = discord.ui.TextInput(
                    label=t("bear.editor.label.minute", parent_view.lang),
                    required=True,
                    default=saved_minute
                )

                self.add_item(self.date)
                self.add_item(self.hour)
                self.add_item(self.minute)

            async def on_submit(self, modal_interaction: discord.Interaction):
                await modal_interaction.response.defer()
                try:
                    new_hours = int(self.hour.value.strip())
                    new_minutes = int(self.minute.value.strip())
                    new_date = self.date.value.strip() if self.date.value else None

                    if not hasattr(self.parent_view, "next_notification"):
                        await modal_interaction.followup.send(
                            t("bear.editor.error_missing_next", self.parent_view.lang, icon=theme.deniedIcon),
                            ephemeral=True
                        )
                        return

                    current_dt = datetime.strptime(self.parent_view.next_notification, "%Y-%m-%dT%H:%M:%S+00:00")
                    new_dt = current_dt.replace(hour=new_hours, minute=new_minutes)

                    if new_date:
                        try:
                            day, month, year = map(int, new_date.split("/"))
                            new_dt = new_dt.replace(day=day, month=month, year=year)
                        except ValueError:
                            await modal_interaction.followup.send(
                                t("bear.editor.error_invalid_date", self.parent_view.lang, icon=theme.deniedIcon),
                                ephemeral=True
                            )
                            return

                    self.parent_view.hours = new_hours
                    self.parent_view.minutes = new_minutes
                    self.parent_view.next_notification = new_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

                    await self.parent_view.cog.update_notification(self.parent_view)
                    await self.parent_view.update_embed(modal_interaction)

                except ValueError:
                    await modal_interaction.followup.send(
                        t("bear.editor.error_numbers_only", self.parent_view.lang, icon=theme.deniedIcon),
                        ephemeral=True
                    )
                except Exception as e:
                    print(f"Error in TimeModal: {e}")
                    await modal_interaction.followup.send(
                        t("bear.editor.modal_error_generic", self.parent_view.lang, icon=theme.deniedIcon),
                        ephemeral=True
                    )

        try:
            await interaction.response.send_modal(TimeModal(self))
        except Exception as e:
            print(f"Error sending modal: {e}")

    @discord.ui.button(label="Repeat", style=discord.ButtonStyle.primary)
    async def edit_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        class RepeatOptionsView(discord.ui.View):
            def __init__(self, parent_view):
                super().__init__(timeout=None)
                self.parent_view = parent_view

                custom_button = discord.ui.Button(
                    label=t("bear.editor.repeat.custom_intervals", parent_view.lang),
                    style=discord.ButtonStyle.secondary
                )
                custom_button.callback = lambda i: send_custom_modal(i, self.parent_view)
                self.add_item(custom_button)

                specific_button = discord.ui.Button(
                    label=t("bear.editor.repeat.specific_days", parent_view.lang),
                    style=discord.ButtonStyle.secondary
                )
                specific_button.callback = lambda i: send_day_selector(i, self.parent_view)
                self.add_item(specific_button)

        async def send_day_selector(interaction: discord.Interaction, parent_view):
            try:
                await interaction.response.defer()

                class DaysView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=None)
                        self.parent_view = parent_view
                        self.selected_days = []

                        self.select = discord.ui.Select(
                            placeholder=t("bear.editor.repeat.select_days", parent_view.lang),
                            min_values=1,
                            max_values=7,
                            options=[
                                discord.SelectOption(label=t("bear.editor.weekday.monday", parent_view.lang), value="Monday"),
                                discord.SelectOption(label=t("bear.editor.weekday.tuesday", parent_view.lang), value="Tuesday"),
                                discord.SelectOption(label=t("bear.editor.weekday.wednesday", parent_view.lang), value="Wednesday"),
                                discord.SelectOption(label=t("bear.editor.weekday.thursday", parent_view.lang), value="Thursday"),
                                discord.SelectOption(label=t("bear.editor.weekday.friday", parent_view.lang), value="Friday"),
                                discord.SelectOption(label=t("bear.editor.weekday.saturday", parent_view.lang), value="Saturday"),
                                discord.SelectOption(label=t("bear.editor.weekday.sunday", parent_view.lang), value="Sunday"),
                            ]
                        )
                        self.select.callback = self.on_select
                        self.add_item(self.select)

                        confirm_button = discord.ui.Button(
                            label=t("bear.editor.confirm", parent_view.lang),
                            style=discord.ButtonStyle.success
                        )
                        confirm_button.callback = self.confirm_days
                        self.add_item(confirm_button)

                    async def on_select(self, interaction: discord.Interaction):
                        self.selected_days = self.select.values
                        await interaction.response.defer()

                    async def confirm_days(self, interaction: discord.Interaction):
                        await interaction.response.defer()

                        if not self.selected_days:
                            await interaction.followup.send(
                                t("bear.editor.repeat.select_one_day", self.parent_view.lang),
                                ephemeral=True
                            )
                            return

                        weekdays_index = {
                            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
                            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
                        }
                        selected_weekdays = [weekdays_index[d] for d in self.selected_days]
                        sorted_days = sorted(selected_weekdays)

                        self.parent_view.repeat = -1
                        self.parent_view.weekdays = "|".join(str(d) for d in sorted_days)

                        await self.parent_view.cog.update_notification(self.parent_view)
                        await self.parent_view.update_embed(interaction)

                await interaction.edit_original_response(
                    content=t("bear.editor.repeat.select_specific", parent_view.lang),
                    view=DaysView()
                )

            except Exception as e:
                print(f"Error in send_day_selector: {e}")

        async def send_custom_modal(interaction: discord.Interaction, parent_view):
            class CustomRepeatModal(discord.ui.Modal, title="Edit Repeat Interval"):
                def __init__(self):
                    super().__init__(title=t("bear.editor.repeat.edit_interval", parent_view.lang))
                    self.parent_view = parent_view
                    self.month = discord.ui.TextInput(label=t("bear.editor.unit.month_plural", parent_view.lang), required=False, default="0")
                    self.week = discord.ui.TextInput(label=t("bear.editor.unit.week_plural", parent_view.lang), required=False, default="0")
                    self.day = discord.ui.TextInput(label=t("bear.editor.unit.day_plural", parent_view.lang), required=False, default="0")
                    self.hour = discord.ui.TextInput(label=t("bear.editor.unit.hour_plural", parent_view.lang), required=False, default="0")
                    self.minute = discord.ui.TextInput(label=t("bear.editor.unit.minute_plural", parent_view.lang), required=False, default="0")
                    self.add_item(self.month)
                    self.add_item(self.week)
                    self.add_item(self.day)
                    self.add_item(self.hour)
                    self.add_item(self.minute)

                async def on_submit(self, modal_interaction: discord.Interaction):
                    await modal_interaction.response.defer()
                    try:
                        repeat_minutes = (
                                int(self.month.value) * 43200 +
                                int(self.week.value) * 10080 +
                                int(self.day.value) * 1440 +
                                int(self.hour.value) * 60 +
                                int(self.minute.value)
                        )

                        self.parent_view.repeat = repeat_minutes

                        await self.parent_view.cog.update_notification(self.parent_view)
                        await self.parent_view.update_embed(modal_interaction)

                    except Exception as e:
                        print(f"Error in CustomRepeatModal: {e}")
                        await modal_interaction.followup.send(
                            t("bear.editor.modal_error_generic", parent_view.lang, icon=theme.deniedIcon),
                            ephemeral=True
                        )

            await interaction.response.send_modal(CustomRepeatModal())

        view = RepeatOptionsView(self)

        await interaction.response.send_message(
            content=t("bear.editor.repeat.choose", self.lang),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="Mention", style=discord.ButtonStyle.primary)
    async def edit_mention(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View()

        async def mention_callback(mention_interaction: discord.Interaction, mention_type: str):
            await mention_interaction.response.defer()

            if mention_type == "everyone":
                self.mention = "everyone"
            elif mention_type == "none":
                self.mention = "none"
            elif mention_type == "role":
                role_select = discord.ui.RoleSelect(
                    placeholder=t("bear.editor.mention.search", self.lang, icon=theme.searchIcon),
                    min_values=1,
                    max_values=1
                )

                async def role_select_callback(select_interaction: discord.Interaction):
                    await select_interaction.response.defer()
                    selected_role_id = select_interaction.data["values"][0]
                    self.mention = f"role_{selected_role_id}"
                    await self.cog.update_notification(self)
                    await self.update_embed(select_interaction)

                role_select.callback = role_select_callback
                role_view = discord.ui.View()
                role_view.add_item(role_select)

                await mention_interaction.followup.send(
                    t("bear.editor.mention.select_role", self.lang),
                    view=role_view,
                    ephemeral=True
                )
                return

            elif mention_type == "member":
                user_select = discord.ui.UserSelect(
                    placeholder=t("bear.editor.mention.search", self.lang, icon=theme.searchIcon),
                    min_values=1,
                    max_values=1
                )

                async def user_select_callback(select_interaction: discord.Interaction):
                    await select_interaction.response.defer()
                    selected_user_id = select_interaction.data["values"][0]
                    self.mention = f"member_{selected_user_id}"
                    await self.cog.update_notification(self)
                    await self.update_embed(select_interaction)

                user_select.callback = user_select_callback
                user_view = discord.ui.View()
                user_view.add_item(user_select)

                await mention_interaction.followup.send(
                    t("bear.editor.mention.select_user", self.lang),
                    view=user_view,
                    ephemeral=True
                )
                return

            # Update the mention type and refresh the embed
            await self.cog.update_notification(self)
            await self.update_embed(mention_interaction)

        # Create buttons for mention types
        for label, mention_type in [
            (t("bear.editor.mention.everyone", self.lang, icon=theme.announceIcon), "everyone"),
            (t("bear.editor.mention.role", self.lang, icon=theme.membersIcon), "role"),
            (t("bear.editor.mention.member", self.lang, icon=theme.userIcon), "member"),
            (t("bear.editor.mention.none", self.lang, icon=theme.muteIcon), "none")
        ]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary)

            async def button_callback(inter: discord.Interaction, t=mention_type):
                await mention_callback(inter, t)

            btn.callback = button_callback
            view.add_item(btn)

        await interaction.response.send_message(
            t("bear.editor.mention.choose", self.lang),
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Notification Ping", style=discord.ButtonStyle.primary)
    async def edit_notification_ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show options for setting when the ping is sent."""
        view = discord.ui.View()

        options = [
            (t("bear.editor.ping.30_10_5", self.lang), 1),
            (t("bear.editor.ping.10_5", self.lang), 2),
            (t("bear.editor.ping.5", self.lang), 3),
            (t("bear.editor.ping.only_5", self.lang), 4),
            (t("bear.editor.ping.only_time", self.lang), 5),
            (t("bear.editor.ping.custom", self.lang), 6),
        ]

        for label, value in options:
            async def callback(interaction: discord.Interaction, value=value):
                self.notification_type = value
                if value == 6:  # Custom Times button pressed
                    class CustomTimeModal(discord.ui.Modal, title="Enter Custom Notification Times"):
                        def __init__(self, parent_view):
                            super().__init__(title=t("bear.editor.ping.custom_title", parent_view.lang))
                            self.parent_view = parent_view
                            self.times_input = discord.ui.TextInput(
                                label=t("bear.editor.ping.custom_label", parent_view.lang),
                                placeholder=t("bear.editor.ping.custom_placeholder", parent_view.lang),
                                required=True
                            )
                            self.add_item(self.times_input)

                        async def on_submit(self, modal_interaction: discord.Interaction):
                            new_times = self.times_input.value.strip()

                            # ✅ Validate format (only numbers and dashes allowed)
                            if not all(c.isdigit() or c == '-' for c in new_times):
                                await modal_interaction.response.send_message(
                                    t("bear.editor.ping.custom_invalid", parent_view.lang, icon=theme.deniedIcon),
                                    ephemeral=True
                                )
                                return

                            # ✅ Check if description contains "CUSTOM_TIMES:"
                            if "CUSTOM_TIMES:" in self.parent_view.description:
                                # Replace existing CUSTOM_TIMES section
                                self.parent_view.description = re.sub(
                                    r"CUSTOM_TIMES:[^\|]+\|", f"CUSTOM_TIMES:{new_times}|", self.parent_view.description
                                )
                            else:
                                # Add CUSTOM_TIMES at the beginning
                                self.parent_view.description = f"CUSTOM_TIMES:{new_times}|{self.parent_view.description}"

                            # ✅ Update notification and embed
                            await self.parent_view.cog.update_notification(self.parent_view)
                            await self.parent_view.update_embed(modal_interaction)
                            await modal_interaction.response.defer()

                    return await interaction.response.send_modal(CustomTimeModal(self))

                await interaction.response.defer()

                # ✅ Remove "CUSTOM_TIMES" if any other option is chosen
                if "CUSTOM_TIMES:" in self.description:
                    self.description = self.description.split("|", 1)[-1]

                await self.cog.update_notification(self)
                await self.update_embed(interaction)

            button = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary)
            button.callback = callback
            view.add_item(button)

        embed = discord.Embed(
            title=t("bear.editor.ping.select_title", self.lang, icon=theme.alarmClockIcon),
            description=t("bear.editor.ping.select_desc", self.lang),
            color=theme.emColor1
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class NotificationEditor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def start_edit_process(self, interaction: discord.Interaction, notification_id: int,
                                 original_message: discord.Message = None):
        lang = _get_lang(interaction)
        # Permission check
        is_admin, _ = PermissionManager.is_admin(interaction.user.id)
        if not is_admin:
            await interaction.response.send_message(
                t("bear.editor.no_permission", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        conn = sqlite3.connect("db/beartime.sqlite")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT channel_id, hour, minute, description, mention_type, repeat_minutes, next_notification, timezone, notification_type, event_type FROM bear_notifications WHERE id = ?",
            (notification_id,))
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message(
                t("bear.editor.notification_id_missing", lang, icon=theme.deniedIcon),
                ephemeral=True
            )
            return

        channel_id, hours, minutes, description, mention, repeat, next_notification, timezone, notification_type, event_type = result
        if "EMBED_MESSAGE" in description:
            cursor.execute(
                "SELECT title, description, color, image_url, thumbnail_url, footer, author, mention_message FROM bear_notification_embeds WHERE notification_id = ?",
                (notification_id,))
            embed_results = cursor.fetchone()
            title, embed_description, color, image_url, thumbnail_url, footer, author, mention_message = embed_results

            view = EmbedDataView(
                self,
                notification_id,
                title,
                embed_description,
                color,
                image_url,
                thumbnail_url,
                footer,
                author,
                mention_message,
                event_type,
                hours,
                minutes,
                next_notification,
                lang=lang
            )

            # Replace variables for initial display
            embed = discord.Embed(
                title=view._replace_variables(title),
                description=view._replace_variables(embed_description),
                color=color,
            )
            if footer:
                embed.set_footer(text=view._replace_variables(footer))
            if author:
                embed.set_author(name=view._replace_variables(author))
            if image_url:
                embed.set_image(url=image_url)
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)

            mention_preview = view._replace_variables(mention_message) if mention_message else ""

            await interaction.response.defer()
            if original_message:
                await original_message.edit(content=mention_preview, embed=embed, view=view)
                message = original_message
            else:
                message = await interaction.followup.send(content=mention_preview, embed=embed, view=view,
                                                          ephemeral=True)

        elif "PLAIN_MESSAGE" in description:
            try:
                view = PlainEditorView(
                    self,
                    notification_id,
                    channel_id,
                    hours,
                    minutes,
                    description,
                    mention,
                    repeat,
                    next_notification,
                    timezone,
                    notification_type,
                    lang=lang
                )

                next_notification_date = datetime.fromisoformat(next_notification).strftime("%d/%m/%Y")
                formatted_repeat = format_repeat_interval(repeat, notification_id, lang=lang)
                formatted_mention = format_mention(mention, lang=lang)
                formatted_type = format_notification_type(notification_type, lang=lang)
                embed = discord.Embed(
                    title=t("bear.editor.edit_title", lang),
                    description=t(
                        "bear.editor.edit_desc",
                        lang,
                        calendar=theme.calendarIcon,
                        time_icon=theme.timeIcon,
                        announce=theme.announceIcon,
                        edit_icon=theme.editListIcon,
                        settings_icon=theme.settingsIcon,
                        members_icon=theme.membersIcon,
                        retry_icon=theme.retryIcon,
                        next_date=next_notification_date,
                        time=f"{hours:02d}:{minutes:02d}",
                        timezone=timezone,
                        channel_id=channel_id,
                        description=description,
                        notification_type=formatted_type,
                        mention=formatted_mention,
                        repeat=formatted_repeat
                    ),
                    color=theme.emColor1,
                )
                await interaction.response.defer()
                message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            except Exception as e:
                print(f"[ERROR] During PLAIN_MESSAGE handling: {e}")
                await interaction.followup.send(
                    t("bear.editor.plain_error", lang, error=str(e)),
                    ephemeral=True
                )
                return
        else:
            print(f"No known format matched, description is {description}")

        view.message = message

    async def update_notification(self, view):
        conn = sqlite3.connect("db/beartime.sqlite")
        cursor = conn.cursor()

        if view.repeat == -1:
            cursor.execute("DELETE FROM notification_days WHERE notification_id = ?", (view.notification_id,))

            weekday = getattr(view, "weekdays", "")
            cursor.execute("INSERT INTO notification_days (notification_id, weekday) VALUES (?, ?)",(view.notification_id, weekday))
        else:
            cursor.execute("DELETE FROM notification_days WHERE notification_id = ?", (view.notification_id,))

        cursor.execute(
            "UPDATE bear_notifications SET channel_id = ?, hour = ?, minute = ?, description = ?, mention_type = ?, repeat_minutes = ?, next_notification = ?, notification_type = ? WHERE id = ?",
            (view.channel_id, view.hours, view.minutes, view.description, view.mention, view.repeat,
             view.next_notification, view.notification_type, view.notification_id)
        )
        conn.commit()

        # Get guild_id for schedule board update
        cursor.execute("SELECT guild_id FROM bear_notifications WHERE id = ?", (view.notification_id,))
        result = cursor.fetchone()
        guild_id = result[0] if result else None

        conn.close()

        # Notify schedule boards of update
        if guild_id:
            schedule_cog = self.bot.get_cog("BearTrapSchedule")
            if schedule_cog:
                await schedule_cog.on_notification_updated(guild_id, view.channel_id)

    async def update_embed_notification(self, view):
        conn = sqlite3.connect("db/beartime.sqlite")
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE bear_notification_embeds SET title = ?, description = ?, color = ?, image_url = ?, thumbnail_url = ?, footer = ?, author = ?, mention_message = ? WHERE notification_id = ?",
            (view.title, view.embed_description, view.color, view.image_url, view.thumbnail_url, view.footer,
             view.author, view.mention_message, view.notification_id)
        )
        conn.commit()

        # Get guild_id and channel_id for schedule board update
        cursor.execute("SELECT guild_id, channel_id FROM bear_notifications WHERE id = ?", (view.notification_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            guild_id, channel_id = result

            # Notify schedule boards of update
            schedule_cog = self.bot.get_cog("BearTrapSchedule")
            if schedule_cog:
                await schedule_cog.on_notification_updated(guild_id, channel_id)

async def setup(bot):
    await bot.add_cog(NotificationEditor(bot))