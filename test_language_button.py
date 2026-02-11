#!/usr/bin/env python3
"""
Test script to verify the complete Arabic-English language button system
Validates all components from database to UI integration
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from i18n import get_guild_language, set_guild_language, t, MESSAGES, SUPPORTED_LANGUAGES

def test_database_setup():
    """Test that the database is properly set up for language settings"""
    print("=" * 70)
    print("🗄️  Testing Database Setup")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('db/settings.sqlite')
        cursor = conn.cursor()
        
        # Check if language_settings table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='language_settings'
        """)
        result = cursor.fetchone()
        
        if result:
            print("✅ language_settings table exists")
        else:
            print("❌ language_settings table NOT found")
            return False
            
        # Check table structure
        cursor.execute("PRAGMA table_info(language_settings)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = ['guild_id', 'language']
        for col in expected_columns:
            if col in column_names:
                print(f"✅ Column '{col}' exists")
            else:
                print(f"❌ Column '{col}' NOT found")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_translation_keys():
    """Test that all required translation keys exist"""
    print("\n" + "=" * 70)
    print("🔑 Testing Translation Keys")
    print("=" * 70)
    
    required_keys = [
        "language.settings.title",
        "language.settings.description",
        "language.current",
        "language.english",
        "language.arabic",
        "language.updated",
        "language.guild_required",
        "language.back",
        "menu.settings.title",
        "menu.settings.language_desc",
    ]
    
    all_passed = True
    for key in required_keys:
        if key in MESSAGES:
            en_text = MESSAGES[key].get('en', 'MISSING')
            ar_text = MESSAGES[key].get('ar', 'MISSING')
            print(f"✅ {key}")
            print(f"   EN: {en_text}")
            print(f"   AR: {ar_text}")
        else:
            print(f"❌ {key} - NOT FOUND")
            all_passed = False
    
    return all_passed

def test_language_functions():
    """Test get/set language functions"""
    print("\n" + "=" * 70)
    print("🔧 Testing Language Functions")
    print("=" * 70)
    
    test_guild_id = 999999999999
    
    try:
        # Test setting language to Arabic
        print(f"Setting language to 'ar' for guild {test_guild_id}...")
        set_guild_language(test_guild_id, 'ar')
        lang = get_guild_language(test_guild_id)
        if lang == 'ar':
            print(f"✅ Language set to Arabic: {lang}")
        else:
            print(f"❌ Expected 'ar', got '{lang}'")
            return False
        
        # Test setting language to English
        print(f"Setting language to 'en' for guild {test_guild_id}...")
        set_guild_language(test_guild_id, 'en')
        lang = get_guild_language(test_guild_id)
        if lang == 'en':
            print(f"✅ Language set to English: {lang}")
        else:
            print(f"❌ Expected 'en', got '{lang}'")
            return False
        
        # Clean up test data
        conn = sqlite3.connect('db/settings.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM language_settings WHERE guild_id = ?", (test_guild_id,))
        conn.commit()
        conn.close()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in language functions: {e}")
        return False

def test_translation_function():
    """Test the t() translation function"""
    print("\n" + "=" * 70)
    print("🌐 Testing Translation Function")
    print("=" * 70)
    
    try:
        # Test simple translation
        en_yes = t('common.yes', 'en')
        ar_yes = t('common.yes', 'ar')
        print(f"✅ t('common.yes', 'en') = '{en_yes}'")
        print(f"✅ t('common.yes', 'ar') = '{ar_yes}'")
        
        # Test translation with variables
        en_current = t('time.seconds_ago', 'en', count=30)
        ar_current = t('time.seconds_ago', 'ar', count=30)
        print(f"✅ t('time.seconds_ago', 'en', count=30) = '{en_current}'")
        print(f"✅ t('time.seconds_ago', 'ar', count=30) = '{ar_current}'")
        
        # Test language button labels
        en_lang_title = t('language.settings.title', 'en')
        ar_lang_title = t('language.settings.title', 'ar')
        print(f"✅ Language Settings Title (EN): '{en_lang_title}'")
        print(f"✅ Language Settings Title (AR): '{ar_lang_title}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in translation function: {e}")
        return False

def test_supported_languages():
    """Test that both languages are supported"""
    print("\n" + "=" * 70)
    print("🌍 Testing Supported Languages")
    print("=" * 70)
    
    print(f"Supported languages: {SUPPORTED_LANGUAGES}")
    
    if 'en' in SUPPORTED_LANGUAGES:
        print("✅ English (en) is supported")
    else:
        print("❌ English (en) NOT supported")
        return False
    
    if 'ar' in SUPPORTED_LANGUAGES:
        print("✅ Arabic (ar) is supported")
    else:
        print("❌ Arabic (ar) NOT supported")
        return False
    
    return True

def test_ui_components():
    """Test that UI components are properly set up"""
    print("\n" + "=" * 70)
    print("🎨 Testing UI Components")
    print("=" * 70)
    
    try:
        # Check if alliance.py has the language button
        with open('cogs/alliance.py', 'r', encoding='utf-8') as f:
            alliance_content = f.read()
        
        if 'language_settings' in alliance_content:
            print("✅ Language settings button found in alliance.py")
        else:
            print("❌ Language settings button NOT found in alliance.py")
            return False
        
        if 't("language.settings.title", lang)' in alliance_content or "t('language.settings.title', lang)" in alliance_content:
            print("✅ Translation function used for button label")
        else:
            print("❌ Translation function NOT used for button label")
            return False
        
        # Check if bot_operations.py has the handlers
        with open('cogs/bot_operations.py', 'r', encoding='utf-8') as f:
            bot_ops_content = f.read()
        
        if 'show_language_settings' in bot_ops_content:
            print("✅ show_language_settings handler found")
        else:
            print("❌ show_language_settings handler NOT found")
            return False
        
        if 'handle_language_action' in bot_ops_content:
            print("✅ handle_language_action handler found")
        else:
            print("❌ handle_language_action handler NOT found")
            return False
        
        if 'language_set_en' in bot_ops_content and 'language_set_ar' in bot_ops_content:
            print("✅ Language toggle buttons (EN/AR) found")
        else:
            print("❌ Language toggle buttons NOT properly configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking UI components: {e}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🧪 COMPREHENSIVE LANGUAGE BUTTON SYSTEM TEST  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Translation Keys", test_translation_keys),
        ("Language Functions", test_language_functions),
        ("Translation Function", test_translation_function),
        ("Supported Languages", test_supported_languages),
        ("UI Components", test_ui_components),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ✅ ALL TESTS PASSED!")
        print("\n✨ The Arabic-English language button system is fully operational!")
        print("\n📖 How to use:")
        print("   1. In Discord, type: /settings")
        print("   2. Click the 🌍 Language Settings button")
        print("   3. Choose العربية (Arabic) or English")
        print("\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("   Please review the errors above")
        print("\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
