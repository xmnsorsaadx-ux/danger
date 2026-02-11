# الأسئلة الشائعة | FAQ - Translation System

## 📌 جدول المحتويات | Table of Contents

1. [أسئلة عامة](#general)
2. [الاستخدام](#usage)
3. [المشاكل الشائعة](#troubleshooting)
4. [التطوير](#development)
5. [الأداء](#performance)

---

## <a name="general"></a>أسئلة عامة | General Questions

### س: ما هي اللغات المدعومة؟
**Q: What languages are supported?**

حاليًا يدعم البوت:
- 🇬🇧 الإنجليزية (English) - `en`
- 🇸🇦 العربية (Arabic) - `ar`

يمكن إضافة لغات جديدة بسهولة. راجع [دليل إضافة لغة](./i18n_guide.md#adding-new-language).

---

### س: كيف يتم اختيار اللغة لكل سيرفر؟
**Q: How is language selected per server?**

- كل سيرفر Discord له لغة مستقلة
- اللغة الافتراضية: الإنجليزية
- يمكن تغيير اللغة عبر `/settings` → Language
- تُحفظ اللغة في قاعدة بيانات `db/settings.sqlite`

---

### س: هل يمكن للمستخدمين اختيار لغتهم الخاصة؟
**Q: Can users choose their own language?**

لا، حاليًا اللغة على مستوى السيرفر فقط. جميع المستخدمين في نفس السيرفر يرون نفس اللغة.

لتنفيذ لغة على مستوى المستخدم:
1. أضف جدول `user_language_settings`
2. عدّل دالة `get_guild_language()` لتفحص المستخدم أولاً
3. أضف أمر `/language` شخصي

---

## <a name="usage"></a>الاستخدام | Usage

### س: كيف أترجم رسالة في الكود؟
**Q: How do I translate a message in code?**

```python
from i18n import t, get_guild_language

# 1. احصل على اللغة | Get the language
lang = get_guild_language(interaction.guild_id)

# 2. استخدم دالة t() | Use t() function
message = t("menu.settings.title", lang)

# 3. مع معاملات | With parameters
message = t("alliance.member.add.success_body", lang, count=10)
```

---

### س: ماذا يحدث إذا كان المفتاح غير موجود؟
**Q: What happens if a key doesn't exist?**

دالة `t()` ترجع المفتاح نفسه:
```python
result = t("non.existent.key", "ar")
# result = "non.existent.key"
```

لاكتشاف المفاتيح المفقودة:
```bash
python i18n_utils.py
```

---

### س: كيف أستخدم معاملات متعددة؟
**Q: How to use multiple parameters?**

```python
# في i18n.py
MESSAGES = {
    "my.key": {
        "en": "{user} added {count} members to {alliance}",
        "ar": "{user} أضاف {count} أعضاء إلى {alliance}"
    }
}

# في الكود
message = t("my.key", lang, 
           user="Admin", 
           count=5, 
           alliance="FireStorm")
```

تأكد من تطابق أسماء المعاملات في جميع اللغات!

---

### س: كيف أترجم Embed؟
**Q: How to translate an Embed?**

```python
lang = get_guild_language(guild_id)

embed = discord.Embed(
    title=t("embed.title", lang),
    description=t("embed.description", lang),
    color=discord.Color.blue()
)

embed.add_field(
    name=t("field.name", lang),
    value=t("field.value", lang, count=10)
)

embed.set_footer(text=t("footer.text", lang))
```

---

## <a name="troubleshooting"></a>المشاكل الشائعة | Troubleshooting

### س: النص العربي يظهر معكوسًا في المحرر
**Q: Arabic text appears reversed in editor**

هذا طبيعي! المحررات التي لا تدعم RTL تعرض النص من اليسار.

**الحلول:**
- استخدم محرر يدعم RTL مثل VS Code مع ملحق Arabic RTL
- أو تجاهل المشكلة - النص سيظهر صحيحًا في Discord

---

### س: الترجمة لا تعمل
**Q: Translation doesn't work**

**تحقق من:**
1. هل المفتاح موجود في `i18n.py`؟
   ```python
   from i18n import MESSAGES
   print("my.key" in MESSAGES)
   ```

2. هل اللغة صحيحة؟
   ```python
   lang = get_guild_language(guild_id)
   print(f"Language: {lang}")
   ```

3. هل هناك أخطاء إملائية؟
   ```python
   # ❌ خطأ
   t("menu.setting.title", lang)  # setting بدون s
   
   # ✅ صحيح
   t("menu.settings.title", lang)
   ```

---

### س: المعاملات لا تظهر في النص
**Q: Parameters don't show in text**

**أسباب محتملة:**

1. **اسم المعامل خطأ:**
   ```python
   # في i18n.py: {count}
   # في الكود:
   t("key", lang, number=5)  # ❌ خطأ - يجب count
   t("key", lang, count=5)   # ✅ صحيح
   ```

2. **نسيت `**kwargs`:**
   ```python
   # ❌ خطأ
   def my_function(key, lang):
       return t(key, lang)
   
   # ✅ صحيح
   def my_function(key, lang, **kwargs):
       return t(key, lang, **kwargs)
   ```

3. **استخدم `format()` يدويًا:**
   ```python
   # ❌ لا تفعل
   text = t("key", lang)
   text = text.format(count=5)
   
   # ✅ استخدم t() مباشرة
   text = t("key", lang, count=5)
   ```

---

### س: كيف أجد الترجمات الناقصة؟
**Q: How to find missing translations?**

```bash
python i18n_utils.py
```

أو في الكود:
```python
from i18n_utils import find_missing_translations

missing = find_missing_translations()
for key, langs in missing.items():
    print(f"{key}: Missing in {langs}")
```

---

## <a name="development"></a>التطوير | Development

### س: كيف أضيف مفتاح ترجمة جديد؟
**Q: How to add a new translation key?**

**الخطوات:**
1. افتح `i18n.py`
2. أضف في `MESSAGES`:
   ```python
   "my.new.key": {
       "en": "English text",
       "ar": "النص العربي"
   }
   ```
3. استخدم في الكود:
   ```python
   text = t("my.new.key", lang)
   ```

**نصائح:**
- استخدم تسمية هرمية: `module.feature.element`
- أضف للغتين معًا
- اختبر بعد الإضافة

---

### س: كيف أختبر الترجمات؟
**Q: How to test translations?**

**اختبار يدوي:**
```python
from i18n import t

# اختبار بسيط
print(t("menu.settings.title", "en"))
print(t("menu.settings.title", "ar"))

# اختبار مع معاملات
print(t("alliance.member.add.success_body", "en", count=10))
print(t("alliance.member.add.success_body", "ar", count=10))
```

**اختبار آلي:**
```python
from i18n_utils import check_format_consistency

issues = check_format_consistency()
if not issues:
    print("✅ All translations consistent!")
else:
    print("❌ Found issues:")
    for key, lang, issue in issues:
        print(f"  {key} ({lang}): {issue}")
```

---

### س: كيف أحافظ على جودة الترجمات؟
**Q: How to maintain translation quality?**

**أفضل الممارسات:**

1. **استخدم مراجع طبيعي:**
   - ✅ "تمت الإضافة بنجاح"
   - ❌ "النجاح تم الإضافة" (ترجمة حرفية)

2. **كن متسقًا:**
   - استخدم نفس المصطلح للمفهوم الواحد
   - راجع [قاموس المصطلحات](./terminology.md)

3. **اختبر في السياق:**
   - لا تترجم الكلمات منفردة
   - اختبر الجملة كاملة في واجهة Discord

4. **استخدم الأدوات:**
   ```bash
   python i18n_utils.py  # تقرير شامل
   ```

---

### س: كيف أصدّر/أستورد الترجمات؟
**Q: How to export/import translations?**

**تصدير:**
```python
from i18n_utils import export_translations_to_json

export_translations_to_json("translations.json")
```

**استيراد:**
```python
from i18n_utils import import_translations_from_json

new_translations = import_translations_from_json("translations.json")

# دمج في i18n.py
from i18n import MESSAGES
MESSAGES.update(new_translations)
```

---

## <a name="performance"></a>الأداء | Performance

### س: هل الترجمة بطيئة؟
**Q: Is translation slow?**

لا، الترجمة سريعة جدًا:
- البحث في قاموس: O(1)
- تنسيق النص: سريع جدًا
- لا استعلامات قاعدة بيانات

**مثال:**
```python
import time

start = time.time()
for _ in range(10000):
    t("menu.settings.title", "ar")
end = time.time()

print(f"10,000 translations in {end - start:.3f} seconds")
# عادة < 0.1 ثانية
```

---

### س: هل يجب cache اللغة؟
**Q: Should I cache the language?**

**نعم في بعض الحالات:**

```python
class MyView(View):
    def __init__(self, guild_id):
        super().__init__()
        # cache اللغة مرة واحدة
        self.lang = get_guild_language(guild_id)
    
    async def button_callback(self, interaction):
        # استخدم self.lang بدلاً من get_guild_language كل مرة
        message = t("button.clicked", self.lang)
```

**متى تستخدم cache:**
- في View/Modal يُستخدم عدة مرات
- في حلقات كبيرة
- عند معالجة قوائم طويلة

**متى لا تستخدم cache:**
- في commands بسيطة (مرة واحدة)
- عند الحاجة للغة الحالية دائماً

---

### س: كم حجم ملف i18n.py؟
**Q: How large is i18n.py file?**

حاليًا:
- ~5200 سطر
- ~1200 مفتاح ترجمة
- لغتان (en, ar)

**هل هذا مشكلة؟**
لا! Python يحمل الملف مرة واحدة عند البدء.

**إذا كبر الملف كثيرًا:**
1. قسّمه لملفات:
   ```
   i18n/
     __init__.py
     alliance.py
     gift.py
     minister.py
   ```

2. استخدم lazy loading:
   ```python
   from importlib import import_module
   
   def get_translations(module):
       return import_module(f"i18n.{module}").MESSAGES
   ```

---

### س: هل يجب استخدام gettext بدلاً من هذا النظام؟
**Q: Should I use gettext instead of this system?**

**النظام الحالي:**
- ✅ بسيط وسهل الفهم
- ✅ لا يحتاج compile (.po → .mo)
- ✅ مناسب للمشاريع الصغيرة/المتوسطة
- ✅ دعم Unicode كامل
- ❌ لا يدعم الجمع التلقائي

**gettext:**
- ✅ معيار صناعي
- ✅ أدوات كثيرة
- ✅ دعم الجمع (pluralization)
- ❌ معقد نوعًا ما
- ❌ يحتاج compile

**التوصية:**
للمشروع الحالي، استمر مع النظام البسيط. إذا كبر المشروع كثيرًا أو احتجت pluralization متقدم، انتقل لـ gettext.

---

## 🔧 مشاكل خاصة | Specific Issues

### س: كيف أتعامل مع الجمع في العربية؟
**Q: How to handle Arabic plurals?**

العربية لها 6 أشكال للجمع! حاليًا النظام لا يدعمها تلقائيًا.

**الحل المؤقت:**
```python
def get_count_text(count, lang):
    if lang == "ar":
        if count == 0:
            return "لا يوجد أعضاء"
        elif count == 1:
            return "عضو واحد"
        elif count == 2:
            return "عضوان"
        elif 3 <= count <= 10:
            return f"{count} أعضاء"
        else:
            return f"{count} عضو"
    else:
        if count == 1:
            return "1 member"
        else:
            return f"{count} members"

# الاستخدام
text = t("alliance.has", lang, members=get_count_text(count, lang))
```

---

### س: كيف أتعامل مع RTL في Embeds؟
**Q: How to handle RTL in Embeds?**

Discord يدعم RTL تلقائيًا! لكن:

**مشاكل محتملة:**
```python
# ❌ قد يظهر غريبًا
f"العضو: {member_name} - المستوى: {level}"

# ✅ أفضل
f"{member_name} :العضو - {level} :المستوى"

# أو استخدم Unicode marks
LRM = "\u200E"  # Left-to-right mark
f"العضو: {LRM}{member_name} - المستوى: {LRM}{level}"
```

---

### س: أحتاج ترجمة ديناميكية (runtime)
**Q: I need dynamic runtime translation**

```python
# ❌ لا يعمل - لا يمكن إضافة مفاتيح جديدة runtime
MESSAGES["new.key"] = {"en": "Text", "ar": "نص"}

# ✅ استخدم قاموس مخصص
DYNAMIC_TRANSLATIONS = {}

def add_dynamic_translation(key, translations):
    DYNAMIC_TRANSLATIONS[key] = translations

def t_dynamic(key, lang, **kwargs):
    # ابحث في الديناميكي أولاً
    if key in DYNAMIC_TRANSLATIONS:
        template = DYNAMIC_TRANSLATIONS[key].get(lang, key)
    else:
        # ثم في الثابت
        from i18n import t
        return t(key, lang, **kwargs)
    
    try:
        return template.format(**kwargs)
    except:
        return template
```

---

## 📚 موارد إضافية | Additional Resources

- [دليل i18n](./i18n_guide.md) - الدليل الشامل
- [أمثلة الاستخدام](./i18n_examples.md) - 13 مثال عملي
- [قاموس المصطلحات](./terminology.md) - مصطلحات متفق عليها
- [كود i18n.py](../i18n.py) - الملف الأساسي
- [أدوات i18n_utils.py](../i18n_utils.py) - أدوات مساعدة

---

## 💬 لديك سؤال آخر؟ | Have Another Question?

لم تجد إجابة لسؤالك؟
- افتح issue في GitHub
- راسل فريق التطوير
- راجع الوثائق الأخرى

---

**آخر تحديث | Last Updated:** 2026-02-11
**الإصدار | Version:** 1.0
