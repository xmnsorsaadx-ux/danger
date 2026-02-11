# دليل نظام الترجمة | Translation System Guide

## 📚 نظرة عامة | Overview

نظام الترجمة في DANGER Bot يدعم حاليًا:
- 🇸🇦 **العربية** (Arabic - ar)
- 🇬🇧 **الإنجليزية** (English - en)

---

## 🚀 البدء السريع | Quick Start

### استخدام الترجمة في الكود | Using Translation in Code

```python
from i18n import t, get_guild_language

# الحصول على لغة السيرفر
# Get guild language
lang = get_guild_language(guild_id)

# الترجمة البسيطة
# Simple translation
message = t("welcome.title", lang)

# الترجمة مع معاملات
# Translation with parameters
message = t("alliance.member.add.success_body", lang, count=5)
```

---

## 📖 بنية نظام الترجمة | Translation System Structure

### ملف i18n.py

```python
MESSAGES = {
    "key.name": {
        "en": "English text",
        "ar": "النص العربي"
    }
}
```

### الدوال المتاحة | Available Functions

#### `get_guild_language(guild_id: int) -> str`
الحصول على اللغة المختارة للسيرفر
Get selected language for guild

**مثال | Example:**
```python
lang = get_guild_language(123456789)
# Returns: "ar" or "en"
```

#### `set_guild_language(guild_id: int, language: str) -> str`
تعيين لغة للسيرفر
Set language for guild

**مثال | Example:**
```python
new_lang = set_guild_language(123456789, "ar")
# Returns: "ar"
```

#### `t(key: str, language: str = None, **kwargs) -> str`
ترجمة مفتاح نصي مع دعم المعاملات
Translate a text key with parameter support

**مثال | Example:**
```python
# ترجمة بسيطة | Simple translation
text = t("menu.settings.title", "ar")

# مع معاملات | With parameters
text = t("gift.redeem.queued_body", "ar", count=10)
```

---

## ✨ إضافة ترجمات جديدة | Adding New Translations

### الخطوات | Steps

1. **إضافة المفتاح في i18n.py**

```python
MESSAGES = {
    # ... existing keys
    "new.feature.title": {
        "en": "New Feature",
        "ar": "ميزة جديدة"
    },
    "new.feature.description": {
        "en": "Description of the new feature",
        "ar": "وصف الميزة الجديدة"
    }
}
```

2. **استخدام المفتاح في الكود**

```python
from i18n import t

async def show_new_feature(interaction, lang):
    title = t("new.feature.title", lang)
    description = t("new.feature.description", lang)
    
    embed = discord.Embed(title=title, description=description)
    await interaction.response.send_message(embed=embed)
```

---

## 🎨 إرشادات الترجمة | Translation Guidelines

### للنصوص العربية | For Arabic Text

✅ **افعل | Do:**
- استخدم اللغة العربية الفصحى المبسطة
- تأكد من الترجمة الطبيعية وليست الحرفية
- استخدم المصطلحات التقنية المعتادة

❌ **لا تفعل | Don't:**
- لا تستخدم الترجمة الآلية دون مراجعة
- لا تخلط بين العامية والفصحى
- لا تترك نصوص إنجليزية في الترجمة العربية

### للنصوص الإنجليزية | For English Text

✅ **Do:**
- Use clear, concise language
- Maintain consistent terminology
- Keep it professional yet friendly

❌ **Don't:**
- Don't use overly technical jargon
- Don't make sentences too long
- Don't mix informal and formal styles

---

## 🔧 أدوات المساعدة | Helper Tools

### فحص الترجمات الناقصة | Check Missing Translations

```bash
python i18n_utils.py
```

### تصدير الترجمات | Export Translations

```python
from i18n_utils import export_translations_to_json

export_translations_to_json("my_translations.json")
```

### استيراد الترجمات | Import Translations

```python
from i18n_utils import import_translations_from_json

new_translations = import_translations_from_json("my_translations.json")
```

---

## 📊 إحصائيات الترجمة | Translation Statistics

استخدم `i18n_utils.py` للحصول على تقرير شامل:
Use `i18n_utils.py` to get comprehensive report:

```bash
python i18n_utils.py
```

سيعرض:
Will display:
- إجمالي عدد المفاتيح | Total number of keys
- نسبة الاكتمال لكل لغة | Completion percentage per language
- المفاتيح الناقصة | Missing keys
- مشاكل التنسيق | Format issues

---

## 🌍 إضافة لغة جديدة | Adding a New Language

### الخطوات | Steps

1. **تحديث SUPPORTED_LANGUAGES في i18n.py**

```python
SUPPORTED_LANGUAGES = {"en", "ar", "fr"}  # إضافة الفرنسية | Adding French
```

2. **إضافة الترجمات لجميع المفاتيح**

```python
MESSAGES = {
    "welcome.title": {
        "en": "Welcome",
        "ar": "مرحبا",
        "fr": "Bienvenue"  # جديد | new
    }
}
```

3. **تحديث واجهة اختيار اللغة**

أضف خيار اللغة الجديدة في القوائم
Add new language option in menus

---

## 🧪 اختبار الترجمات | Testing Translations

### اختبار يدوي | Manual Testing

```python
from i18n import t

# اختبار العربية | Test Arabic
print(t("menu.settings.title", "ar"))

# اختبار الإنجليزية | Test English  
print(t("menu.settings.title", "en"))

# اختبار مع معاملات | Test with parameters
print(t("alliance.member.add.progress_desc", "ar", count=5, alliance="Test", current=3, total=5))
```

### اختبار آلي | Automated Testing

```python
from i18n_utils import check_format_consistency, find_missing_translations

# فحص التنسيق | Check format
issues = check_format_consistency()
if issues:
    print("Found issues:", issues)

# فحص الترجمات الناقصة | Check missing
missing = find_missing_translations()
if missing:
    print("Missing translations:", missing)
```

---

## 🎯 أفضل الممارسات | Best Practices

### تسمية المفاتيح | Key Naming

استخدم بنية هرمية واضحة:
Use clear hierarchical structure:

```
module.feature.element.property
```

**أمثلة | Examples:**
- `alliance.member.add.title`
- `gift.redeem.progress_desc`
- `minister.menu.schedule_title`

### المعاملات المتغيرة | Variable Parameters

استخدم أسماء واضحة للمعاملات:
Use clear parameter names:

```python
# ✅ جيد | Good
"Added {count} members to {alliance}"

# ❌ سيء | Bad
"Added {x} members to {y}"
```

### الاتساق | Consistency

حافظ على نفس المعاملات في جميع اللغات:
Keep same parameters across all languages:

```python
{
    "en": "Welcome {user} to {server}",
    "ar": "مرحبا {user} في {server}"
}
```

---

## 🔍 استكشاف الأخطاء | Troubleshooting

### المشكلة: الترجمة لا تظهر
**Problem: Translation doesn't show**

**الحلول | Solutions:**
1. تحقق من وجود المفتاح في MESSAGES
2. تحقق من اسم المفتاح (حساس لحالة الأحرف)
3. تحقق من اللغة المحددة

### المشكلة: المعاملات لا تعمل
**Problem: Parameters don't work**

**الحلول | Solutions:**
1. تحقق من تطابق اسم المعامل في النص والكود
2. تأكد من استخدام `**kwargs` في دالة `t()`
3. تحقق من صيغة `{param}` في النص

### المشكلة: نص عربي معكوس
**Problem: Arabic text reversed**

**الحل | Solution:**
تأكد من أن المحرر/IDE يدعم RTL بشكل صحيح
Make sure editor/IDE supports RTL properly

---

## 📚 موارد إضافية | Additional Resources

- [قاموس المصطلحات](./terminology.md)
- [أمثلة الاستخدام](./examples.md)
- [FAQ](./faq.md)

---

## 🤝 المساهمة | Contributing

نرحب بمساهماتكم في تحسين الترجمات!
We welcome contributions to improve translations!

### كيفية المساهمة | How to Contribute

1. Fork المشروع
2. أضف/حسّن الترجمات
3. اختبر التغييرات
4. أرسل Pull Request

---

**آخر تحديث | Last Updated:** 2026-02-11
**الإصدار | Version:** 3.0
