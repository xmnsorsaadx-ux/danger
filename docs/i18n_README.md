# 🌍 نظام الترجمة | Translation System

## نظام i18n الاحترافي لـ DANGER Bot
**Professional i18n System for DANGER Bot**

---

## 🎯 نظرة عامة | Overview

نظام ترجمة شامل واحترافي يدعم لغات متعددة مع أدوات مساعدة متقدمة وتوثيق كامل.

A comprehensive professional translation system supporting multiple languages with advanced helper tools and complete documentation.

### اللغات المدعومة | Supported Languages

- 🇬🇧 **English** (`en`) - Default
- 🇸🇦 **العربية** (`ar`) - Arabic

---

## 📁 هيكل الملفات | File Structure

```
.
├── i18n.py                    # نظام الترجمة الأساسي | Core translation system
├── i18n_utils.py              # أدوات مساعدة | Helper utilities
└── docs/                      # الوثائق | Documentation
    ├── i18n_guide.md         # دليل شامل | Comprehensive guide
    ├── i18n_examples.md      # أمثلة عملية | Practical examples
    ├── i18n_faq.md          # أسئلة شائعة | FAQ
    └── terminology.md        # قاموس المصطلحات | Terminology dictionary
```

---

## 🚀 البدء السريع | Quick Start

### استخدام أساسي | Basic Usage

```python
from i18n import t, get_guild_language

# الحصول على لغة السيرفر | Get guild language
lang = get_guild_language(guild_id)

# ترجمة بسيطة | Simple translation
message = t("menu.settings.title", lang)

# ترجمة مع معاملات | Translation with parameters
message = t("alliance.member.add.success_body", lang, count=10)
```

### في Discord Command

```python
import discord
from discord import app_commands
from i18n import t, get_guild_language

@app_commands.command(name="test")
async def test_command(interaction: discord.Interaction):
    lang = get_guild_language(interaction.guild_id)
    
    title = t("test.title", lang)
    description = t("test.description", lang, user=interaction.user.name)
    
    embed = discord.Embed(title=title, description=description)
    await interaction.response.send_message(embed=embed)
```

---

## 📊 الإحصائيات | Statistics

### تشغيل تقرير الترجمة | Run Translation Report

```bash
python i18n_utils.py
```

**مثال على النتيجة | Sample Output:**
```
============================================================
تقرير حالة الترجمة | Translation Status Report
============================================================

📊 إحصائيات عامة | General Statistics:
   إجمالي المفاتيح | Total Keys: 1200

🌍 نسبة الاكتمال لكل لغة | Completion by Language:
   English (en): 1200/1200 (100.0%)
   العربية (ar): 1200/1200 (100.0%)

✅ جميع الترجمات مكتملة | All translations complete!

✅ جميع القوالب متسقة | All format templates consistent!
============================================================
```

---

## 🔧 الأدوات المساعدة | Helper Tools

### i18n_utils.py

أدوات متقدمة لإدارة الترجمات:

#### 1. فحص الترجمات الناقصة
**Check Missing Translations**

```python
from i18n_utils import find_missing_translations

missing = find_missing_translations()
for key, langs in missing.items():
    print(f"{key}: Missing in {langs}")
```

#### 2. فحص اتساق التنسيق
**Check Format Consistency**

```python
from i18n_utils import check_format_consistency

issues = check_format_consistency()
for key, lang, issue in issues:
    print(f"{key} ({lang}): {issue}")
```

#### 3. تصدير الترجمات
**Export Translations**

```python
from i18n_utils import export_translations_to_json

export_translations_to_json("translations.json")
```

#### 4. فحص جودة النصوص العربية
**Validate Arabic Text Quality**

```python
from i18n_utils import validate_arabic_text_quality

issues = validate_arabic_text_quality()
for key, issue in issues:
    print(f"{key}: {issue}")
```

---

## 📚 الوثائق | Documentation

### 1. [دليل i18n الشامل](docs/i18n_guide.md)
**Comprehensive i18n Guide**

- كيفية الاستخدام
- إضافة ترجمات جديدة
- إرشادات الترجمة
- إضافة لغات جديدة
- أفضل الممارسات

### 2. [أمثلة عملية](docs/i18n_examples.md)
**Practical Examples**

13 مثالاً شاملاً:
- أمثلة بسيطة
- الترجمة في Commands
- الترجمة في Embeds
- الترجمة في Views/Buttons
- الترجمة المتقدمة

### 3. [الأسئلة الشائعة](docs/i18n_faq.md)
**Frequently Asked Questions**

- أسئلة عامة
- الاستخدام
- المشاكل الشائعة
- التطوير
- الأداء

### 4. [قاموس المصطلحات](docs/terminology.md)
**Terminology Dictionary**

- مصطلحات اللعبة
- مصطلحات البوت
- عبارات شائعة
- قواعد الترجمة

---

## ✨ الميزات | Features

### ✅ الميزات الحالية | Current Features

- ✅ دعم لغتين (عربي/إنجليزي)
- ✅ ترجمة ديناميكية مع معاملات
- ✅ تخزين اللغة لكل سيرفر
- ✅ أدوات فحص وتحقق شاملة
- ✅ تقارير مفصلة
- ✅ تصدير/استيراد JSON
- ✅ توثيق كامل بالعربية والإنجليزية
- ✅ 13 مثال عملي
- ✅ أكثر من 1200 مفتاح ترجمة

### 🔜 ميزات مستقبلية | Future Features

- ⏳ دعم الجمع التلقائي (Pluralization)
- ⏳ واجهة ويب لإدارة الترجمات
- ⏳ ترجمة على مستوى المستخدم
- ⏳ دعم لغات إضافية
- ⏳ تكامل مع خدمات الترجمة الآلية

---

## 🎨 أفضل الممارسات | Best Practices

### تسمية المفاتيح | Key Naming

استخدم بنية هرمية واضحة:
```
module.feature.element.property
```

**أمثلة | Examples:**
```python
"alliance.member.add.title"
"gift.redeem.progress_desc"
"minister.menu.schedule_title"
```

### المعاملات | Parameters

استخدم أسماء واضحة ومتسقة:
```python
# ✅ جيد | Good
"Added {count} members to {alliance}"

# ❌ سيء | Bad  
"Added {x} members to {y}"
```

### الاتساق | Consistency

حافظ على نفس المعاملات في جميع اللغات:
```python
{
    "en": "Welcome {user} to {server}",
    "ar": "مرحبا {user} في {server}"
}
```

---

## 🧪 الاختبار | Testing

### اختبار يدوي | Manual Testing

```python
from i18n import t

# اختبار العربية | Test Arabic
print(t("menu.settings.title", "ar"))

# اختبار الإنجليزية | Test English
print(t("menu.settings.title", "en"))

# اختبار مع معاملات | Test with parameters
print(t("alliance.member.add.success_body", "ar", count=10))
```

### اختبار آلي | Automated Testing

```bash
# تشغيل جميع الفحوصات | Run all checks
python i18n_utils.py

# فحص محدد | Specific check
python -c "from i18n_utils import check_format_consistency; print(check_format_consistency())"
```

---

## 📈 الإحصائيات الحالية | Current Statistics

- **إجمالي المفاتيح | Total Keys:** ~1,200
- **اللغات المدعومة | Supported Languages:** 2
- **نسبة الاكتمال | Completion Rate:** 100%
- **عدد الأسطر | Lines of Code:** ~5,200
- **الملفات | Files:** 5 (1 core + 4 docs)

---

## 🤝 المساهمة | Contributing

### كيفية المساهمة | How to Contribute

1. **تحسين الترجمات | Improve Translations**
   - راجع الترجمات الموجودة
   - قدم ترجمات أفضل
   - أضف سياقات مفقودة

2. **إضافة لغات جديدة | Add New Languages**
   - راجع [دليل إضافة لغة](docs/i18n_guide.md#adding-new-language)
   - ترجم جميع المفاتيح
   - اختبر الترجمات

3. **تحسين الأدوات | Improve Tools**
   - أضف ميزات جديدة لـ `i18n_utils.py`
   - حسّن الأداء
   - أضف اختبارات

4. **توثيق | Documentation**
   - حسّن الأدلة الموجودة
   - أضف أمثلة جديدة
   - ترجم الوثائق

---

## 🐛 الإبلاغ عن المشاكل | Reporting Issues

وجدت مشكلة؟ | Found an issue?

1. **ترجمة خاطئة | Wrong Translation**
   - حدد المفتاح
   - اقترح الترجمة الصحيحة
   - اشرح السبب

2. **مفتاح ناقص | Missing Key**
   - حدد أين يظهر
   - اقترح المفتاح والترجمات
   - أرفق لقطة شاشة إن أمكن

3. **خطأ تقني | Technical Error**
   - وصف المشكلة
   - خطوات إعادة إنتاجها
   - رسالة الخطأ

---

## 📞 الدعم | Support

- **الوثائق:** راجع مجلد `docs/`
- **الأمثلة:** راجع `docs/i18n_examples.md`
- **FAQ:** راجع `docs/i18n_faq.md`
- **GitHub:** افتح issue

---

## 📄 الترخيص | License

هذا المشروع مفتوح المصدر ومتاح تحت نفس ترخيص المشروع الأساسي.

This project is open source and available under the same license as the main project.

---

## 🎉 شكر خاص | Special Thanks

- فريق DANGER Bot Team
- المساهمون في الترجمة
- مجتمع Discord

---

**🔗 روابط سريعة | Quick Links**

- [دليل شامل](docs/i18n_guide.md) | [Comprehensive Guide](docs/i18n_guide.md)
- [أمثلة عملية](docs/i18n_examples.md) | [Practical Examples](docs/i18n_examples.md)
- [أسئلة شائعة](docs/i18n_faq.md) | [FAQ](docs/i18n_faq.md)
- [قاموس مصطلحات](docs/terminology.md) | [Terminology](docs/terminology.md)

---

**آخر تحديث | Last Updated:** 2026-02-11  
**الإصدار | Version:** 3.0  
**الحالة | Status:** ✅ Production Ready
