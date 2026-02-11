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
    "alliance.operations.title": {
        "en": "Alliance Operations",
        "ar": "عمليات التحالف",
    },
    "alliance.operations.prompt": {
        "en": "Please select an operation:",
        "ar": "يرجى اختيار العملية:",
    },
    "alliance.operations.available": {
        "en": "Available Operations",
        "ar": "العمليات المتاحة",
    },
    "alliance.operations.add": {
        "en": "Add Alliance",
        "ar": "إضافة تحالف",
    },
    "alliance.operations.add_desc": {
        "en": "Create a new alliance",
        "ar": "إنشاء تحالف جديد",
    },
    "alliance.operations.edit": {
        "en": "Edit Alliance",
        "ar": "تعديل تحالف",
    },
    "alliance.operations.edit_desc": {
        "en": "Modify existing alliance settings",
        "ar": "تعديل اعدادات التحالف الموجود",
    },
    "alliance.operations.delete": {
        "en": "Delete Alliance",
        "ar": "حذف تحالف",
    },
    "alliance.operations.delete_desc": {
        "en": "Remove an existing alliance",
        "ar": "إزالة تحالف موجود",
    },
    "alliance.operations.view": {
        "en": "View Alliances",
        "ar": "عرض التحالفات",
    },
    "alliance.operations.view_desc": {
        "en": "List all available alliances",
        "ar": "عرض جميع التحالفات المتاحة",
    },
    "alliance.operations.check": {
        "en": "Check Alliance",
        "ar": "فحص تحالف",
    },
    "alliance.operations.check_desc": {
        "en": "Check alliance status",
        "ar": "فحص حالة التحالف",
    },
    "common.main_menu": {
        "en": "Main Menu",
        "ar": "القائمة الرئيسية",
    },
    "common.confirm": {
        "en": "Confirm",
        "ar": "تأكيد",
    },
    "common.cancel": {
        "en": "Cancel",
        "ar": "إلغاء",
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
    "menu.settings.language": {"en": "Language", "ar": "اللغة"},
    "menu.settings.language_desc": {
        "en": "Change bot language",
        "ar": "تغيير لغة البوت",
    },
    "menu.settings.other": {"en": "Other Features", "ar": "ميزات اخرى"},
    "other.features.title": {
        "en": "Other Features",
        "ar": "ميزات اخرى",
    },
    "other.features.description": {
        "en": "This section was created according to users' requests:",
        "ar": "تمت اضافة هذا القسم بناء على طلبات المستخدمين:",
    },
    "other.features.available": {
        "en": "Available Operations",
        "ar": "العمليات المتاحة",
    },
    "other.features.notification.title": {
        "en": "Notification System",
        "ar": "نظام الاشعارات",
    },
    "other.features.notification.desc1": {
        "en": "Event notification system",
        "ar": "نظام اشعارات الاحداث",
    },
    "other.features.notification.desc2": {
        "en": "Not just for Bear! Use it for any event:",
        "ar": "ليس للدب فقط! استخدمه لاي حدث:",
    },
    "other.features.notification.desc3": {
        "en": "Bear - KE - Frostfire - CJ and everything else",
        "ar": "Bear - KE - Frostfire - CJ وغيرها",
    },
    "other.features.notification.desc4": {
        "en": "Add unlimited notifications",
        "ar": "اضف اشعارات بلا حدود",
    },
    "other.features.id_channel.title": {
        "en": "ID Channel",
        "ar": "قناة المعرف",
    },
    "other.features.id_channel.desc1": {
        "en": "Create and manage ID channels",
        "ar": "انشاء وادارة قنوات المعرفات",
    },
    "other.features.id_channel.desc2": {
        "en": "Automatic ID verification system",
        "ar": "نظام تحقق تلقائي للمعرفات",
    },
    "other.features.id_channel.desc3": {
        "en": "Custom channel settings",
        "ar": "اعدادات مخصصة للقناة",
    },
    "other.features.registration.title": {
        "en": "Registration System",
        "ar": "نظام التسجيل",
    },
    "other.features.registration.desc1": {
        "en": "Enable/disable user self-registration (Global Admin only)",
        "ar": "تفعيل/تعطيل التسجيل الذاتي (مشرف عام فقط)",
    },
    "other.features.registration.desc2": {
        "en": "Users can /register to add themselves based on ID",
        "ar": "يمكن للمستخدمين /register لاضافة انفسهم حسب المعرف",
    },
    "other.features.attendance.title": {
        "en": "Attendance System",
        "ar": "نظام الحضور",
    },
    "other.features.attendance.desc1": {
        "en": "Manage event attendance records",
        "ar": "ادارة سجلات حضور الاحداث",
    },
    "other.features.attendance.desc2": {
        "en": "View detailed attendance reports",
        "ar": "عرض تقارير الحضور التفصيلية",
    },
    "other.features.attendance.desc3": {
        "en": "Export attendance data to CSV, TSV, HTML",
        "ar": "تصدير بيانات الحضور بصيغ CSV و TSV و HTML",
    },
    "other.features.minister.title": {
        "en": "Minister Scheduling",
        "ar": "جدولة الوزراء",
    },
    "other.features.minister.desc1": {
        "en": "Manage your state minister appointments",
        "ar": "ادارة تعيينات وزراء الولاية",
    },
    "other.features.minister.desc2": {
        "en": "Schedule Construction, Research, Training days",
        "ar": "جدولة ايام البناء والبحث والتدريب",
    },
    "other.features.minister.desc3": {
        "en": "Configure minister log channels",
        "ar": "تهيئة قنوات سجل الوزراء",
    },
    "other.features.backup.title": {
        "en": "Backup System",
        "ar": "نظام النسخ الاحتياطي",
    },
    "other.features.backup.desc1": {
        "en": "Automatic database backup",
        "ar": "نسخ احتياطي تلقائي لقاعدة البيانات",
    },
    "other.features.backup.desc2": {
        "en": "Send backups to your DMs",
        "ar": "ارسال النسخ الاحتياطية الى الخاص",
    },
    "other.features.backup.desc3": {
        "en": "Only for Global Admin",
        "ar": "للمشرف العام فقط",
    },
    "other.features.main_menu": {
        "en": "Main Menu",
        "ar": "القائمة الرئيسية",
    },
    "other.features.module.notification": {
        "en": "Notification System",
        "ar": "نظام الاشعارات",
    },
    "other.features.module.id_channel": {
        "en": "ID Channel",
        "ar": "قناة المعرف",
    },
    "other.features.module.minister": {
        "en": "Minister Scheduling",
        "ar": "جدولة الوزراء",
    },
    "other.features.module.backup": {
        "en": "Backup System",
        "ar": "نظام النسخ الاحتياطي",
    },
    "other.features.module.registration": {
        "en": "Registration System",
        "ar": "نظام التسجيل",
    },
    "other.features.module.attendance": {
        "en": "Attendance System",
        "ar": "نظام الحضور",
    },
    "minister.channel.select_placeholder": {
        "en": "Select a channel",
        "ar": "اختر قناة",
    },
    "minister.channel.setup_title": {
        "en": "Minister Channel Setup",
        "ar": "اعدادات قناة الوزراء",
    },
    "minister.channel.setup_desc": {
        "en": "Channel saved for {context}: <#{channel_id}>\n\n{settings_icon} Settings | {search_icon} Search | {alliance_icon} Alliance | {document_icon} Documents",
        "ar": "تم حفظ القناة لـ {context}: <#{channel_id}>\n\n{settings_icon} الاعدادات | {search_icon} بحث | {alliance_icon} التحالف | {document_icon} مستندات",
    },
    "minister.channel.set_success": {
        "en": "{icon} Channel set for {context}: <#{channel_id}>",
        "ar": "{icon} تم تعيين القناة لـ {context}: <#{channel_id}>",
    },
    "minister.channel.update_failed": {
        "en": "{icon} Failed to update channel: {error}",
        "ar": "{icon} فشل تحديث القناة: {error}",
    },
    "minister.error.no_permission": {
        "en": "You do not have permission to use this command.",
        "ar": "ليس لديك صلاحية لاستخدام هذا الامر.",
    },
    "minister.error.log_guild_missing": {
        "en": "Could not find the minister log guild. Make sure the bot is in that server.\n\nIf issue persists, run the `/settings` command --> Other Features --> Minister Scheduling --> Delete Server ID and try again in the desired server",
        "ar": "تعذر العثور على سيرفر سجل الوزراء. تاكد من وجود البوت في ذلك السيرفر.\n\nاذا استمرت المشكلة، شغل الامر `/settings` --> Other Features --> Minister Scheduling --> Delete Server ID ثم حاول مرة اخرى في السيرفر المطلوب",
    },
    "minister.error.channels_missing": {
        "en": "Minister channels or log channel are missing. This command must be run in the server:`{guild}` to configure missing channels.\n\nIf you want to change that to another server, run `/settings` --> Other Features --> Minister Scheduling --> Delete Server ID and try again in the desired server",
        "ar": "قنوات الوزراء او قناة السجل مفقودة. يجب تشغيل هذا الامر داخل السيرفر:`{guild}` لتهيئة القنوات الناقصة.\n\nاذا تريد تغيير ذلك لسيرفر اخر، شغل `/settings` --> Other Features --> Minister Scheduling --> Delete Server ID ثم حاول مرة اخرى في السيرفر المطلوب",
    },
    "minister.channel.select_for_type": {
        "en": "Please select a channel to use for `{appointment_type}` notifications:",
        "ar": "يرجى اختيار قناة لاشعارات `{appointment_type}`:",
    },
    "minister.channel.select_log": {
        "en": "Please select a log channel to use:",
        "ar": "يرجى اختيار قناة السجل:",
    },
    "minister.channel.select_failed": {
        "en": "Could not select the channel: {error}",
        "ar": "تعذر اختيار القناة: {error}",
    },
    "minister.time.invalid_format": {
        "en": "Invalid time format. Please use HH:MM (e.g., 08:00, 14:30).",
        "ar": "صيغة الوقت غير صحيحة. استخدم HH:MM (مثال 08:00، 14:30).",
    },
    "minister.time.invalid_standard": {
        "en": "Invalid time. In Standard mode, appointments can only be booked at :00 or :30 (e.g., 08:00, 08:30).",
        "ar": "وقت غير صحيح. في الوضع القياسي يمكن الحجز عند :00 او :30 فقط (مثال 08:00، 08:30).",
    },
    "minister.time.invalid_offset": {
        "en": "Invalid time. In Offset mode, appointments can only be booked at :00, :15, or :45 (e.g., 08:00, 08:15, 08:45).",
        "ar": "وقت غير صحيح. في وضع الازاحة يمكن الحجز عند :00 او :15 او :45 فقط (مثال 08:00، 08:15، 08:45).",
    },
    "minister.time.invalid_slot": {
        "en": "Invalid time slot `{time}` for current slot mode.",
        "ar": "وقت غير صالح `{time}` للوضع الحالي.",
    },
    "minister.user.not_registered": {
        "en": "This ID {fid} is not registered.",
        "ar": "المعرف {fid} غير مسجل.",
    },
    "minister.user.alliance_not_found": {
        "en": "Alliance not found for this user.",
        "ar": "لم يتم العثور على تحالف لهذا المستخدم.",
    },
    "minister.booking.already": {
        "en": "{nickname} already has an appointment for {appointment_type} at {time}.",
        "ar": "لدى {nickname} موعد مسبق لـ {appointment_type} في {time}.",
    },
    "minister.booking.taken": {
        "en": "The time {time} for {appointment_type} is already taken by {nickname}.",
        "ar": "الوقت {time} لـ {appointment_type} محجوز بالفعل من {nickname}.",
    },
    "minister.embed.add_title": {
        "en": "Player added to {appointment_type}",
        "ar": "تمت اضافة لاعب الى {appointment_type}",
    },
    "minister.embed.add_description": {
        "en": "{nickname} ({fid}) from **{alliance_name}** at {time}",
        "ar": "{nickname} ({fid}) من **{alliance_name}** في {time}",
    },
    "minister.embed.add_author": {
        "en": "Added by {user}",
        "ar": "تمت الاضافة بواسطة {user}",
    },
    "minister.booking.added_short": {
        "en": "Added {nickname} to {time}",
        "ar": "تمت اضافة {nickname} الى {time}",
    },
    "minister.list.slots": {
        "en": "**{appointment_type}** slots:",
        "ar": "**{appointment_type}** المواعيد:",
    },
    "minister.list.booked": {
        "en": "**{appointment_type}** booked slots:",
        "ar": "**{appointment_type}** المواعيد المحجوزة:",
    },
    "minister.list.available": {
        "en": "**{appointment_type}** available slots:",
        "ar": "**{appointment_type}** المواعيد المتاحة:",
    },
    "minister.list.full": {
        "en": "All appointment slots are filled for {appointment_type}",
        "ar": "جميع المواعيد ممتلئة لـ {appointment_type}",
    },
    "minister.error.unexpected": {
        "en": "An unexpected error occurred while processing the request: {error}",
        "ar": "حدث خطا غير متوقع اثناء معالجة الطلب: {error}",
    },
    "minister.booking.not_listed": {
        "en": "{nickname} is not on the minister list for {appointment_type}.",
        "ar": "{nickname} ليس ضمن قائمة الوزراء لـ {appointment_type}.",
    },
    "minister.booking.removed_short": {
        "en": "Removed {nickname}",
        "ar": "تمت ازالة {nickname}",
    },
    "minister.error.cancel_failed": {
        "en": "An error occurred while canceling the slot: {error}",
        "ar": "حدث خطا اثناء الغاء الموعد: {error}",
    },
    "minister.embed.remove_title": {
        "en": "Player removed from {appointment_type}",
        "ar": "تمت ازالة لاعب من {appointment_type}",
    },
    "minister.embed.remove_description": {
        "en": "{nickname} ({fid})",
        "ar": "{nickname} ({fid})",
    },
    "minister.embed.remove_author": {
        "en": "Removed by {user}",
        "ar": "تمت الازالة بواسطة {user}",
    },
    "minister.clear.log_channel_missing": {
        "en": "[Warning] Could not find a log channel. Log channel is needed before clearing the appointment\n\nRun the `/settings` command --> Other Features --> Minister Scheduling --> Channel Setup and choose a log channel",
        "ar": "[تحذير] تعذر العثور على قناة السجل. قناة السجل مطلوبة قبل مسح المواعيد\n\nشغل الامر `/settings` --> Other Features --> Minister Scheduling --> Channel Setup واختر قناة السجل",
    },
    "minister.clear.confirm_title": {
        "en": "{icon} Confirm clearing {appointment_type} list.",
        "ar": "{icon} تاكيد مسح قائمة {appointment_type}.",
    },
    "minister.clear.confirm_desc": {
        "en": "Are you sure you want to remove all minister appointment slots for: {appointment_type}?\n**{icon} This action cannot be undone and all names will be removed {icon}**.\nYou have 10 seconds to reply with 'Yes' to confirm or 'No' to cancel.",
        "ar": "هل انت متاكد من حذف جميع مواعيد الوزراء لـ {appointment_type}?\n**{icon} هذا الاجراء لا يمكن التراجع عنه وسيتم حذف جميع الاسماء {icon}**.\nلديك 10 ثوان للرد بـ 'Yes' للتاكيد او 'No' للالغاء.",
    },
    "minister.clear.previous_header": {
        "en": "**Previous {appointment_type} schedule** (before clearing):",
        "ar": "**جدول {appointment_type} السابق** (قبل المسح):",
    },
    "minister.clear.cleared_title": {
        "en": "Cleared {appointment_type}",
        "ar": "تم مسح {appointment_type}",
    },
    "minister.clear.cleared_title_continued": {
        "en": "Cleared {appointment_type} (continued)",
        "ar": "تم مسح {appointment_type} (متابعة)",
    },
    "minister.clear.message_missing": {
        "en": "[Warning] Could not find message or channel for {appointment_type}, skipping message update.\n\nNext time you run the `/minister_add` command that channel will be used",
        "ar": "[تحذير] تعذر العثور على الرسالة او القناة لـ {appointment_type}، سيتم تخطي التحديث.\n\nعند تشغيل `/minister_add` لاحقا سيتم استخدام تلك القناة",
    },
    "minister.clear.success_title": {
        "en": "Cleared {appointment_type} list",
        "ar": "تم مسح قائمة {appointment_type}",
    },
    "minister.clear.success_desc": {
        "en": "All appointments for {appointment_type} have been successfully removed.",
        "ar": "تم حذف جميع مواعيد {appointment_type} بنجاح.",
    },
    "minister.clear.success_author": {
        "en": "Cleared by {user}",
        "ar": "تم المسح بواسطة {user}",
    },
    "minister.clear.success_message": {
        "en": "{icon} Deleted all {appointment_type} appointments.",
        "ar": "{icon} تم حذف جميع مواعيد {appointment_type}.",
    },
    "minister.clear.cancelled": {
        "en": "Cancelled the action. Nothing was removed from {appointment_type}.",
        "ar": "تم الغاء العملية. لم يتم حذف اي شيء من {appointment_type}.",
    },
    "minister.clear.timeout": {
        "en": "Time ran out. Run the command again if you want to clear the appointment",
        "ar": "انتهى الوقت. شغل الامر مرة اخرى اذا كنت تريد المسح",
    },
    "minister.clear.timeout_user": {
        "en": "<@{user_id}> did not respond in time. The action has been cancelled.",
        "ar": "<@{user_id}> لم يرد في الوقت المحدد. تم الغاء العملية.",
    },
    "minister.clear.error": {
        "en": "An error occurred while clearing the appointments: {error}",
        "ar": "حدث خطا اثناء مسح المواعيد: {error}",
    },
    "minister.list.waiting": {
        "en": "waiting 60 seconds before continuing",
        "ar": "انتظار 60 ثانية قبل المتابعة",
    },
    "minister.list.updating": {
        "en": "Updating names",
        "ar": "تحديث الاسماء",
    },
    "minister.list.progress": {
        "en": "Checked {checked}/{total} minister appointees",
        "ar": "تم فحص {checked}/{total} من المواعيد",
    },
    "minister.list.schedule_title": {
        "en": "Schedule for {appointment_type}",
        "ar": "جدول {appointment_type}",
    },
    "minister.list.available_plain": {
        "en": "{appointment_type} available slots:\n{time_list}",
        "ar": "المواعيد المتاحة لـ {appointment_type}:\n{time_list}",
    },
    "minister.list.error": {
        "en": "An error occurred while fetching the schedule: {error}",
        "ar": "حدث خطا اثناء جلب الجدول: {error}",
    },
    "minister.archive.menu_missing": {
        "en": "{icon} Minister Menu module not found.",
        "ar": "{icon} لم يتم العثور على وحدة قائمة الوزراء.",
    },
    "minister.archive.module_missing": {
        "en": "{icon} Minister Archive module not found.",
        "ar": "{icon} لم يتم العثور على وحدة ارشيف الوزراء.",
    },
    "minister.archive.save_forbidden": {
        "en": "{icon} Only global administrators can save archives.",
        "ar": "{icon} المشرفون العامون فقط يمكنهم حفظ الارشيف.",
    },
    "minister.archive.list_forbidden": {
        "en": "{icon} Only global administrators can view archives.",
        "ar": "{icon} المشرفون العامون فقط يمكنهم عرض الارشيف.",
    },
    "minister.archive.history_forbidden": {
        "en": "{icon} Only global administrators can view change history.",
        "ar": "{icon} المشرفون العامون فقط يمكنهم عرض سجل التغييرات.",
    },
    "minister.archive.history_empty": {
        "en": "No change history found with the specified filters.",
        "ar": "لا توجد تغييرات حسب عوامل التصفية المحددة.",
    },
    "minister.menu.filter_title": {
        "en": "Filter Users",
        "ar": "تصفية المستخدمين",
    },
    "minister.menu.filter_label": {
        "en": "Filter by ID or Name",
        "ar": "تصفية بالمعرف او الاسم",
    },
    "minister.menu.filter_placeholder": {
        "en": "Enter ID or nickname (partial match supported)",
        "ar": "ادخل المعرف او الاسم المستعار (يدعم التطابق الجزئي)",
    },
    "minister.menu.users_none_filtered": {
        "en": "No users found",
        "ar": "لا يوجد مستخدمون",
    },
    "minister.menu.users_none": {
        "en": "No users available",
        "ar": "لا يوجد مستخدمون متاحون",
    },
    "minister.menu.users_none_option": {
        "en": "No users",
        "ar": "لا يوجد مستخدمون",
    },
    "minister.menu.user_select_placeholder": {
        "en": "Select a user... (Page {page}/{max_page})",
        "ar": "اختر مستخدما... (صفحة {page}/{max_page})",
    },
    "minister.menu.user_not_found": {
        "en": "{icon} User not found.",
        "ar": "{icon} لم يتم العثور على المستخدم.",
    },
    "minister.menu.manage_title": {
        "en": "🧑‍💼 {activity_name} Management",
        "ar": "🧑‍💼 ادارة {activity_name}",
    },
    "minister.menu.manage_desc": {
        "en": "Select a user to manage their {activity_name} appointment.\n\n",
        "ar": "اختر مستخدما لادارة موعده في {activity_name}.\n\n",
    },
    "minister.menu.filter_status": {
        "en": "**Filter:** `{filter_text}`\n**Filtered Users:** {filtered}/{total}\n\n",
        "ar": "**التصفية:** `{filter_text}`\n**المستخدمون المصفون:** {filtered}/{total}\n\n",
    },
    "minister.menu.status_block": {
        "en": "**Current Status**\n{upper}\n📅 **Booked Slots:** `{booked}/48`\n{time_icon} **Available Slots:** `{available}/48`\n{lower}\n\n📅 = User already has a booking",
        "ar": "**الحالة الحالية**\n{upper}\n📅 **المواعيد المحجوزة:** `{booked}/48`\n{time_icon} **المواعيد المتاحة:** `{available}/48`\n{lower}\n\n📅 = لدى المستخدم حجز بالفعل",
    },
    "minister.menu.status_message": {
        "en": "{status_emoji} **{message}**\n\n",
        "ar": "{status_emoji} **{message}**\n\n",
    },
    "minister.menu.clear_all_message": {
        "en": "Cleared all {count} appointments for {activity_name}",
        "ar": "تم مسح {count} موعدا لـ {activity_name}",
    },
    "minister.menu.clear_alliance_message": {
        "en": "Cleared {count} alliance appointments for {activity_name}",
        "ar": "تم مسح {count} من مواعيد التحالف لـ {activity_name}",
    },
    "minister.menu.cleared_title": {
        "en": "Appointments Cleared - {activity_name}",
        "ar": "تم مسح المواعيد - {activity_name}",
    },
    "minister.menu.cleared_desc": {
        "en": "{count} appointments were cleared",
        "ar": "تم مسح {count} موعد",
    },
    "minister.menu.settings_title": {
        "en": "{icon} Minister Settings",
        "ar": "{icon} اعدادات الوزراء",
    },
    "minister.menu.settings_desc": {
        "en": "{verified} **{message}**\n\nAdministrative settings for minister scheduling:\n\nAvailable Actions\n{upper}\n\n{edit_icon} **Update Names**\n└ Update nicknames from API for booked users\n\n{list_icon} **Schedule List Type**\n└ Change the type of schedule list message when adding/removing people\n\n{calendar_icon} **Delete All Reservations**\n└ Clear appointments for a specific day\n\n{announce_icon} **Clear Channels**\n└ Clear channel configurations\n\n{fid_icon} **Delete Server ID**\n└ Remove configured server from database\n\n{lower}",
        "ar": "{verified} **{message}**\n\nاعدادات ادارية لجدولة الوزراء:\n\nالاجراءات المتاحة\n{upper}\n\n{edit_icon} **تحديث الاسماء**\n└ تحديث الاسماء من الواجهة للمحجوزين\n\n{list_icon} **نوع القائمة**\n└ تغيير نوع رسالة القائمة عند الاضافة/الازالة\n\n{calendar_icon} **حذف كل المواعيد**\n└ مسح مواعيد يوم محدد\n\n{announce_icon} **مسح القنوات**\n└ مسح تهيئة القنوات\n\n{fid_icon} **حذف معرف السيرفر**\n└ حذف السيرفر من قاعدة البيانات\n\n{lower}",
    },
    "minister.menu.settings_desc_no_status": {
        "en": "Administrative settings for minister scheduling:\n\nAvailable Actions\n{upper}\n\n{edit_icon} **Update Names**\n└ Update nicknames from API for booked users\n\n{list_icon} **Schedule List Type**\n└ Change the type of schedule list message when adding/removing people\n\n{time_icon} **Time Slot Mode**\n└ Toggle between standard (00:00/00:30) and offset (00:00/00:15/00:45) time slots\n\n{calendar_icon} **Delete All Reservations**\n└ Clear appointments for a specific day\n\n{announce_icon} **Clear Channels**\n└ Clear channel configurations\n\n{fid_icon} **Delete Server ID**\n└ Remove configured server from database\n\n{lower}",
        "ar": "اعدادات ادارية لجدولة الوزراء:\n\nالاجراءات المتاحة\n{upper}\n\n{edit_icon} **تحديث الاسماء**\n└ تحديث الاسماء من الواجهة للمحجوزين\n\n{list_icon} **نوع القائمة**\n└ تغيير نوع رسالة القائمة عند الاضافة/الازالة\n\n{time_icon} **وضع المواعيد**\n└ التبديل بين القياسي والازاحة\n\n{calendar_icon} **حذف كل المواعيد**\n└ مسح مواعيد يوم محدد\n\n{announce_icon} **مسح القنوات**\n└ مسح تهيئة القنوات\n\n{fid_icon} **حذف معرف السيرفر**\n└ حذف السيرفر من قاعدة البيانات\n\n{lower}",
    },
    "minister.menu.activity_select_placeholder": {
        "en": "Select an activity day...",
        "ar": "اختر يوم النشاط...",
    },
    "minister.menu.activity.construction": {
        "en": "Construction Day",
        "ar": "يوم البناء",
    },
    "minister.menu.activity.research": {
        "en": "Research Day",
        "ar": "يوم البحث",
    },
    "minister.menu.activity.training": {
        "en": "Troops Training Day",
        "ar": "يوم تدريب القوات",
    },
    "minister.menu.no_permission_update": {
        "en": "{icon} You do not have permission to update names.",
        "ar": "{icon} ليس لديك صلاحية لتحديث الاسماء.",
    },
    "minister.menu.no_permission_slot": {
        "en": "{icon} You do not have permission to change time slot mode.",
        "ar": "{icon} ليس لديك صلاحية لتغيير وضع المواعيد.",
    },
    "minister.menu.only_global_clear": {
        "en": "{icon} Only global administrators can clear reservations.",
        "ar": "{icon} المشرفون العامون فقط يمكنهم مسح الحجوزات.",
    },
    "minister.menu.only_global_clear_channels": {
        "en": "{icon} Only global administrators can clear channel configurations.",
        "ar": "{icon} المشرفون العامون فقط يمكنهم مسح تهيئة القنوات.",
    },
    "minister.menu.only_global_delete": {
        "en": "{icon} Only global administrators can delete server configuration.",
        "ar": "{icon} المشرفون العامون فقط يمكنهم حذف تهيئة السيرفر.",
    },
    "minister.menu.server_deleted": {
        "en": "{icon} Server ID deleted from the database.",
        "ar": "{icon} تم حذف معرف السيرفر من قاعدة البيانات.",
    },
    "minister.menu.server_delete_failed": {
        "en": "{icon} Failed to delete server ID: {error}",
        "ar": "{icon} فشل حذف معرف السيرفر: {error}",
    },
    "minister.menu.no_permission_channels": {
        "en": "{icon} You do not have permission to configure channels.",
        "ar": "{icon} ليس لديك صلاحية لتهيئة القنوات.",
    },
    "minister.menu.only_global_archives": {
        "en": "{icon} Only global administrators can access archives.",
        "ar": "{icon} المشرفون العامون فقط يمكنهم الوصول للارشيف.",
    },
    "minister.menu.other_features_missing": {
        "en": "{icon} Other Features module not found.",
        "ar": "{icon} لم يتم العثور على وحدة الميزات الاخرى.",
    },
    "minister.menu.other_features_error": {
        "en": "{icon} An error occurred while returning to Other Features menu: {error}",
        "ar": "{icon} حدث خطا اثناء الرجوع لقائمة الميزات الاخرى: {error}",
    },
    "minister.menu.schedule_missing": {
        "en": "{icon} Minister Schedule module not found.",
        "ar": "{icon} لم يتم العثور على وحدة جدول الوزراء.",
    },
    "minister.menu.schedule_load_failed": {
        "en": "Couldn't load minister_schedule.py cog",
        "ar": "تعذر تحميل ملف minister_schedule.py",
    },
    "minister.menu.log_server_missing": {
        "en": "Could not find the minister log server. Make sure the bot is in that server.\n\nIf issue persists, run the `/settings` command --> Other Features --> Minister Scheduling --> Delete Server ID and try again in the desired server",
        "ar": "تعذر العثور على سيرفر سجل الوزراء. تاكد من وجود البوت في ذلك السيرفر.\n\nاذا استمرت المشكلة، شغل `/settings` --> Other Features --> Minister Scheduling --> Delete Server ID ثم حاول مرة اخرى.",
    },
    "minister.menu.channel_missing": {
        "en": "Could not find {activity_name} channel or log channel. Make sure to select a channel for each minister type for the bot to send the updated list, and a log channel.\n\nYou can do so by running the `/settings` command --> Other Features --> Minister Scheduling --> Channel Setup",
        "ar": "تعذر العثور على قناة {activity_name} او قناة السجل. تاكد من اختيار قناة لكل نوع وتعيين قناة سجل.\n\nيمكنك ذلك عبر `/settings` --> Other Features --> Minister Scheduling --> Channel Setup",
    },
    "minister.menu.server_mismatch": {
        "en": "This menu must be used in the configured server: `{guild}`.\n\nIf you want to change the server, run `/settings` command --> Other Features --> Minister Scheduling --> Delete Server ID and try again in the desired server",
        "ar": "يجب استخدام هذه القائمة في السيرفر المحدد: `{guild}`.\n\nلتغيير السيرفر شغل `/settings` --> Other Features --> Minister Scheduling --> Delete Server ID ثم حاول مرة اخرى.",
    },
    "minister.menu.channel_setup_title": {
        "en": "{icon} Channel Setup",
        "ar": "{icon} اعداد القنوات",
    },
    "minister.menu.channel_setup_desc": {
        "en": "Configure channels for minister scheduling:\n\nChannel Types\n{upper}\n\n{construction} **Construction Channel**\n└ Shows available Construction Day slots\n\n{research} **Research Channel**\n└ Shows available Research Day slots\n\n{training} **Training Channel**\n└ Shows available Training Day slots\n\n{list_icon} **Log Channel**\n└ Receives add/remove notifications\n\n{lower}\n\nSelect a channel type to configure:",
        "ar": "تهيئة قنوات جدولة الوزراء:\n\nانواع القنوات\n{upper}\n\n{construction} **قناة البناء**\n└ تعرض مواعيد يوم البناء\n\n{research} **قناة البحث**\n└ تعرض مواعيد يوم البحث\n\n{training} **قناة التدريب**\n└ تعرض مواعيد يوم التدريب\n\n{list_icon} **قناة السجل**\n└ تستقبل اشعارات الاضافة/الازالة\n\n{lower}\n\nاختر نوع القناة للتهيئة:",
    },
    "minister.menu.channel_select": {
        "en": "Select a channel for {activity_name}:",
        "ar": "اختر قناة لـ {activity_name}:",
    },
    "minister.menu.time_select_placeholder": {
        "en": "Select an available time slot...",
        "ar": "اختر موعدا متاحا...",
    },
    "minister.menu.time_select_paged": {
        "en": "Select time... (Page {page}/{max_page})",
        "ar": "اختر وقتا... (صفحة {page}/{max_page})",
    },
    "minister.menu.main_title": {
        "en": "🏛️ Minister Scheduling",
        "ar": "🏛️ جدولة الوزراء",
    },
    "minister.menu.main_desc": {
        "en": "Manage your minister appointments here:\n\n**Channel Status**\n{upper}\n{channel_status}\n{middle}\n\n**Available Operations**\n{middle}\n{construction} **Construction Day**\n└ Manage Construction Day appointments\n\n{research} **Research Day**\n└ Manage Research Day appointments\n\n{training} **Training Day**\n└ Manage Troops Training Day appointments\n\n{edit_icon} **Channel Setup**\n└ Configure channels for appointments and logging\n\n{archive_icon} **Event Archive**\n└ Save and view past SvS minister schedules\n\n{settings_icon} **Settings**\n└ Update names, clear reservations and more\n{lower}",
        "ar": "ادارة مواعيد الوزراء هنا:\n\n**حالة القنوات**\n{upper}\n{channel_status}\n{middle}\n\n**العمليات المتاحة**\n{middle}\n{construction} **يوم البناء**\n└ ادارة مواعيد يوم البناء\n\n{research} **يوم البحث**\n└ ادارة مواعيد يوم البحث\n\n{training} **يوم التدريب**\n└ ادارة مواعيد يوم التدريب\n\n{edit_icon} **اعداد القنوات**\n└ تهيئة قنوات المواعيد والسجل\n\n{archive_icon} **ارشيف الاحداث**\n└ حفظ وعرض جداول سابقة\n\n{settings_icon} **الاعدادات**\n└ تحديث الاسماء ومسح الحجوزات وغيرها\n{lower}",
    },
    "minister.menu.schedule_not_loaded": {
        "en": "{icon} **Minister Schedule module not loaded**\n",
        "ar": "{icon} **لم يتم تحميل وحدة جدول الوزراء**\n",
    },
    "minister.menu.channel_status_missing": {
        "en": "{label}: {icon} Not Configured",
        "ar": "{label}: {icon} غير مهيء",
    },
    "minister.menu.channel_status_ok": {
        "en": "{label}: {icon} {mention}",
        "ar": "{label}: {icon} {mention}",
    },
    "minister.menu.channel_status_invalid": {
        "en": "{label}: {icon} Invalid Channel",
        "ar": "{label}: {icon} قناة غير صالحة",
    },
    "minister.menu.no_permission_manage": {
        "en": "{icon} You do not have permission to manage minister appointments.",
        "ar": "{icon} ليس لديك صلاحية لادارة مواعيد الوزراء.",
    },
    "minister.menu.no_users_alliance": {
        "en": "{icon} No users found in your allowed alliances.",
        "ar": "{icon} لا يوجد مستخدمون في تحالفاتك المسموحة.",
    },
    "minister.menu.schedule_title": {
        "en": "{icon} {activity_name} Schedule",
        "ar": "{icon} جدول {activity_name}",
    },
    "minister.menu.schedule_empty": {
        "en": "No appointments currently booked.",
        "ar": "لا توجد مواعيد محجوزة حاليا.",
    },
    "minister.menu.schedule_footer": {
        "en": "Total bookings: {count}/48",
        "ar": "اجمالي الحجوزات: {count}/48",
    },
    "minister.menu.no_appointments": {
        "en": "{icon} No appointments to update.",
        "ar": "{icon} لا توجد مواعيد للتحديث.",
    },
    "minister.menu.update_names_result": {
        "en": "Updated {updated} nicknames for {activity_name}",
        "ar": "تم تحديث {updated} اسماء لـ {activity_name}",
    },
    "minister.menu.update_names_failed": {
        "en": " ({failed} failed)",
        "ar": " ({failed} فشل)",
    },
    "minister.menu.clear_all_title": {
        "en": "{icon} Clear All Appointments",
        "ar": "{icon} مسح كل المواعيد",
    },
    "minister.menu.clear_all_desc": {
        "en": "Are you sure you want to clear **ALL {count} appointments** for {activity_name}?\n\nThis action cannot be undone.",
        "ar": "هل انت متاكد من مسح **كل {count} المواعيد** لـ {activity_name}?\n\nلا يمكن التراجع عن هذا الاجراء.",
    },
    "minister.menu.no_permission_clear": {
        "en": "{icon} You don't have permission to clear appointments.",
        "ar": "{icon} ليس لديك صلاحية لمسح المواعيد.",
    },
    "minister.menu.clear_alliance_title": {
        "en": "{icon} Clear Alliance Appointments",
        "ar": "{icon} مسح مواعيد التحالف",
    },
    "minister.menu.clear_alliance_desc": {
        "en": "Are you sure you want to clear **{count} appointments** for your alliance(s) in {activity_name}?\n\nThis action cannot be undone.",
        "ar": "هل انت متاكد من مسح **{count} المواعيد** لتحالفك في {activity_name}?\n\nلا يمكن التراجع عن هذا الاجراء.",
    },
    "minister.menu.no_time_slots": {
        "en": "{icon} No available time slots for {activity_name}.",
        "ar": "{icon} لا توجد مواعيد متاحة لـ {activity_name}.",
    },
    "minister.menu.time_select_desc": {
        "en": "Choose an available time slot for **{nickname}** in {activity_name}:",
        "ar": "اختر موعدا متاحا لـ **{nickname}** في {activity_name}:",
    },
    "minister.menu.time_select_current": {
        "en": "\n\n**Current booking:** `{current_time}`\n\nSelecting a new time will move the booking.",
        "ar": "\n\n**الحجز الحالي:** `{current_time}`\n\nاختيار وقت جديد سيغير الحجز.",
    },
    "minister.menu.time_select_title": {
        "en": "{icon} Select Time for {nickname}",
        "ar": "{icon} اختر الوقت لـ {nickname}",
    },
    "minister.menu.user_not_registered": {
        "en": "{icon} User {fid} is not registered.",
        "ar": "{icon} المستخدم {fid} غير مسجل.",
    },
    "minister.menu.rescheduled_title": {
        "en": "Player rescheduled in {activity_name}",
        "ar": "تم تغيير موعد لاعب في {activity_name}",
    },
    "minister.menu.rescheduled_desc": {
        "en": "{nickname} ({fid}) from **{alliance_name}** moved from {old_time} to {new_time}",
        "ar": "{nickname} ({fid}) من **{alliance_name}** تم نقله من {old_time} الى {new_time}",
    },
    "minister.menu.rescheduled_success": {
        "en": "Successfully moved {nickname} from {old_time} to {new_time}",
        "ar": "تم نقل {nickname} من {old_time} الى {new_time} بنجاح",
    },
    "minister.menu.added_success": {
        "en": "Successfully added {nickname} to {activity_name} at {time}",
        "ar": "تمت اضافة {nickname} الى {activity_name} في {time}",
    },
    "minister.menu.booking_error": {
        "en": "{icon} Error booking appointment: {error}",
        "ar": "{icon} خطا في حجز الموعد: {error}",
    },
    "minister.menu.remove_desc": {
        "en": "{nickname} ({fid}) from **{alliance_name}** at {time}",
        "ar": "{nickname} ({fid}) من **{alliance_name}** في {time}",
    },
    "minister.menu.clear_success": {
        "en": "Successfully cleared {nickname}'s reservation at {time}",
        "ar": "تم مسح حجز {nickname} في {time} بنجاح",
    },
    "minister.menu.clear_error": {
        "en": "{icon} Error clearing reservation: {error}",
        "ar": "{icon} خطا في مسح الحجز: {error}",
    },
    "minister.menu.clear_channels_placeholder": {
        "en": "Select channels to clear...",
        "ar": "اختر القنوات للمسح...",
    },
    "minister.menu.channel.construction": {
        "en": "Construction Channel",
        "ar": "قناة البناء",
    },
    "minister.menu.channel.research": {
        "en": "Research Channel",
        "ar": "قناة البحث",
    },
    "minister.menu.channel.training": {
        "en": "Training Channel",
        "ar": "قناة التدريب",
    },
    "minister.menu.channel.log": {
        "en": "Log Channel",
        "ar": "قناة السجل",
    },
    "minister.menu.channel.all": {
        "en": "All Channels",
        "ar": "كل القنوات",
    },
    "minister.menu.channel.all_desc": {
        "en": "Clear all channel configurations",
        "ar": "مسح جميع تهيئات القنوات",
    },
    "minister.menu.clear_channels_success": {
        "en": "Successfully cleared the following configurations:\n{channels}",
        "ar": "تم مسح التهيئات التالية بنجاح:\n{channels}",
    },
    "minister.menu.clear_channels_error": {
        "en": "{icon} Error clearing channels: {error}",
        "ar": "{icon} خطا في مسح القنوات: {error}",
    },
    "minister.menu.clear_channels_title": {
        "en": "🗑️ Clear Channel Configurations",
        "ar": "🗑️ مسح تهيئة القنوات",
    },
    "minister.menu.clear_channels_desc": {
        "en": "Select which channel configurations you want to clear.\n\n**Warning:** This will remove the channel configuration and delete any existing appointment messages in those channels.\n\n**Note:** Appointment records will be preserved.",
        "ar": "اختر تهيئات القنوات التي تريد مسحها.\n\n**تحذير:** سيتم حذف التهيئة وحذف رسائل المواعيد في تلك القنوات.\n\n**ملاحظة:** ستظل سجلات المواعيد محفوظة.",
    },
    "minister.menu.update_names_title": {
        "en": "{icon} Update Names",
        "ar": "{icon} تحديث الاسماء",
    },
    "minister.menu.update_names_desc": {
        "en": "Select which activity day you want to update names for:",
        "ar": "اختر يوم النشاط الذي تريد تحديث الاسماء له:",
    },
    "minister.menu.clear_reservations_title": {
        "en": "📅 Delete All Reservations",
        "ar": "📅 حذف كل الحجوزات",
    },
    "minister.menu.clear_reservations_desc": {
        "en": "Select which activity day you want to clear reservations for:",
        "ar": "اختر يوم النشاط الذي تريد مسح حجوزاته:",
    },
    "minister.menu.slot_mode_title": {
        "en": "{icon} Time Slot Mode",
        "ar": "{icon} وضع المواعيد",
    },
    "minister.menu.slot_mode_desc": {
        "en": "**Current Mode:** {current_label}\n\n**Mode 0 (Standard):**\n└ 48 slots: 00:00, 00:30, 01:00, 01:30... 23:30\n└ Each slot is 30 minutes\n\n**Mode 1 (Offset):**\n└ 48 slots: 00:00 (15min), 00:15, 00:45, 01:15... 23:45 (15min to midnight)\n└ First slot: 00:00-00:15 (15 min)\n└ Middle slots: 30 min each\n└ Last slot: 23:45-00:00 (15 min, ends at daily reset)\n\n{warn_icon} **Warning:** Changing modes will automatically migrate all existing reservations to the new time slots.",
        "ar": "**الوضع الحالي:** {current_label}\n\n**الوضع 0 (قياسي):**\n└ 48 موعد: 00:00، 00:30، 01:00، 01:30... 23:30\n└ كل موعد 30 دقيقة\n\n**الوضع 1 (ازاحة):**\n└ 48 موعد: 00:00 (15د)، 00:15، 00:45، 01:15... 23:45 (15د حتى منتصف الليل)\n└ اول موعد: 00:00-00:15 (15د)\n└ المواعيد الوسطى: 30 دقيقة\n└ اخر موعد: 23:45-00:00 (15د)\n\n{warn_icon} **تحذير:** تغيير الوضع سينقل جميع الحجوزات الى المواعيد الجديدة تلقائيا.",
    },
    "minister.menu.slot_mode_placeholder": {
        "en": "Choose a time slot mode:",
        "ar": "اختر وضع المواعيد:",
    },
    "minister.menu.slot_mode_standard": {
        "en": "Standard",
        "ar": "قياسي",
    },
    "minister.menu.slot_mode_standard_desc": {
        "en": "00:00, 00:30, 01:00... (30min slots)",
        "ar": "00:00، 00:30، 01:00... (30 دقيقة)",
    },
    "minister.menu.slot_mode_offset": {
        "en": "Offset",
        "ar": "ازاحة",
    },
    "minister.menu.slot_mode_offset_desc": {
        "en": "00:00, 00:15, 00:45... (offset 15min)",
        "ar": "00:00، 00:15، 00:45... (ازاحة 15د)",
    },
    "minister.menu.slot_mode_already": {
        "en": "{icon} Already using this mode.",
        "ar": "{icon} هذا الوضع مستخدم بالفعل.",
    },
    "minister.menu.slot_mode_updated_title": {
        "en": "{icon} Time Slot Mode Updated",
        "ar": "{icon} تم تحديث وضع المواعيد",
    },
    "minister.menu.slot_mode_updated_empty": {
        "en": "Successfully switched to **Mode {mode}** (no reservations to migrate).",
        "ar": "تم التحويل الى **الوضع {mode}** (لا توجد حجوزات للنقل).",
    },
    "minister.menu.slot_mode_changed_title": {
        "en": "Time Slot Mode Changed: Mode {old_mode} → Mode {new_mode}",
        "ar": "تم تغيير وضع المواعيد: {old_mode} → {new_mode}",
    },
    "minister.menu.slot_mode_changed_desc": {
        "en": "**Migrated {count} reservations:**\n\n{migration_text}",
        "ar": "**تم نقل {count} حجوزات:**\n\n{migration_text}",
    },
    "minister.menu.changed_by": {
        "en": "Changed by {user}",
        "ar": "تم التغيير بواسطة {user}",
    },
    "minister.menu.slot_mode_updated_desc": {
        "en": "Successfully switched to **{mode_label}** mode.\n\n{count} reservations were migrated.",
        "ar": "تم التحويل الى وضع **{mode_label}**.\n\nتم نقل {count} حجوزات.",
    },
    "minister.menu.slot_mode_error": {
        "en": "{icon} Error migrating time slots: {error}",
        "ar": "{icon} خطا في نقل المواعيد: {error}",
    },
    "minister.menu.list_type_title": {
        "en": "📋 Schedule List Type",
        "ar": "📋 نوع قائمة الجدول",
    },
    "minister.menu.list_type_desc": {
        "en": "Select the type of generated minister list message when adding/removing people:\n\n**Currently showing:** {current_label}",
        "ar": "اختر نوع رسالة القائمة عند الاضافة/الازالة:\n\n**المعروض حاليا:** {current_label}",
    },
    "minister.menu.list_type_placeholder": {
        "en": "Choose a schedule list type:",
        "ar": "اختر نوع القائمة:",
    },
    "minister.menu.list_type_available": {
        "en": "Available",
        "ar": "المتاح",
    },
    "minister.menu.list_type_available_desc": {
        "en": "Show only available slots",
        "ar": "عرض المواعيد المتاحة فقط",
    },
    "minister.menu.list_type_booked": {
        "en": "Booked",
        "ar": "محجوز",
    },
    "minister.menu.list_type_booked_desc": {
        "en": "Show only booked slots",
        "ar": "عرض المواعيد المحجوزة فقط",
    },
    "minister.menu.list_type_all": {
        "en": "All",
        "ar": "الكل",
    },
    "minister.menu.list_type_all_desc": {
        "en": "Show all slots",
        "ar": "عرض كل المواعيد",
    },
    "minister.menu.list_type_updated": {
        "en": "{icon} Schedule list type updated successfully!\n\n**Now showing:** {label}\n\nNew changes will take effect when you add/remove a person to/from the minister schedule.",
        "ar": "{icon} تم تحديث نوع القائمة بنجاح!\n\n**يعرض الان:** {label}\n\nستظهر التغييرات عند اضافة/ازالة شخص من الجدول.",
    },
    "bear.editor.warn_embed_mention": {
        "en": "{icon} You typed `{examples}` but mentions don't work inside embeds.\nUse `{{tag}}` instead - it will add the mention above the embed.",
        "ar": "{icon} كتبت `{examples}` لكن المنشن لا يعمل داخل الامبد.\nاستخدم `{{tag}}` بدلا من ذلك وسيتم اضافة المنشن فوق الامبد.",
    },
    "bear.editor.warn_plain_mention": {
        "en": "{icon} You typed `{examples}` but this won't ping anyone.\nUse `{{tag}}` instead - it will be replaced with your configured mention.",
        "ar": "{icon} كتبت `{examples}` لكنه لن ينبه احدا.\nاستخدم `{{tag}}` وسيتم استبداله بالمنشن المحدد.",
    },
    "bear.editor.repeat.none": {
        "en": "{icon} No repeat",
        "ar": "{icon} بدون تكرار",
    },
    "bear.editor.repeat.custom_days": {
        "en": "Custom Days",
        "ar": "ايام مخصصة",
    },
    "bear.editor.repeat.no_days": {
        "en": "{icon} No days selected",
        "ar": "{icon} لم يتم اختيار اي يوم",
    },
    "bear.editor.repeat.every": {
        "en": "Every {days}",
        "ar": "كل {days}",
    },
    "bear.editor.and": {
        "en": "and",
        "ar": "و",
    },
    "bear.editor.repeat.invalid": {
        "en": "Invalid repeat interval",
        "ar": "تكرار غير صالح",
    },
    "bear.editor.unit.month_single": {"en": "month", "ar": "شهر"},
    "bear.editor.unit.month_plural": {"en": "months", "ar": "اشهر"},
    "bear.editor.unit.week_single": {"en": "week", "ar": "اسبوع"},
    "bear.editor.unit.week_plural": {"en": "weeks", "ar": "اسابيع"},
    "bear.editor.unit.day_single": {"en": "day", "ar": "يوم"},
    "bear.editor.unit.day_plural": {"en": "days", "ar": "ايام"},
    "bear.editor.unit.hour_single": {"en": "hour", "ar": "ساعة"},
    "bear.editor.unit.hour_plural": {"en": "hours", "ar": "ساعات"},
    "bear.editor.unit.minute_single": {"en": "minute", "ar": "دقيقة"},
    "bear.editor.unit.minute_plural": {"en": "minutes", "ar": "دقائق"},
    "bear.editor.mention.none": {
        "en": "No Mention",
        "ar": "بدون منشن",
    },
    "bear.editor.notify_type.1": {
        "en": "Sends notifications at 30 minutes, 10 minutes, 5 minutes before and when time's up",
        "ar": "يرسل الاشعارات قبل 30 و 10 و 5 دقائق وعند انتهاء الوقت",
    },
    "bear.editor.notify_type.2": {
        "en": "Sends notifications at 10 minutes, 5 minutes before and when time's up",
        "ar": "يرسل الاشعارات قبل 10 و 5 دقائق وعند انتهاء الوقت",
    },
    "bear.editor.notify_type.3": {
        "en": "Sends notifications at 5 minutes before and when time's up",
        "ar": "يرسل الاشعارات قبل 5 دقائق وعند انتهاء الوقت",
    },
    "bear.editor.notify_type.4": {
        "en": "Sends notification only 5 minutes before",
        "ar": "يرسل اشعارا قبل 5 دقائق فقط",
    },
    "bear.editor.notify_type.5": {
        "en": "Sends notification only when time's up",
        "ar": "يرسل اشعارا عند انتهاء الوقت فقط",
    },
    "bear.editor.notify_type.6": {
        "en": "Sends notifications at custom times",
        "ar": "يرسل الاشعارات في اوقات مخصصة",
    },
    "bear.editor.notify_type.unknown": {
        "en": "Unknown notification type",
        "ar": "نوع اشعار غير معروف",
    },
    "bear.editor.modal.edit_field": {
        "en": "Edit {field}",
        "ar": "تعديل {field}",
    },
    "bear.editor.color_invalid": {
        "en": "Invalid hex color code!",
        "ar": "رمز لون غير صالح!",
    },
    "bear.editor.modal_error": {
        "en": "An error occurred! {error}",
        "ar": "حدث خطا! {error}",
    },
    "bear.editor.label.embed_title": {"en": "Embed Title", "ar": "عنوان الامبد"},
    "bear.editor.placeholder.title": {"en": "Enter notification title", "ar": "ادخل عنوان الاشعار"},
    "bear.editor.label.embed_description": {"en": "Embed Description", "ar": "وصف الامبد"},
    "bear.editor.placeholder.description": {"en": "Enter notification description", "ar": "ادخل وصف الاشعار"},
    "bear.editor.label.color": {"en": "Embed hex code", "ar": "رمز لون الامبد"},
    "bear.editor.placeholder.color": {"en": "Enter hex code", "ar": "ادخل رمز اللون"},
    "bear.editor.label.mention_message": {"en": "mention message", "ar": "رسالة المنشن"},
    "bear.editor.placeholder.mention_message": {
        "en": "Variables: %t=time left, %n=name, %e=time, %d=date, %i=emoji, @tag=mention",
        "ar": "المتغيرات: %t=الوقت المتبقي، %n=الاسم، %e=الوقت، %d=التاريخ، %i=الايموجي، @tag=منشن",
    },
    "bear.editor.label.footer": {"en": "Embed Footer", "ar": "تذييل الامبد"},
    "bear.editor.placeholder.footer": {"en": "Enter Footer", "ar": "ادخل التذييل"},
    "bear.editor.label.author": {"en": "Embed Author", "ar": "كاتب الامبد"},
    "bear.editor.placeholder.author": {"en": "Enter Author message", "ar": "ادخل رسالة الكاتب"},
    "bear.editor.label.image": {"en": "Embed Image", "ar": "صورة الامبد"},
    "bear.editor.placeholder.image": {"en": "Enter image url", "ar": "ادخل رابط الصورة"},
    "bear.editor.label.thumbnail": {"en": "Embed Thumbnail URL", "ar": "رابط الصورة المصغرة"},
    "bear.editor.placeholder.thumbnail": {"en": "Enter Thumbnail URL", "ar": "ادخل رابط الصورة المصغرة"},
    "bear.editor.notification_missing": {
        "en": "{icon} Notification not found in database.",
        "ar": "{icon} لم يتم العثور على الاشعار في قاعدة البيانات.",
    },
    "bear.editor.edit_title": {"en": "Editing Notification", "ar": "تعديل الاشعار"},
    "bear.editor.edit_desc": {
        "en": "**{calendar} Next Notification date:** {next_date}\n**{time_icon} Time:** {time} ({timezone})\n**{announce} Channel:** <#{channel_id}>\n**{edit_icon} Description:** {description}\n\n**{settings_icon} Notification Type**\n{notification_type}\n\n**{members_icon} Mention:** {mention}\n**{retry_icon} Repeat:** {repeat}\n",
        "ar": "**{calendar} تاريخ الاشعار القادم:** {next_date}\n**{time_icon} الوقت:** {time} ({timezone})\n**{announce} القناة:** <#{channel_id}>\n**{edit_icon} الوصف:** {description}\n\n**{settings_icon} نوع الاشعار**\n{notification_type}\n\n**{members_icon} المنشن:** {mention}\n**{retry_icon} التكرار:** {repeat}\n",
    },
    "bear.editor.button.title": {"en": "Title", "ar": "العنوان"},
    "bear.editor.button.color": {"en": "Color", "ar": "اللون"},
    "bear.editor.button.mention_message": {"en": "Mention message", "ar": "رسالة المنشن"},
    "bear.editor.button.footer": {"en": "Footer", "ar": "تذييل"},
    "bear.editor.button.author": {"en": "Author", "ar": "الكاتب"},
    "bear.editor.button.image": {"en": "Add Image", "ar": "اضافة صورة"},
    "bear.editor.button.thumbnail": {"en": "Add Thumbnail", "ar": "اضافة صورة مصغرة"},
    "bear.editor.button.settings": {"en": "Edit Notification settings", "ar": "تعديل اعدادات الاشعار"},
    "bear.editor.button.channel": {"en": "Channel", "ar": "القناة"},
    "bear.editor.button.time": {"en": "Time", "ar": "الوقت"},
    "bear.editor.button.repeat": {"en": "Repeat", "ar": "التكرار"},
    "bear.editor.button.mention": {"en": "Mention", "ar": "المنشن"},
    "bear.editor.button.notification_ping": {"en": "Notification Ping", "ar": "اشعار التنبيه"},
    "bear.editor.button.edit_embed": {"en": "Edit Embed", "ar": "تعديل الامبد"},
    "bear.editor.button.description": {"en": "Description", "ar": "الوصف"},
    "bear.editor.modal.edit_description": {"en": "Edit Description", "ar": "تعديل الوصف"},
    "bear.editor.label.message": {"en": "Message", "ar": "الرسالة"},
    "bear.editor.placeholder.message": {
        "en": "Variables: {tag}=mention, {time}=time left, %n=name, %e=time, %d=date, %i=emoji",
        "ar": "المتغيرات: {tag}=منشن، {time}=الوقت المتبقي، %n=الاسم، %e=الوقت، %d=التاريخ، %i=الايموجي",
    },
    "bear.editor.modal_error_generic": {
        "en": "{icon} An error occurred!",
        "ar": "{icon} حدث خطا!",
    },
    "bear.editor.placeholder.channel": {
        "en": "Select a channel for notifications",
        "ar": "اختر قناة للاشعارات",
    },
    "bear.editor.channel_select": {
        "en": "Select a new channel:",
        "ar": "اختر قناة جديدة:",
    },
    "bear.editor.modal.edit_time": {"en": "Edit Notification Time", "ar": "تعديل وقت الاشعار"},
    "bear.editor.label.date": {"en": "Date (DD/MM/YYYY)", "ar": "التاريخ (DD/MM/YYYY)"},
    "bear.editor.label.hour": {"en": "Hour (0-23)", "ar": "الساعة (0-23)"},
    "bear.editor.label.minute": {"en": "Minute (0-59)", "ar": "الدقيقة (0-59)"},
    "bear.editor.error_missing_next": {
        "en": "{icon} Error: `next_notification` is missing!",
        "ar": "{icon} خطا: `next_notification` مفقود!",
    },
    "bear.editor.error_invalid_date": {
        "en": "{icon} Invalid date format! Use DD/MM/YYYY.",
        "ar": "{icon} صيغة التاريخ غير صحيحة! استخدم DD/MM/YYYY.",
    },
    "bear.editor.error_numbers_only": {
        "en": "{icon} Invalid input! Please enter numbers only.",
        "ar": "{icon} ادخال غير صالح! ادخل ارقاما فقط.",
    },
    "bear.editor.repeat.custom_intervals": {
        "en": "Custom Intervals",
        "ar": "فواصل مخصصة",
    },
    "bear.editor.repeat.specific_days": {
        "en": "Specific Days",
        "ar": "ايام محددة",
    },
    "bear.editor.repeat.select_days": {
        "en": "Select days of the week",
        "ar": "اختر ايام الاسبوع",
    },
    "bear.editor.weekday.monday": {"en": "Monday", "ar": "الاثنين"},
    "bear.editor.weekday.tuesday": {"en": "Tuesday", "ar": "الثلاثاء"},
    "bear.editor.weekday.wednesday": {"en": "Wednesday", "ar": "الاربعاء"},
    "bear.editor.weekday.thursday": {"en": "Thursday", "ar": "الخميس"},
    "bear.editor.weekday.friday": {"en": "Friday", "ar": "الجمعة"},
    "bear.editor.weekday.saturday": {"en": "Saturday", "ar": "السبت"},
    "bear.editor.weekday.sunday": {"en": "Sunday", "ar": "الاحد"},
    "bear.editor.confirm": {"en": "Confirm", "ar": "تاكيد"},
    "bear.editor.repeat.select_one_day": {
        "en": "Please select at least one day.",
        "ar": "يرجى اختيار يوم واحد على الاقل.",
    },
    "bear.editor.repeat.select_specific": {
        "en": "Select specific days for the notification:",
        "ar": "اختر اياما محددة للاشعار:",
    },
    "bear.editor.repeat.edit_interval": {"en": "Edit Repeat Interval", "ar": "تعديل فترة التكرار"},
    "bear.editor.repeat.choose": {
        "en": "Choose how you want to repeat the notification:\n*  Custom intervals --> Every 2 days, 1 week, 1 month, etc\n*  Specific days --> Every Sunday, Sunday and Tuesday, etc",
        "ar": "اختر طريقة تكرار الاشعار:\n*  فواصل مخصصة --> كل يومين، اسبوع، شهر...\n*  ايام محددة --> كل احد، الاحد والثلاثاء...",
    },
    "bear.editor.mention.search": {
        "en": "{icon} Search and select who to mention...",
        "ar": "{icon} ابحث واختر من تريد منشنه...",
    },
    "bear.editor.mention.select_role": {"en": "Select a role:", "ar": "اختر رتبة:"},
    "bear.editor.mention.select_user": {"en": "Select a user:", "ar": "اختر مستخدما:"},
    "bear.editor.mention.everyone": {"en": "{icon} everyone", "ar": "{icon} الجميع"},
    "bear.editor.mention.role": {"en": "{icon} Select Role", "ar": "{icon} اختر رتبة"},
    "bear.editor.mention.member": {"en": "{icon} Select Member", "ar": "{icon} اختر عضوا"},
    "bear.editor.mention.choose": {"en": "Choose mention type:", "ar": "اختر نوع المنشن:"},
    "bear.editor.ping.30_10_5": {"en": "30m, 10m, 5m & Time", "ar": "30د، 10د، 5د والوقت"},
    "bear.editor.ping.10_5": {"en": "10m, 5m & Time", "ar": "10د، 5د والوقت"},
    "bear.editor.ping.5": {"en": "5m & Time", "ar": "5د والوقت"},
    "bear.editor.ping.only_5": {"en": "Only 5m", "ar": "5د فقط"},
    "bear.editor.ping.only_time": {"en": "Only Time", "ar": "الوقت فقط"},
    "bear.editor.ping.custom": {"en": "Custom Times", "ar": "اوقات مخصصة"},
    "bear.editor.ping.custom_title": {"en": "Enter Custom Notification Times", "ar": "ادخل اوقات اشعار مخصصة"},
    "bear.editor.ping.custom_label": {"en": "Enter times (e.g., 20-10-3-2-1-0)", "ar": "ادخل الاوقات (مثال 20-10-3-2-1-0)"},
    "bear.editor.ping.custom_placeholder": {"en": "Separate times with '-'", "ar": "افصل الاوقات باستخدام '-'"},
    "bear.editor.ping.custom_invalid": {"en": "{icon} Invalid format! Use numbers separated by '-'.", "ar": "{icon} صيغة غير صحيحة! استخدم ارقاما مفصولة بـ '-'."},
    "bear.editor.ping.select_title": {"en": "{icon} Select Notification Type", "ar": "{icon} اختر نوع الاشعار"},
    "bear.editor.ping.select_desc": {
        "en": "Choose when to send notifications:\n\n**30m, 10m, 5m & Time**\n• 30 minutes before\n• 10 minutes before\n• 5 minutes before\n• When time's up\n\n**10m, 5m & Time**\n• 10 minutes before\n• 5 minutes before\n• When time's up\n\n**5m & Time**\n• 5 minutes before\n• When time's up\n\n**Only 5m**\n• Only 5 minutes before\n\n**Only Time**\n• Only when time's up\n\n**Custom Times**\n• Set your own notification times",
        "ar": "اختر وقت ارسال الاشعارات:\n\n**30د، 10د، 5د والوقت**\n• قبل 30 دقيقة\n• قبل 10 دقائق\n• قبل 5 دقائق\n• عند انتهاء الوقت\n\n**10د، 5د والوقت**\n• قبل 10 دقائق\n• قبل 5 دقائق\n• عند انتهاء الوقت\n\n**5د والوقت**\n• قبل 5 دقائق\n• عند انتهاء الوقت\n\n**5د فقط**\n• قبل 5 دقائق فقط\n\n**الوقت فقط**\n• عند انتهاء الوقت فقط\n\n**اوقات مخصصة**\n• حدد اوقاتك الخاصة",
    },
    "bear.editor.preview.time": {
        "en": "30 minutes",
        "ar": "30 دقيقة",
    },
    "bear.editor.preview.event": {
        "en": "Event",
        "ar": "حدث",
    },
    "bear.editor.preview.date_fallback": {
        "en": "Dec 06",
        "ar": "06 ديسمبر",
    },
    "bear.editor.no_permission": {
        "en": "{icon} You don't have permission to edit notifications!",
        "ar": "{icon} ليس لديك صلاحية لتعديل الاشعارات!",
    },
    "bear.editor.notification_id_missing": {
        "en": "{icon} Notification ID not found.",
        "ar": "{icon} لم يتم العثور على رقم الاشعار.",
    },
    "bear.editor.plain_error": {
        "en": "An error occurred in PLAIN_MESSAGE section. {error}",
        "ar": "حدث خطا في قسم PLAIN_MESSAGE. {error}",
    },
    "bear.editor.preview.time": {
        "en": "30 minutes",
        "ar": "30 دقيقة",
    },
    "bear.editor.preview.event": {
        "en": "Event",
        "ar": "حدث",
    },
    "bear.editor.preview.date_fallback": {
        "en": "Dec 06",
        "ar": "06 Dec",
    },
    "gift.menu.title": {
        "en": "Gift Code Operations",
        "ar": "عمليات اكواد الهدايا",
    },
    "gift.menu.intro": {
        "en": "Here you can manage everything related to gift code redemption.",
        "ar": "يمكنك هنا ادارة كل ما يتعلق باسترداد اكواد الهدايا.",
    },
    "gift.menu.auto_fetch": {
        "en": "The bot automatically retrieves new gift codes from the distribution API.",
        "ar": "يقوم البوت تلقائيا بجلب اكواد الهدايا الجديدة من واجهة التوزيع.",
    },
    "gift.menu.auto_validate": {
        "en": "Codes are validated periodically and removed if they become invalid.",
        "ar": "يتم التحقق من الاكواد بشكل دوري وحذف غير الصالح منها.",
    },
    "gift.menu.getting_started": {
        "en": "If you're new here, head to **Settings** and configure:",
        "ar": "اذا كنت جديدا هنا، توجه الى **الاعدادات** وقم بالتهيئة:",
    },
    "gift.menu.tip_auto": {
        "en": "Enable auto redemption from **Automatic Redemption**.",
        "ar": "فعّل الاسترداد التلقائي من **الاسترداد التلقائي**.",
    },
    "gift.menu.tip_channel": {
        "en": "Set a scan channel from **Channel Management**.",
        "ar": "حدد قناة الفحص من **ادارة القنوات**.",
    },
    "gift.menu.tip_priority": {
        "en": "Adjust alliance order via **Redemption Priority**.",
        "ar": "عدل ترتيب التحالفات عبر **اولوية الاسترداد**.",
    },
    "gift.menu.available": {
        "en": "Available Operations",
        "ar": "العمليات المتاحة",
    },
    "gift.menu.add": {
        "en": "Add Gift Code",
        "ar": "اضافة كود هدية",
    },
    "gift.menu.add_desc": {
        "en": "Manually input a new gift code",
        "ar": "ادخال كود هدية جديد يدويا",
    },
    "gift.menu.list": {
        "en": "List Gift Codes",
        "ar": "عرض اكواد الهدايا",
    },
    "gift.menu.list_desc": {
        "en": "View all active, valid codes",
        "ar": "عرض جميع الاكواد الصالحة والنشطة",
    },
    "gift.menu.redeem": {
        "en": "Redeem Gift Code",
        "ar": "استرداد كود هدية",
    },
    "gift.menu.redeem_desc": {
        "en": "Redeem gift code(s) for one or more alliances",
        "ar": "استرداد الاكواد لتحالف او اكثر",
    },
    "gift.menu.settings": {
        "en": "Settings",
        "ar": "الاعدادات",
    },
    "gift.menu.settings_desc": {
        "en": "Set up a gift code channel, configure auto redemption, and more...",
        "ar": "اعداد قناة الاكواد وتهيئة الاسترداد التلقائي والمزيد...",
    },
    "gift.menu.delete": {
        "en": "Delete Gift Code",
        "ar": "حذف كود هدية",
    },
    "gift.menu.delete_desc": {
        "en": "Remove existing codes (rarely needed)",
        "ar": "ازالة الاكواد الموجودة (نادرا ما تحتاج)",
    },
    "gift.button.add": {
        "en": "Add Gift Code",
        "ar": "اضافة كود هدية",
    },
    "gift.button.list": {
        "en": "List Gift Codes",
        "ar": "عرض اكواد الهدايا",
    },
    "gift.button.redeem": {
        "en": "Redeem Gift Code",
        "ar": "استرداد كود هدية",
    },
    "gift.button.settings": {
        "en": "Settings",
        "ar": "الاعدادات",
    },
    "gift.button.delete": {
        "en": "Delete Gift Code",
        "ar": "حذف كود هدية",
    },
    "gift.button.main_menu": {
        "en": "Main Menu",
        "ar": "القائمة الرئيسية",
    },
    "gift.button.confirm": {
        "en": "Confirm",
        "ar": "تاكيد",
    },
    "gift.button.cancel": {
        "en": "Cancel",
        "ar": "الغاء",
    },
    "gift.error.not_authorized": {
        "en": "You are not authorized to perform this action.",
        "ar": "ليست لديك صلاحية تنفيذ هذا الاجراء.",
    },
    "gift.error.create_not_authorized": {
        "en": "You are not authorized to create gift codes.",
        "ar": "ليست لديك صلاحية انشاء اكواد هدايا.",
    },
    "gift.error.create_form": {
        "en": "An error occurred while showing the gift code creation form.",
        "ar": "حدث خطا اثناء عرض نموذج انشاء كود الهدية.",
    },
    "gift.list.none": {
        "en": "No active gift codes found in the database.",
        "ar": "لا توجد اكواد هدايا نشطة في قاعدة البيانات.",
    },
    "gift.list.title": {
        "en": "Active Gift Codes",
        "ar": "اكواد الهدايا النشطة",
    },
    "gift.list.description": {
        "en": "Currently active and valid gift codes.",
        "ar": "اكواد الهدايا الصالحة والنشطة حاليا.",
    },
    "gift.list.code_label": {
        "en": "Code: {code}",
        "ar": "الكود: {code}",
    },
    "gift.list.code_value": {
        "en": "Created: {date}\nUsed by: {used} users",
        "ar": "تم الانشاء: {date}\nتم الاستخدام بواسطة: {used}",
    },
    "gift.delete.title": {
        "en": "Delete Gift Code",
        "ar": "حذف كود هدية",
    },
    "gift.delete.unauthorized_title": {
        "en": "Unauthorized Access",
        "ar": "وصول غير مصرح",
    },
    "gift.delete.unauthorized_body": {
        "en": "This action requires Global Admin privileges.",
        "ar": "هذا الاجراء يتطلب صلاحيات المشرف العام.",
    },
    "gift.delete.none_title": {
        "en": "No Gift Codes",
        "ar": "لا توجد اكواد هدايا",
    },
    "gift.delete.none_body": {
        "en": "There are no gift codes in the database to delete.",
        "ar": "لا توجد اكواد هدايا في قاعدة البيانات للحذف.",
    },
    "gift.delete.status_valid": {
        "en": "Valid",
        "ar": "صالح",
    },
    "gift.delete.status_invalid": {
        "en": "Invalid",
        "ar": "غير صالح",
    },
    "gift.delete.status_pending": {
        "en": "Pending",
        "ar": "قيد الانتظار",
    },
    "gift.delete.status_unknown": {
        "en": "Unknown",
        "ar": "غير معروف",
    },
    "gift.delete.option_desc": {
        "en": "{status} | Created: {date} | Used: {used}",
        "ar": "{status} | تم الانشاء: {date} | تم الاستخدام: {used}",
    },
    "gift.delete.select_placeholder": {
        "en": "Select a gift code to delete",
        "ar": "اختر كودا لحذفه",
    },
    "gift.delete.confirm_label": {
        "en": "Confirm Delete",
        "ar": "تاكيد الحذف",
    },
    "gift.delete.success_title": {
        "en": "Gift Code Deleted",
        "ar": "تم حذف كود الهدية",
    },
    "gift.delete.details": {
        "en": "Deletion Details",
        "ar": "تفاصيل الحذف",
    },
    "gift.delete.code_label": {
        "en": "Gift Code:",
        "ar": "كود الهدية:",
    },
    "gift.delete.deleted_by": {
        "en": "Deleted by:",
        "ar": "تم الحذف بواسطة:",
    },
    "gift.delete.time": {
        "en": "Time:",
        "ar": "الوقت:",
    },
    "gift.delete.error_deleting": {
        "en": "An error occurred while deleting the gift code.",
        "ar": "حدث خطا اثناء حذف كود الهدية.",
    },
    "gift.delete.cancelled_title": {
        "en": "Deletion Cancelled",
        "ar": "تم الغاء الحذف",
    },
    "gift.delete.cancelled_body": {
        "en": "The gift code deletion was cancelled.",
        "ar": "تم الغاء حذف كود الهدية.",
    },
    "gift.delete.confirm_title": {
        "en": "Confirm Deletion",
        "ar": "تاكيد الحذف",
    },
    "gift.delete.selected_code": {
        "en": "Selected Code:",
        "ar": "الكود المختار:",
    },
    "gift.delete.warning": {
        "en": "Warning:",
        "ar": "تحذير:",
    },
    "gift.delete.warning_body": {
        "en": "This action cannot be undone!",
        "ar": "لا يمكن التراجع عن هذا الاجراء!",
    },
    "gift.delete.instructions": {
        "en": "Instructions",
        "ar": "التعليمات",
    },
    "gift.delete.step1": {
        "en": "Select a gift code from the menu below",
        "ar": "اختر كودا من القائمة بالاسفل",
    },
    "gift.delete.step2": {
        "en": "Confirm your selection",
        "ar": "قم بتاكيد اختيارك",
    },
    "gift.delete.step3": {
        "en": "The code will be permanently deleted",
        "ar": "سيتم حذف الكود نهائيا",
    },
    "gift.delete.note": {
        "en": "Note: Showing 25 of {total} codes.",
        "ar": "ملاحظة: عرض 25 من {total} كود.",
    },
    "gift.delete.note_oldest": {
        "en": "Oldest codes are shown first.",
        "ar": "يتم عرض الاكواد الاقدم اولا.",
    },
    "gift.delete.note_delete_order": {
        "en": "To delete newer codes, delete older ones first.",
        "ar": "لحذف الاكواد الاحدث، احذف الاقدم اولا.",
    },
    "gift.channel.none_set_title": {
        "en": "No Channels Set",
        "ar": "لا توجد قنوات مضبوطة",
    },
    "gift.channel.none_set_body": {
        "en": "There are no gift code channels set for your alliances.",
        "ar": "لا توجد قنوات اكواد هدايا مضبوطة لتحالفاتك.",
    },
    "gift.channel.remove_title": {
        "en": "Remove Gift Code Channel",
        "ar": "ازالة قناة اكواد الهدايا",
    },
    "gift.channel.remove_select": {
        "en": "Select an alliance to remove its gift code channel:",
        "ar": "اختر تحالفا لازالة قناة اكواد الهدايا:",
    },
    "gift.channel.current_channels": {
        "en": "Current Log Channels",
        "ar": "القنوات الحالية",
    },
    "gift.channel.select_from_list": {
        "en": "Select an alliance from the list below:",
        "ar": "اختر تحالفا من القائمة بالاسفل:",
    },
    "gift.channel.confirm_remove_title": {
        "en": "Confirm Removal",
        "ar": "تاكيد الازالة",
    },
    "gift.channel.confirm_remove_body": {
        "en": "Are you sure you want to remove the gift code channel for:",
        "ar": "هل انت متاكد من ازالة قناة اكواد الهدايا لـ:",
    },
    "gift.channel.warning_body": {
        "en": "This action cannot be undone!",
        "ar": "لا يمكن التراجع عن هذا الاجراء!",
    },
    "gift.channel.alliance_label": {
        "en": "Alliance:",
        "ar": "التحالف:",
    },
    "gift.channel.channel_label": {
        "en": "Channel:",
        "ar": "القناة:",
    },
    "gift.channel.removed_title": {
        "en": "Gift Code Channel Removed",
        "ar": "تمت ازالة قناة اكواد الهدايا",
    },
    "gift.channel.removed_body": {
        "en": "Successfully removed gift code channel for:",
        "ar": "تمت ازالة قناة اكواد الهدايا لـ:",
    },
    "gift.channel.remove_error": {
        "en": "An error occurred while removing the gift code channel.",
        "ar": "حدث خطا اثناء ازالة قناة اكواد الهدايا.",
    },
    "gift.channel.cancelled_title": {
        "en": "Removal Cancelled",
        "ar": "تم الغاء الازالة",
    },
    "gift.channel.cancelled_body": {
        "en": "The gift code channel removal has been cancelled.",
        "ar": "تم الغاء ازالة قناة اكواد الهدايا.",
    },
    "gift.channel.none_for_alliance": {
        "en": "No gift code channel is set for this alliance.",
        "ar": "لا توجد قناة اكواد هدايا مضبوطة لهذا التحالف.",
    },
    "gift.channel.confirm_setting_body": {
        "en": "Are you sure you want to remove the gift code channel setting?",
        "ar": "هل انت متاكد من ازالة ضبط قناة اكواد الهدايا؟",
    },
    "gift.channel.current_channel_label": {
        "en": "Current Channel:",
        "ar": "القناة الحالية:",
    },
    "gift.channel.setting_removed_title": {
        "en": "Channel Setting Removed",
        "ar": "تمت ازالة ضبط القناة",
    },
    "gift.channel.setting_removed_body": {
        "en": "Successfully removed gift code channel setting:",
        "ar": "تمت ازالة ضبط قناة اكواد الهدايا:",
    },
    "gift.channel.setting_removed_hint": {
        "en": "You can set a new channel anytime by selecting a channel from the list above.",
        "ar": "يمكنك ضبط قناة جديدة في اي وقت من القائمة بالاعلى.",
    },
    "gift.channel.manage_title": {
        "en": "Channel Management",
        "ar": "ادارة القنوات",
    },
    "gift.channel.manage_desc": {
        "en": "Manage gift code channels for your alliances.",
        "ar": "ادارة قنوات اكواد الهدايا لتحالفاتك.",
    },
    "gift.channel.current_configs": {
        "en": "Current Configurations",
        "ar": "الاعدادات الحالية",
    },
    "gift.channel.no_configs": {
        "en": "No gift code channels configured yet.",
        "ar": "لا توجد قنوات اكواد هدايا مهيئة بعد.",
    },
    "gift.channel.configure_button": {
        "en": "Configure Channel",
        "ar": "تهيئة القناة",
    },
    "gift.channel.select_config_title": {
        "en": "Select Alliance to Configure",
        "ar": "اختر تحالفا للتهيئة",
    },
    "gift.channel.select_config_desc": {
        "en": "Choose an alliance to set up or change its gift code channel:",
        "ar": "اختر تحالفا لضبط او تغيير قناة اكواد الهدايا:",
    },
    "gift.channel.current_channel_named": {
        "en": "Currently: #{name}",
        "ar": "الحالي: #{name}",
    },
    "gift.channel.current_channel_unknown": {
        "en": "Currently: Unknown Channel ({channel_id})",
        "ar": "الحالي: قناة غير معروفة ({channel_id})",
    },
    "gift.channel.not_configured": {
        "en": "Not configured",
        "ar": "غير مهيأة",
    },
    "gift.channel.select_config_placeholder": {
        "en": "Select alliance to configure...",
        "ar": "اختر تحالفا للتهيئة...",
    },
    "gift.channel.configure_for": {
        "en": "Configure Channel for {alliance}",
        "ar": "تهيئة القناة لـ {alliance}",
    },
    "gift.channel.select_channel": {
        "en": "Select a channel for gift codes:",
        "ar": "اختر قناة لاكواد الهدايا:",
    },
    "gift.channel.configured_title": {
        "en": "Channel Configured",
        "ar": "تمت تهيئة القناة",
    },
    "gift.channel.configured_body": {
        "en": "Channel has been successfully configured for gift code monitoring.",
        "ar": "تمت تهيئة القناة لمراقبة اكواد الهدايا بنجاح.",
    },
    "gift.channel.configure_error": {
        "en": "An error occurred while configuring the channel.",
        "ar": "حدث خطا اثناء تهيئة القناة.",
    },
    "gift.channel.remove_button": {
        "en": "Remove Channel",
        "ar": "ازالة القناة",
    },
    "gift.channel.select_remove_title": {
        "en": "Select Alliance to Remove",
        "ar": "اختر تحالفا للازالة",
    },
    "gift.channel.select_remove_desc": {
        "en": "Choose an alliance to remove its gift code channel configuration:",
        "ar": "اختر تحالفا لازالة تهيئة قناة اكواد الهدايا:",
    },
    "gift.channel.remove_option_desc": {
        "en": "Remove channel <#{channel_id}>",
        "ar": "ازالة القناة <#{channel_id}>",
    },
    "gift.channel.select_remove_placeholder": {
        "en": "Select alliance to remove channel...",
        "ar": "اختر تحالفا لازالة القناة...",
    },
    "gift.channel.config_not_found": {
        "en": "Configuration not found.",
        "ar": "لم يتم العثور على الاعدادات.",
    },
    "gift.channel.confirm_config_body": {
        "en": "Are you sure you want to remove the gift code channel configuration?",
        "ar": "هل انت متاكد من ازالة تهيئة قناة اكواد الهدايا؟",
    },
    "gift.channel.warning": {
        "en": "Warning:",
        "ar": "تحذير:",
    },
    "gift.channel.warning_stop": {
        "en": "This will stop the bot from monitoring this channel for gift codes.",
        "ar": "سيؤدي ذلك الى ايقاف مراقبة هذه القناة لاكواد الهدايا.",
    },
    "gift.channel.confirm_remove_button": {
        "en": "Yes, Remove",
        "ar": "نعم، ازالة",
    },
    "gift.channel.config_removed_title": {
        "en": "Channel Configuration Removed",
        "ar": "تمت ازالة تهيئة القناة",
    },
    "gift.channel.config_removed_body": {
        "en": "Successfully removed gift code channel configuration:",
        "ar": "تمت ازالة تهيئة قناة اكواد الهدايا:",
    },
    "gift.scan.title": {
        "en": "Channel History Scan",
        "ar": "فحص سجل القناة",
    },
    "gift.scan.select_alliance": {
        "en": "Select an alliance to scan its message history for potential gift codes:",
        "ar": "اختر تحالفا لفحص سجل الرسائل بحثا عن اكواد هدايا:",
    },
    "gift.scan.option_desc": {
        "en": "Scan {channel}",
        "ar": "فحص {channel}",
    },
    "gift.scan.select_placeholder": {
        "en": "Select alliance to scan...",
        "ar": "اختر تحالفا للفحص...",
    },
    "gift.scan.no_channels_title": {
        "en": "No Configured Channels",
        "ar": "لا توجد قنوات مهيأة",
    },
    "gift.scan.no_channels_body": {
        "en": "No gift code channels have been configured yet.\nUse **Channel Management** to set up channels first.",
        "ar": "لا توجد قنوات اكواد هدايا مهيأة بعد.\nاستخدم **ادارة القنوات** لضبط القنوات اولا.",
    },
    "gift.scan.no_access_title": {
        "en": "No Accessible Channels",
        "ar": "لا توجد قنوات متاحة",
    },
    "gift.scan.no_access_body": {
        "en": "You don't have access to any configured gift code channels.",
        "ar": "لا تملك صلاحية الوصول الى اي قناة اكواد هدايا مهيأة.",
    },
    "gift.scan.no_channel_title": {
        "en": "No Channel Configured",
        "ar": "لا توجد قناة مهيأة",
    },
    "gift.scan.no_channel_body": {
        "en": "No gift code channel is configured for {alliance}.",
        "ar": "لا توجد قناة اكواد هدايا مهيأة لـ {alliance}.",
    },
    "gift.scan.channel_not_found_title": {
        "en": "Channel Not Found",
        "ar": "لم يتم العثور على القناة",
    },
    "gift.scan.channel_not_found_body": {
        "en": "The configured channel could not be found.",
        "ar": "تعذر العثور على القناة المهيأة.",
    },
    "gift.scan.confirm_title": {
        "en": "Confirm Historical Scan",
        "ar": "تاكيد الفحص التاريخي",
    },
    "gift.scan.details": {
        "en": "Scan Details",
        "ar": "تفاصيل الفحص",
    },
    "gift.scan.limit": {
        "en": "Scan Limit:",
        "ar": "حد الفحص:",
    },
    "gift.scan.limit_value": {
        "en": "Up to 75 historical messages",
        "ar": "حتى 75 رسالة سابقة",
    },
    "gift.scan.note": {
        "en": "Note:",
        "ar": "ملاحظة:",
    },
    "gift.scan.note_body": {
        "en": "This will scan historical messages to find potential gift codes. Use carefully in busy channels.",
        "ar": "سيتم فحص الرسائل السابقة لايجاد اكواد محتملة. استخدم بحذر في القنوات المزدحمة.",
    },
    "gift.scan.proceed": {
        "en": "Do you want to proceed with the historical scan?",
        "ar": "هل تريد متابعة الفحص التاريخي؟",
    },
    "gift.scan.start_button": {
        "en": "Start Scan",
        "ar": "ابدأ الفحص",
    },
    "gift.scan.messages_scanned": {
        "en": "Messages Scanned:",
        "ar": "الرسائل المفحوصة:",
    },
    "gift.scan.total_found": {
        "en": "Total Codes Found:",
        "ar": "اجمالي الاكواد المكتشفة:",
    },
    "gift.scan.validation_results": {
        "en": "Validation Results:",
        "ar": "نتائج التحقق:",
    },
    "gift.scan.new_valid": {
        "en": "New Valid Codes:",
        "ar": "اكواد صالحة جديدة:",
    },
    "gift.scan.new_invalid": {
        "en": "New Invalid Codes:",
        "ar": "اكواد غير صالحة جديدة:",
    },
    "gift.scan.prev_valid": {
        "en": "Previously Valid:",
        "ar": "صالحة سابقا:",
    },
    "gift.scan.prev_invalid": {
        "en": "Previously Invalid:",
        "ar": "غير صالحة سابقا:",
    },
    "gift.scan.pending": {
        "en": "Pending Validation:",
        "ar": "قيد التحقق:",
    },
    "gift.scan.summary_posted": {
        "en": "A detailed summary has been posted in #{channel}",
        "ar": "تم نشر ملخص مفصل في #{channel}",
    },
    "gift.scan.none_found": {
        "en": "No gift codes found in the scanned messages.",
        "ar": "لم يتم العثور على اكواد هدايا في الرسائل المفحوصة.",
    },
    "gift.scan.complete_title": {
        "en": "History Scan Complete",
        "ar": "اكتمل فحص السجل",
    },
    "gift.scan.cancelled_title": {
        "en": "Scan Cancelled",
        "ar": "تم الغاء الفحص",
    },
    "gift.scan.cancelled_body": {
        "en": "History scan has been cancelled.",
        "ar": "تم الغاء فحص السجل.",
    },
    "gift.auto.title": {
        "en": "Gift Code Settings",
        "ar": "اعدادات اكواد الهدايا",
    },
    "gift.auto.select_alliance": {
        "en": "Select an alliance to configure automatic redemption:",
        "ar": "اختر تحالفا لتهيئة الاسترداد التلقائي:",
    },
    "gift.auto.enable_all": {
        "en": "ENABLE ALL ALLIANCES",
        "ar": "تفعيل كل التحالفات",
    },
    "gift.auto.enable_all_desc": {
        "en": "Enable automatic redemption for all alliances",
        "ar": "تفعيل الاسترداد التلقائي لجميع التحالفات",
    },
    "gift.auto.disable_all": {
        "en": "DISABLE ALL ALLIANCES",
        "ar": "تعطيل كل التحالفات",
    },
    "gift.auto.disable_all_desc": {
        "en": "Disable automatic redemption for all alliances",
        "ar": "تعطيل الاسترداد التلقائي لجميع التحالفات",
    },
    "gift.auto.enabled": {
        "en": "enabled",
        "ar": "مفعل",
    },
    "gift.auto.disabled": {
        "en": "disabled",
        "ar": "معطل",
    },
    "gift.auto.updated_title": {
        "en": "Automatic Redemption Updated",
        "ar": "تم تحديث الاسترداد التلقائي",
    },
    "gift.auto.details": {
        "en": "Configuration Details",
        "ar": "تفاصيل الاعداد",
    },
    "gift.auto.scope": {
        "en": "Scope:",
        "ar": "النطاق:",
    },
    "gift.auto.scope_all": {
        "en": "All Alliances",
        "ar": "كل التحالفات",
    },
    "gift.auto.status": {
        "en": "Status:",
        "ar": "الحالة:",
    },
    "gift.auto.status_text": {
        "en": "Automatic redemption {status}",
        "ar": "الاسترداد التلقائي {status}",
    },
    "gift.auto.updated_by": {
        "en": "Updated by:",
        "ar": "تم التحديث بواسطة:",
    },
    "gift.auto.config_title": {
        "en": "Automatic Redemption Configuration",
        "ar": "تهيئة الاسترداد التلقائي",
    },
    "gift.auto.alliance_details": {
        "en": "Alliance Details",
        "ar": "تفاصيل التحالف",
    },
    "gift.auto.current_status": {
        "en": "Current Status:",
        "ar": "الحالة الحالية:",
    },
    "gift.auto.current_status_text": {
        "en": "Automatic redemption is {status}",
        "ar": "الاسترداد التلقائي {status}",
    },
    "gift.auto.enable_disable_prompt": {
        "en": "Do you want to enable or disable automatic redemption for this alliance?",
        "ar": "هل تريد تفعيل او تعطيل الاسترداد التلقائي لهذا التحالف؟",
    },
    "gift.auto.update_error": {
        "en": "An error occurred while updating the settings.",
        "ar": "حدث خطا اثناء تحديث الاعدادات.",
    },
    "gift.auto.enable": {
        "en": "Enable",
        "ar": "تفعيل",
    },
    "gift.auto.disable": {
        "en": "Disable",
        "ar": "تعطيل",
    },
    "gift.error.no_alliances_title": {
        "en": "No Available Alliances",
        "ar": "لا توجد تحالفات متاحة",
    },
    "gift.error.no_alliances_body": {
        "en": "You don't have access to any alliances.",
        "ar": "لا تملك صلاحية الوصول الى اي تحالف.",
    },
    "gift.error.process_request": {
        "en": "An error occurred while processing the request.",
        "ar": "حدث خطا اثناء معالجة الطلب.",
    },
    "gift.error.process_alliance": {
        "en": "An error occurred while processing the alliance selection.",
        "ar": "حدث خطا اثناء معالجة اختيار التحالف.",
    },
    "gift.error.process_gift": {
        "en": "An error occurred while processing the gift code.",
        "ar": "حدث خطا اثناء معالجة كود الهدية.",
    },
    "gift.error.queue_failed": {
        "en": "An error occurred while queueing the gift code redemptions.",
        "ar": "حدث خطا اثناء اضافة استرداد الاكواد للطابور.",
    },
    "gift.error.delete_request": {
        "en": "An error occurred while processing delete request.",
        "ar": "حدث خطا اثناء معالجة طلب الحذف.",
    },
    "gift.error.generic": {
        "en": "An error occurred",
        "ar": "حدث خطا",
    },
    "gift.redeem.title": {
        "en": "Redeem Gift Code",
        "ar": "استرداد كود هدية",
    },
    "gift.redeem.select_alliance": {
        "en": "Select an alliance to use gift code:",
        "ar": "اختر تحالفا لاستخدام كود الهدية:",
    },
    "gift.redeem.alliance_list": {
        "en": "Alliance List",
        "ar": "قائمة التحالفات",
    },
    "gift.redeem.select_alliance_hint": {
        "en": "Select an alliance from the list below:",
        "ar": "اختر تحالفا من القائمة بالاسفل:",
    },
    "gift.redeem.all_alliances": {
        "en": "ALL ALLIANCES",
        "ar": "كل التحالفات",
    },
    "gift.redeem.all_alliances_desc": {
        "en": "Apply to all {count} alliances",
        "ar": "تطبيق على {count} تحالف",
    },
    "gift.redeem.no_active_codes": {
        "en": "No active gift codes available.",
        "ar": "لا توجد اكواد هدايا نشطة حاليا.",
    },
    "gift.redeem.select_code_title": {
        "en": "Select Gift Code",
        "ar": "اختر كود الهدية",
    },
    "gift.redeem.select_code": {
        "en": "Select a gift code to use:",
        "ar": "اختر كود الهدية للاستخدام:",
    },
    "gift.redeem.code_list": {
        "en": "Gift Code List",
        "ar": "قائمة اكواد الهدايا",
    },
    "gift.redeem.select_code_hint": {
        "en": "Select a gift code from the list below:",
        "ar": "اختر كودا من القائمة بالاسفل:",
    },
    "gift.redeem.select_code_placeholder": {
        "en": "Select a gift code",
        "ar": "اختر كود هدية",
    },
    "gift.redeem.code_created": {
        "en": "Created: {date}",
        "ar": "تم الانشاء: {date}",
    },
    "gift.redeem.all_codes": {
        "en": "ALL CODES",
        "ar": "كل الاكواد",
    },
    "gift.redeem.all_codes_desc": {
        "en": "Redeem all {count} active codes",
        "ar": "استرداد جميع الاكواد النشطة ({count})",
    },
    "gift.redeem.code_all_display": {
        "en": "ALL ({count} codes)",
        "ar": "الكل ({count} اكواد)",
    },
    "gift.redeem.all": {
        "en": "ALL",
        "ar": "الكل",
    },
    "gift.redeem.unknown": {
        "en": "Unknown",
        "ar": "غير معروف",
    },
    "gift.redeem.confirm_title": {
        "en": "Confirm Gift Code Usage",
        "ar": "تاكيد استخدام كود الهدية",
    },
    "gift.redeem.confirm_body_single": {
        "en": "Are you sure you want to use this gift code?",
        "ar": "هل انت متاكد من استخدام هذا الكود؟",
    },
    "gift.redeem.confirm_body_multi": {
        "en": "Are you sure you want to use these gift codes?",
        "ar": "هل انت متاكد من استخدام هذه الاكواد؟",
    },
    "gift.redeem.details": {
        "en": "Details",
        "ar": "التفاصيل",
    },
    "gift.redeem.codes_label": {
        "en": "Gift Code{plural}:",
        "ar": "كود{plural} الهدية:",
    },
    "gift.redeem.alliances_label": {
        "en": "Alliances:",
        "ar": "التحالفات:",
    },
    "gift.redeem.total_redemptions": {
        "en": "Total redemptions:",
        "ar": "اجمالي الاستردادات:",
    },
    "gift.redeem.and_more": {
        "en": "and {count} more",
        "ar": "و {count} اخر",
    },
    "gift.redeem.queued_title": {
        "en": "Redemptions Queued Successfully",
        "ar": "تمت اضافة الاستردادات للطابور",
    },
    "gift.redeem.queued_body": {
        "en": "Gift code redemptions added to the queue.",
        "ar": "تمت اضافة استرداد اكواد الهدايا للطابور.",
    },
    "gift.redeem.your_redemption": {
        "en": "Your Redemption",
        "ar": "استردادك",
    },
    "gift.redeem.queue_details": {
        "en": "Full Queue Details",
        "ar": "تفاصيل الطابور",
    },
    "gift.redeem.queue_total": {
        "en": "Total items in queue:",
        "ar": "اجمالي العناصر في الطابور:",
    },
    "gift.redeem.queue_position": {
        "en": "Your position:",
        "ar": "ترتيبك:",
    },
    "gift.redeem.queue_processing": {
        "en": "Processing",
        "ar": "قيد المعالجة",
    },
    "gift.redeem.queue_notify": {
        "en": "You'll receive notifications as each alliance is processed.",
        "ar": "سيتم اشعارك عند معالجة كل تحالف.",
    },
    "gift.redeem.queue_footer": {
        "en": "Gift codes are processed sequentially to prevent issues.",
        "ar": "تتم معالجة الاكواد بالتسلسل لتجنب المشاكل.",
    },
    "gift.redeem.cancelled_title": {
        "en": "Operation Cancelled",
        "ar": "تم الغاء العملية",
    },
    "gift.redeem.cancelled_body": {
        "en": "The gift code usage has been cancelled.",
        "ar": "تم الغاء استخدام كود الهدية.",
    },
    "gift.settings.title": {
        "en": "Gift Code Settings",
        "ar": "اعدادات اكواد الهدايا",
    },
    "gift.settings.channel_mgmt": {
        "en": "Channel Management",
        "ar": "ادارة القنوات",
    },
    "gift.settings.channel_mgmt_desc": {
        "en": "Set up and manage the channel(s) where the bot scans for new codes",
        "ar": "اعداد وادارة القنوات التي يفحص فيها البوت الاكواد الجديدة",
    },
    "gift.settings.auto_redemption": {
        "en": "Automatic Redemption",
        "ar": "الاسترداد التلقائي",
    },
    "gift.settings.auto_redemption_desc": {
        "en": "Enable/disable auto-redemption of new valid gift codes",
        "ar": "تفعيل/تعطيل استرداد الاكواد الجديدة تلقائيا",
    },
    "gift.settings.priority": {
        "en": "Redemption Priority",
        "ar": "اولوية الاسترداد",
    },
    "gift.settings.priority_desc": {
        "en": "Change the order in which alliances auto-redeem new gift codes",
        "ar": "تغيير ترتيب التحالفات في الاسترداد التلقائي",
    },
    "gift.settings.history_scan": {
        "en": "Channel History Scan",
        "ar": "فحص سجل القناة",
    },
    "gift.settings.history_scan_desc": {
        "en": "Scan for gift codes in existing messages in a gift channel",
        "ar": "فحص الاكواد في الرسائل السابقة داخل قناة الهدايا",
    },
    "gift.settings.captcha": {
        "en": "CAPTCHA Settings",
        "ar": "اعدادات CAPTCHA",
    },
    "gift.settings.captcha_desc": {
        "en": "Configure CAPTCHA-solver related settings and image saving",
        "ar": "تهيئة اعدادات حل CAPTCHA وحفظ الصور",
    },
    "gift.priority.title": {
        "en": "Redemption Priority",
        "ar": "اولوية الاسترداد",
    },
    "gift.priority.description": {
        "en": "Configure the order in which alliances receive gift codes.\nSelect an alliance and use the buttons to change its position.",
        "ar": "قم بتحديد ترتيب استلام التحالفات لاكواد الهدايا.\nاختر تحالفا ثم استخدم الازرار لتغيير الترتيب.",
    },
    "gift.priority.current_order": {
        "en": "Current Priority Order",
        "ar": "ترتيب الاولوية الحالي",
    },
    "gift.priority.none": {
        "en": "No alliances configured",
        "ar": "لا توجد تحالفات مهيئة",
    },
    "gift.priority.position": {
        "en": "Priority position {position}",
        "ar": "ترتيب الاولوية {position}",
    },
    "gift.priority.select_placeholder": {
        "en": "Select an alliance to move",
        "ar": "اختر تحالفا لنقله",
    },
    "gift.priority.select_first": {
        "en": "Please select an alliance first.",
        "ar": "يرجى اختيار تحالف اولا.",
    },
    "gift.priority.already_top": {
        "en": "Alliance is already at the top.",
        "ar": "التحالف في الاعلى بالفعل.",
    },
    "gift.priority.already_bottom": {
        "en": "Alliance is already at the bottom.",
        "ar": "التحالف في الاسفل بالفعل.",
    },
    "gift.priority.updated_title": {
        "en": "Priority Updated",
        "ar": "تم تحديث الاولوية",
    },
    "gift.priority.updated_body": {
        "en": "Redemption priority order has been saved.",
        "ar": "تم حفظ ترتيب اولوية الاسترداد.",
    },
    "gift.priority.global_only": {
        "en": "Only global administrators can manage redemption priority.",
        "ar": "فقط المشرف العام يمكنه ادارة اولوية الاسترداد.",
    },
    "gift.priority.none_found": {
        "en": "No alliances found.",
        "ar": "لم يتم العثور على تحالفات.",
    },
    "gift.common.details_title": {
        "en": "Gift Code Details",
        "ar": "تفاصيل كود الهدية",
    },
    "gift.common.gift_code_label": {
        "en": "Gift Code:",
        "ar": "كود الهدية:",
    },
    "gift.common.status_label": {
        "en": "Status:",
        "ar": "الحالة:",
    },
    "gift.common.action_label": {
        "en": "Action:",
        "ar": "الاجراء:",
    },
    "gift.common.reason_label": {
        "en": "Reason:",
        "ar": "السبب:",
    },
    "gift.common.time_label": {
        "en": "Time:",
        "ar": "الوقت:",
    },
    "gift.common.processed_label": {
        "en": "Processed:",
        "ar": "المعالج:",
    },
    "gift.common.processed_before_halt_label": {
        "en": "Processed before halt:",
        "ar": "المعالج قبل الايقاف:",
    },
    "gift.common.total_members_label": {
        "en": "Total Members:",
        "ar": "اجمالي الاعضاء:",
    },
    "gift.common.success_label": {
        "en": "Success:",
        "ar": "الناجح:",
    },
    "gift.common.already_redeemed_label": {
        "en": "Already Redeemed:",
        "ar": "تم الاسترداد مسبقا:",
    },
    "gift.common.retrying_label": {
        "en": "Retrying:",
        "ar": "اعادة المحاولة:",
    },
    "gift.common.failed_label": {
        "en": "Failed:",
        "ar": "فشل:",
    },
    "gift.common.na": {
        "en": "N/A",
        "ar": "غير متاح",
    },
    "gift.common.yes": {
        "en": "Yes",
        "ar": "نعم",
    },
    "gift.common.no": {
        "en": "No",
        "ar": "لا",
    },
    "gift.redeem.process_title": {
        "en": "Processing Redemption",
        "ar": "جاري معالجة الاسترداد",
    },
    "gift.redeem.process_desc": {
        "en": "Starting gift code redemption for **{alliance}**...\n**Gift Code:** `{code}`",
        "ar": "بدء استرداد كود الهدية للتحالف **{alliance}**...\n**كود الهدية:** `{code}`",
    },
    "gift.redeem.complete_title": {
        "en": "Redemption Complete",
        "ar": "اكتمل الاسترداد",
    },
    "gift.redeem.complete_desc": {
        "en": "Gift code redemption completed for **{alliance}**.\n**Gift Code:** `{code}`",
        "ar": "اكتمل استرداد كود الهدية للتحالف **{alliance}**.\n**كود الهدية:** `{code}`",
    },
    "gift.redeem.error_title": {
        "en": "Redemption Error",
        "ar": "خطا في الاسترداد",
    },
    "gift.redeem.error_desc": {
        "en": "An error occurred during redemption for **{alliance}**: {error}",
        "ar": "حدث خطا اثناء الاسترداد للتحالف **{alliance}**: {error}",
    },
    "gift.redeem.progress_title": {
        "en": "Gift Code Redemption: {code}",
        "ar": "استرداد كود الهدية: {code}",
    },
    "gift.redeem.progress_status_for": {
        "en": "Status for Alliance:",
        "ar": "حالة التحالف:",
    },
    "gift.redeem.error_breakdown_title": {
        "en": "Error Breakdown:",
        "ar": "تفاصيل الاخطاء:",
    },
    "gift.redeem.error_breakdown.too_poor_spend_more": {
        "en": "**{count}** members failed to spend enough to reach VIP12.",
        "ar": "فشل **{count}** عضو بسبب عدم انفاق كاف للوصول الى VIP12.",
    },
    "gift.redeem.error_breakdown.too_small_spend_more": {
        "en": "**{count}** members failed due to insufficient furnace level.",
        "ar": "فشل **{count}** عضو بسبب انخفاض مستوى الفرن.",
    },
    "gift.redeem.error_breakdown.timeout_retry": {
        "en": "**{count}** members were staring into the void, until the void finally timed out on them.",
        "ar": "واجه **{count}** عضو مهلة وانتظار طويل حتى انتهت المهلة.",
    },
    "gift.redeem.error_breakdown.login_expired_mid_process": {
        "en": "**{count}** members login failed mid-process. How'd that even happen?",
        "ar": "فشل تسجيل الدخول لـ **{count}** عضو اثناء المعالجة.",
    },
    "gift.redeem.error_breakdown.login_failed": {
        "en": "**{count}** members failed due to login issues. Try logging it off and on again!",
        "ar": "فشل **{count}** عضو بسبب مشكلة تسجيل الدخول.",
    },
    "gift.redeem.error_breakdown.captcha_solving_failed": {
        "en": "**{count}** members lost the battle against CAPTCHA. You sure those weren't just bots?",
        "ar": "فشل **{count}** عضو بسبب فشل حل CAPTCHA.",
    },
    "gift.redeem.error_breakdown.captcha_solver_error": {
        "en": "**{count}** members failed due to a CAPTCHA solver issue. We're still trying to solve that one.",
        "ar": "فشل **{count}** عضو بسبب مشكلة في حل CAPTCHA.",
    },
    "gift.redeem.error_breakdown.ocr_disabled": {
        "en": "**{count}** members failed since OCR is disabled. Try turning it on first!",
        "ar": "فشل **{count}** عضو لان OCR معطل. قم بتفعيله اولا.",
    },
    "gift.redeem.error_breakdown.sign_error": {
        "en": "**{count}** members failed due to a signature error. Something went wrong.",
        "ar": "فشل **{count}** عضو بسبب خطا في التوقيع.",
    },
    "gift.redeem.error_breakdown.error": {
        "en": "**{count}** members failed due to a general error. Might want to check the logs.",
        "ar": "فشل **{count}** عضو بسبب خطا عام. تحقق من السجلات.",
    },
    "gift.redeem.error_breakdown.unknown_api_response": {
        "en": "**{count}** members failed with an unknown API response. Say what?",
        "ar": "فشل **{count}** عضو بسبب استجابة API غير معروفة.",
    },
    "gift.redeem.error_breakdown.connection_error": {
        "en": "**{count}** members failed due to bot connection issues. Did the admin trip over the cable again?",
        "ar": "فشل **{count}** عضو بسبب مشكلة اتصال البوت.",
    },
    "gift.redeem.error_breakdown.unknown": {
        "en": "**{count}** members failed with status: {status}",
        "ar": "فشل **{count}** عضو بالحالة: {status}",
    },
    "gift.redeem.ocr_disabled_title": {
        "en": "OCR/Captcha Solver Disabled",
        "ar": "حل OCR/CAPTCHA معطل",
    },
    "gift.redeem.ocr_required": {
        "en": "Gift code redemption requires the OCR/captcha solver to be enabled.\nPlease enable it first using the settings command.",
        "ar": "استرداد اكواد الهدايا يتطلب تفعيل حل OCR/CAPTCHA.\nيرجى تفعيله اولا من الاعدادات.",
    },
    "gift.redeem.invalid_title": {
        "en": "Gift Code Invalid",
        "ar": "كود الهدية غير صالح",
    },
    "gift.redeem.invalid_previously": {
        "en": "Code previously marked as invalid",
        "ar": "تم تعليم الكود كغير صالح مسبقا",
    },
    "gift.redeem.invalid_time_error": {
        "en": "Code has expired (TIME_ERROR)",
        "ar": "انتهت صلاحية الكود (TIME_ERROR)",
    },
    "gift.redeem.invalid_cdk_not_found": {
        "en": "Code not found or incorrect (CDK_NOT_FOUND)",
        "ar": "الكود غير موجود او غير صحيح (CDK_NOT_FOUND)",
    },
    "gift.redeem.invalid_usage_limit": {
        "en": "Usage limit reached (USAGE_LIMIT)",
        "ar": "تم الوصول لحد الاستخدام (USAGE_LIMIT)",
    },
    "gift.redeem.invalid_generic": {
        "en": "Code invalid ({status})",
        "ar": "الكود غير صالح ({status})",
    },
    "gift.redeem.invalid_action": {
        "en": "Code status is 'invalid' in database",
        "ar": "حالة الكود 'غير صالح' في قاعدة البيانات",
    },
    "gift.redeem.invalid_runtime_title": {
        "en": "Gift Code Invalid: {code}",
        "ar": "كود الهدية غير صالح: {code}",
    },
    "gift.redeem.halted_title": {
        "en": "Gift Code Redemption Halted",
        "ar": "تم ايقاف استرداد كود الهدية",
    },
    "gift.redeem.invalid_action_halt": {
        "en": "Code marked as invalid in database. Remaining members for this alliance will not be processed.",
        "ar": "تم تعليم الكود كغير صالح في قاعدة البيانات. لن تتم معالجة بقية اعضاء هذا التحالف.",
    },
    "gift.redeem.sign_error_title": {
        "en": "Sign Error: {code}",
        "ar": "خطا التوقيع: {code}",
    },
    "gift.redeem.sign_error_heading": {
        "en": "Bot Configuration Error",
        "ar": "خطا في تهيئة البوت",
    },
    "gift.redeem.sign_error_reason": {
        "en": "Sign Error (check bot config/encrypt key)",
        "ar": "خطا في التوقيع (تحقق من اعدادات البوت/مفتاح التشفير)",
    },
    "gift.redeem.sign_error_action": {
        "en": "Redemption stopped. Check bot configuration.",
        "ar": "تم ايقاف الاسترداد. تحقق من اعدادات البوت.",
    },
    "gift.redeem.complete_title_with_code": {
        "en": "Gift Code Process Complete: {code}",
        "ar": "اكتملت معالجة كود الهدية: {code}",
    },
    "gift.redeem.no_members_title_with_code": {
        "en": "No Members to Process for Code: {code}",
        "ar": "لا يوجد اعضاء لمعالجة الكود: {code}",
    },
    "gift.redeem.unexpected_error": {
        "en": "An unexpected error occurred processing `{code}` for {alliance}.",
        "ar": "حدث خطا غير متوقع اثناء معالجة `{code}` للتحالف {alliance}.",
    },
    "gift.error.process_selection": {
        "en": "An error occurred while processing your selection.",
        "ar": "حدث خطا اثناء معالجة اختيارك.",
    },
    "gift.channel.remove_setting_button": {
        "en": "Remove Setting",
        "ar": "ازالة الاعداد",
    },
    "gift.channel.remove_request_error": {
        "en": "An error occurred while processing the removal request.",
        "ar": "حدث خطا اثناء معالجة طلب الازالة.",
    },
    "gift.ocr.admin_only": {
        "en": "Only global administrators can access OCR settings.",
        "ar": "فقط المشرف العام يمكنه الوصول الى اعدادات OCR.",
    },
    "gift.ocr.title": {
        "en": "CAPTCHA Solver Settings (ONNX)",
        "ar": "اعدادات حل CAPTCHA (ONNX)",
    },
    "gift.ocr.description": {
        "en": "Configure the automatic CAPTCHA solver for gift code redemption.",
        "ar": "تهيئة حل CAPTCHA التلقائي لاسترداد اكواد الهدايا.",
    },
    "gift.ocr.current_settings": {
        "en": "Current Settings",
        "ar": "الاعدادات الحالية",
    },
    "gift.ocr.ocr_enabled": {
        "en": "OCR Enabled:",
        "ar": "تفعيل OCR:",
    },
    "gift.ocr.save_images": {
        "en": "Save CAPTCHA Images:",
        "ar": "حفظ صور CAPTCHA:",
    },
    "gift.ocr.test_id": {
        "en": "Test ID:",
        "ar": "معرف الاختبار:",
    },
    "gift.ocr.onnx_runtime": {
        "en": "ONNX Runtime:",
        "ar": "ONNX Runtime:",
    },
    "gift.ocr.onnx_found": {
        "en": "Found",
        "ar": "موجود",
    },
    "gift.ocr.onnx_missing": {
        "en": "Missing",
        "ar": "غير موجود",
    },
    "gift.ocr.solver_status": {
        "en": "Solver Status:",
        "ar": "حالة الحل:",
    },
    "gift.ocr.status.ready": {
        "en": "Initialized & Ready",
        "ar": "مهيأ وجاهز",
    },
    "gift.ocr.status.init_failed": {
        "en": "Initialization Failed (Check Logs)",
        "ar": "فشل التهيئة (تحقق من السجلات)",
    },
    "gift.ocr.status.instance_error": {
        "en": "Error (Instance missing flags)",
        "ar": "خطا (المثيل يفتقد المؤشرات)",
    },
    "gift.ocr.status.disabled_or_failed": {
        "en": "Disabled or Init Failed",
        "ar": "معطل او فشلت التهيئة",
    },
    "gift.ocr.status.missing_lib": {
        "en": "onnxruntime library missing",
        "ar": "مكتبة onnxruntime غير موجودة",
    },
    "gift.ocr.save.none": {
        "en": "None",
        "ar": "لا شيء",
    },
    "gift.ocr.save.failed_only": {
        "en": "Failed Only",
        "ar": "الفاشلة فقط",
    },
    "gift.ocr.save.success_only": {
        "en": "Success Only",
        "ar": "الناجحة فقط",
    },
    "gift.ocr.save.all": {
        "en": "All",
        "ar": "الكل",
    },
    "gift.ocr.save.unknown": {
        "en": "Unknown ({value})",
        "ar": "غير معروف ({value})",
    },
    "gift.ocr.missing_library_title": {
        "en": "Missing Library",
        "ar": "مكتبة مفقودة",
    },
    "gift.ocr.missing_library_body": {
        "en": "ONNX Runtime and required libraries are needed for CAPTCHA solving.\nThe model files must be in the bot/models/ directory.\nTry installing dependencies:\n```pip install onnxruntime pillow numpy\n",
        "ar": "مكتبة ONNX Runtime والمكتبات المطلوبة ضرورية لحل CAPTCHA.\nيجب ان تكون ملفات النموذج في مجلد bot/models/.\nجرب تثبيت الاعتمادات:\n```pip install onnxruntime pillow numpy\n",
    },
    "gift.ocr.stats.solver_title": {
        "en": "Captcha Solver (Raw Format):",
        "ar": "حل CAPTCHA (صيغة خام):",
    },
    "gift.ocr.stats.solver_calls": {
        "en": "• Solver Calls: `{count}`",
        "ar": "• عدد مرات الحل: `{count}`",
    },
    "gift.ocr.stats.valid_format": {
        "en": "• Valid Format Returns: `{count}` ({rate}%)",
        "ar": "• ارجاع صيغة صالحة: `{count}` ({rate}%)",
    },
    "gift.ocr.stats.redemption_title": {
        "en": "Redemption Process (Server Side):",
        "ar": "عملية الاسترداد (جانب الخادم):",
    },
    "gift.ocr.stats.captcha_submissions": {
        "en": "• Captcha Submissions: `{count}`",
        "ar": "• ارسال CAPTCHA: `{count}`",
    },
    "gift.ocr.stats.server_success": {
        "en": "• Server Validation Success: `{count}`",
        "ar": "• نجاح تحقق الخادم: `{count}`",
    },
    "gift.ocr.stats.server_failure": {
        "en": "• Server Validation Failure: `{count}`",
        "ar": "• فشل تحقق الخادم: `{count}`",
    },
    "gift.ocr.stats.server_pass_rate": {
        "en": "• Server Pass Rate: `{rate}%`",
        "ar": "• معدل المرور في الخادم: `{rate}%`",
    },
    "gift.ocr.stats.avg_processing": {
        "en": "• Avg. ID Processing Time: `{seconds}s` (over `{total}` IDs)",
        "ar": "• متوسط وقت معالجة المعرف: `{seconds}s` (من `{total}` معرف)",
    },
    "gift.ocr.stats.title": {
        "en": "Processing Statistics (Since Bot Start)",
        "ar": "احصائيات المعالجة (منذ بدء البوت)",
    },
    "gift.ocr.note_title": {
        "en": "Important Note",
        "ar": "ملاحظة مهمة",
    },
    "gift.ocr.note_body": {
        "en": "Saving images (especially 'All') can consume significant disk space over time.",
        "ar": "حفظ الصور (خصوصا 'الكل') قد يستهلك مساحة كبيرة مع الوقت.",
    },
    "gift.ocr.error.db": {
        "en": "A database error occurred while loading OCR settings.",
        "ar": "حدث خطا في قاعدة البيانات اثناء تحميل اعدادات OCR.",
    },
    "gift.ocr.error.unexpected": {
        "en": "An unexpected error occurred while loading OCR settings.",
        "ar": "حدث خطا غير متوقع اثناء تحميل اعدادات OCR.",
    },
    "gift.ocr.button.enable_solver": {
        "en": "Enable CAPTCHA Solver",
        "ar": "تفعيل حل CAPTCHA",
    },
    "gift.ocr.button.disable_solver": {
        "en": "Disable CAPTCHA Solver",
        "ar": "تعطيل حل CAPTCHA",
    },
    "gift.ocr.button.test_solver": {
        "en": "Test CAPTCHA Solver",
        "ar": "اختبار حل CAPTCHA",
    },
    "gift.ocr.button.change_test_id": {
        "en": "Change Test ID",
        "ar": "تغيير معرف الاختبار",
    },
    "gift.ocr.button.clear_cache": {
        "en": "Clear Redemption Cache",
        "ar": "مسح كاش الاسترداد",
    },
    "gift.ocr.select.placeholder": {
        "en": "Select Captcha Image Saving Option",
        "ar": "اختر خيار حفظ صور CAPTCHA",
    },
    "gift.ocr.select.none": {
        "en": "Don't Save Any Images",
        "ar": "لا تحفظ اي صور",
    },
    "gift.ocr.select.none_desc": {
        "en": "Fastest, no disk usage",
        "ar": "الاسرع، بدون استخدام قرص",
    },
    "gift.ocr.select.failed": {
        "en": "Save Only Failed Captchas",
        "ar": "احفظ CAPTCHA الفاشلة فقط",
    },
    "gift.ocr.select.failed_desc": {
        "en": "For debugging server rejects",
        "ar": "لتصحيح رفض الخادم",
    },
    "gift.ocr.select.success": {
        "en": "Save Only Successful Captchas",
        "ar": "احفظ CAPTCHA الناجحة فقط",
    },
    "gift.ocr.select.success_desc": {
        "en": "To see what worked",
        "ar": "لرؤية ما نجح",
    },
    "gift.ocr.select.all": {
        "en": "Save All Captchas (High Disk Usage!)",
        "ar": "احفظ كل CAPTCHA (استهلاك عالي للقرص!)",
    },
    "gift.ocr.select.all_desc": {
        "en": "Comprehensive debugging",
        "ar": "تصحيح شامل",
    },
    "gift.ocr.select_invalid": {
        "en": "Invalid selection value for image saving.",
        "ar": "قيمة اختيار غير صالحة لحفظ الصور.",
    },
    "gift.ocr.select_update_error": {
        "en": "An error occurred while updating image saving settings.",
        "ar": "حدث خطا اثناء تحديث اعدادات حفظ الصور.",
    },
    "gift.ocr.error.onnx_missing": {
        "en": "Required library (onnxruntime) is not installed or failed to load.",
        "ar": "المكتبة المطلوبة (onnxruntime) غير مثبتة او فشل تحميلها.",
    },
    "gift.ocr.error.solver_not_ready": {
        "en": "CAPTCHA solver is not initialized. Ensure OCR is enabled.",
        "ar": "حل CAPTCHA غير مهيأ. تاكد من تفعيل OCR.",
    },
    "gift.ocr.error.test_cooldown": {
        "en": "Please wait {seconds} more seconds before testing again.",
        "ar": "يرجى الانتظار {seconds} ثانية قبل الاختبار مرة اخرى.",
    },
    "gift.ocr.test_login_failed": {
        "en": "Login failed with test ID {test_id}. Please check if the ID is valid.",
        "ar": "فشل تسجيل الدخول بمعرف الاختبار {test_id}. يرجى التحقق من صحة المعرف.",
    },
    "gift.ocr.test_login_parse_error": {
        "en": "Error processing login response.",
        "ar": "حدث خطا اثناء معالجة استجابة تسجيل الدخول.",
    },
    "gift.ocr.test_fetch_error": {
        "en": "Error fetching test captcha from the API: `{error}`",
        "ar": "حدث خطا اثناء جلب CAPTCHA التجريبية من API: `{error}`",
    },
    "gift.ocr.test_decode_error": {
        "en": "Failed to decode captcha image data.",
        "ar": "فشل في فك ترميز بيانات صورة CAPTCHA.",
    },
    "gift.ocr.test_no_image": {
        "en": "Failed to retrieve captcha image data from API.",
        "ar": "فشل في استرجاع بيانات صورة CAPTCHA من API.",
    },
    "gift.ocr.test_internal_error": {
        "en": "Internal error before solving captcha.",
        "ar": "حدث خطا داخلي قبل حل CAPTCHA.",
    },
    "gift.ocr.test_results_title": {
        "en": "CAPTCHA Solver Test Results (ONNX)",
        "ar": "نتائج اختبار حل CAPTCHA (ONNX)",
    },
    "gift.ocr.test_summary": {
        "en": "Test Summary",
        "ar": "ملخص الاختبار",
    },
    "gift.ocr.test_ocr_success": {
        "en": "OCR Success:",
        "ar": "نجاح OCR:",
    },
    "gift.ocr.test_code": {
        "en": "Recognized Code:",
        "ar": "الكود المعترف به:",
    },
    "gift.ocr.test_confidence": {
        "en": "Confidence:",
        "ar": "الثقة:",
    },
    "gift.ocr.test_solve_time": {
        "en": "Solve Time:",
        "ar": "وقت الحل:",
    },
    "gift.ocr.test_image_saved_title": {
        "en": "Captcha Image Saved",
        "ar": "تم حفظ صورة CAPTCHA",
    },
    "gift.ocr.test_image_saved_body": {
        "en": "`{filename}` in `{directory}`",
        "ar": "`{filename}` في `{directory}`",
    },
    "gift.ocr.test_image_save_error_title": {
        "en": "Image Save Error",
        "ar": "خطا حفظ الصورة",
    },
    "gift.ocr.test_save_name_error": {
        "en": "Could not find unique filename for {filename} after 100 tries.",
        "ar": "تعذر ايجاد اسم ملف فريد لـ {filename} بعد 100 محاولة.",
    },
    "gift.ocr.test_save_error": {
        "en": "Error during saving: {error}",
        "ar": "حدث خطا اثناء الحفظ: {error}",
    },
    "gift.ocr.test_connection_error": {
        "en": "Connection error: Unable to reach WOS API. Please check your internet connection.",
        "ar": "خطا اتصال: تعذر الوصول الى WOS API. تحقق من اتصال الانترنت.",
    },
    "gift.ocr.test_timeout": {
        "en": "Connection error: Request timed out. WOS API may be overloaded or unavailable.",
        "ar": "خطا اتصال: انتهت مهلة الطلب. قد يكون WOS API مزدحما او غير متاح.",
    },
    "gift.ocr.test_request_error": {
        "en": "Connection error: {error}. Please try again later.",
        "ar": "خطا اتصال: {error}. يرجى المحاولة لاحقا.",
    },
    "gift.ocr.test_unexpected_error": {
        "en": "An unexpected error occurred during the test: `{error}`. Please check the bot logs.",
        "ar": "حدث خطا غير متوقع اثناء الاختبار: `{error}`. يرجى التحقق من سجلات البوت.",
    },
    "gift.ocr.cache_clear_title": {
        "en": "Clear Redemption Cache",
        "ar": "مسح كاش الاسترداد",
    },
    "gift.ocr.cache_clear_desc": {
        "en": "This will **permanently delete** all gift code redemption records from the database.\n\n**What this does:**\n• Removes all entries from the `user_giftcodes` table\n• Allows users to attempt redeeming gift codes again\n• Useful for development testing and image collection\n\n**Warning:** This action cannot be undone!",
        "ar": "سيقوم هذا **بحذف دائم** لجميع سجلات استرداد اكواد الهدايا من قاعدة البيانات.\n\n**ما الذي يفعله هذا:**\n• يزيل كل الادخالات من جدول `user_giftcodes`\n• يسمح للمستخدمين بمحاولة استرداد الاكواد مجددا\n• مفيد لاختبارات التطوير وجمع الصور\n\n**تحذير:** لا يمكن التراجع عن هذا الاجراء!",
    },
    "gift.ocr.cache_current_records": {
        "en": "Current Records",
        "ar": "السجلات الحالية",
    },
    "gift.ocr.cache_current_records_value": {
        "en": "{count} redemption records will be deleted",
        "ar": "سيتم حذف {count} سجل استرداد",
    },
    "gift.ocr.cache_current_records_error": {
        "en": "Unable to count records",
        "ar": "تعذر عد السجلات",
    },
    "gift.ocr.cache_confirm_button": {
        "en": "Confirm Clear",
        "ar": "تاكيد المسح",
    },
    "gift.ocr.cache_cleared_title": {
        "en": "Redemption Cache Cleared",
        "ar": "تم مسح كاش الاسترداد",
    },
    "gift.ocr.cache_cleared_body": {
        "en": "Successfully deleted {count} redemption records.\n\nUsers can now attempt to redeem gift codes again.",
        "ar": "تم حذف {count} سجل استرداد بنجاح.\n\nيمكن للمستخدمين الان محاولة استرداد الاكواد مجددا.",
    },
    "gift.ocr.cache_clear_error_title": {
        "en": "Error",
        "ar": "خطا",
    },
    "gift.ocr.cache_clear_error_body": {
        "en": "Failed to clear redemption cache: {error}",
        "ar": "فشل مسح كاش الاسترداد: {error}",
    },
    "gift.ocr.cache_cancelled_title": {
        "en": "Operation Cancelled",
        "ar": "تم الغاء العملية",
    },
    "gift.ocr.cache_cancelled_body": {
        "en": "Redemption cache was not cleared.",
        "ar": "لم يتم مسح كاش الاسترداد.",
    },
    "gift.ocr.cache_timeout_title": {
        "en": "Timeout",
        "ar": "انتهت المهلة",
    },
    "gift.ocr.cache_timeout_body": {
        "en": "Confirmation timed out. Redemption cache was not cleared.",
        "ar": "انتهت مهلة التاكيد. لم يتم مسح كاش الاسترداد.",
    },
    "gift.ocr.update_in_progress": {
        "en": "Your settings are being updated... Please wait.",
        "ar": "يتم تحديث اعداداتك... يرجى الانتظار.",
    },
    "gift.ocr.update_timeout": {
        "en": "Timed out waiting for settings to update. Please try again or check logs.",
        "ar": "انتهت المهلة اثناء انتظار تحديث الاعدادات. حاول مرة اخرى او تحقق من السجلات.",
    },
    "gift.ocr.update_error": {
        "en": "An error occurred during the update: {error}",
        "ar": "حدث خطا اثناء التحديث: {error}",
    },
    "gift.ocr.update_refresh_warn": {
        "en": "Couldn't fully refresh the view.",
        "ar": "تعذر تحديث الواجهة بالكامل.",
    },
    "gift.ocr.update.settings_updated": {
        "en": "Settings updated.",
        "ar": "تم تحديث الاعدادات.",
    },
    "gift.ocr.update.solver_enabled": {
        "en": "Solver has been enabled.",
        "ar": "تم تفعيل الحل.",
    },
    "gift.ocr.update.solver_disabled": {
        "en": "Solver has been disabled.",
        "ar": "تم تعطيل الحل.",
    },
    "gift.ocr.update.image_saving_updated": {
        "en": "Image saving preference updated.",
        "ar": "تم تحديث تفضيل حفظ الصور.",
    },
    "gift.ocr.update.solver_reinitialized": {
        "en": "Solver reinitialized.",
        "ar": "تم اعادة تهيئة الحل.",
    },
    "gift.ocr.update.solver_reinit_failed": {
        "en": "Solver reinitialization failed.",
        "ar": "فشلت اعادة تهيئة الحل.",
    },
    "gift.ocr.update.solver_init_missing_lib": {
        "en": "Solver initialization failed (Missing Library: {error}).",
        "ar": "فشلت تهيئة الحل (مكتبة مفقودة: {error}).",
    },
    "gift.ocr.update.solver_init_failed": {
        "en": "Solver initialization failed ({error}).",
        "ar": "فشلت تهيئة الحل ({error}).",
    },
    "gift.ocr.update.result": {
        "en": "CAPTCHA solver settings: {detail}",
        "ar": "اعدادات حل CAPTCHA: {detail}",
    },
    "gift.ocr.update.db_error": {
        "en": "Database error updating OCR settings: {error}",
        "ar": "خطا قاعدة بيانات اثناء تحديث اعدادات OCR: {error}",
    },
    "gift.ocr.update.unexpected_error": {
        "en": "Unexpected error updating OCR settings: {error}",
        "ar": "خطا غير متوقع اثناء تحديث اعدادات OCR: {error}",
    },
    "gift.ocr.test_id_title": {
        "en": "Change Test ID",
        "ar": "تغيير معرف الاختبار",
    },
    "gift.ocr.test_id_label": {
        "en": "Enter New Player ID",
        "ar": "ادخل معرف لاعب جديد",
    },
    "gift.ocr.test_id_placeholder": {
        "en": "Example: 244886619",
        "ar": "مثال: 244886619",
    },
    "gift.ocr.test_id_invalid_format": {
        "en": "Invalid ID format. Please enter a numeric ID.",
        "ar": "صيغة المعرف غير صالحة. يرجى ادخال رقم.",
    },
    "gift.ocr.test_id_updated_title": {
        "en": "Test ID Updated",
        "ar": "تم تحديث معرف الاختبار",
    },
    "gift.ocr.test_id_config_title": {
        "en": "Test ID Configuration",
        "ar": "تهيئة معرف الاختبار",
    },
    "gift.ocr.test_id_status_validated": {
        "en": "Validated",
        "ar": "تم التحقق",
    },
    "gift.ocr.test_id_action_updated": {
        "en": "Updated in database",
        "ar": "تم التحديث في قاعدة البيانات",
    },
    "gift.ocr.test_id_update_failed": {
        "en": "Failed to update test ID in database. Check logs for details.",
        "ar": "فشل تحديث معرف الاختبار في قاعدة البيانات. تحقق من السجلات.",
    },
    "gift.ocr.test_id_invalid_title": {
        "en": "Invalid Test ID",
        "ar": "معرف اختبار غير صالح",
    },
    "gift.ocr.test_id_validation_title": {
        "en": "Test ID Validation",
        "ar": "التحقق من معرف الاختبار",
    },
    "gift.ocr.test_id_status_invalid": {
        "en": "Invalid ID",
        "ar": "معرف غير صالح",
    },
    "gift.ocr.test_id_error": {
        "en": "An error occurred: {error}",
        "ar": "حدث خطا: {error}",
    },
    "gift.modal.create_title": {
        "en": "Create Gift Code",
        "ar": "انشاء كود هدية",
    },
    "gift.modal.create_label": {
        "en": "Gift Code",
        "ar": "كود الهدية",
    },
    "gift.modal.create_placeholder": {
        "en": "Enter the gift code",
        "ar": "ادخل كود الهدية",
    },
    "gift.modal.create_result_title": {
        "en": "Gift Code Creation Result",
        "ar": "نتيجة انشاء كود الهدية",
    },
    "gift.modal.exists_title": {
        "en": "Gift Code Exists",
        "ar": "كود الهدية موجود",
    },
    "gift.modal.exists_status": {
        "en": "Code already exists in database.",
        "ar": "الكود موجود بالفعل في قاعدة البيانات.",
    },
    "gift.modal.validation_title": {
        "en": "Validating Gift Code...",
        "ar": "جار التحقق من كود الهدية...",
    },
    "gift.modal.validation_desc": {
        "en": "Checking if `{code}` is valid...",
        "ar": "جار التحقق من صلاحية `{code}`...",
    },
    "gift.modal.validated_title": {
        "en": "Gift Code Validated",
        "ar": "تم التحقق من كود الهدية",
    },
    "gift.modal.action_added": {
        "en": "Added to database and sent to API",
        "ar": "تمت اضافته لقاعدة البيانات وارساله الى API",
    },
    "gift.modal.invalid_title": {
        "en": "Invalid Gift Code",
        "ar": "كود الهدية غير صالح",
    },
    "gift.modal.action_not_added": {
        "en": "Code not added to database",
        "ar": "لم يتم اضافة الكود الى قاعدة البيانات",
    },
    "gift.modal.pending_title": {
        "en": "Gift Code Added (Pending)",
        "ar": "تمت اضافة كود الهدية (قيد التحقق)",
    },
    "gift.modal.action_pending": {
        "en": "Added for later validation",
        "ar": "تمت اضافته للتحقق لاحقا",
    },
    "gift.modal.db_error_title": {
        "en": "Database Error",
        "ar": "خطا في قاعدة البيانات",
    },
    "gift.modal.db_error_body": {
        "en": "Failed to save gift code `{code}` to the database. Please check logs.",
        "ar": "فشل حفظ كود الهدية `{code}` في قاعدة البيانات. تحقق من السجلات.",
    },
    "gift.modal.delete_title": {
        "en": "Delete Gift Code",
        "ar": "حذف كود هدية",
    },
    "gift.modal.delete_label": {
        "en": "Gift Code",
        "ar": "كود الهدية",
    },
    "gift.modal.delete_placeholder": {
        "en": "Enter the gift code to delete",
        "ar": "ادخل كود الهدية المراد حذفه",
    },
    "gift.modal.delete_not_found": {
        "en": "Gift code not found!",
        "ar": "لم يتم العثور على كود الهدية!",
    },
    "gift.modal.delete_success_title": {
        "en": "Gift Code Deleted",
        "ar": "تم حذف كود الهدية",
    },
    "gift.modal.delete_success_body": {
        "en": "Gift code `{code}` has been deleted successfully.",
        "ar": "تم حذف كود الهدية `{code}` بنجاح.",
    },
    "gift.validation.processing_title": {
        "en": "Processing Gift Code...",
        "ar": "جاري معالجة كود الهدية...",
    },
    "gift.validation.processing_desc": {
        "en": "Validating `{code}` (Position in queue: Processing now)",
        "ar": "جار التحقق من `{code}` (الموقع في الطابور: تتم المعالجة الان)",
    },
    "gift.validation.exists_title": {
        "en": "Gift Code Already Known",
        "ar": "كود الهدية معروف مسبقا",
    },
    "gift.validation.exists_status": {
        "en": "Already in database.",
        "ar": "موجود في قاعدة البيانات.",
    },
    "gift.validation.sender_label": {
        "en": "Sender:",
        "ar": "المرسل:",
    },
    "gift.validation.validated_title": {
        "en": "Gift Code Validated",
        "ar": "تم التحقق من كود الهدية",
    },
    "gift.validation.invalid_title": {
        "en": "Invalid Gift Code",
        "ar": "كود الهدية غير صالح",
    },
    "gift.validation.pending_title": {
        "en": "Gift Code Added (Pending)",
        "ar": "تمت اضافة كود الهدية (قيد التحقق)",
    },
    "gift.validation.action_not_added": {
        "en": "Code not added to database",
        "ar": "لم يتم اضافة الكود الى قاعدة البيانات",
    },
    "gift.validation.action_pending": {
        "en": "Added for later validation",
        "ar": "تمت اضافته للتحقق لاحقا",
    },
    "gift.validation.invalidated_title": {
        "en": "Gift Code Invalidated",
        "ar": "تم ابطال كود الهدية",
    },
    "gift.validation.added_reply": {
        "en": "Gift code successfully added.",
        "ar": "تمت اضافة كود الهدية بنجاح.",
    },
    "gift.validation.expired_reply": {
        "en": "Gift code expired.",
        "ar": "انتهت صلاحية كود الهدية.",
    },
    "gift.validation.incorrect_reply": {
        "en": "The gift code is incorrect.",
        "ar": "كود الهدية غير صحيح.",
    },
    "gift.validation.usage_limit_reply": {
        "en": "Usage limit has been reached for this code.",
        "ar": "تم الوصول لحد الاستخدام لهذا الكود.",
    },
    "gift.batch.title": {
        "en": "Batch Redemption Progress",
        "ar": "تقدم الاسترداد الجماعي",
    },
    "gift.batch.codes_label": {
        "en": "Gift Code",
        "ar": "كود الهدية",
    },
    "gift.batch.codes_label_singular": {
        "en": "Gift Code",
        "ar": "كود الهدية",
    },
    "gift.batch.codes_label_plural": {
        "en": "Gift Codes",
        "ar": "اكواد الهدايا",
    },
    "gift.batch.code_all_display": {
        "en": "ALL ({count} codes)",
        "ar": "الكل ({count} اكواد)",
    },
    "gift.batch.progress_label": {
        "en": "Progress:",
        "ar": "التقدم:",
    },
    "gift.batch.alliances_label": {
        "en": "alliances",
        "ar": "تحالفات",
    },
    "gift.channel.setup.not_authorized": {
        "en": "You are not authorized to perform this action.",
        "ar": "ليس لديك صلاحية لتنفيذ هذا الاجراء.",
    },
    "gift.channel.setup.no_alliances_title": {
        "en": "No Available Alliances",
        "ar": "لا توجد تحالفات متاحة",
    },
    "gift.channel.setup.no_alliances_body": {
        "en": "You don't have access to any alliances.",
        "ar": "لا تملك صلاحية الوصول الى اي تحالف.",
    },
    "gift.channel.setup.title": {
        "en": "Gift Code Channel Setup",
        "ar": "اعداد قناة اكواد الهدايا",
    },
    "gift.channel.setup.select_alliance": {
        "en": "Please select an alliance to set up gift code channel:",
        "ar": "يرجى اختيار تحالف لاعداد قناة اكواد الهدايا:",
    },
    "gift.channel.setup.select_alliance_hint": {
        "en": "Select an alliance from the list below:",
        "ar": "اختر تحالفا من القائمة بالاسفل:",
    },
    "gift.channel.setup.instructions": {
        "en": "Instructions:",
        "ar": "التعليمات:",
    },
    "gift.channel.setup.select_channel": {
        "en": "Please select a channel for gift codes",
        "ar": "يرجى اختيار قناة لاكواد الهدايا",
    },
    "gift.channel.setup.page": {
        "en": "Page:",
        "ar": "الصفحة:",
    },
    "gift.channel.setup.total_channels": {
        "en": "Total Channels:",
        "ar": "اجمالي القنوات:",
    },
    "gift.channel.setup.success_title": {
        "en": "Gift Code Channel Set",
        "ar": "تم ضبط قناة اكواد الهدايا",
    },
    "gift.channel.setup.success_desc": {
        "en": "Successfully set gift code channel:",
        "ar": "تم ضبط قناة اكواد الهدايا بنجاح:",
    },
    "gift.channel.setup.configured_line": {
        "en": "Channel has been configured for gift code monitoring.",
        "ar": "تم تهيئة القناة لمراقبة اكواد الهدايا.",
    },
    "gift.channel.setup.history_hint": {
        "en": "Use **Channel History Scan** in Gift Code Settings to scan historical messages on-demand.",
        "ar": "استخدم **فحص سجل القناة** في اعدادات اكواد الهدايا لفحص الرسائل السابقة عند الحاجة.",
    },
    "gift.channel.setup.tip": {
        "en": "**Tip:** Follow the official WOS #giftcodes channel in your gift code channel to easily find new codes.",
        "ar": "**نصيحة:** تابع قناة WOS #giftcodes الرسمية داخل قناة اكواد الهدايا للعثور على اكواد جديدة بسهولة.",
    },
    "gift.channel.setup.error": {
        "en": "An error occurred while setting the gift code channel.",
        "ar": "حدث خطا اثناء ضبط قناة اكواد الهدايا.",
    },
    "alliance.member.menu.title": {
        "en": "Alliance Member Operations",
        "ar": "عمليات اعضاء التحالف",
    },
    "alliance.member.menu.prompt": {
        "en": "Please choose an operation:",
        "ar": "يرجى اختيار عملية:",
    },
    "alliance.member.menu.available": {
        "en": "Available Operations",
        "ar": "العمليات المتاحة",
    },
    "alliance.member.menu.add_desc": {
        "en": "Add members to an alliance",
        "ar": "اضافة اعضاء الى تحالف",
    },
    "alliance.member.menu.transfer_desc": {
        "en": "Transfer members between alliances",
        "ar": "نقل الاعضاء بين التحالفات",
    },
    "alliance.member.menu.remove_desc": {
        "en": "Remove members from alliance",
        "ar": "ازالة اعضاء من التحالف",
    },
    "alliance.member.menu.view_desc": {
        "en": "View alliance members",
        "ar": "عرض اعضاء التحالف",
    },
    "alliance.member.menu.export_desc": {
        "en": "Export members list",
        "ar": "تصدير قائمة الاعضاء",
    },
    "alliance.member.menu.main_menu_desc": {
        "en": "Return to main menu",
        "ar": "العودة للقائمة الرئيسية",
    },
    "alliance.member.menu.footer": {
        "en": "Use the buttons below to continue.",
        "ar": "استخدم الازرار بالاسفل للمتابعة.",
    },
    "alliance.member.button.add": {
        "en": "Add Members",
        "ar": "اضافة اعضاء",
    },
    "alliance.member.button.transfer": {
        "en": "Transfer Members",
        "ar": "نقل الاعضاء",
    },
    "alliance.member.button.remove": {
        "en": "Remove Members",
        "ar": "ازالة الاعضاء",
    },
    "alliance.member.button.view": {
        "en": "View Members",
        "ar": "عرض الاعضاء",
    },
    "alliance.member.button.export": {
        "en": "Export Members",
        "ar": "تصدير الاعضاء",
    },
    "alliance.member.button.main_menu": {
        "en": "Main Menu",
        "ar": "القائمة الرئيسية",
    },
    "alliance.member.common.admin_label": {
        "en": "Administrator:",
        "ar": "المشرف:",
    },
    "alliance.member.common.alliance_label": {
        "en": "Alliance:",
        "ar": "التحالف:",
    },
    "alliance.member.common.cancel": {
        "en": "Cancel",
        "ar": "الغاء",
    },
    "alliance.member.common.cancelled_title": {
        "en": "Cancelled",
        "ar": "تم الغاء العملية",
    },
    "alliance.member.common.confirm": {
        "en": "Confirm",
        "ar": "تاكيد",
    },
    "alliance.member.common.confirm_delete": {
        "en": "Confirm Delete",
        "ar": "تاكيد الحذف",
    },
    "alliance.member.common.current_alliance_label": {
        "en": "Current Alliance:",
        "ar": "التحالف الحالي:",
    },
    "alliance.member.common.date_label": {
        "en": "Date:",
        "ar": "التاريخ:",
    },
    "alliance.member.common.error_title": {
        "en": "Error",
        "ar": "خطا",
    },
    "alliance.member.common.id_label": {
        "en": "ID:",
        "ar": "المعرف:",
    },
    "alliance.member.common.level_label": {
        "en": "Level:",
        "ar": "المستوى:",
    },
    "alliance.member.common.main_menu_error": {
        "en": "An error occurred while returning to main menu.",
        "ar": "حدث خطا اثناء الرجوع الى القائمة الرئيسية.",
    },
    "alliance.member.common.member_label": {
        "en": "Member:",
        "ar": "العضو:",
    },
    "alliance.member.common.name_label": {
        "en": "Name:",
        "ar": "الاسم:",
    },
    "alliance.member.common.seconds": {
        "en": "seconds",
        "ar": "ثانية",
    },
    "alliance.member.common.select_prompt": {
        "en": "Select members from the list below:",
        "ar": "اختر الاعضاء من القائمة بالاسفل:",
    },
    "alliance.member.common.selected_count": {
        "en": "Selected: {count}",
        "ar": "تم اختيار: {count}",
    },
    "alliance.member.common.selection_title": {
        "en": "Member Selection - {alliance}",
        "ar": "اختيار الاعضاء - {alliance}",
    },
    "alliance.member.common.state_label": {
        "en": "State:",
        "ar": "الولاية:",
    },
    "alliance.member.common.try_again": {
        "en": "Please try again.",
        "ar": "حاول مرة اخرى.",
    },
    "alliance.member.common.back": {
        "en": "Back",
        "ar": "رجوع",
    },
    "alliance.member.common.next": {
        "en": "Next",
        "ar": "التالي",
    },
    "alliance.member.common.none": {
        "en": "None",
        "ar": "لا يوجد",
    },
    "alliance.member.common.unknown": {
        "en": "Unknown",
        "ar": "غير معروف",
    },
    "alliance.member.common.no_members_selected": {
        "en": "No members selected.",
        "ar": "لم يتم اختيار اي عضو.",
    },
    "alliance.member.common.select_error": {
        "en": "Please select at least one member.",
        "ar": "يرجى اختيار عضو واحد على الاقل.",
    },
    "alliance.member.common.select_by_id": {
        "en": "Select by ID",
        "ar": "اختيار بالمعرف",
    },
    "alliance.member.common.process_selected": {
        "en": "Process Selected",
        "ar": "معالجة المحدد",
    },
    "alliance.member.common.clear_selection": {
        "en": "Clear Selection",
        "ar": "مسح التحديد",
    },
    "alliance.member.error.no_alliances": {
        "en": "No alliances available for you.",
        "ar": "لا توجد تحالفات متاحة لك.",
    },
    "alliance.member.error.no_authorized_alliance": {
        "en": "You are not authorized to manage this alliance.",
        "ar": "ليست لديك صلاحية ادارة هذا التحالف.",
    },
    "alliance.member.error.no_members": {
        "en": "No members found for this alliance.",
        "ar": "لا يوجد اعضاء لهذا التحالف.",
    },
    "alliance.member.error.request": {
        "en": "An error occurred while processing your request.",
        "ar": "حدث خطا اثناء معالجة طلبك.",
    },
    "alliance.member.permissions.title": {
        "en": "Permissions",
        "ar": "الصلاحيات",
    },
    "alliance.member.permissions.access_level": {
        "en": "Access Level",
        "ar": "مستوى الصلاحية",
    },
    "alliance.member.permissions.access_type": {
        "en": "Access Type",
        "ar": "نوع الصلاحية",
    },
    "alliance.member.permissions.global_admin": {
        "en": "Global Admin",
        "ar": "مشرف عام",
    },
    "alliance.member.permissions.alliance_admin": {
        "en": "Alliance Admin",
        "ar": "مشرف تحالف",
    },
    "alliance.member.permissions.all_alliances": {
        "en": "All Alliances",
        "ar": "جميع التحالفات",
    },
    "alliance.member.permissions.assigned_alliances": {
        "en": "Assigned Alliances",
        "ar": "التحالفات المعينة",
    },
    "alliance.member.permissions.available_alliances": {
        "en": "Available Alliances",
        "ar": "التحالفات المتاحة",
    },
    "alliance.member.select_alliance_title": {
        "en": "Select Alliance",
        "ar": "اختر التحالف",
    },
    "alliance.member.select_add_prompt": {
        "en": "Please select an alliance to add members:",
        "ar": "يرجى اختيار تحالف لاضافة اعضاء:",
    },
    "alliance.member.select.placeholder": {
        "en": "Select an alliance... (Page {current}/{total})",
        "ar": "اختر تحالفا... (صفحة {current}/{total})",
    },
    "alliance.member.select.assigned": {
        "en": "Assigned",
        "ar": "معين",
    },
    "alliance.member.select.option_desc": {
        "en": "ID: {alliance_id} | Members: {count}",
        "ar": "المعرف: {alliance_id} | الاعضاء: {count}",
    },
    "alliance.member.select.option_desc_assigned": {
        "en": "ID: {alliance_id} | Members: {count} {assigned}",
        "ar": "المعرف: {alliance_id} | الاعضاء: {count} {assigned}",
    },
    "alliance.member.select.option_desc_id": {
        "en": "ID: {alliance_id}",
        "ar": "المعرف: {alliance_id}",
    },
    "alliance.member.select.filter_id": {
        "en": "Filter by ID",
        "ar": "تصفية بالمعرف",
    },
    "alliance.member.stats.title": {
        "en": "Stats",
        "ar": "الاحصائيات",
    },
    "alliance.member.stats.total_members": {
        "en": "Total Members:",
        "ar": "اجمالي الاعضاء:",
    },
    "alliance.member.stats.highest_level": {
        "en": "Highest Level:",
        "ar": "اعلى مستوى:",
    },
    "alliance.member.stats.avg_level": {
        "en": "Average Level:",
        "ar": "متوسط المستوى:",
    },
    "alliance.member.remove.select_title": {
        "en": "Remove Members",
        "ar": "ازالة اعضاء",
    },
    "alliance.member.remove.select_prompt": {
        "en": "Select an alliance to remove members:",
        "ar": "اختر تحالفا لازالة الاعضاء:",
    },
    "alliance.member.remove.selection_title": {
        "en": "Remove Members - {alliance}",
        "ar": "ازالة اعضاء - {alliance}",
    },
    "alliance.member.remove.select_member": {
        "en": "Select members to remove:",
        "ar": "اختر الاعضاء لازالتهم:",
    },
    "alliance.member.remove.select_placeholder": {
        "en": "Select members... (Page {current}/{total})",
        "ar": "اختر الاعضاء... (صفحة {current}/{total})",
    },
    "alliance.member.remove.confirm_title": {
        "en": "Confirm Removal",
        "ar": "تاكيد الازالة",
    },
    "alliance.member.remove.confirm_body": {
        "en": "Are you sure you want to remove {count} members?",
        "ar": "هل انت متاكد من ازالة {count} عضو؟",
    },
    "alliance.member.remove.delete_all_confirm": {
        "en": "Remove all {count} members from {alliance}?",
        "ar": "ازالة جميع الاعضاء ({count}) من {alliance}؟",
    },
    "alliance.member.remove.delete_all": {
        "en": "Delete All",
        "ar": "حذف الكل",
    },
    "alliance.member.remove.delete_all_cancelled": {
        "en": "Delete all cancelled.",
        "ar": "تم الغاء حذف الكل.",
    },
    "alliance.member.remove.cancelled_body": {
        "en": "Removal cancelled.",
        "ar": "تم الغاء الازالة.",
    },
    "alliance.member.remove.success_title": {
        "en": "Members Removed",
        "ar": "تمت ازالة الاعضاء",
    },
    "alliance.member.remove.success_body": {
        "en": "Successfully removed {count} members.",
        "ar": "تمت ازالة {count} عضو بنجاح.",
    },
    "alliance.member.remove.error_body": {
        "en": "An error occurred while removing members.",
        "ar": "حدث خطا اثناء ازالة الاعضاء.",
    },
    "alliance.member.remove.error_process": {
        "en": "Failed to process removal.",
        "ar": "فشل في معالجة الازالة.",
    },
    "alliance.member.remove.log_mass_title": {
        "en": "Mass Removal Log",
        "ar": "سجل الازالة الجماعية",
    },
    "alliance.member.remove.log_bulk_title": {
        "en": "Bulk Removal Log",
        "ar": "سجل الازالة الجماعية",
    },
    "alliance.member.remove.log_total": {
        "en": "Total Removed:",
        "ar": "اجمالي المحذوفين:",
    },
    "alliance.member.remove.log_removed": {
        "en": "Removed Members:",
        "ar": "الاعضاء المحذوفون:",
    },
    "alliance.member.remove.log_more": {
        "en": "...and {count} more.",
        "ar": "...و {count} اخرين.",
    },
    "alliance.member.view.select_prompt": {
        "en": "Select an alliance to view members:",
        "ar": "اختر تحالفا لعرض الاعضاء:",
    },
    "alliance.member.view.list_title": {
        "en": "Members List - {alliance}",
        "ar": "قائمة الاعضاء - {alliance}",
    },
    "alliance.member.view.list_header": {
        "en": "Members:",
        "ar": "الاعضاء:",
    },
    "alliance.member.view.list_posted": {
        "en": "Member list posted.",
        "ar": "تم نشر قائمة الاعضاء.",
    },
    "alliance.member.view.error_display": {
        "en": "Failed to display member list.",
        "ar": "فشل عرض قائمة الاعضاء.",
    },
    "alliance.member.transfer.select_title": {
        "en": "Transfer Members",
        "ar": "نقل الاعضاء",
    },
    "alliance.member.transfer.select_prompt": {
        "en": "Select a source alliance:",
        "ar": "اختر تحالفا مصدرا:",
    },
    "alliance.member.transfer.selection_title": {
        "en": "Transfer Members - {alliance}",
        "ar": "نقل الاعضاء - {alliance}",
    },
    "alliance.member.transfer.select_member": {
        "en": "Select members to transfer:",
        "ar": "اختر الاعضاء للنقل:",
    },
    "alliance.member.transfer.select_placeholder": {
        "en": "Select members... (Page {current}/{total})",
        "ar": "اختر الاعضاء... (صفحة {current}/{total})",
    },
    "alliance.member.transfer.methods_title": {
        "en": "Transfer Methods",
        "ar": "طرق النقل",
    },
    "alliance.member.transfer.method_menu": {
        "en": "Select from list",
        "ar": "اختيار من القائمة",
    },
    "alliance.member.transfer.method_id": {
        "en": "Transfer by ID",
        "ar": "نقل بالمعرف",
    },
    "alliance.member.transfer.no_members_selected": {
        "en": "No members selected to transfer.",
        "ar": "لم يتم اختيار اعضاء للنقل.",
    },
    "alliance.member.transfer.more_members": {
        "en": "\n...and {count} more.",
        "ar": "\n...و {count} اخرين.",
    },
    "alliance.member.transfer.target_title": {
        "en": "Select Target Alliance",
        "ar": "اختر التحالف الهدف",
    },
    "alliance.member.transfer.transferring": {
        "en": "Transferring {count} members",
        "ar": "جار نقل {count} عضو",
    },
    "alliance.member.transfer.target_prompt": {
        "en": "Select the target alliance for these members:",
        "ar": "اختر التحالف الهدف لهؤلاء الاعضاء:",
    },
    "alliance.member.transfer.target_option": {
        "en": "ID: {alliance_id} | Members: {count}",
        "ar": "المعرف: {alliance_id} | الاعضاء: {count}",
    },
    "alliance.member.transfer.target_placeholder": {
        "en": "Select target alliance...",
        "ar": "اختر التحالف الهدف...",
    },
    "alliance.member.transfer.success_title": {
        "en": "Transfer Complete",
        "ar": "اكتمل النقل",
    },
    "alliance.member.transfer.transferred_count": {
        "en": "Transferred:",
        "ar": "تم نقل:",
    },
    "alliance.member.transfer.transferred_members": {
        "en": "Transferred Members",
        "ar": "الاعضاء المنقولون",
    },
    "alliance.member.transfer.source_label": {
        "en": "From:",
        "ar": "من:",
    },
    "alliance.member.transfer.target_label": {
        "en": "To:",
        "ar": "الى:",
    },
    "alliance.member.transfer.error_body": {
        "en": "An error occurred during transfer.",
        "ar": "حدث خطا اثناء النقل.",
    },
    "alliance.member.id_search.title": {
        "en": "Search by ID",
        "ar": "بحث بالمعرف",
    },
    "alliance.member.id_search.label": {
        "en": "Member ID",
        "ar": "معرف العضو",
    },
    "alliance.member.id_search.placeholder": {
        "en": "Enter member ID",
        "ar": "ادخل معرف العضو",
    },
    "alliance.member.id_search.invalid_id": {
        "en": "Invalid ID.",
        "ar": "معرف غير صالح.",
    },
    "alliance.member.id_search.history_unavailable": {
        "en": "History system not available.",
        "ar": "نظام السجل غير متوفر.",
    },
    "alliance.member.id_search.not_found": {
        "en": "Member not found.",
        "ar": "لم يتم العثور على العضو.",
    },
    "alliance.member.id_search.member_info": {
        "en": "Member Information",
        "ar": "معلومات العضو",
    },
    "alliance.member.id_search.remove_title": {
        "en": "Confirm Removal",
        "ar": "تاكيد الازالة",
    },
    "alliance.member.id_search.remove_confirm": {
        "en": "Remove this member?",
        "ar": "هل تريد ازالة هذا العضو؟",
    },
    "alliance.member.id_search.deleted_title": {
        "en": "Member Deleted",
        "ar": "تم حذف العضو",
    },
    "alliance.member.id_search.delete_error": {
        "en": "Failed to delete member.",
        "ar": "فشل حذف العضو.",
    },
    "alliance.member.id_search.delete_cancel_title": {
        "en": "Deletion Cancelled",
        "ar": "تم الغاء الحذف",
    },
    "alliance.member.id_search.delete_cancel_body": {
        "en": "Deletion was cancelled.",
        "ar": "تم الغاء الحذف.",
    },
    "alliance.member.id_search.no_permission": {
        "en": "No permission to manage this alliance.",
        "ar": "ليست لديك صلاحية ادارة هذا التحالف.",
    },
    "alliance.member.id_search.transfer_title": {
        "en": "Transfer Member",
        "ar": "نقل العضو",
    },
    "alliance.member.id_search.transfer_process": {
        "en": "Transfer Process",
        "ar": "عملية النقل",
    },
    "alliance.member.id_search.transfer_prompt": {
        "en": "Select a target alliance below.",
        "ar": "اختر التحالف الهدف بالاسفل.",
    },
    "alliance.member.export.select_title": {
        "en": "Export Members",
        "ar": "تصدير الاعضاء",
    },
    "alliance.member.export.select_prompt": {
        "en": "Select an alliance to export members:",
        "ar": "اختر تحالفا لتصدير الاعضاء:",
    },
    "alliance.member.export.select_placeholder": {
        "en": "Select an alliance...",
        "ar": "اختر تحالفا...",
    },
    "alliance.member.export.all_alliances": {
        "en": "All Alliances",
        "ar": "جميع التحالفات",
    },
    "alliance.member.export.all_alliances_desc": {
        "en": "All alliances ({total_alliances}) - {total_members} members",
        "ar": "جميع التحالفات ({total_alliances}) - {total_members} عضو",
    },
    "alliance.member.export.columns_title": {
        "en": "Export Columns",
        "ar": "اعمدة التصدير",
    },
    "alliance.member.export.columns_instructions": {
        "en": "Select which columns to include.",
        "ar": "اختر الاعمدة المراد تضمينها.",
    },
    "alliance.member.export.columns_default": {
        "en": "All columns selected by default.",
        "ar": "جميع الاعمدة محددة افتراضيا.",
    },
    "alliance.member.export.columns_available": {
        "en": "Available Columns",
        "ar": "الاعمدة المتاحة",
    },
    "alliance.member.export.column_alliance": {
        "en": "Alliance",
        "ar": "التحالف",
    },
    "alliance.member.export.column_alliance_desc": {
        "en": "Alliance name",
        "ar": "اسم التحالف",
    },
    "alliance.member.export.column_id": {
        "en": "ID",
        "ar": "المعرف",
    },
    "alliance.member.export.column_id_desc": {
        "en": "Player ID",
        "ar": "معرف اللاعب",
    },
    "alliance.member.export.column_name": {
        "en": "Name",
        "ar": "الاسم",
    },
    "alliance.member.export.column_name_desc": {
        "en": "Player nickname",
        "ar": "لقب اللاعب",
    },
    "alliance.member.export.column_fc": {
        "en": "FC Level",
        "ar": "مستوى الفرن",
    },
    "alliance.member.export.column_fc_desc": {
        "en": "Furnace/FC level",
        "ar": "مستوى الفرن/FC",
    },
    "alliance.member.export.column_state": {
        "en": "State",
        "ar": "الولاية",
    },
    "alliance.member.export.column_state_desc": {
        "en": "State ID",
        "ar": "معرف الولاية",
    },
    "db.transfer.warning_title": {
        "en": "Warning",
        "ar": "تحذير",
    },
    "db.transfer.warning_body": {
        "en": "Please do not mix V2 and V3 databases!\nMake sure to place the database you want to transfer in the same folder as main.py and ensure its name is gift_db.sqlite.",
        "ar": "يرجى عدم خلط قواعد بيانات V2 و V3!\nتأكد من وضع قاعدة البيانات المراد نقلها في نفس مجلد main.py وان يكون اسمها gift_db.sqlite.",
    },
    "db.transfer.button_v2": {
        "en": "V2 Database",
        "ar": "قاعدة بيانات V2",
    },
    "db.transfer.button_v3": {
        "en": "V3 Database",
        "ar": "قاعدة بيانات V3",
    },
    "db.transfer.title": {
        "en": "Database Transfer",
        "ar": "نقل قاعدة البيانات",
    },
    "db.transfer.title_v2": {
        "en": "Database Transfer (V2)",
        "ar": "نقل قاعدة البيانات (V2)",
    },
    "db.transfer.status_label": {
        "en": "Status",
        "ar": "الحالة",
    },
    "db.transfer.status_missing": {
        "en": "gift_db.sqlite not found.",
        "ar": "لم يتم العثور على gift_db.sqlite.",
    },
    "db.transfer.status_in_progress": {
        "en": "Database transfer in progress...",
        "ar": "نقل قاعدة البيانات جار...",
    },
    "db.transfer.status_done": {
        "en": "All database transfers completed successfully!",
        "ar": "تم اكتمال نقل قاعدة البيانات بنجاح!",
    },
    "db.transfer.step_label": {
        "en": "Step {table}",
        "ar": "خطوة {table}",
    },
    "db.transfer.step_value": {
        "en": "Transferred {count} rows ✔",
        "ar": "تم نقل {count} صف ✔",
    },
    "db.transfer.step_error": {
        "en": "Error at {table}",
        "ar": "خطا عند {table}",
    },
    "db.transfer.no_alliances": {
        "en": "Please create an alliance before transferring the database!",
        "ar": "يرجى انشاء تحالف قبل نقل قاعدة البيانات!",
    },
    "db.transfer.select_alliance_prompt": {
        "en": "Please select the alliance to transfer users to:",
        "ar": "يرجى اختيار التحالف الذي سيتم نقل المستخدمين اليه:",
    },
    "db.transfer.select_alliance": {
        "en": "Select Alliance",
        "ar": "اختر التحالف",
    },
    "changes.menu.title": {
        "en": "Alliance History Menu",
        "ar": "قائمة سجل التحالف",
    },
    "changes.menu.available": {
        "en": "Available Operations",
        "ar": "العمليات المتاحة",
    },
    "changes.menu.furnace": {
        "en": "Furnace Changes",
        "ar": "تغييرات الفرن",
    },
    "changes.menu.furnace_desc": {
        "en": "View furnace level changes",
        "ar": "عرض تغييرات مستوى الفرن",
    },
    "changes.menu.nickname": {
        "en": "Nickname Changes",
        "ar": "تغييرات الالقاب",
    },
    "changes.menu.nickname_desc": {
        "en": "View nickname history",
        "ar": "عرض سجل الالقاب",
    },
    "changes.permissions.title": {
        "en": "Permission Details",
        "ar": "تفاصيل الصلاحيات",
    },
    "changes.permissions.access_level": {
        "en": "Access Level:",
        "ar": "مستوى الصلاحية:",
    },
    "changes.permissions.access_type": {
        "en": "Access Type:",
        "ar": "نوع الصلاحية:",
    },
    "changes.permissions.global_admin": {
        "en": "Global Admin",
        "ar": "مشرف عام",
    },
    "changes.permissions.alliance_admin": {
        "en": "Alliance Admin",
        "ar": "مشرف تحالف",
    },
    "changes.permissions.all_alliances": {
        "en": "All Alliances",
        "ar": "جميع التحالفات",
    },
    "changes.permissions.assigned_alliances": {
        "en": "Assigned Alliances",
        "ar": "التحالفات المعينة",
    },
    "changes.permissions.available_alliances": {
        "en": "Available Alliances:",
        "ar": "التحالفات المتاحة:",
    },
    "changes.permissions.none": {
        "en": "No alliances found for your permissions.",
        "ar": "لا توجد تحالفات لصلاحياتك.",
    },
    "changes.furnace.title": {
        "en": "Furnace Level History",
        "ar": "سجل مستوى الفرن",
    },
    "changes.furnace.no_changes": {
        "en": "No furnace changes found for this player.",
        "ar": "لا توجد تغييرات للفرن لهذا اللاعب.",
    },
    "changes.furnace.change_at": {
        "en": "Level Change at {date}",
        "ar": "تغيير المستوى في {date}",
    },
    "changes.furnace.error": {
        "en": "An error occurred while displaying the furnace history.",
        "ar": "حدث خطا اثناء عرض سجل الفرن.",
    },
    "changes.furnace.select_title": {
        "en": "Furnace Changes",
        "ar": "تغييرات الفرن",
    },
    "changes.furnace.select_prompt": {
        "en": "Select an alliance to view furnace changes:",
        "ar": "اختر تحالفا لعرض تغييرات الفرن:",
    },
    "changes.furnace.select_member_prompt": {
        "en": "Select a member to view furnace history:",
        "ar": "اختر عضوا لعرض سجل الفرن:",
    },
    "changes.nickname.title": {
        "en": "Nickname History",
        "ar": "سجل الالقاب",
    },
    "changes.nickname.no_changes": {
        "en": "No nickname changes found for this player.",
        "ar": "لا توجد تغييرات لقب لهذا اللاعب.",
    },
    "changes.nickname.change_at": {
        "en": "Nickname Change at {date}",
        "ar": "تغيير اللقب في {date}",
    },
    "changes.nickname.error": {
        "en": "An error occurred while displaying the nickname history.",
        "ar": "حدث خطا اثناء عرض سجل الالقاب.",
    },
    "changes.nickname.select_title": {
        "en": "Alliance Selection - Nickname Changes",
        "ar": "اختيار التحالف - تغييرات الالقاب",
    },
    "changes.nickname.select_prompt": {
        "en": "Select an alliance to view nickname changes:",
        "ar": "اختر تحالفا لعرض تغييرات الالقاب:",
    },
    "changes.nickname.select_member_prompt": {
        "en": "Select a member to view nickname history:",
        "ar": "اختر عضوا لعرض سجل الالقاب:",
    },
    "changes.member_list.title": {
        "en": "{icon} {alliance} - Member List",
        "ar": "{icon} {alliance} - قائمة الاعضاء",
    },
    "changes.member_list.select_placeholder": {
        "en": "Select a member (Page {current}/{total})",
        "ar": "اختر عضوا (صفحة {current}/{total})",
    },
    "changes.member_list.option_desc": {
        "en": "ID: {fid} | Level: {level}",
        "ar": "المعرف: {fid} | المستوى: {level}",
    },
    "changes.recent.last_hour": {
        "en": "Last Hour Changes",
        "ar": "تغييرات اخر ساعة",
    },
    "changes.recent.last_24h": {
        "en": "Last 24h Changes",
        "ar": "تغييرات اخر 24 ساعة",
    },
    "changes.recent.custom_time": {
        "en": "Custom Time",
        "ar": "وقت مخصص",
    },
    "changes.recent.error": {
        "en": "An error occurred while showing recent changes.",
        "ar": "حدث خطا اثناء عرض التغييرات الاخيرة.",
    },
    "changes.recent.showing": {
        "en": "Showing changes in the last {hours} hour(s)",
        "ar": "عرض التغييرات خلال اخر {hours} ساعة",
    },
    "changes.recent.total_changes": {
        "en": "Total Changes:",
        "ar": "اجمالي التغييرات:",
    },
    "changes.recent.furnace_title": {
        "en": "{icon} Recent Level Changes - {alliance}",
        "ar": "{icon} التغييرات الاخيرة للمستوى - {alliance}",
    },
    "changes.recent.nickname_title": {
        "en": "{icon} Recent Nickname Changes - {alliance}",
        "ar": "{icon} تغييرات الالقاب الاخيرة - {alliance}",
    },
    "changes.recent.member_line": {
        "en": "{name} (ID: {fid})",
        "ar": "{name} (المعرف: {fid})",
    },
    "changes.recent.none_furnace": {
        "en": "No level changes found in the last {hours} hour(s) for {alliance}.",
        "ar": "لا توجد تغييرات مستوى خلال اخر {hours} ساعة لـ {alliance}.",
    },
    "changes.recent.none_nickname": {
        "en": "No nickname changes found in the last {hours} hour(s) for {alliance}.",
        "ar": "لا توجد تغييرات لقب خلال اخر {hours} ساعة لـ {alliance}.",
    },
    "changes.custom_time.title": {
        "en": "Custom Time Range",
        "ar": "نطاق وقت مخصص",
    },
    "changes.custom_time.label": {
        "en": "Hours (1-24)",
        "ar": "الساعات (1-24)",
    },
    "changes.custom_time.placeholder": {
        "en": "Enter number of hours (max 24)...",
        "ar": "ادخل عدد الساعات (حد اقصى 24)...",
    },
    "changes.custom_time.range_error": {
        "en": "Please enter a number between 1 and 24.",
        "ar": "يرجى ادخال رقم بين 1 و 24.",
    },
    "changes.custom_time.invalid_number": {
        "en": "Please enter a valid number.",
        "ar": "يرجى ادخال رقم صحيح.",
    },
    "changes.custom_time.error_open": {
        "en": "An error occurred while showing the time input.",
        "ar": "حدث خطا اثناء عرض ادخال الوقت.",
    },
    "changes.common.player": {
        "en": "Player:",
        "ar": "اللاعب:",
    },
    "changes.common.id": {
        "en": "ID",
        "ar": "المعرف",
    },
    "changes.common.id_placeholder": {
        "en": "Enter ID number...",
        "ar": "ادخل رقم المعرف...",
    },
    "changes.common.current_level": {
        "en": "Current Level:",
        "ar": "المستوى الحالي:",
    },
    "changes.common.total_members": {
        "en": "Total Members:",
        "ar": "اجمالي الاعضاء:",
    },
    "changes.common.current_page": {
        "en": "Current Page:",
        "ar": "الصفحة الحالية:",
    },
    "changes.common.page": {
        "en": "Page",
        "ar": "صفحة",
    },
    "changes.common.page_of": {
        "en": "Page {current} of {total}",
        "ar": "صفحة {current} من {total}",
    },
    "changes.common.previous": {
        "en": "Previous",
        "ar": "السابق",
    },
    "changes.common.next": {
        "en": "Next",
        "ar": "التالي",
    },
    "changes.common.search_by_id": {
        "en": "Search by ID",
        "ar": "بحث بالمعرف",
    },
    "changes.common.search_title": {
        "en": "Search by ID",
        "ar": "بحث بالمعرف",
    },
    "changes.common.invalid_id": {
        "en": "Invalid ID format. Please enter a valid number.",
        "ar": "صيغة معرف غير صحيحة. يرجى ادخال رقم صحيح.",
    },
    "changes.common.search_error": {
        "en": "An error occurred while searching for the player.",
        "ar": "حدث خطا اثناء البحث عن اللاعب.",
    },
    "changes.common.selection_error": {
        "en": "An error occurred while processing your selection.",
        "ar": "حدث خطا اثناء معالجة اختيارك.",
    },
    "changes.common.request_error": {
        "en": "An error occurred while processing the request.",
        "ar": "حدث خطا اثناء معالجة الطلب.",
    },
    "changes.common.member_list_error": {
        "en": "An error occurred while showing member list.",
        "ar": "حدث خطا اثناء عرض قائمة الاعضاء.",
    },
    "changes.common.main_menu_error": {
        "en": "An error occurred while returning to the main menu.",
        "ar": "حدث خطا اثناء الرجوع الى القائمة الرئيسية.",
    },
    "changes.common.main_menu": {
        "en": "Main Menu",
        "ar": "القائمة الرئيسية",
    },
    "changes.common.no_members": {
        "en": "No members found in this alliance.",
        "ar": "لا يوجد اعضاء في هذا التحالف.",
    },
    "changes.common.unknown": {
        "en": "Unknown",
        "ar": "غير معروف",
    },
    "alliance.member.export.columns_required": {
        "en": "At least one column is required.",
        "ar": "يجب اختيار عمود واحد على الاقل.",
    },
    "alliance.member.export.columns_selected": {
        "en": "Columns Selected",
        "ar": "الاعمدة المختارة",
    },
    "alliance.member.export.format_title": {
        "en": "Export Format",
        "ar": "صيغة التصدير",
    },
    "alliance.member.export.format_prompt": {
        "en": "Choose the export format:",
        "ar": "اختر صيغة التصدير:",
    },
    "alliance.member.export.format_label": {
        "en": "Format:",
        "ar": "الصيغة:",
    },
    "alliance.member.export.format_csv": {
        "en": "CSV (Comma-separated)",
        "ar": "CSV (مفصول بفواصل)",
    },
    "alliance.member.export.format_tsv": {
        "en": "TSV (Tab-separated)",
        "ar": "TSV (مفصول بعلامة تبويب)",
    },
    "alliance.member.export.cancelled": {
        "en": "Export cancelled.",
        "ar": "تم الغاء التصدير.",
    },
    "alliance.member.export.processing_title": {
        "en": "Preparing Export",
        "ar": "جار تجهيز التصدير",
    },
    "alliance.member.export.processing_body": {
        "en": "Please wait while the export is prepared.",
        "ar": "يرجى الانتظار حتى يتم تجهيز التصدير.",
    },
    "alliance.member.export.no_members_title": {
        "en": "No Members Found",
        "ar": "لا يوجد اعضاء",
    },
    "alliance.member.export.no_members_body": {
        "en": "No members found to export.",
        "ar": "لا يوجد اعضاء للتصدير.",
    },
    "alliance.member.export.ready_title": {
        "en": "Export Ready",
        "ar": "التصدير جاهز",
    },
    "alliance.member.export.total_members": {
        "en": "Total Members:",
        "ar": "اجمالي الاعضاء:",
    },
    "alliance.member.export.total_alliances": {
        "en": "Total Alliances:",
        "ar": "اجمالي التحالفات:",
    },
    "alliance.member.export.columns_included": {
        "en": "Columns Included:",
        "ar": "الاعمدة المضمنة:",
    },
    "alliance.member.export.dm_attempt": {
        "en": "Attempting to send the export via DM...",
        "ar": "جاري ارسال التصدير في الخاص...",
    },
    "alliance.member.export.dm_title": {
        "en": "Member Export",
        "ar": "تصدير الاعضاء",
    },
    "alliance.member.export.date_label": {
        "en": "Date:",
        "ar": "التاريخ:",
    },
    "alliance.member.export.columns_label": {
        "en": "Columns:",
        "ar": "الاعمدة:",
    },
    "alliance.member.export.stats_title": {
        "en": "Statistics",
        "ar": "احصائيات",
    },
    "alliance.member.export.stats_highest": {
        "en": "Highest FC",
        "ar": "اعلى FC",
    },
    "alliance.member.export.stats_average": {
        "en": "Average FC",
        "ar": "متوسط FC",
    },
    "alliance.member.export.dm_success": {
        "en": "Sent to your DMs.",
        "ar": "تم الارسال في الخاص.",
    },
    "alliance.member.export.dm_failed": {
        "en": "DM failed.",
        "ar": "فشل الارسال في الخاص.",
    },
    "alliance.member.export.dm_fallback": {
        "en": "Here is the file instead.",
        "ar": "اليك الملف هنا.",
    },
    "alliance.member.export.failed_title": {
        "en": "Export Failed",
        "ar": "فشل التصدير",
    },
    "alliance.member.export.failed_body": {
        "en": "Export failed: {error}",
        "ar": "فشل التصدير: {error}",
    },
    "alliance.member.export.error_process": {
        "en": "Failed to start export.",
        "ar": "فشل بدء التصدير.",
    },
    "alliance.member.export.type_label": {
        "en": "Export Type:",
        "ar": "نوع التصدير:",
    },
    "alliance.member.add.alliance_not_found": {
        "en": "Alliance not found.",
        "ar": "لم يتم العثور على التحالف.",
    },
    "alliance.member.add.no_permission": {
        "en": "You do not have permission to add members.",
        "ar": "ليست لديك صلاحية اضافة الاعضاء.",
    },
    "alliance.member.add.queued_title": {
        "en": "Queued",
        "ar": "تمت الاضافة للطابور",
    },
    "alliance.member.add.queue_in_progress": {
        "en": "Another operation is in progress.",
        "ar": "هناك عملية اخرى قيد التنفيذ.",
    },
    "alliance.member.add.queue_details": {
        "en": "Queue Details",
        "ar": "تفاصيل الطابور",
    },
    "alliance.member.add.queue_position": {
        "en": "Queue Position:",
        "ar": "ترتيبك في الطابور:",
    },
    "alliance.member.add.members_to_add": {
        "en": "Members to add:",
        "ar": "الاعضاء للاضافة:",
    },
    "alliance.member.add.queue_notify": {
        "en": "You will be notified when processing starts.",
        "ar": "سيتم اشعارك عند بدء المعالجة.",
    },
    "alliance.member.add.progress_title": {
        "en": "Adding Members",
        "ar": "جار اضافة الاعضاء",
    },
    "alliance.member.add.progress_desc": {
        "en": "Adding {count} members to {alliance} ({current}/{total}).",
        "ar": "جار اضافة {count} عضو الى {alliance} ({current}/{total}).",
    },
    "alliance.member.add.progress_desc_short": {
        "en": "Adding {count} members ({current}/{total}).",
        "ar": "جار اضافة {count} عضو ({current}/{total}).",
    },
    "alliance.member.add.progress_desc_rate": {
        "en": "Adding {count} members ({current}/{total})\nRate: {rate}{queue_info}",
        "ar": "جار اضافة {count} عضو ({current}/{total})\nالسرعة: {rate}{queue_info}",
    },
    "alliance.member.add.added_field": {
        "en": "Added ({current}/{total})",
        "ar": "تمت الاضافة ({current}/{total})",
    },
    "alliance.member.add.failed_field": {
        "en": "Failed ({current}/{total})",
        "ar": "فشل ({current}/{total})",
    },
    "alliance.member.add.exists_field": {
        "en": "Already Exists ({current}/{total})",
        "ar": "موجود مسبقا ({current}/{total})",
    },
    "alliance.member.add.list_too_long": {
        "en": "List too long to display.",
        "ar": "القائمة طويلة جدا للعرض.",
    },
    "alliance.member.add.checking_api": {
        "en": "Checking API availability...",
        "ar": "جار التحقق من توفر الواجهة...",
    },
    "alliance.member.add.no_api": {
        "en": "No APIs available.",
        "ar": "لا توجد واجهات متاحة.",
    },
    "alliance.member.add.queue_size": {
        "en": "Queue size:",
        "ar": "حجم الطابور:",
    },
    "alliance.member.add.rate_limit_wait": {
        "en": "Rate limit reached. Waiting {seconds}s...{queue_info}",
        "ar": "تم الوصول للحد. جاري الانتظار {seconds}ث...{queue_info}",
    },
    "alliance.member.add.log_title": {
        "en": "Add Members Log",
        "ar": "سجل اضافة الاعضاء",
    },
    "alliance.member.add.results_title": {
        "en": "Results",
        "ar": "النتائج",
    },
    "alliance.member.add.results_added": {
        "en": "Added:",
        "ar": "تمت الاضافة:",
    },
    "alliance.member.add.results_failed": {
        "en": "Failed:",
        "ar": "فشل:",
    },
    "alliance.member.add.results_exists": {
        "en": "Already Exists:",
        "ar": "موجود مسبقا:",
    },
    "alliance.member.add.ids_title": {
        "en": "IDs",
        "ar": "المعرفات",
    },
    "alliance.member.add.queue_still": {
        "en": "Queue remaining:",
        "ar": "المتبقي في الطابور:",
    },
    "alliance.member.add.completed_title": {
        "en": "Add Members Complete",
        "ar": "اكتملت اضافة الاعضاء",
    },
    "alliance.member.add.completed_body": {
        "en": "Processed {count} members.",
        "ar": "تمت معالجة {count} عضو.",
    },
    "alliance.member.add.processing_time": {
        "en": "Processing Time:",
        "ar": "مدة المعالجة:",
    },
    "alliance.member.add.modal_title": {
        "en": "Add Members",
        "ar": "اضافة اعضاء",
    },
    "alliance.member.add.modal_label": {
        "en": "Member IDs",
        "ar": "معرفات الاعضاء",
    },
    "alliance.member.add.modal_placeholder": {
        "en": "Enter IDs separated by commas or new lines",
        "ar": "ادخل المعرفات مفصولة بفواصل او اسطر جديدة",
    },
    "other.features.error.generic": {
        "en": "An error occurred. Please try again.",
        "ar": "حدث خطا. حاول مرة اخرى.",
    },
    "other.features.error.module_not_found": {
        "en": "{module} module not found.",
        "ar": "لم يتم العثور على وحدة {module}.",
    },
    "other.features.error.loading": {
        "en": "An error occurred while loading {module} menu.",
        "ar": "حدث خطا اثناء تحميل قائمة {module}.",
    },
    "other.features.error.main_menu": {
        "en": "An error occurred while returning to main menu.",
        "ar": "حدث خطا اثناء الرجوع الى القائمة الرئيسية.",
    },
    "registration.settings.enable": {
        "en": "Enable",
        "ar": "تفعيل",
    },
    "registration.settings.disable": {
        "en": "Disable",
        "ar": "تعطيل",
    },
    "registration.settings.enabled": {
        "en": "Registration has been enabled.",
        "ar": "تم تفعيل التسجيل.",
    },
    "registration.settings.disabled": {
        "en": "Registration has been disabled.",
        "ar": "تم تعطيل التسجيل.",
    },
    "registration.settings.enable_error": {
        "en": "An error occurred while enabling registration.",
        "ar": "حدث خطا اثناء تفعيل التسجيل.",
    },
    "registration.settings.disable_error": {
        "en": "An error occurred while disabling registration.",
        "ar": "حدث خطا اثناء تعطيل التسجيل.",
    },
    "registration.settings.no_permission": {
        "en": "You do not have permission to access this command.",
        "ar": "ليست لديك صلاحية استخدام هذا الامر.",
    },
    "registration.settings.prompt": {
        "en": "Choose an option to enable or disable the registration system:",
        "ar": "اختر خيارا لتفعيل او تعطيل نظام التسجيل:",
    },
    "registration.command.desc": {
        "en": "Registers yourself into the bot's database.",
        "ar": "تسجيل نفسك في قاعدة بيانات البوت.",
    },
    "registration.command.fid": {
        "en": "Your In-Game ID",
        "ar": "معرفك داخل اللعبة",
    },
    "registration.command.alliance": {
        "en": "Your Alliance Name",
        "ar": "اسم التحالف",
    },
    "registration.disabled": {
        "en": "Registration is currently disabled.",
        "ar": "التسجيل معطل حاليا.",
    },
    "registration.already_registered": {
        "en": "You are already registered in the bot's database.",
        "ar": "انت مسجل بالفعل في قاعدة بيانات البوت.",
    },
    "registration.invalid_id": {
        "en": "Invalid ID. Please try again.",
        "ar": "معرف غير صالح. حاول مرة اخرى.",
    },
    "registration.invalid_id_detail": {
        "en": "Invalid ID: {error}",
        "ar": "معرف غير صالح: {error}",
    },
    "registration.invalid_response": {
        "en": "Invalid response from server. Please try again later.",
        "ar": "استجابة غير صالحة من الخادم. حاول لاحقا.",
    },
    "registration.rate_limited": {
        "en": "⏳ Rate limit reached. Please wait a minute before trying again.",
        "ar": "⏳ تم الوصول للحد. يرجى الانتظار دقيقة قبل المحاولة مرة اخرى.",
    },
    "registration.fetch_error": {
        "en": "Failed to fetch user data. Please try again later.",
        "ar": "فشل جلب بيانات المستخدم. حاول لاحقا.",
    },
    "registration.success": {
        "en": "Registration successful! You are now in the bot's database.",
        "ar": "تم التسجيل بنجاح! انت الان في قاعدة بيانات البوت.",
    },
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
    "support.info.dm_closed": {
        "en": "Could not send DM because your DMs are closed!",
        "ar": "تعذر ارسال رسالة خاصة لان الرسائل مغلقة!",
    },
    "support.about.title": {"en": "About DANGER", "ar": "حول ديـنجر"},
    "support.about.body": {
        "en": "This is an open source Discord bot for Whiteout Survival. It is community-driven and freely available for self-hosting.",
        "ar": "هذا بوت ديسكورد مفتوح المصدر للعبة Whiteout Survival، مدعوم من المجتمع ومتاح للاستضافة الذاتية.",
    },
    "support.about.open_source": {"en": "Open Source Bot", "ar": "بوت مفتوح المصدر"},
    "support.about.features": {"en": "Features", "ar": "الميزات"},
    "support.about.feature_members": {
        "en": "Alliance member management",
        "ar": "ادارة اعضاء التحالف",
    },
    "support.about.feature_gifts": {
        "en": "Gift code operations",
        "ar": "عمليات اكواد الهدايا",
    },
    "support.about.feature_tracking": {
        "en": "Automated member tracking",
        "ar": "تتبع الاعضاء تلقائيا",
    },
    "support.about.feature_bear": {
        "en": "Bear trap notifications",
        "ar": "اشعارات فخ الدب",
    },
    "support.about.feature_id": {
        "en": "ID channel verification",
        "ar": "تحقق قناة المعرفات",
    },
    "support.about.feature_more": {
        "en": "and more...",
        "ar": "والمزيد...",
    },
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
    "attendance.matplotlib_unavailable": {
        "en": "Matplotlib not available - using text attendance reports only",
        "ar": "مكتبة Matplotlib غير متوفرة - سيتم استخدام تقارير نصية فقط",
    },
    "attendance.export.format.placeholder": {
        "en": "Select export format...",
        "ar": "اختر صيغة التصدير...",
    },
    "attendance.export.format.csv_desc": {
        "en": "Comma-separated values",
        "ar": "قيم مفصولة بفواصل",
    },
    "attendance.export.format.tsv_desc": {
        "en": "Tab-separated values",
        "ar": "قيم مفصولة بعلامة تبويب",
    },
    "attendance.export.format.html_desc": {
        "en": "Web page format",
        "ar": "تنسيق صفحة ويب",
    },
    "attendance.channel.placeholder": {
        "en": "Select channel to post report...",
        "ar": "اختر القناة لنشر التقرير...",
    },
    "attendance.export.session_name": {"en": "Session Name:", "ar": "اسم الجلسة:"},
    "attendance.export.alliance": {"en": "Alliance:", "ar": "التحالف:"},
    "attendance.export.event_type": {"en": "Event Type:", "ar": "نوع الحدث:"},
    "attendance.event.other": {"en": "Other", "ar": "اخرى"},
    "attendance.export.event_date": {"en": "Event Date:", "ar": "تاريخ الحدث:"},
    "attendance.export.export_date": {"en": "Export Date:", "ar": "تاريخ التصدير:"},
    "attendance.export.total_players": {"en": "Total Players:", "ar": "اجمالي اللاعبين:"},
    "attendance.export.total_records": {"en": "Total Records:", "ar": "اجمالي السجلات:"},
    "attendance.export.title": {"en": "Attendance Report Export", "ar": "تصدير تقرير الحضور"},
    "attendance.export.format": {"en": "Format:", "ar": "الصيغة:"},
    "attendance.export.invalid_format": {
        "en": "Invalid export format selected.",
        "ar": "تم اختيار صيغة تصدير غير صالحة.",
    },
    "attendance.export.dm_sent": {
        "en": "Attendance report sent to your DMs!",
        "ar": "تم ارسال تقرير الحضور في الرسائل الخاصة.",
    },
    "attendance.export.dm_disabled": {
        "en": "Could not send DM. Please enable DMs from server members and try again.",
        "ar": "تعذر ارسال رسالة خاصة. الرجاء تفعيل الرسائل من اعضاء السيرفر ثم حاول مرة اخرى.",
    },
    "attendance.export.too_large": {
        "en": "Report too large to send via Discord (8MB limit). Please try exporting fewer records.",
        "ar": "التقرير كبير جدا ولا يمكن ارساله (حد 8MB). حاول تصدير عدد اقل من السجلات.",
    },
    "attendance.export.send_error": {
        "en": "An error occurred while sending the report: {error}",
        "ar": "حدث خطا اثناء ارسال التقرير: {error}",
    },
    "attendance.export.generate_error": {
        "en": "An error occurred while generating the export.",
        "ar": "حدث خطا اثناء إنشاء التصدير.",
    },
    "attendance.export.select_format": {
        "en": "Select export format:",
        "ar": "اختر صيغة التصدير:",
    },
    "attendance.channel.select": {
        "en": "Select a channel to post the attendance report:",
        "ar": "اختر قناة لنشر تقرير الحضور:",
    },
    "attendance.channel.no_access": {
        "en": "Could not access that channel.",
        "ar": "تعذر الوصول الى هذه القناة.",
    },
    "attendance.channel.bot_no_permission": {
        "en": "I don't have permission to send messages in that channel.",
        "ar": "لا املك صلاحية ارسال الرسائل في هذه القناة.",
    },
    "attendance.channel.user_no_permission": {
        "en": "You don't have permission to send messages in that channel.",
        "ar": "لا تملك صلاحية ارسال الرسائل في هذه القناة.",
    },
    "attendance.channel.posted": {
        "en": "Attendance report posted to {channel}!",
        "ar": "تم نشر تقرير الحضور في {channel}.",
    },
    "attendance.menu.title": {
        "en": "Attendance System",
        "ar": "نظام الحضور",
    },
    "attendance.menu.prompt": {
        "en": "Please select an operation:",
        "ar": "يرجى اختيار عملية:",
    },
    "attendance.menu.available": {
        "en": "Available Operations",
        "ar": "العمليات المتاحة",
    },
    "attendance.menu.mark": {
        "en": "Mark Attendance",
        "ar": "تسجيل الحضور",
    },
    "attendance.menu.mark_desc": {
        "en": "Create or modify attendance records",
        "ar": "انشاء او تعديل سجلات الحضور",
    },
    "attendance.menu.view": {
        "en": "View Attendance",
        "ar": "عرض الحضور",
    },
    "attendance.menu.view_desc": {
        "en": "View attendance records and export reports",
        "ar": "عرض سجلات الحضور وتصدير التقارير",
    },
    "attendance.menu.settings": {
        "en": "Settings",
        "ar": "الاعدادات",
    },
    "attendance.menu.settings_desc": {
        "en": "Configure attendance preferences",
        "ar": "تهيئة تفضيلات الحضور",
    },
    "attendance.settings.title": {
        "en": "Attendance Settings",
        "ar": "اعدادات الحضور",
    },
    "attendance.settings.description": {
        "en": "Configure your attendance system preferences:",
        "ar": "قم بتهيئة تفضيلات نظام الحضور:",
    },
    "attendance.settings.available": {
        "en": "Available Options",
        "ar": "الخيارات المتاحة",
    },
    "attendance.settings.report_type": {
        "en": "Report Type",
        "ar": "نوع التقرير",
    },
    "attendance.settings.report_type_desc": {
        "en": "Choose between text or visual reports",
        "ar": "اختر بين التقارير النصية او المرئية",
    },
    "attendance.settings.sort_order": {
        "en": "Sort Order",
        "ar": "ترتيب الفرز",
    },
    "attendance.settings.sort_order_desc": {
        "en": "Choose how to sort players in the reports",
        "ar": "اختر طريقة ترتيب اللاعبين في التقارير",
    },
    "attendance.settings.report_type_title": {
        "en": "Report Type Settings",
        "ar": "اعدادات نوع التقرير",
    },
    "attendance.settings.sort_order_title": {
        "en": "Sort Order Settings",
        "ar": "اعدادات ترتيب الفرز",
    },
    "attendance.settings.current": {
        "en": "Current Setting:",
        "ar": "الاعداد الحالي:",
    },
    "attendance.settings.matplotlib_status": {
        "en": "Matplotlib Status:",
        "ar": "حالة Matplotlib:",
    },
    "attendance.settings.available_status": {
        "en": "Available",
        "ar": "متوفر",
    },
    "attendance.settings.unavailable_status": {
        "en": "Not Available",
        "ar": "غير متوفر",
    },
    "attendance.settings.select_report_type": {
        "en": "Select your preferred report type below:",
        "ar": "اختر نوع التقرير المفضل ادناه:",
    },
    "attendance.settings.select_report_type_placeholder": {
        "en": "Select report type...",
        "ar": "اختر نوع التقرير...",
    },
    "attendance.settings.select_sort": {
        "en": "Select your preferred sort order below:",
        "ar": "اختر ترتيب الفرز المفضل ادناه:",
    },
    "attendance.settings.select_sort_placeholder": {
        "en": "Select sort order...",
        "ar": "اختر ترتيب الفرز...",
    },
    "attendance.settings.updated_title": {
        "en": "Settings Updated",
        "ar": "تم تحديث الاعدادات",
    },
    "attendance.settings.updated_description": {
        "en": "Report type has been set to: **{report_type}**",
        "ar": "تم تعيين نوع التقرير الى: **{report_type}**",
    },
    "attendance.settings.sort_updated_title": {
        "en": "Sort Order Updated",
        "ar": "تم تحديث ترتيب الفرز",
    },
    "attendance.settings.sort_updated_description": {
        "en": "Sort order has been set to: **{sort_name}**",
        "ar": "تم تعيين ترتيب الفرز الى: **{sort_name}**",
    },
    "attendance.report_type.text": {
        "en": "Text",
        "ar": "نصي",
    },
    "attendance.report_type.text_desc": {
        "en": "Text-based reports (faster, no requirements)",
        "ar": "تقارير نصية (اسرع بدون متطلبات)",
    },
    "attendance.report_type.matplotlib": {
        "en": "Matplotlib",
        "ar": "Matplotlib",
    },
    "attendance.report_type.matplotlib_desc": {
        "en": "Visual table reports (requires matplotlib)",
        "ar": "تقارير مرئية على شكل جدول (تتطلب matplotlib)",
    },
    "attendance.sort.by_points": {
        "en": "By Points",
        "ar": "حسب النقاط",
    },
    "attendance.sort.by_points_desc": {
        "en": "Highest points first (Present -> Absent)",
        "ar": "الاعلى نقاطا اولا (حاضر -> غائب)",
    },
    "attendance.sort.name_az": {
        "en": "Name A-Z",
        "ar": "الاسم من A-Z",
    },
    "attendance.sort.name_az_desc": {
        "en": "Alphabetical order (Present -> Absent)",
        "ar": "ترتيب ابجدي (حاضر -> غائب)",
    },
    "attendance.sort.name_az_all": {
        "en": "Name A-Z (All)",
        "ar": "الاسم من A-Z (الكل)",
    },
    "attendance.sort.name_az_all_desc": {
        "en": "Alphabetical order (All Users)",
        "ar": "ترتيب ابجدي (جميع المستخدمين)",
    },
    "attendance.sort.last_attended": {
        "en": "Last Attended First",
        "ar": "الاحدث حضورا اولا",
    },
    "attendance.sort.last_attended_desc": {
        "en": "Most recent attendance first",
        "ar": "الاحدث حضورا اولا",
    },
    "attendance.view.title": {
        "en": "View Attendance - Alliance Selection",
        "ar": "عرض الحضور - اختيار التحالف",
    },
    "attendance.view.select_alliance": {
        "en": "Please select an alliance to view attendance records:",
        "ar": "يرجى اختيار تحالف لعرض سجلات الحضور:",
    },
    "attendance.mark.title": {
        "en": "Attendance - Alliance Selection",
        "ar": "الحضور - اختيار التحالف",
    },
    "attendance.mark.title_short": {
        "en": "Mark Attendance",
        "ar": "تسجيل الحضور",
    },
    "attendance.mark.select_alliance": {
        "en": "Please select an alliance to mark attendance:",
        "ar": "يرجى اختيار تحالف لتسجيل الحضور:",
    },
    "attendance.permissions.title": {
        "en": "Permission Details",
        "ar": "تفاصيل الصلاحيات",
    },
    "attendance.permissions.level": {
        "en": "Access Level:",
        "ar": "مستوى الوصول:",
    },
    "attendance.permissions.type": {
        "en": "Access Type:",
        "ar": "نوع الوصول:",
    },
    "attendance.permissions.available_alliances": {
        "en": "Available Alliances:",
        "ar": "التحالفات المتاحة:",
    },
    "attendance.permissions.global_admin": {
        "en": "Global Admin",
        "ar": "مشرف عام",
    },
    "attendance.permissions.alliance_admin": {
        "en": "Alliance Admin",
        "ar": "مشرف تحالف",
    },
    "attendance.permissions.all_alliances": {
        "en": "All Alliances",
        "ar": "كل التحالفات",
    },
    "attendance.permissions.assigned_alliances": {
        "en": "Assigned Alliances",
        "ar": "التحالفات المعينة",
    },
    "attendance.alliance.select_placeholder": {
        "en": "Select an alliance... (Page {page}/{total_pages})",
        "ar": "اختر تحالفا... (صفحة {page}/{total_pages})",
    },
    "attendance.alliance.option_desc": {
        "en": "ID: {alliance_id} | Members: {member_count}",
        "ar": "المعرف: {alliance_id} | الاعضاء: {member_count}",
    },
    "attendance.session.select_placeholder": {
        "en": "Select a session...",
        "ar": "اختر جلسة...",
    },
    "attendance.session.new": {
        "en": "New Session",
        "ar": "جلسة جديدة",
    },
    "attendance.session.not_found": {
        "en": "Session not found.",
        "ar": "لم يتم العثور على الجلسة.",
    },
    "attendance.session.load_error": {
        "en": "An error occurred while loading the session.",
        "ar": "حدث خطا اثناء تحميل الجلسة.",
    },
    "attendance.session.new_title": {
        "en": "Create New Session",
        "ar": "انشاء جلسة جديدة",
    },
    "attendance.session.title": {
        "en": "Attendance Session",
        "ar": "جلسة الحضور",
    },
    "attendance.session.name_label": {
        "en": "Session Name",
        "ar": "اسم الجلسة",
    },
    "attendance.session.name_placeholder": {
        "en": "Enter a name for this attendance session",
        "ar": "ادخل اسما لهذه الجلسة",
    },
    "attendance.session.name_placeholder_marking": {
        "en": "Enter session name (e.g., 'Bear Tuesday', 'Canyon Sunday')",
        "ar": "ادخل اسم الجلسة (مثال: 'Bear Tuesday', 'Canyon Sunday')",
    },
    "attendance.session.date_label": {
        "en": "Event Date/Time (UTC)",
        "ar": "تاريخ/وقت الحدث (UTC)",
    },
    "attendance.session.date_placeholder": {
        "en": "YYYY-MM-DD HH:MM (Leave empty for current time)",
        "ar": "YYYY-MM-DD HH:MM (اتركه فارغا للوقت الحالي)",
    },
    "attendance.session.name_required": {
        "en": "Session name cannot be empty.",
        "ar": "لا يمكن ترك اسم الجلسة فارغا.",
    },
    "attendance.session.invalid_date_title": {
        "en": "Invalid Date Format",
        "ar": "صيغة تاريخ غير صحيحة",
    },
    "attendance.session.invalid_date_body": {
        "en": "Please use the format: YYYY-MM-DD HH:MM (e.g., 2024-03-15 14:30)",
        "ar": "يرجى استخدام الصيغة: YYYY-MM-DD HH:MM (مثل 2024-03-15 14:30)",
    },
    "attendance.session.unknown_date": {
        "en": "Unknown date",
        "ar": "تاريخ غير معروف",
    },
    "attendance.session.option_desc": {
        "en": "{date} - {marked}/{total} marked",
        "ar": "{date} - تم تسجيل {marked}/{total}",
    },
    "attendance.session.select_or_create": {
        "en": "Please select an existing session or create a new one:",
        "ar": "يرجى اختيار جلسة موجودة او انشاء جلسة جديدة:",
    },
    "attendance.session.available": {
        "en": "Available Sessions:",
        "ar": "الجلسات المتاحة:",
    },
    "attendance.session.sorted_newest": {
        "en": "Sessions are sorted by date (newest first).",
        "ar": "الجلسات مرتبة حسب التاريخ (الاحدث اولا).",
    },
    "attendance.session.none": {
        "en": "No sessions found",
        "ar": "لا توجد جلسات",
    },
    "attendance.session.create_first": {
        "en": "Click the **New Session** button below to create your first attendance session for this alliance.",
        "ar": "اضغط زر **جلسة جديدة** بالاسفل لانشاء اول جلسة حضور لهذا التحالف.",
    },
    "attendance.event.select_placeholder": {
        "en": "Select Event Type...",
        "ar": "اختر نوع الحدث...",
    },
    "attendance.event.select_legion_placeholder": {
        "en": "Select Legion...",
        "ar": "اختر الفيلق...",
    },
    "attendance.event.legion_1": {
        "en": "Legion 1",
        "ar": "الفيلق 1",
    },
    "attendance.event.legion_2": {
        "en": "Legion 2",
        "ar": "الفيلق 2",
    },
    "attendance.event.select_legion_title": {
        "en": "Select Legion",
        "ar": "اختر الفيلق",
    },
    "attendance.event.type": {
        "en": "Event Type:",
        "ar": "نوع الحدث:",
    },
    "attendance.event.select_legion_prompt": {
        "en": "Please select the legion for this attendance session:",
        "ar": "يرجى اختيار الفيلق لهذه الجلسة:",
    },
    "attendance.event.select_title": {
        "en": "Select Event Type",
        "ar": "اختر نوع الحدث",
    },
    "attendance.event.select_prompt": {
        "en": "Please select the event type for this attendance session:",
        "ar": "يرجى اختيار نوع الحدث لهذه الجلسة:",
    },
    "attendance.event.foundry": {
        "en": "Foundry",
        "ar": "فاوندري",
    },
    "attendance.event.canyon_clash": {
        "en": "Canyon Clash",
        "ar": "صراع الوادي",
    },
    "attendance.event.crazy_joe": {
        "en": "Crazy Joe",
        "ar": "كريزي جو",
    },
    "attendance.event.bear_trap": {
        "en": "Bear Trap",
        "ar": "فخ الدب",
    },
    "attendance.event.castle_battle": {
        "en": "Castle Battle",
        "ar": "معركة القلعة",
    },
    "attendance.event.frostdragon_tyrant": {
        "en": "Frostdragon Tyrant",
        "ar": "طاغية تنين الصقيع",
    },
    "attendance.event.other": {
        "en": "Other",
        "ar": "اخرى",
    },
    "attendance.error.title": {
        "en": "Error",
        "ar": "خطا",
    },
    "attendance.error.load_settings": {
        "en": "An error occurred while loading settings.",
        "ar": "حدث خطا اثناء تحميل الاعدادات.",
    },
    "attendance.error.update_report_type": {
        "en": "Failed to update report type.",
        "ar": "فشل تحديث نوع التقرير.",
    },
    "attendance.error.update_sort": {
        "en": "Failed to update sort order.",
        "ar": "فشل تحديث ترتيب الفرز.",
    },
    "attendance.error.update_settings": {
        "en": "Failed to update settings.",
        "ar": "فشل تحديث الاعدادات.",
    },
    "attendance.error.matplotlib_unavailable": {
        "en": "Matplotlib is not available on this system.",
        "ar": "مكتبة Matplotlib غير متوفرة على هذا النظام.",
    },
    "attendance.error.report_unavailable": {
        "en": "Attendance report system not available.",
        "ar": "نظام تقارير الحضور غير متوفر.",
    },
    "attendance.error.access_denied": {
        "en": "Access Denied",
        "ar": "تم رفض الوصول",
    },
    "attendance.error.no_permission": {
        "en": "You do not have permission to use this command.",
        "ar": "ليست لديك صلاحية استخدام هذا الامر.",
    },
    "attendance.error.no_alliances_title": {
        "en": "No Alliances Found",
        "ar": "لا توجد تحالفات",
    },
    "attendance.error.no_alliances_body": {
        "en": "No alliances found for your permissions.",
        "ar": "لا توجد تحالفات لصلاحياتك.",
    },
    "attendance.error.processing_request": {
        "en": "An error occurred while processing your request.",
        "ar": "حدث خطا اثناء معالجة طلبك.",
    },
    "attendance.error.settings_permission": {
        "en": "You do not have permission to access settings.",
        "ar": "ليست لديك صلاحية الوصول للاعدادات.",
    },
    "attendance.error.back_other_features": {
        "en": "An error occurred while returning to other features.",
        "ar": "حدث خطا اثناء الرجوع للميزات الاخرى.",
    },
    "attendance.error.select_alliance_error": {
        "en": "An error occurred while showing alliance selection.",
        "ar": "حدث خطا اثناء عرض اختيار التحالف.",
    },
    "attendance.error.guild_only": {
        "en": "This command can only be used in a server, not in DMs.",
        "ar": "هذا الامر يعمل داخل السيرفر فقط وليس في الرسائل الخاصة.",
    },
    "attendance.channel.post_error": {
        "en": "An error occurred while posting the report.",
        "ar": "حدث خطا اثناء نشر التقرير.",
    },
    "attendance.report.title": {"en": "Attendance Report", "ar": "تقرير الحضور"},
    "attendance.report.footer": {"en": "Generated by DANGER Bot", "ar": "تم الانشاء بواسطة بوت ديـنجر"},
    "attendance.report.generate_error": {
        "en": "An error occurred while generating attendance report.",
        "ar": "حدث خطا اثناء انشاء تقرير الحضور.",
    },
    "attendance.report.no_marks": {
        "en": "No attendance has been marked yet.",
        "ar": "لم يتم تسجيل اي حضور بعد.",
    },
    "attendance.report.no_records": {
        "en": "No attendance records found for session '{session}' in {alliance}.",
        "ar": "لا توجد سجلات حضور للجلسة '{session}' في {alliance}.",
    },
    "attendance.summary.title": {"en": "SUMMARY", "ar": "الملخص"},
    "attendance.summary.session": {"en": "Session:", "ar": "الجلسة:"},
    "attendance.summary.alliance": {"en": "Alliance:", "ar": "التحالف:"},
    "attendance.summary.date": {"en": "Date:", "ar": "التاريخ:"},
    "attendance.summary.total_marked": {"en": "Total Marked:", "ar": "اجمالي المسجلين:"},
    "attendance.summary.session_id": {"en": "Session ID:", "ar": "معرف الجلسة:"},
    "attendance.player_details": {"en": "PLAYER DETAILS", "ar": "تفاصيل اللاعبين"},
    "attendance.player_details_continued": {"en": "PLAYER DETAILS (continued)", "ar": "تفاصيل اللاعبين (متابعة)"},
    "attendance.header.id": {"en": "ID", "ar": "المعرف"},
    "attendance.header.nickname": {"en": "Nickname", "ar": "اللقب"},
    "attendance.header.status": {"en": "Status", "ar": "الحالة"},
    "attendance.header.points": {"en": "Points", "ar": "النقاط"},
    "attendance.header.last_event": {"en": "Last Event Attendance", "ar": "حضور اخر حدث"},
    "attendance.header.marked_by": {"en": "Marked By", "ar": "تم التحديد بواسطة"},
    "attendance.header.player": {"en": "Player", "ar": "اللاعب"},
    "attendance.status.present": {"en": "Present", "ar": "حاضر"},
    "attendance.status.absent": {"en": "Absent", "ar": "غائب"},
    "attendance.status.not_recorded": {"en": "Not Recorded", "ar": "غير مسجل"},
    "attendance.players": {"en": "players", "ar": "لاعب"},
    "attendance.points": {"en": "points", "ar": "نقطة"},
    "attendance.last": {"en": "Last:", "ar": "اخر:"},
    "attendance.sort.points_desc": {
        "en": "Sorted by Points (Highest to Lowest)",
        "ar": "مرتب حسب النقاط (من الاعلى الى الادنى)",
    },
    "attendance.sort.name_asc": {
        "en": "Sorted by Name (A-Z)",
        "ar": "مرتب حسب الاسم (A-Z)",
    },
    "attendance.sort.name_asc_all": {
        "en": "Sorted by Name (A-Z, All Users)",
        "ar": "مرتب حسب الاسم (A-Z, جميع المستخدمين)",
    },
    "attendance.sort.last_attended_first": {
        "en": "Sorted by Last Attended (Most Recent First)",
        "ar": "مرتب حسب اخر حضور (الاحدث اولا)",
    },
    "attendance.page": {"en": "Page", "ar": "صفحة"},
    "attendance.button.export": {"en": "Export", "ar": "تصدير"},
    "attendance.button.post_channel": {"en": "Post to Channel", "ar": "نشر في القناة"},
    "attendance.button.back_marking": {"en": "Back to Marking", "ar": "العودة للتسجيل"},
    "attendance.button.back_sessions": {"en": "Back to Sessions", "ar": "العودة للجلسات"},
    "attendance.button.back_alliance_selection": {"en": "Back to Alliance Selection", "ar": "العودة لاختيار التحالف"},
    "attendance.sessions.title": {
        "en": "Attendance Sessions - {alliance}",
        "ar": "جلسات الحضور - {alliance}",
    },
    "attendance.sessions.none": {
        "en": "No attendance sessions found for {alliance}.",
        "ar": "لا توجد جلسات حضور لـ {alliance}.",
    },
    "attendance.sessions.none_hint": {
        "en": "To create attendance records, use the 'Mark Attendance' option from the main menu.",
        "ar": "لانشاء سجلات حضور، استخدم خيار 'تسجيل الحضور' من القائمة الرئيسية.",
    },
    "attendance.sessions.select": {
        "en": "Please select a session to view attendance records:",
        "ar": "يرجى اختيار جلسة لعرض سجلات الحضور:",
    },
    "attendance.sessions.load_error": {
        "en": "An error occurred while loading sessions.",
        "ar": "حدث خطا اثناء تحميل الجلسات.",
    },
    "attendance.alliance_select.title": {
        "en": "View Attendance - Alliance Selection",
        "ar": "عرض الحضور - اختيار التحالف",
    },
    "attendance.alliance_select.desc": {
        "en": "Please select an alliance to view attendance records:",
        "ar": "يرجى اختيار التحالف لعرض سجلات الحضور:",
    },
    "attendance.unknown_alliance": {"en": "Unknown Alliance", "ar": "تحالف غير معروف"},
    "attendance.unknown": {"en": "Unknown", "ar": "غير معروف"},
    "attendance.na": {"en": "N/A", "ar": "غير متاح"},
    "attendance.last.new_player": {"en": "New Player", "ar": "لاعب جديد"},
    "attendance.last.first_event": {"en": "First Event", "ar": "اول حدث"},
    
    # ==================== ترجمات إضافية شاملة | Comprehensive Additional Translations ====================
    # تمت الإضافة: 2026-02-11 | Added: 2026-02-11
    
    # عام | General
    "common.yes": {"en": "Yes", "ar": "نعم"},
    "common.no": {"en": "No", "ar": "لا"},
    "common.ok": {"en": "OK", "ar": "حسنا"},
    "common.done": {"en": "Done", "ar": "تم"},
    "common.ready": {"en": "Ready", "ar": "جاهز"},
    "common.loading": {"en": "Loading...", "ar": "جاري التحميل..."},
    "common.processing": {"en": "Processing...", "ar": "جاري المعالجة..."},
    "common.please_wait": {"en": "Please wait...", "ar": "يرجى الانتظار..."},
    "common.success": {"en": "Success", "ar": "نجح"},
    "common.failed": {"en": "Failed", "ar": "فشل"},
    "common.error": {"en": "Error", "ar": "خطأ"},
    "common.warning": {"en": "Warning", "ar": "تحذير"},
    "common.info": {"en": "Information", "ar": "معلومات"},
    "common.unknown": {"en": "Unknown", "ar": "غير معروف"},
    "common.none": {"en": "None", "ar": "لا يوجد"},
    "common.all": {"en": "All", "ar": "الكل"},
    "common.any": {"en": "Any", "ar": "أي"},
    "common.other": {"en": "Other", "ar": "أخرى"},
    "common.custom": {"en": "Custom", "ar": "مخصص"},
    "common.default": {"en": "Default", "ar": "افتراضي"},
    
    # الوقت والتاريخ | Time and Date
    "time.now": {"en": "Now", "ar": "الآن"},
    "time.today": {"en": "Today", "ar": "اليوم"},
    "time.yesterday": {"en": "Yesterday", "ar": "أمس"},
    "time.tomorrow": {"en": "Tomorrow", "ar": "غدا"},
    "time.this_week": {"en": "This Week", "ar": "هذا الأسبوع"},
    "time.last_week": {"en": "Last Week", "ar": "الأسبوع الماضي"},
    "time.next_week": {"en": "Next Week", "ar": "الأسبوع القادم"},
    "time.this_month": {"en": "This Month", "ar": "هذا الشهر"},
    "time.last_month": {"en": "Last Month", "ar": "الشهر الماضي"},
    "time.next_month": {"en": "Next Month", "ar": "الشهر القادم"},
    "time.seconds_ago": {"en": "{count} seconds ago", "ar": "منذ {count} ثانية"},
    "time.minutes_ago": {"en": "{count} minutes ago", "ar": "منذ {count} دقيقة"},
    "time.hours_ago": {"en": "{count} hours ago", "ar": "منذ {count} ساعة"},
    "time.days_ago": {"en": "{count} days ago", "ar": "منذ {count} يوم"},
    
    # الحالة | Status
    "status.online": {"en": "Online", "ar": "متصل"},
    "status.offline": {"en": "Offline", "ar": "غير متصل"},
    "status.busy": {"en": "Busy", "ar": "مشغول"},
    "status.away": {"en": "Away", "ar": "بعيد"},
    "status.active": {"en": "Active", "ar": "نشط"},
    "status.inactive": {"en": "Inactive", "ar": "غير نشط"},
    "status.enabled": {"en": "Enabled", "ar": "مفعل"},
    "status.disabled": {"en": "Disabled", "ar": "معطل"},
    "status.running": {"en": "Running", "ar": "يعمل"},
    "status.stopped": {"en": "Stopped", "ar": "متوقف"},
    "status.pending": {"en": "Pending", "ar": "قيد الانتظار"},
    "status.completed": {"en": "Completed", "ar": "مكتمل"},
    "status.in_progress": {"en": "In Progress", "ar": "قيد التنفيذ"},
    "status.cancelled": {"en": "Cancelled", "ar": "ملغي"},
    
    # الأفعال | Actions
    "action.create": {"en": "Create", "ar": "إنشاء"},
    "action.edit": {"en": "Edit", "ar": "تعديل"},
    "action.update": {"en": "Update", "ar": "تحديث"},
    "action.delete": {"en": "Delete", "ar": "حذف"},
    "action.save": {"en": "Save", "ar": "حفظ"},
    "action.cancel": {"en": "Cancel", "ar": "إلغاء"},
    "action.confirm": {"en": "Confirm", "ar": "تأكيد"},
    "action.submit": {"en": "Submit", "ar": "إرسال"},
    "action.send": {"en": "Send", "ar": "إرسال"},
    "action.search": {"en": "Search", "ar": "بحث"},
    "action.filter": {"en": "Filter", "ar": "تصفية"},
    "action.sort": {"en": "Sort", "ar": "ترتيب"},
    "action.refresh": {"en": "Refresh", "ar": "تحديث"},
    "action.reload": {"en": "Reload", "ar": "إعادة تحميل"},
    "action.reset": {"en": "Reset", "ar": "إعادة تعيين"},
    "action.clear": {"en": "Clear", "ar": "مسح"},
    "action.copy": {"en": "Copy", "ar": "نسخ"},
    "action.paste": {"en": "Paste", "ar": "لصق"},
    "action.download": {"en": "Download", "ar": "تحميل"},
    "action.upload": {"en": "Upload", "ar": "رفع"},
    "action.import": {"en": "Import", "ar": "استيراد"},
    "action.export": {"en": "Export", "ar": "تصدير"},
    "action.print": {"en": "Print", "ar": "طباعة"},
    "action.share": {"en": "Share", "ar": "مشاركة"},
    
    # التنقل | Navigation
    "nav.home": {"en": "Home", "ar": "الرئيسية"},
    "nav.back": {"en": "Back", "ar": "رجوع"},
    "nav.next": {"en": "Next", "ar": "التالي"},
    "nav.previous": {"en": "Previous", "ar": "السابق"},
    "nav.first": {"en": "First", "ar": "الأول"},
    "nav.last": {"en": "Last", "ar": "الأخير"},
    "nav.goto": {"en": "Go to", "ar": "اذهب إلى"},
    "nav.page": {"en": "Page", "ar": "صفحة"},
    "nav.of": {"en": "of", "ar": "من"},
    
    # رسائل النجاح | Success Messages
    "success.created": {"en": "Successfully created!", "ar": "تم الإنشاء بنجاح!"},
    "success.updated": {"en": "Successfully updated!", "ar": "تم التحديث بنجاح!"},
    "success.deleted": {"en": "Successfully deleted!", "ar": "تم الحذف بنجاح!"},
    "success.saved": {"en": "Successfully saved!", "ar": "تم الحفظ بنجاح!"},
    "success.sent": {"en": "Successfully sent!", "ar": "تم الإرسال بنجاح!"},
    "success.completed": {"en": "Successfully completed!", "ar": "تم الاكتمال بنجاح!"},
    "success.operation": {"en": "Operation successful!", "ar": "نجحت العملية!"},
    
    # رسائل الخطأ | Error Messages
    "error.generic": {"en": "An error occurred", "ar": "حدث خطأ"},
    "error.unknown": {"en": "Unknown error", "ar": "خطأ غير معروف"},
    "error.network": {"en": "Network error", "ar": "خطأ في الشبكة"},
    "error.timeout": {"en": "Request timed out", "ar": "انتهت مهلة الطلب"},
    "error.connection": {"en": "Connection error", "ar": "خطأ في الاتصال"},
    "error.not_found": {"en": "Not found", "ar": "غير موجود"},
    "error.forbidden": {"en": "Forbidden", "ar": "ممنوع"},
    "error.unauthorized": {"en": "Unauthorized", "ar": "غير مصرح"},
    "error.invalid": {"en": "Invalid input", "ar": "إدخال غير صالح"},
    "error.required": {"en": "This field is required", "ar": "هذا الحقل مطلوب"},
    "error.too_long": {"en": "Input is too long", "ar": "الإدخال طويل جدا"},
    "error.too_short": {"en": "Input is too short", "ar": "الإدخال قصير جدا"},
    "error.format": {"en": "Invalid format", "ar": "صيغة غير صالحة"},
    "error.permission": {"en": "Permission denied", "ar": "تم رفض الصلاحية"},
    
    # رسائل التأكيد | Confirmation Messages
    "confirm.delete": {"en": "Are you sure you want to delete this?", "ar": "هل أنت متأكد من حذف هذا؟"},
    "confirm.remove": {"en": "Are you sure you want to remove this?", "ar": "هل أنت متأكد من إزالة هذا؟"},
    "confirm.cancel": {"en": "Are you sure you want to cancel?", "ar": "هل أنت متأكد من الإلغاء؟"},
    "confirm.continue": {"en": "Do you want to continue?", "ar": "هل تريد المتابعة؟"},
    "confirm.action": {"en": "This action cannot be undone. Continue?", "ar": "لا يمكن التراجع عن هذا الإجراء. متابعة؟"},
    "confirm.permanent": {"en": "This action is permanent and cannot be undone!", "ar": "هذا الإجراء دائم ولا يمكن التراجع عنه!"},
    
    # التقويم | Calendar
    "calendar.january": {"en": "January", "ar": "يناير"},
    "calendar.february": {"en": "February", "ar": "فبراير"},
    "calendar.march": {"en": "March", "ar": "مارس"},
    "calendar.april": {"en": "April", "ar": "أبريل"},
    "calendar.may": {"en": "May", "ar": "مايو"},
    "calendar.june": {"en": "June", "ar": "يونيو"},
    "calendar.july": {"en": "July", "ar": "يوليو"},
    "calendar.august": {"en": "August", "ar": "أغسطس"},
    "calendar.september": {"en": "September", "ar": "سبتمبر"},
    "calendar.october": {"en": "October", "ar": "أكتوبر"},
    "calendar.november": {"en": "November", "ar": "نوفمبر"},
    "calendar.december": {"en": "December", "ar": "ديسمبر"},
    
    # العدد والكمية | Numbers and Quantity
    "quantity.zero": {"en": "Zero", "ar": "صفر"},
    "quantity.one": {"en": "One", "ar": "واحد"},
    "quantity.few": {"en": "Few", "ar": "قليل"},
    "quantity.many": {"en": "Many", "ar": "كثير"},
    "quantity.empty": {"en": "Empty", "ar": "فارغ"},
    "quantity.full": {"en": "Full", "ar": "ممتلئ"},
    "quantity.total": {"en": "Total", "ar": "إجمالي"},
    "quantity.count": {"en": "Count", "ar": "العدد"},
    "quantity.items": {"en": "items", "ar": "عناصر"},
    
    # الإشعارات | Notifications
    "notif.new_message": {"en": "You have a new message", "ar": "لديك رسالة جديدة"},
    "notif.new_messages": {"en": "You have {count} new messages", "ar": "لديك {count} رسائل جديدة"},
    "notif.no_notifications": {"en": "No notifications", "ar": "لا توجد إشعارات"},
    "notif.mark_read": {"en": "Mark as read", "ar": "تعليم كمقروء"},
    "notif.mark_all_read": {"en": "Mark all as read", "ar": "تعليم الكل كمقروء"},
    "notif.clear_all": {"en": "Clear all notifications", "ar": "مسح جميع الإشعارات"},
    
    # الإعدادات | Settings
    "settings.general": {"en": "General Settings", "ar": "الإعدادات العامة"},
    "settings.advanced": {"en": "Advanced Settings", "ar": "إعدادات متقدمة"},
    "settings.privacy": {"en": "Privacy Settings", "ar": "إعدادات الخصوصية"},
    "settings.security": {"en": "Security Settings", "ar": "إعدادات الأمان"},
    "settings.notifications": {"en": "Notification Settings", "ar": "إعدادات الإشعارات"},
    "settings.appearance": {"en": "Appearance Settings", "ar": "إعدادات المظهر"},
    "settings.language": {"en": "Language Settings", "ar": "إعدادات اللغة"},
    "settings.theme": {"en": "Theme", "ar": "المظهر"},
    "settings.dark_mode": {"en": "Dark Mode", "ar": "الوضع الداكن"},
    "settings.light_mode": {"en": "Light Mode", "ar": "الوضع الفاتح"},
    
    # البحث والتصفية | Search and Filter
    "search.placeholder": {"en": "Search...", "ar": "بحث..."},
    "search.no_results": {"en": "No results found", "ar": "لم يتم العثور على نتائج"},
    "search.results": {"en": "{count} results found", "ar": "تم العثور على {count} نتائج"},
    "search.searching": {"en": "Searching...", "ar": "جاري البحث..."},
    "filter.all": {"en": "All", "ar": "الكل"},
    "filter.active": {"en": "Active", "ar": "نشط"},
    "filter.inactive": {"en": "Inactive", "ar": "غير نشط"},
    "filter.apply": {"en": "Apply Filter", "ar": "تطبيق التصفية"},
    "filter.clear": {"en": "Clear Filter", "ar": "مسح التصفية"},
    
    # عناصر النماذج | Form Elements
    "form.title": {"en": "Title", "ar": "العنوان"},
    "form.name": {"en": "Name", "ar": "الاسم"},
    "form.description": {"en": "Description", "ar": "الوصف"},
    "form.email": {"en": "Email", "ar": "البريد الإلكتروني"},
    "form.password": {"en": "Password", "ar": "كلمة المرور"},
    "form.username": {"en": "Username", "ar": "اسم المستخدم"},
    "form.message": {"en": "Message", "ar": "الرسالة"},
    "form.subject": {"en": "Subject", "ar": "الموضوع"},
    "form.optional": {"en": "Optional", "ar": "اختياري"},
    "form.required": {"en": "Required", "ar": "مطلوب"},
    
    # التحميل والتنزيل | Upload and Download
    "upload.select_file": {"en": "Select a file", "ar": "اختر ملفا"},
    "upload.drag_drop": {"en": "Drag and drop files here", "ar": "اسحب وأفلت الملفات هنا"},
    "upload.uploading": {"en": "Uploading...", "ar": "جاري الرفع..."},
    "upload.success": {"en": "File uploaded successfully", "ar": "تم رفع الملف بنجاح"},
    "upload.failed": {"en": "Upload failed", "ar": "فشل الرفع"},
    "download.downloading": {"en": "Downloading...", "ar": "جاري التحميل..."},
    "download.complete": {"en": "Download complete", "ar": "اكتمل التحميل"},
    "download.failed": {"en": "Download failed", "ar": "فشل التحميل"},
    
    # المساعدة والدعم | Help and Support
    "help.title": {"en": "Help", "ar": "المساعدة"},
    "help.documentation": {"en": "Documentation", "ar": "الوثائق"},
    "help.tutorial": {"en": "Tutorial", "ar": "دليل"},
    "help.faq": {"en": "FAQ", "ar": "الأسئلة الشائعة"},
    "help.contact": {"en": "Contact Support", "ar": "اتصل بالدعم"},
    "help.feedback": {"en": "Send Feedback", "ar": "إرسال ملاحظات"},
    "help.report_bug": {"en": "Report a Bug", "ar": "الإبلاغ عن خطأ"},
    
    # الصلاحيات | Permissions
    "perm.admin": {"en": "Administrator", "ar": "مشرف"},
    "perm.moderator": {"en": "Moderator", "ar": "مشرف"},
    "perm.user": {"en": "User", "ar": "مستخدم"},
    "perm.guest": {"en": "Guest", "ar": "ضيف"},
    "perm.read": {"en": "Read", "ar": "قراءة"},
    "perm.write": {"en": "Write", "ar": "كتابة"},
    "perm.edit": {"en": "Edit", "ar": "تعديل"},
    "perm.delete": {"en": "Delete", "ar": "حذف"},
    "perm.manage": {"en": "Manage", "ar": "إدارة"},
    "perm.view": {"en": "View", "ar": "عرض"},
    
    # الإحصائيات | Statistics
    "stats.total": {"en": "Total", "ar": "الإجمالي"},
    "stats.average": {"en": "Average", "ar": "المتوسط"},
    "stats.minimum": {"en": "Minimum", "ar": "الحد الأدنى"},
    "stats.maximum": {"en": "Maximum", "ar": "الحد الأقصى"},
    "stats.median": {"en": "Median", "ar": "الوسيط"},
    "stats.percentage": {"en": "Percentage", "ar": "النسبة المئوية"},
    "stats.growth": {"en": "Growth", "ar": "النمو"},
    "stats.decline": {"en": "Decline", "ar": "التراجع"},
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
