# أمثلة استخدام نظام الترجمة | Translation System Examples

## 📌 جدول المحتويات | Table of Contents

1. [أمثلة بسيطة | Basic Examples](#basic-examples)
2. [الترجمة في Commands](#translation-in-commands)
3. [الترجمة في Embeds](#translation-in-embeds)
4. [الترجمة في Views/Buttons](#translation-in-views)
5. [الترجمة المتقدمة | Advanced Translation](#advanced-translation)

---

## <a name="basic-examples"></a>أمثلة بسيطة | Basic Examples

### مثال 1: ترجمة نص بسيط
**Example 1: Simple Text Translation**

```python
from i18n import t

# الإنجليزية | English
text_en = t("menu.settings.title", "en")
print(text_en)  # Output: "Settings Menu"

# العربية | Arabic
text_ar = t("menu.settings.title", "ar")
print(text_ar)  # Output: "قائمة الاعدادات"
```

### مثال 2: ترجمة مع معامل واحد
**Example 2: Translation with Single Parameter**

```python
from i18n import t

# الإنجليزية | English
msg_en = t("language.current", "en", language="English")
print(msg_en)  # Output: "Current language: English"

# العربية | Arabic
msg_ar = t("language.current", "ar", language="العربية")
print(msg_ar)  # Output: "اللغة الحالية: العربية"
```

### مثال 3: ترجمة مع معاملات متعددة
**Example 3: Translation with Multiple Parameters**

```python
from i18n import t

# الإنجليزية | English
msg_en = t("alliance.member.add.progress_desc", "en", 
          count=10, alliance="FireStorm", current=5, total=10)
print(msg_en)  
# Output: "Adding 10 members to FireStorm (5/10)."

# العربية | Arabic
msg_ar = t("alliance.member.add.progress_desc", "ar",
          count=10, alliance="FireStorm", current=5, total=10)
print(msg_ar)
# Output: "جار اضافة 10 عضو الى FireStorm (5/10)."
```

---

## <a name="translation-in-commands"></a>الترجمة في Commands

### مثال 4: Command بسيط مع ترجمة
**Example 4: Simple Command with Translation**

```python
import discord
from discord import app_commands
from discord.ext import commands
from i18n import t, get_guild_language


class MyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="info", description="Show bot information")
    async def info_command(self, interaction: discord.Interaction):
        # الحصول على لغة السيرفر
        # Get guild language
        lang = get_guild_language(interaction.guild_id)
        
        # الترجمة
        # Translation
        title = t("support.info.title", lang)
        body = t("support.info.body", lang)
        
        # إنشاء Embed
        # Create Embed
        embed = discord.Embed(
            title=title,
            description=body,
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(MyCommands(bot))
```

### مثال 5: Command مع خيارات مترجمة
**Example 5: Command with Translated Options**

```python
import discord
from discord import app_commands
from discord.ext import commands
from i18n import t, get_guild_language


class AllianceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="alliance", description="Alliance operations")
    @app_commands.describe(
        action="Choose an action",
        member_count="Number of members"
    )
    async def alliance_command(
        self, 
        interaction: discord.Interaction,
        action: str,
        member_count: int = 0
    ):
        lang = get_guild_language(interaction.guild_id)
        
        if action == "add":
            # ترجمة رسالة النجاح
            # Translate success message
            message = t("alliance.member.add.success_body", lang, count=member_count)
            await interaction.response.send_message(message)
        
        elif action == "view":
            # ترجمة عنوان القائمة
            # Translate list title
            title = t("alliance.member.view.list_title", lang, alliance="MyAlliance")
            await interaction.response.send_message(title)


async def setup(bot):
    await bot.add_cog(AllianceCommands(bot))
```

---

## <a name="translation-in-embeds"></a>الترجمة في Embeds

### مثال 6: Embed كامل مترجم
**Example 6: Fully Translated Embed**

```python
import discord
from i18n import t, get_guild_language


async def send_welcome_embed(channel, guild_id):
    """إرسال رسالة ترحيب مترجمة | Send translated welcome message"""
    
    lang = get_guild_language(guild_id)
    
    # ترجمة جميع عناصر Embed
    # Translate all Embed elements
    embed = discord.Embed(
        title=t("welcome.title", lang),
        description=t("welcome.system_status", lang),
        color=0x00ff00
    )
    
    # إضافة حقول مترجمة
    # Add translated fields
    embed.add_field(
        name=t("welcome.online", lang),
        value="✅",
        inline=True
    )
    
    embed.add_field(
        name=t("welcome.db", lang),
        value="✅",
        inline=True
    )
    
    embed.add_field(
        name=t("welcome.commands", lang),
        value="✅",
        inline=True
    )
    
    # Footer مترجم
    # Translated footer
    embed.set_footer(text=t("welcome.footer", lang, heart="❤️"))
    
    await channel.send(embed=embed)
```

### مثال 7: Embed ديناميكي مع بيانات
**Example 7: Dynamic Embed with Data**

```python
import discord
from i18n import t, get_guild_language


async def send_stats_embed(interaction, alliance_data):
    """إرسال إحصائيات مترجمة | Send translated statistics"""
    
    lang = get_guild_language(interaction.guild_id)
    
    embed = discord.Embed(
        title=t("alliance.member.stats.title", lang),
        color=discord.Color.gold()
    )
    
    # إحصائيات مترجمة
    # Translated statistics
    total = t("alliance.member.stats.total_members", lang)
    highest = t("alliance.member.stats.highest_level", lang)
    average = t("alliance.member.stats.avg_level", lang)
    
    embed.add_field(name=total, value=str(alliance_data['total']), inline=False)
    embed.add_field(name=highest, value=str(alliance_data['highest']), inline=True)
    embed.add_field(name=average, value=f"{alliance_data['average']:.1f}", inline=True)
    
    await interaction.response.send_message(embed=embed)
```

---

## <a name="translation-in-views"></a>الترجمة في Views/Buttons

### مثال 8: View مع أزرار مترجمة
**Example 8: View with Translated Buttons**

```python
import discord
from discord.ui import View, Button
from i18n import t, get_guild_language


class ConfirmView(View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.lang = get_guild_language(guild_id)
        self.value = None
        
        # إضافة أزرار مترجمة
        # Add translated buttons
        self.add_item(Button(
            label=t("alliance.member.common.confirm", self.lang),
            style=discord.ButtonStyle.green,
            custom_id="confirm"
        ))
        
        self.add_item(Button(
            label=t("alliance.member.common.cancel", self.lang),
            style=discord.ButtonStyle.red,
            custom_id="cancel"
        ))


# الاستخدام | Usage
async def confirm_action(interaction):
    lang = get_guild_language(interaction.guild_id)
    
    # رسالة التأكيد المترجمة
    # Translated confirmation message
    message = t("alliance.member.remove.confirm_body", lang, count=5)
    
    view = ConfirmView(interaction.guild_id)
    await interaction.response.send_message(message, view=view, ephemeral=True)
```

### مثال 9: Select Menu مترجم
**Example 9: Translated Select Menu**

```python
import discord
from discord.ui import View, Select
from i18n import t, get_guild_language


class LanguageSelect(View):
    def __init__(self, guild_id):
        super().__init__(timeout=30)
        self.lang = get_guild_language(guild_id)
        
        # قائمة منسدلة مترجمة
        # Translated select menu
        select = Select(
            placeholder=t("language.settings.description", self.lang),
            options=[
                discord.SelectOption(
                    label=t("language.english", self.lang),
                    value="en",
                    emoji="🇬🇧"
                ),
                discord.SelectOption(
                    label=t("language.arabic", self.lang),
                    value="ar",
                    emoji="🇸🇦"
                )
            ]
        )
        
        select.callback = self.language_callback
        self.add_item(select)
    
    async def language_callback(self, interaction: discord.Interaction):
        selected_lang = interaction.data['values'][0]
        
        # تحديث اللغة
        # Update language
        from i18n import set_guild_language
        set_guild_language(interaction.guild_id, selected_lang)
        
        # رسالة نجاح مترجمة
        # Translated success message
        lang_name = t(f"language.{selected_lang if selected_lang == 'english' else 'arabic'}", selected_lang)
        message = t("language.updated", selected_lang, language=lang_name)
        
        await interaction.response.send_message(message, ephemeral=True)


# الاستخدام | Usage
async def show_language_menu(interaction):
    view = LanguageSelect(interaction.guild_id)
    
    lang = get_guild_language(interaction.guild_id)
    title = t("language.settings.title", lang)
    
    await interaction.response.send_message(title, view=view)
```

---

## <a name="advanced-translation"></a>الترجمة المتقدمة | Advanced Translation

### مثال 10: ترجمة قوائم ديناميكية
**Example 10: Dynamic List Translation**

```python
from i18n import t, get_guild_language


def translate_member_list(members, guild_id):
    """ترجمة قائمة أعضاء | Translate member list"""
    
    lang = get_guild_language(guild_id)
    
    # عنوان القائمة
    # List header
    header = t("alliance.member.view.list_header", lang)
    
    # ترجمة كل عضو
    # Translate each member
    lines = [header]
    for member in members:
        line = t("changes.recent.member_line", lang, 
                name=member['name'], 
                fid=member['id'])
        lines.append(f"• {line}")
    
    # إضافة تذييل
    # Add footer
    total = t("alliance.member.stats.total_members", lang)
    lines.append(f"\n{total}: {len(members)}")
    
    return "\n".join(lines)


# الاستخدام | Usage
members = [
    {'name': 'Player1', 'id': 123456},
    {'name': 'Player2', 'id': 789012}
]

text = translate_member_list(members, guild_id=123)
print(text)
```

### مثال 11: ترجمة رسائل الأخطاء
**Example 11: Error Message Translation**

```python
import discord
from i18n import t, get_guild_language


class TranslatedError(Exception):
    """خطأ مخصص مع دعم الترجمة | Custom error with translation support"""
    
    def __init__(self, key, lang="en", **kwargs):
        self.key = key
        self.lang = lang
        self.kwargs = kwargs
        self.message = t(key, lang, **kwargs)
        super().__init__(self.message)


async def handle_command_error(interaction, error):
    """معالج أخطاء مترجم | Translated error handler"""
    
    lang = get_guild_language(interaction.guild_id)
    
    if isinstance(error, TranslatedError):
        # الخطأ مترجم بالفعل
        # Error already translated
        message = error.message
    
    elif isinstance(error, discord.errors.Forbidden):
        # ترجمة خطأ الصلاحيات
        # Translate permission error
        message = t("alliance.member.error.no_authorized_alliance", lang)
    
    elif isinstance(error, ValueError):
        # ترجمة خطأ القيمة
        # Translate value error
        message = t("alliance.member.common.invalid", lang)
    
    else:
        # خطأ عام
        # Generic error
        message = t("other.features.error.generic", lang)
    
    # إرسال رسالة الخطأ
    # Send error message
    embed = discord.Embed(
        title=t("alliance.member.common.error_title", lang),
        description=message,
        color=discord.Color.red()
    )
    
    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        await interaction.followup.send(embed=embed, ephemeral=True)


# الاستخدام | Usage
try:
    # عملية قد تفشل
    # Operation that might fail
    if not user_has_permission:
        raise TranslatedError("alliance.member.error.no_permission", lang)
except TranslatedError as e:
    await handle_command_error(interaction, e)
```

### مثال 12: ترجمة مع شروط
**Example 12: Conditional Translation**

```python
from i18n import t, get_guild_language


def get_status_message(status, count, guild_id):
    """الحصول على رسالة حالة مترجمة حسب العدد | Get translated status based on count"""
    
    lang = get_guild_language(guild_id)
    
    # اختيار مفتاح الترجمة حسب العدد
    # Choose translation key based on count
    if count == 0:
        key = "alliance.member.view.error_display"
    elif count == 1:
        key = "alliance.member.remove.success_title"
    else:
        key = "alliance.member.add.completed_body"
    
    return t(key, lang, count=count)


# استخدام | Usage
message_0 = get_status_message("success", 0, guild_id=123)
message_1 = get_status_message("success", 1, guild_id=123)
message_many = get_status_message("success", 10, guild_id=123)
```

### مثال 13: ترجمة تقدم العمليات
**Example 13: Progress Operation Translation**

```python
import discord
import asyncio
from i18n import t, get_guild_language


async def process_members_with_progress(interaction, members):
    """معالجة أعضاء مع عرض التقدم المترجم | Process members with translated progress"""
    
    lang = get_guild_language(interaction.guild_id)
    total = len(members)
    
    # رسالة البداية
    # Initial message
    title = t("alliance.member.add.progress_title", lang)
    embed = discord.Embed(title=title, color=discord.Color.blue())
    
    message = await interaction.followup.send(embed=embed)
    
    # معالجة كل عضو
    # Process each member
    for current, member in enumerate(members, 1):
        # تحديث الرسالة
        # Update message
        desc = t("alliance.member.add.progress_desc_short", lang,
                count=total, current=current, total=total)
        
        embed.description = desc
        embed.set_footer(text=f"{current}/{total}")
        
        await message.edit(embed=embed)
        await asyncio.sleep(0.5)  # محاكاة العملية | Simulate processing
    
    # رسالة الاكتمال
    # Completion message
    complete_title = t("alliance.member.add.completed_title", lang)
    complete_body = t("alliance.member.add.completed_body", lang, count=total)
    
    embed.title = complete_title
    embed.description = complete_body
    embed.color = discord.Color.green()
    
    await message.edit(embed=embed)
```

---

## 💡 نصائح إضافية | Additional Tips

### نصيحة 1: احفظ اللغة في Context
**Tip 1: Cache Language in Context**

```python
class MyView(View):
    def __init__(self, interaction):
        super().__init__()
        # حفظ اللغة مرة واحدة
        # Cache language once
        self.lang = get_guild_language(interaction.guild_id)
        self.interaction = interaction
    
    def t(self, key, **kwargs):
        """اختصار للترجمة | Translation shortcut"""
        return t(key, self.lang, **kwargs)
    
    async def some_button_callback(self, interaction):
        # استخدام مباشر
        # Direct usage
        message = self.t("button.clicked")
        await interaction.response.send_message(message)
```

### نصيحة 2: استخدم ملف ثوابت للمفاتيح
**Tip 2: Use Constants File for Keys**

```python
# translation_keys.py
class Keys:
    """ثوابت مفاتيح الترجمة | Translation key constants"""
    
    # Menu
    MENU_TITLE = "menu.settings.title"
    MENU_PROMPT = "menu.settings.prompt"
    
    # Alliance
    ALLIANCE_ADD_SUCCESS = "alliance.member.add.success_body"
    ALLIANCE_REMOVE_CONFIRM = "alliance.member.remove.confirm_body"
    
    # Errors
    ERROR_GENERIC = "other.features.error.generic"
    ERROR_NO_PERMISSION = "alliance.member.error.no_permission"


# الاستخدام | Usage
from translation_keys import Keys
from i18n import t

message = t(Keys.MENU_TITLE, lang)
```

### نصيحة 3: دالة مساعدة للترجمة السريعة
**Tip 3: Helper Function for Quick Translation**

```python
from functools import lru_cache
from i18n import t, get_guild_language


class Translator:
    """مترجم بسيط مع ذاكرة تخزين مؤقت | Simple translator with cache"""
    
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.lang = get_guild_language(guild_id)
    
    def __call__(self, key, **kwargs):
        """استدعاء مباشر للترجمة | Direct translation call"""
        return t(key, self.lang, **kwargs)
    
    @property
    def is_arabic(self):
        """هل اللغة عربية؟ | Is language Arabic?"""
        return self.lang == "ar"
    
    @property
    def is_english(self):
        """هل اللغة إنجليزية؟ | Is language English?"""
        return self.lang == "en"


# الاستخدام | Usage
async def my_command(interaction):
    tr = Translator(interaction.guild_id)
    
    title = tr("menu.settings.title")
    desc = tr("alliance.member.add.success_body", count=10)
    
    if tr.is_arabic:
        # منطق خاص بالعربية
        # Arabic-specific logic
        pass
```

---

**الملف الكامل متاح في:** [GitHub Repository](https://github.com/yourusername/danger)

**للمزيد من المساعدة:** راجع [دليل i18n](./i18n_guide.md)
