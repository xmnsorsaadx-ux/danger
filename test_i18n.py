#!/usr/bin/env python3
"""
سكريبت اختبار شامل لنظام الترجمة
Comprehensive Translation System Test Script

يقوم بـ:
1. فحص الترجمات الناقصة
2. فحص اتساق القوالب
3. فحص جودة النصوص العربية
4. اختبار الدوال الأساسية
5. توليد تقرير HTML
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple

# إضافة المسار الأساسي
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from i18n import MESSAGES, SUPPORTED_LANGUAGES, t, get_guild_language
from i18n_utils import (
    find_missing_translations,
    check_format_consistency,
    validate_arabic_text_quality,
    generate_translation_report
)


class Colors:
    """ألوان الطباعة | Print colors"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """طباعة عنوان | Print header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    """طباعة نجاح | Print success"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_warning(text: str):
    """طباعة تحذير | Print warning"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_error(text: str):
    """طباعة خطأ | Print error"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    """طباعة معلومة | Print info"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def test_basic_functions():
    """اختبار الدوال الأساسية | Test basic functions"""
    print_header("اختبار الدوال الأساسية | Testing Basic Functions")
    
    errors = []
    
    # Test 1: t() function
    try:
        result_en = t("menu.settings.title", "en")
        result_ar = t("menu.settings.title", "ar")
        
        if result_en and result_ar:
            print_success("دالة t() تعمل بشكل صحيح | t() function works correctly")
        else:
            errors.append("دالة t() ترجع قيماً فارغة | t() returns empty values")
            print_error("دالة t() ترجع قيماً فارغة")
    except Exception as e:
        errors.append(f"خطأ في دالة t(): {e}")
        print_error(f"Error in t(): {e}")
    
    # Test 2: t() with parameters
    try:
        result = t("alliance.member.add.success_body", "ar", count=10)
        if "{count}" not in result and "10" in result:
            print_success("دالة t() مع المعاملات تعمل | t() with parameters works")
        else:
            errors.append("دالة t() لا تستبدل المعاملات بشكل صحيح")
            print_error("Parameter substitution failed")
    except Exception as e:
        errors.append(f"خطأ في المعاملات: {e}")
        print_error(f"Parameter error: {e}")
    
    # Test 3: Non-existent key
    try:
        result = t("non.existent.key", "ar")
        if result == "non.existent.key":
            print_success("دالة t() تتعامل مع المفاتيح المفقودة بشكل صحيح")
        else:
            print_warning(f"Unexpected result for missing key: {result}")
    except Exception as e:
        errors.append(f"خطأ في التعامل مع مفتاح مفقود: {e}")
        print_error(f"Missing key handling error: {e}")
    
    # Test 4: SUPPORTED_LANGUAGES
    try:
        if "en" in SUPPORTED_LANGUAGES and "ar" in SUPPORTED_LANGUAGES:
            print_success(f"اللغات المدعومة: {SUPPORTED_LANGUAGES}")
        else:
            errors.append("SUPPORTED_LANGUAGES لا يحتوي على اللغات المتوقعة")
            print_error("SUPPORTED_LANGUAGES missing expected languages")
    except Exception as e:
        errors.append(f"خطأ في SUPPORTED_LANGUAGES: {e}")
        print_error(f"SUPPORTED_LANGUAGES error: {e}")
    
    return errors


def test_translation_coverage():
    """اختبار تغطية الترجمات | Test translation coverage"""
    print_header("تغطية الترجمات | Translation Coverage")
    
    errors = []
    total_keys = len(MESSAGES)
    
    print_info(f"إجمالي المفاتيح | Total keys: {total_keys}")
    
    for lang in SUPPORTED_LANGUAGES:
        lang_name = "العربية" if lang == "ar" else "English"
        complete = sum(1 for key in MESSAGES if lang in MESSAGES[key] and MESSAGES[key][lang])
        percentage = (complete / total_keys * 100) if total_keys > 0 else 0
        
        if percentage == 100:
            print_success(f"{lang_name} ({lang}): {complete}/{total_keys} ({percentage:.1f}%)")
        elif percentage >= 90:
            print_warning(f"{lang_name} ({lang}): {complete}/{total_keys} ({percentage:.1f}%)")
        else:
            print_error(f"{lang_name} ({lang}): {complete}/{total_keys} ({percentage:.1f}%)")
            errors.append(f"{lang} has low coverage: {percentage:.1f}%")
    
    return errors


def test_missing_translations():
    """اختبار الترجمات الناقصة | Test missing translations"""
    print_header("الترجمات الناقصة | Missing Translations")
    
    errors = []
    missing = find_missing_translations()
    
    if not missing:
        print_success("لا توجد ترجمات ناقصة | No missing translations!")
    else:
        print_warning(f"عدد المفاتيح الناقصة | Missing keys: {len(missing)}")
        
        # عرض أول 10
        for i, (key, langs) in enumerate(list(missing.items())[:10]):
            print(f"   {i+1}. {key}: {', '.join(langs)}")
            errors.append(f"Missing {key} in {', '.join(langs)}")
        
        if len(missing) > 10:
            print(f"   ... و {len(missing) - 10} أخرى | and {len(missing) - 10} more")
    
    return errors


def test_format_consistency():
    """اختبار اتساق القوالب | Test format consistency"""
    print_header("اتساق القوالب | Format Consistency")
    
    errors = []
    inconsistencies = check_format_consistency()
    
    if not inconsistencies:
        print_success("جميع القوالب متسقة | All format templates consistent!")
    else:
        print_warning(f"عدد المشاكل | Issues found: {len(inconsistencies)}")
        
        # عرض أول 5
        for i, (key, lang, issue) in enumerate(inconsistencies[:5]):
            print(f"   {i+1}. {key} ({lang}): {issue}")
            errors.append(f"Format issue in {key} ({lang}): {issue}")
        
        if len(inconsistencies) > 5:
            print(f"   ... و {len(inconsistencies) - 5} أخرى | and {len(inconsistencies) - 5} more")
    
    return errors


def test_arabic_quality():
    """اختبار جودة النصوص العربية | Test Arabic text quality"""
    print_header("جودة النصوص العربية | Arabic Text Quality")
    
    errors = []
    issues = validate_arabic_text_quality()
    
    if not issues:
        print_success("جميع النصوص العربية ذات جودة عالية | All Arabic texts are high quality!")
    else:
        print_warning(f"عدد المشاكل المحتملة | Potential issues: {len(issues)}")
        
        # عرض أول 10
        for i, (key, issue) in enumerate(issues[:10]):
            print(f"   {i+1}. {key}: {issue}")
            # هذه تحذيرات فقط، ليست أخطاء
        
        if len(issues) > 10:
            print(f"   ... و {len(issues) - 10} أخرى | and {len(issues) - 10} more")
    
    return errors


def test_sample_translations():
    """اختبار عينة من الترجمات | Test sample translations"""
    print_header("عينة من الترجمات | Translation Samples")
    
    sample_keys = [
        "menu.settings.title",
        "alliance.member.add.success_body",
        "gift.redeem.progress_title",
        "minister.menu.main_title",
        "language.current"
    ]
    
    errors = []
    
    for key in sample_keys:
        try:
            en = t(key, "en", count=5, alliance="Test", code="ABC123")
            ar = t(key, "ar", count=5, alliance="Test", code="ABC123")
            
            print(f"\n📝 {key}:")
            print(f"   EN: {en}")
            print(f"   AR: {ar}")
            
            if not en or not ar:
                errors.append(f"Empty translation for {key}")
                print_error(f"Empty translation detected")
        
        except Exception as e:
            errors.append(f"Error translating {key}: {e}")
            print_error(f"Translation error: {e}")
    
    return errors


def generate_html_report(all_errors: List[str]):
    """توليد تقرير HTML | Generate HTML report"""
    print_header("توليد تقرير HTML | Generating HTML Report")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير اختبار الترجمة | Translation Test Report</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            padding: 30px;
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #764ba2;
            border-left: 5px solid #764ba2;
            padding-left: 15px;
            margin-top: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 36px;
            font-weight: bold;
        }}
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
        }}
        .status.success {{
            background: #10b981;
            color: white;
        }}
        .status.warning {{
            background: #f59e0b;
            color: white;
        }}
        .status.error {{
            background: #ef4444;
            color: white;
        }}
        .error-list {{
            background: #fee;
            border-left: 4px solid #ef4444;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .success-box {{
            background: #efe;
            border-left: 4px solid #10b981;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 تقرير اختبار نظام الترجمة<br>Translation System Test Report</h1>
        
        <div class="stats">
            <div class="stat-card">
                <h3>إجمالي المفاتيح<br>Total Keys</h3>
                <div class="value">{len(MESSAGES)}</div>
            </div>
            <div class="stat-card">
                <h3>اللغات المدعومة<br>Supported Languages</h3>
                <div class="value">{len(SUPPORTED_LANGUAGES)}</div>
            </div>
            <div class="stat-card">
                <h3>الأخطاء المكتشفة<br>Errors Found</h3>
                <div class="value">{len(all_errors)}</div>
            </div>
        </div>
        
        <h2>📊 حالة الاختبارات | Test Status</h2>
"""
    
    if not all_errors:
        html += """
        <div class="success-box">
            <strong>✅ جميع الاختبارات نجحت!</strong><br>
            <strong>✅ All tests passed!</strong>
        </div>
"""
    else:
        html += f"""
        <div class="error-list">
            <strong>⚠️ تم اكتشاف {len(all_errors)} مشكلة</strong><br>
            <strong>⚠️ {len(all_errors)} issues detected</strong>
        </div>
"""
    
    # إضافة تفاصيل الترجمات
    html += """
        <h2>📈 تفاصيل التغطية | Coverage Details</h2>
        <table>
            <tr>
                <th>اللغة | Language</th>
                <th>المكتملة | Complete</th>
                <th>الإجمالي | Total</th>
                <th>النسبة | Percentage</th>
            </tr>
"""
    
    for lang in SUPPORTED_LANGUAGES:
        lang_name = "العربية" if lang == "ar" else "English"
        complete = sum(1 for key in MESSAGES if lang in MESSAGES[key] and MESSAGES[key][lang])
        total = len(MESSAGES)
        percentage = (complete / total * 100) if total > 0 else 0
        
        status_class = "success" if percentage == 100 else ("warning" if percentage >= 90 else "error")
        
        html += f"""
            <tr>
                <td>{lang_name} ({lang})</td>
                <td>{complete}</td>
                <td>{total}</td>
                <td><span class="status {status_class}">{percentage:.1f}%</span></td>
            </tr>
"""
    
    html += """
        </table>
"""
    
    # إضافة قائمة الأخطاء إن وجدت
    if all_errors:
        html += """
        <h2>⚠️ قائمة المشاكل | Issues List</h2>
        <div class="error-list">
            <ul>
"""
        for error in all_errors[:50]:  # أول 50 خطأ
            html += f"                <li>{error}</li>\n"
        
        if len(all_errors) > 50:
            html += f"                <li>... و {len(all_errors) - 50} مشكلة أخرى</li>\n"
        
        html += """
            </ul>
        </div>
"""
    
    html += f"""
        <div class="timestamp">
            📅 تم التوليد في | Generated at: {timestamp}<br>
            🤖 DANGER Bot Translation System v3.0
        </div>
    </div>
</body>
</html>
"""
    
    # حفظ الملف
    report_path = "translation_test_report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print_success(f"تم حفظ التقرير في | Report saved to: {report_path}")
    print_info(f"افتح الملف في المتصفح | Open file in browser to view")


def main():
    """الدالة الرئيسية | Main function"""
    print("\n")
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║        🌍 نظام اختبار الترجمة الشامل 🌍                ║")
    print("║     Comprehensive Translation Testing System            ║")
    print("║                                                           ║")
    print("║                 DANGER Bot v3.0                          ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    all_errors = []
    
    # تشغيل جميع الاختبارات
    all_errors.extend(test_basic_functions())
    all_errors.extend(test_translation_coverage())
    all_errors.extend(test_missing_translations())
    all_errors.extend(test_format_consistency())
    all_errors.extend(test_arabic_quality())
    all_errors.extend(test_sample_translations())
    
    # عرض التقرير النصي
    print("\n")
    print(generate_translation_report())
    
    # توليد تقرير HTML
    generate_html_report(all_errors)
    
    # النتيجة النهائية
    print_header("النتيجة النهائية | Final Result")
    
    if not all_errors:
        print_success("🎉 جميع الاختبارات نجحت! النظام جاهز للإنتاج")
        print_success("🎉 All tests passed! System is production ready")
        return 0
    else:
        print_warning(f"⚠️  تم اكتشاف {len(all_errors)} مشكلة")
        print_warning(f"⚠️  {len(all_errors)} issues detected")
        print_info("راجع التقرير للمزيد من التفاصيل | Check report for details")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
