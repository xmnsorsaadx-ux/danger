import os
import sqlite3
from typing import Dict

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "ar"}

MESSAGES: Dict[str, Dict[str, str]] = {
    "language.settings.title": {
        "en": "Language Settings",
        "ar": "اعدادات اللغة",
    },
    "language.settings.description": {
        "en": "Choose the default language for this server.",
        "ar": "اختر اللغة الافتراضية لهذا السيرفر.",
    },
    "language.current": {
        "en": "Current language: {language}",
        "ar": "اللغة الحالية: {language}",
    },
    "language.english": {"en": "English", "ar": "الانجليزية"},
    "language.arabic": {"en": "Arabic", "ar": "العربية"},
    "language.updated": {
        "en": "Language updated to {language}.",
        "ar": "تم تحديث اللغة الى {language}.",
    },
    "language.guild_required": {
        "en": "This setting can only be changed inside a server.",
        "ar": "يمكن تغيير هذا الاعداد داخل السيرفر فقط.",
    },
    "language.back": {"en": "Back", "ar": "رجوع"},
    "menu.settings.title": {"en": "Settings Menu", "ar": "قائمة الاعدادات"},
    "menu.settings.prompt": {
        "en": "Please select a category:",
        "ar": "يرجى اختيار الفئة:",
    },
    "menu.settings.categories": {
        "en": "Menu Categories",
        "ar": "فئات القائمة",
    },
    "menu.settings.alliance_ops": {
        "en": "Alliance Operations",
        "ar": "عمليات التحالف",
    },
    "menu.settings.alliance_ops_desc": {
        "en": "Manage alliances and settings",
        "ar": "ادارة التحالفات والاعدادات",
    },
    "menu.settings.member_ops": {
        "en": "Alliance Member Operations",
        "ar": "عمليات اعضاء التحالف",
    },
    "menu.settings.member_ops_desc": {
        "en": "Add, remove, and view members",
        "ar": "اضافة الاعضاء وازالتهم وعرضهم",
    },
    "menu.settings.bot_ops": {"en": "Bot Operations", "ar": "عمليات البوت"},
    "menu.settings.bot_ops_desc": {
        "en": "Configure bot settings",
        "ar": "تهيئة اعدادات البوت",
    },
    "menu.settings.gift_ops": {
        "en": "Gift Code Operations",
        "ar": "عمليات اكواد الهدايا",
    },
    "menu.settings.gift_ops_desc": {
        "en": "Manage gift codes and rewards",
        "ar": "ادارة اكواد الهدايا والمكافآت",
    },
    "menu.settings.history": {"en": "Alliance History", "ar": "سجل التحالف"},
    "menu.settings.history_desc": {
        "en": "View alliance changes and history",
        "ar": "عرض تغييرات وسجل التحالف",
    },
    "menu.settings.support": {
        "en": "Support Operations",
        "ar": "عمليات الدعم",
    },
    "menu.settings.support_desc": {
        "en": "Access support features",
        "ar": "الوصول الى ميزات الدعم",
    },
    "menu.settings.theme": {"en": "Theme Settings", "ar": "اعدادات المظهر"},
    "menu.settings.theme_desc": {
        "en": "Customize bot icons and colors",
        "ar": "تخصيص ايقونات والوان البوت",
    },
    "menu.settings.other": {"en": "Other Features", "ar": "ميزات اخرى"},
    "bot.ops.title": {"en": "Bot Operations", "ar": "عمليات البوت"},
    "bot.ops.prompt": {"en": "Please choose an operation:", "ar": "يرجى اختيار عملية:"},
    "bot.ops.available": {"en": "Available Operations", "ar": "العمليات المتاحة"},
    "bot.ops.admin_mgmt": {"en": "Admin Management", "ar": "ادارة المشرفين"},
    "bot.ops.admin_mgmt_desc": {
        "en": "Manage bot administrators",
        "ar": "ادارة مشرفي البوت",
    },
    "bot.ops.admin_perms": {
        "en": "Admin Permissions",
        "ar": "صلاحيات المشرفين",
    },
    "bot.ops.admin_perms_desc": {
        "en": "View and manage admin permissions",
        "ar": "عرض وادارة صلاحيات المشرفين",
    },
    "bot.ops.control_settings": {
        "en": "Control Settings",
        "ar": "اعدادات التحكم",
    },
    "bot.ops.control_settings_desc": {
        "en": "Configure alliance control behaviors",
        "ar": "تهيئة سلوكيات التحكم بالتحالف",
    },
    "bot.ops.updates": {"en": "Bot Updates", "ar": "تحديثات البوت"},
    "bot.ops.updates_desc": {
        "en": "Check and manage updates",
        "ar": "التحقق وادارة التحديثات",
    },
    "bot.ops.language": {"en": "Language", "ar": "اللغة"},
    "bot.ops.language_desc": {
        "en": "Set server language",
        "ar": "تحديد لغة السيرفر",
    },
    "button.add_admin": {"en": "Add Admin", "ar": "اضافة مشرف"},
    "button.remove_admin": {"en": "Remove Admin", "ar": "ازالة مشرف"},
    "button.view_admins": {"en": "View Administrators", "ar": "عرض المشرفين"},
    "button.assign_alliance": {"en": "Assign Alliance to Admin", "ar": "تعيين تحالف لمشرف"},
    "button.delete_admin_permissions": {"en": "Delete Admin Permissions", "ar": "حذف صلاحيات المشرف"},
    "button.transfer_old_db": {"en": "Transfer Old Database", "ar": "نقل قاعدة بيانات قديمة"},
    "button.check_updates": {"en": "Check for Updates", "ar": "التحقق من التحديثات"},
    "button.log_system": {"en": "Log System", "ar": "نظام السجلات"},
    "button.alliance_control_messages": {
        "en": "Alliance Control Messages",
        "ar": "رسائل التحكم بالتحالف",
    },
    "button.control_settings": {"en": "Control Settings", "ar": "اعدادات التحكم"},
    "button.main_menu": {"en": "Main Menu", "ar": "القائمة الرئيسية"},
    "support.menu.title": {"en": "Support Operations", "ar": "عمليات الدعم"},
    "support.menu.prompt": {"en": "Please select an operation:", "ar": "يرجى اختيار عملية:"},
    "support.menu.available": {"en": "Available Operations", "ar": "العمليات المتاحة"},
    "support.menu.request": {"en": "Request Support", "ar": "طلب دعم"},
    "support.menu.request_desc": {"en": "Get help and support", "ar": "الحصول على المساعدة"},
    "support.menu.about": {"en": "About Project", "ar": "حول المشروع"},
    "support.menu.about_desc": {"en": "Project information", "ar": "معلومات المشروع"},
    "support.info.title": {"en": "Bot Support Information", "ar": "معلومات دعم البوت"},
    "support.info.body": {
        "en": "If you need help with the bot, please contact your server administrators.",
        "ar": "اذا احتجت مساعدة مع البوت، يرجى التواصل مع مشرفي السيرفر.",
    },
    "support.about.title": {"en": "About DANGER", "ar": "حول ديـنجر"},
    "support.about.body": {
        "en": "This is an open source Discord bot for Whiteout Survival. It is community-driven and freely available for self-hosting.",
        "ar": "هذا بوت ديسكورد مفتوح المصدر للعبة Whiteout Survival، مدعوم من المجتمع ومتاح للاستضافة الذاتية.",
    },
    "support.about.open_source": {"en": "Open Source Bot", "ar": "بوت مفتوح المصدر"},
    "support.about.features": {"en": "Features", "ar": "الميزات"},
    "support.about.contributing": {"en": "Contributing", "ar": "المساهمة"},
    "support.about.contributing_body": {
        "en": "Contributions are welcome. Please coordinate with the project maintainers.",
        "ar": "المساهمات مرحب بها، يرجى التنسيق مع القائمين على المشروع.",
    },
    "support.about.footer": {
        "en": "Made with {heart} by the DANGER Bot Team.",
        "ar": "صنع بحب {heart} بواسطة فريق ديـنجر.",
    },
    "welcome.title": {"en": "Bot Successfully Activated", "ar": "تم تفعيل البوت بنجاح"},
    "welcome.system_status": {"en": "System Status", "ar": "حالة النظام"},
    "welcome.online": {"en": "Bot is now online and operational", "ar": "البوت الان متصل وجاهز"},
    "welcome.db": {"en": "Database connections established", "ar": "تم الاتصال بقاعدة البيانات"},
    "welcome.commands": {"en": "Command systems initialized", "ar": "تم تهيئة الاوامر"},
    "welcome.control_msgs": {"en": "Alliance Control Messages", "ar": "رسائل التحكم بالتحالف"},
    "welcome.community_title": {"en": "Community & Support", "ar": "المجتمع والدعم"},
    "welcome.community_body": {
        "en": "Support links are not configured yet.",
        "ar": "روابط الدعم غير مهيئة حاليا.",
    },
    "welcome.footer": {
        "en": "Thanks for using the bot! Maintained by the DANGER Bot Team.",
        "ar": "شكرا لاستخدامك البوت! يتم صيانته بواسطة فريق ديـنجر.",
    },
}


def ensure_language_table() -> None:
    os.makedirs("db", exist_ok=True)
    with sqlite3.connect("db/settings.sqlite") as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS language_settings (
                guild_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'en'
            )
            """
        )
        conn.commit()


def get_guild_language(guild_id: int | None) -> str:
    if guild_id is None:
        return DEFAULT_LANGUAGE

    ensure_language_table()
    with sqlite3.connect("db/settings.sqlite") as conn:
        cursor = conn.execute(
            "SELECT language FROM language_settings WHERE guild_id = ?",
            (guild_id,),
        )
        row = cursor.fetchone()

    if row and row[0] in SUPPORTED_LANGUAGES:
        return row[0]

    return DEFAULT_LANGUAGE


def set_guild_language(guild_id: int, language: str) -> str:
    if not guild_id:
        return DEFAULT_LANGUAGE

    ensure_language_table()
    selected = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    with sqlite3.connect("db/settings.sqlite") as conn:
        conn.execute(
            "INSERT OR REPLACE INTO language_settings (guild_id, language) VALUES (?, ?)",
            (guild_id, selected),
        )
        conn.commit()

    return selected


def t(key: str, language: str | None = None, **kwargs: object) -> str:
    lang = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    template = MESSAGES.get(key, {}).get(lang) or MESSAGES.get(key, {}).get(DEFAULT_LANGUAGE) or key
    try:
        return template.format(**kwargs)
    except Exception:
        return template
