"""
ترجمات إضافية شائعة ومفيدة
Additional Common and Useful Translations

هذا الملف يحتوي على ترجمات إضافية يمكن دمجها مع i18n.py
This file contains additional translations that can be merged into i18n.py
"""

ADDITIONAL_TRANSLATIONS = {
    # ==================== عام | General ====================
    
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
    "common.warning": {"en": "Warning", "ar": " تحذير"},
    "common.info": {"en": "Information", "ar": "معلومات"},
    "common.unknown": {"en": "Unknown", "ar": "غير معروف"},
    "common.none": {"en": "None", "ar": "لا يوجد"},
    "common.all": {"en": "All", "ar": "الكل"},
    "common.any": {"en": "Any", "ar": "أي"},
    "common.other": {"en": "Other", "ar": "أخرى"},
    "common.custom": {"en": "Custom", "ar": "مخصص"},
    "common.default": {"en": "Default", "ar": "افتراضي"},
    
    # ==================== الوقت والتاريخ | Time and Date ====================
    
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
    
    "time.seconds_ago": {
        "en": "{count} seconds ago",
        "ar": "منذ {count} ثانية"
    },
    "time.minutes_ago": {
        "en": "{count} minutes ago",
        "ar": "منذ {count} دقيقة"
    },
    "time.hours_ago": {
        "en": "{count} hours ago",
        "ar": "منذ {count} ساعة"
    },
    "time.days_ago": {
        "en": "{count} days ago",
        "ar": "منذ {count} يوم"
    },
    
    # ==================== الحالة | Status ====================
    
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
    
    # ==================== الأفعال | Actions ====================
    
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
    
    # ==================== التنقل | Navigation ====================
    
    "nav.home": {"en": "Home", "ar": "الرئيسية"},
    "nav.back": {"en": "Back", "ar": "رجوع"},
    "nav.next": {"en": "Next", "ar": "التالي"},
    "nav.previous": {"en": "Previous", "ar": "السابق"},
    "nav.first": {"en": "First", "ar": "الأول"},
    "nav.last": {"en": "Last", "ar": "الأخير"},
    "nav.goto": {"en": "Go to", "ar": "اذهب إلى"},
    "nav.page": {"en": "Page", "ar": "صفحة"},
    "nav.of": {"en": "of", "ar": "من"},
    
    # ==================== رسائل النجاح | Success Messages ====================
    
    "success.created": {"en": "Successfully created!", "ar": "تم الإنشاء بنجاح!"},
    "success.updated": {"en": "Successfully updated!", "ar": "تم التحديث بنجاح!"},
    "success.deleted": {"en": "Successfully deleted!", "ar": "تم الحذف بنجاح!"},
    "success.saved": {"en": "Successfully saved!", "ar": "تم الحفظ بنجاح!"},
    "success.sent": {"en": "Successfully sent!", "ar": "تم الإرسال بنجاح!"},
    "success.completed": {"en": "Successfully completed!", "ar": "تم الاكتمال بنجاح!"},
    "success.operation": {"en": "Operation successful!", "ar": "نجحت العملية!"},
    
    # ==================== رسائل الخطأ | Error Messages ====================
    
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
    
    # ==================== رسالة التأكيد | Confirmation Messages ====================
    
    "confirm.delete": {
        "en": "Are you sure you want to delete this?",
        "ar": "هل أنت متأكد من حذف هذا؟"
    },
    "confirm.remove": {
        "en": "Are you sure you want to remove this?",
        "ar": "هل أنت متأكد من إزالة هذا؟"
    },
    "confirm.cancel": {
        "en": "Are you sure you want to cancel?",
        "ar": "هل أنت متأكد من الإلغاء؟"
    },
    "confirm.continue": {
        "en": "Do you want to continue?",
        "ar": "هل تريد المتابعة؟"
    },
    "confirm.action": {
        "en": "This action cannot be undone. Continue?",
        "ar": "لا يمكن التراجع عن هذا الإجراء. متابعة؟"
    },
    "confirm.permanent": {
        "en": "This action is permanent and cannot be undone!",
        "ar": "هذا الإجراء دائم ولا يمكن التراجع عنه!"
    },
    
    # ==================== التقويم | Calendar ====================
    
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
    
    # ==================== العدد والكمية | Numbers and Quantity ====================
    
    "quantity.zero": {"en": "Zero", "ar": "صفر"},
    "quantity.one": {"en": "One", "ar": "واحد"},
    "quantity.few": {"en": "Few", "ar": "قليل"},
    "quantity.many": {"en": "Many", "ar": "كثير"},
    "quantity.empty": {"en": "Empty", "ar": "فارغ"},
    "quantity.full": {"en": "Full", "ar": "ممتلئ"},
    "quantity.total": {"en": "Total", "ar": "إجمالي"},
    "quantity.count": {"en": "Count", "ar": "العدد"},
    "quantity.items": {"en": "items", "ar": "عناصر"},
    
    # ==================== الإشعارات | Notifications ====================
    
    "notif.new_message": {
        "en": "You have a new message",
        "ar": "لديك رسالة جديدة"
    },
    "notif.new_messages": {
        "en": "You have {count} new messages",
        "ar": "لديك {count} رسائل جديدة"
    },
    "notif.no_notifications": {
        "en": "No notifications",
        "ar": "لا توجد إشعارات"
    },
    "notif.mark_read": {
        "en": "Mark as read",
        "ar": "تعليم كمقروء"
    },
    "notif.mark_all_read": {
        "en": "Mark all as read",
        "ar": "تعليم الكل كمقروء"
    },
    "notif.clear_all": {
        "en": "Clear all notifications",
        "ar": "مسح جميع الإشعارات"
    },
    
    # ==================== الإعدادات | Settings ====================
    
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
    
    # ==================== البحث والتصفية | Search and Filter ====================
    
    "search.placeholder": {
        "en": "Search...",
        "ar": "بحث..."
    },
    "search.no_results": {
        "en": "No results found",
        "ar": "لم يتم العثور على نتائج"
    },
    "search.results": {
        "en": "{count} results found",
        "ar": "تم العثور على {count} نتائج"
    },
    "search.searching": {
        "en": "Searching...",
        "ar": "جاري البحث..."
    },
    
    "filter.all": {"en": "All", "ar": "الكل"},
    "filter.active": {"en": "Active", "ar": "نشط"},
    "filter.inactive": {"en": "Inactive", "ar": "غير نشط"},
    "filter.apply": {"en": "Apply Filter", "ar": "تطبيق التصفية"},
    "filter.clear": {"en": "Clear Filter", "ar": "مسح التصفية"},
    
    # ==================== عناصر النماذج | Form Elements ====================
    
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
    
    # ==================== التحميل والتنزيل | Upload and Download ====================
    
    "upload.select_file": {
        "en": "Select a file",
        "ar": "اختر ملفا"
    },
    "upload.drag_drop": {
        "en": "Drag and drop files here",
        "ar": "اسحب وأفلت الملفات هنا"
    },
    "upload.uploading": {
        "en": "Uploading...",
        "ar": "جاري الرفع..."
    },
    "upload.success": {
        "en": "File uploaded successfully",
        "ar": "تم رفع الملف بنجاح"
    },
    "upload.failed": {
        "en": "Upload failed",
        "ar": "فشل الرفع"
    },
    
    "download.downloading": {
        "en": "Downloading...",
        "ar": "جاري التحميل..."
    },
    "download.complete": {
        "en": "Download complete",
        "ar": "اكتمل التحميل"
    },
    "download.failed": {
        "en": "Download failed",
        "ar": "فشل التحميل"
    },
    
    # ==================== المساعدة والدعم | Help and Support ====================
    
    "help.title": {"en": "Help", "ar": "المساعدة"},
    "help.documentation": {"en": "Documentation", "ar": "الوثائق"},
    "help.tutorial": {"en": "Tutorial", "ar": "دليل"},
    "help.faq": {"en": "FAQ", "ar": "الأسئلة الشائعة"},
    "help.contact": {"en": "Contact Support", "ar": "اتصل بالدعم"},
    "help.feedback": {"en": "Send Feedback", "ar": "إرسال ملاحظات"},
    "help.report_bug": {"en": "Report a Bug", "ar": "الإبلاغ عن خطأ"},
    
    # ==================== الصلاحيات | Permissions ====================
    
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
    
    # ==================== الإحصائيات | Statistics ====================
    
    "stats.total": {"en": "Total", "ar": "الإجمالي"},
    "stats.average": {"en": "Average", "ar": "المتوسط"},
    "stats.minimum": {"en": "Minimum", "ar": "الحد الأدنى"},
    "stats.maximum": {"en": "Maximum", "ar": "الحد الأقصى"},
    "stats.median": {"en": "Median", "ar": "الوسيط"},
    "stats.percentage": {"en": "Percentage", "ar": "النسبة المئوية"},
    "stats.growth": {"en": "Growth", "ar": "النمو"},
    "stats.decline": {"en": "Decline", "ar": "التراجع"},
    
    # ==================== الرموز والأيقونات | Icons and Emojis ====================
    
    "icon.info": {"en": "ℹ️", "ar": "ℹ️"},
    "icon.warning": {"en": "⚠️", "ar": "⚠️"},
    "icon.error": {"en": "❌", "ar": "❌"},
    "icon.success": {"en": "✅", "ar": "✅"},
    "icon.loading": {"en": "⏳", "ar": "⏳"},
    "icon.settings": {"en": "⚙️", "ar": "⚙️"},
    "icon.calendar": {"en": "📅", "ar": "📅"},
    "icon.clock": {"en": "🕐", "ar": "🕐"},
    "icon.user": {"en": "👤", "ar": "👤"},
    "icon.search": {"en": "🔍", "ar": "🔍"},
    "icon.heart": {"en": "❤️", "ar": "❤️"},
    "icon.star": {"en": "⭐", "ar": "⭐"},
}


# دالة لدمج الترجمات الإضافية | Function to merge additional translations
def merge_additional_translations():
    """
    دمج الترجمات الإضافية مع i18n.py
    Merge additional translations with i18n.py
    
    Usage:
        from i18n import MESSAGES
        from additional_translations import ADDITIONAL_TRANSLATIONS, merge_additional_translations
        
        # الدمج | Merge
        MESSAGES.update(ADDITIONAL_TRANSLATIONS)
        
        # أو استخدم الدالة | Or use the function
        merge_additional_translations()
    """
    try:
        from i18n import MESSAGES
        
        before = len(MESSAGES)
        MESSAGES.update(ADDITIONAL_TRANSLATIONS)
        after = len(MESSAGES)
        
        print(f"✅ تم دمج {after - before} مفتاح ترجمة جديد")
        print(f"✅ Merged {after - before} new translation keys")
        print(f"📊 الإجمالي | Total: {after} مفتاح")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في الدمج | Merge error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ترجمات إضافية | Additional Translations")
    print("=" * 60)
    print(f"\n📊 عدد الترجمات الإضافية | Additional translations: {len(ADDITIONAL_TRANSLATIONS)}")
    print("\nلدمج هذه الترجمات مع i18n.py:")
    print("To merge these with i18n.py:\n")
    print("from additional_translations import merge_additional_translations")
    print("merge_additional_translations()")
