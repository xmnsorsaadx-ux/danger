"""
أدوات مساعدة لنظام الترجمة i18n
Translation System Utilities

هذا الملف يحتوي على أدوات مساعدة لتحسين وإدارة نظام الترجمة
"""

import json
from typing import Dict, List, Tuple, Set
from i18n import MESSAGES, SUPPORTED_LANGUAGES


def find_missing_translations() -> Dict[str, List[str]]:
    """
    البحث عن المفاتيح التي تحتوي على ترجمات ناقصة
    Find keys with missing translations
    
    Returns:
        قاموس بالمفاتيح والغات الناقصة
        Dictionary of keys with missing languages
    """
    missing = {}
    
    for key, translations in MESSAGES.items():
        missing_langs = []
        for lang in SUPPORTED_LANGUAGES:
            if lang not in translations or not translations[lang]:
                missing_langs.append(lang)
        
        if missing_langs:
            missing[key] = missing_langs
    
    return missing


def check_format_consistency() -> List[Tuple[str, str, str]]:
    """
    التحقق من اتساق قوالب التنسيق بين اللغات
    Check format template consistency between languages
    
    Returns:
        قائمة بالمفاتيح التي تحتوي على اختلافات في معاملات التنسيق
        List of keys with format parameter differences
    """
    inconsistencies = []
    
    for key, translations in MESSAGES.items():
        # استخراج المعاملات من كل لغة
        # Extract parameters from each language
        params_by_lang = {}
        
        for lang, text in translations.items():
            if not text:
                continue
            # البحث عن {param} في النص
            import re
            params = set(re.findall(r'\{(\w+)\}', text))
            params_by_lang[lang] = params
        
        # مقارنة المعاملات بين اللغات
        # Compare parameters between languages
        if len(params_by_lang) > 1:
            all_params = list(params_by_lang.values())
            first_params = all_params[0]
            
            for lang, params in params_by_lang.items():
                if params != first_params:
                    inconsistencies.append((key, lang, f"Expected {first_params}, got {params}"))
    
    return inconsistencies


def generate_translation_report() -> str:
    """
    إنشاء تقرير شامل عن حالة الترجمات
    Generate comprehensive translation status report
    
    Returns:
        تقرير نصي
        Text report
    """
    total_keys = len(MESSAGES)
    missing = find_missing_translations()
    inconsistencies = check_format_consistency()
    
    # حساب نسبة الاكتمال لكل لغة
    # Calculate completion percentage for each language
    completion_stats = {}
    for lang in SUPPORTED_LANGUAGES:
        complete = sum(1 for key in MESSAGES if lang in MESSAGES[key] and MESSAGES[key][lang])
        percentage = (complete / total_keys * 100) if total_keys > 0 else 0
        completion_stats[lang] = {
            'complete': complete,
            'total': total_keys,
            'percentage': percentage
        }
    
    # بناء التقرير
    # Build report
    report = []
    report.append("=" * 60)
    report.append("تقرير حالة الترجمة | Translation Status Report")
    report.append("=" * 60)
    report.append("")
    
    report.append("📊 إحصائيات عامة | General Statistics:")
    report.append(f"   إجمالي المفاتيح | Total Keys: {total_keys}")
    report.append("")
    
    report.append("🌍 نسبة الاكتمال لكل لغة | Completion by Language:")
    for lang, stats in completion_stats.items():
        lang_name = "العربية" if lang == "ar" else "English"
        report.append(f"   {lang_name} ({lang}): {stats['complete']}/{stats['total']} ({stats['percentage']:.1f}%)")
    report.append("")
    
    if missing:
        report.append(f"⚠️  ترجمات ناقصة | Missing Translations: {len(missing)}")
        report.append("   أول 10 مفاتيح | First 10 Keys:")
        for i, (key, langs) in enumerate(list(missing.items())[:10]):
            report.append(f"   {i+1}. {key}: {', '.join(langs)}")
        if len(missing) > 10:
            report.append(f"   ... و {len(missing) - 10} أخرى | and {len(missing) - 10} more")
        report.append("")
    else:
        report.append("✅ جميع الترجمات مكتملة | All translations complete!")
        report.append("")
    
    if inconsistencies:
        report.append(f"⚠️  عدم اتساق في التنسيق | Format Inconsistencies: {len(inconsistencies)}")
        report.append("   أول 5 مشاكل | First 5 Issues:")
        for i, (key, lang, issue) in enumerate(inconsistencies[:5]):
            report.append(f"   {i+1}. {key} ({lang}): {issue}")
        if len(inconsistencies) > 5:
            report.append(f"   ... و {len(inconsistencies) - 5} أخرى | and {len(inconsistencies) - 5} more")
        report.append("")
    else:
        report.append("✅ جميع القوالب متسقة | All format templates consistent!")
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)


def export_translations_to_json(filepath: str = "translations_export.json") -> None:
    """
    تصدير جميع الترجمات إلى ملف JSON
    Export all translations to JSON file
    
    Args:
        filepath: مسار الملف للحفظ | File path to save
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(MESSAGES, f, ensure_ascii=False, indent=2)
    print(f"✅ تم التصدير إلى | Exported to: {filepath}")


def import_translations_from_json(filepath: str) -> Dict[str, Dict[str, str]]:
    """
    استيراد الترجمات من ملف JSON
    Import translations from JSON file
    
    Args:
        filepath: مسار الملف | File path
        
    Returns:
        قاموس الترجمات المستوردة | Imported translations dictionary
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_unused_keys(code_directory: str = "./cogs") -> Set[str]:
    """
    البحث عن مفاتيح الترجمة غير المستخدمة في الكود
    Find translation keys not used in code
    
    Args:
        code_directory: مسار مجلد الكود | Code directory path
        
    Returns:
        مجموعة المفاتيح غير المستخدمة | Set of unused keys
    """
    import os
    import re
    
    # جمع جميع المفاتيح المستخدمة في الكود
    # Collect all keys used in code
    used_keys = set()
    
    for root, _, files in os.walk(code_directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # البحث عن t("key") أو t('key')
                        # Search for t("key") or t('key')
                        matches = re.findall(r't\(["\']([^"\']+)["\']', content)
                        used_keys.update(matches)
                except Exception as e:
                    print(f"خطأ في قراءة | Error reading {filepath}: {e}")
    
    # إيجاد المفاتيح المعرفة ولكن غير المستخدمة
    # Find defined but unused keys
    all_keys = set(MESSAGES.keys())
    unused = all_keys - used_keys
    
    return unused


def validate_arabic_text_quality() -> List[Tuple[str, str]]:
    """
    التحقق من جودة النصوص العربية
    Validate Arabic text quality
    
    Returns:
        قائمة بالمشاكل المحتملة | List of potential issues
    """
    issues = []
    
    for key, translations in MESSAGES.items():
        if 'ar' not in translations:
            continue
        
        ar_text = translations['ar']
        
        # التحقق من الأحرف العربية
        # Check for Arabic characters
        if ar_text and not any('\u0600' <= c <= '\u06FF' for c in ar_text.replace(' ', '')):
            # إذا كان النص لا يحتوي على أي حرف عربي
            # If text contains no Arabic characters
            if not any(c.isdigit() or c in '{}()[],.!?-_/' for c in ar_text):
                issues.append((key, "لا يحتوي على أحرف عربية | Contains no Arabic characters"))
        
        # التحقق من التنسيق الصحيح
        # Check for proper formatting
        if ar_text and ar_text != ar_text.strip():
            issues.append((key, "يحتوي على مسافات زائدة | Contains extra spaces"))
    
    return issues


if __name__ == "__main__":
    # عند تشغيل الملف مباشرة، طباعة التقرير
    # When running file directly, print report
    print(generate_translation_report())
    
    # طباعة مشاكل جودة النص العربي
    # Print Arabic text quality issues
    ar_issues = validate_arabic_text_quality()
    if ar_issues:
        print("\n⚠️  مشاكل محتملة في النصوص العربية | Potential Arabic Text Issues:")
        for key, issue in ar_issues[:10]:
            print(f"   - {key}: {issue}")
