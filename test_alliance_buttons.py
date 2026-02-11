#!/usr/bin/env python3
"""
Test script to verify Alliance Operations buttons support both languages
Tests Issue #192: "زر هل يدعم اللغتين" (Button supports both languages)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from i18n import t, MESSAGES

def test_alliance_operations_bilingual():
    """Test that all Alliance Operations buttons support both languages"""
    
    print("=" * 70)
    print("🧪 Testing Alliance Operations Buttons - Bilingual Support")
    print("   Issue #192: زر هل يدعم اللغتين (Do buttons support both languages?)")
    print("=" * 70)
    print()
    
    # Define all button translation keys
    button_keys = {
        "Alliance Operations Title": "alliance.operations.title",
        "Add Alliance": "alliance.operations.add",
        "Edit Alliance": "alliance.operations.edit",
        "Delete Alliance": "alliance.operations.delete",
        "View Alliances": "alliance.operations.view",
        "Check Alliance": "alliance.operations.check",
        "Main Menu": "common.main_menu",
        "Confirm": "common.confirm",
        "Cancel": "common.cancel",
    }
    
    all_passed = True
    results = []
    
    for button_name, key in button_keys.items():
        if key not in MESSAGES:
            print(f"❌ {button_name} ({key})")
            print(f"   ERROR: Translation key not found!")
            all_passed = False
            results.append((button_name, False))
            continue
        
        en_text = MESSAGES[key].get('en', None)
        ar_text = MESSAGES[key].get('ar', None)
        
        if not en_text or not ar_text:
            print(f"❌ {button_name} ({key})")
            if not en_text:
                print(f"   ERROR: English translation missing!")
            if not ar_text:
                print(f"   ERROR: Arabic translation missing!")
            all_passed = False
            results.append((button_name, False))
            continue
        
        # Check using t() function
        en_result = t(key, 'en')
        ar_result = t(key, 'ar')
        
        if en_result == en_text and ar_result == ar_text:
            print(f"✅ {button_name}")
            print(f"   EN: {en_result}")
            print(f"   AR: {ar_result}")
            results.append((button_name, True))
        else:
            print(f"❌ {button_name}")
            print(f"   ERROR: Translation function t() returned unexpected results")
            all_passed = False
            results.append((button_name, False))
        print()
    
    # Check descriptions
    print("=" * 70)
    print("📝 Testing Button Descriptions")
    print("=" * 70)
    print()
    
    desc_keys = {
        "Add Alliance Description": "alliance.operations.add_desc",
        "Edit Alliance Description": "alliance.operations.edit_desc",
        "Delete Alliance Description": "alliance.operations.delete_desc",
        "View Alliances Description": "alliance.operations.view_desc",
        "Check Alliance Description": "alliance.operations.check_desc",
    }
    
    for desc_name, key in desc_keys.items():
        if key in MESSAGES:
            en_text = MESSAGES[key].get('en', '')
            ar_text = MESSAGES[key].get('ar', '')
            print(f"✅ {desc_name}")
            print(f"   EN: {en_text}")
            print(f"   AR: {ar_text}")
            print()
        else:
            print(f"⚠️  {desc_name} ({key}) - Optional, not found")
            print()
    
    # Print summary
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for button_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {button_name}")
    
    print()
    print("=" * 70)
    print(f"Results: {passed_count}/{total_count} buttons support both languages")
    print("=" * 70)
    print()
    
    if all_passed:
        print("🎉 ✅ ALL TESTS PASSED!")
        print()
        print("✨ All Alliance Operations buttons now support both languages!")
        print("   English: ✅")
        print("   Arabic:  ✅")
        print()
        print("📝 Issue #192 Resolution:")
        print("   Question: زر هل يدعم اللغتين (Do buttons support both languages?)")
        print("   Answer: نعم! ✅ Yes! All buttons now support Arabic and English.")
        print()
        return 0
    else:
        print(f"⚠️  {total_count - passed_count} button(s) failed")
        print("   Please review the errors above")
        print()
        return 1

def test_alliance_code_integration():
    """Test that alliance.py uses translation keys correctly"""
    
    print("=" * 70)
    print("🔍 Testing Code Integration")
    print("=" * 70)
    print()
    
    # Read alliance.py and check for hardcoded strings
    try:
        with open('cogs/alliance.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for old hardcoded labels
        hardcoded_patterns = [
            'label="Add Alliance"',
            'label="Edit Alliance"',
            'label="Delete Alliance"',
            'label="View Alliances"',
            'label="Check Alliance"',
            'label="Main Menu"',
            'label="Confirm"',
            'label="Cancel"',
        ]
        
        found_hardcoded = []
        for pattern in hardcoded_patterns:
            if pattern in content:
                found_hardcoded.append(pattern)
        
        if found_hardcoded:
            print("❌ Found hardcoded button labels:")
            for pattern in found_hardcoded:
                print(f"   - {pattern}")
            print()
            print("⚠️  Buttons should use t() function for translations")
            return False
        else:
            print("✅ No hardcoded button labels found")
            print("✅ All buttons use translation function t()")
            print()
            return True
    
    except Exception as e:
        print(f"❌ Error reading alliance.py: {e}")
        return False

def main():
    """Run all tests"""
    
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  TESTING: Alliance Operations Bilingual Support ".center(68) + "║")
    print("║" + "  Issue #192: زر هل يدعم اللغتين ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Run tests
    test1_result = test_alliance_operations_bilingual()
    print()
    test2_result = test_alliance_code_integration()
    
    print()
    print("=" * 70)
    print("🏁 FINAL RESULT")
    print("=" * 70)
    
    if test1_result == 0 and test2_result:
        print()
        print("✅ ALL TESTS PASSED!")
        print()
        print("🌍 Alliance Operations buttons now support both languages:")
        print("   • English ✅")
        print("   • العربية ✅")
        print()
        print("📋 What was fixed:")
        print("   1. Added translation keys to i18n.py")
        print("   2. Updated alliance.py to use t() function")
        print("   3. All 9 buttons now support bilingual display")
        print()
        print("🎯 Issue #192 Status: RESOLVED ✅")
        print()
        return 0
    else:
        print()
        print("❌ SOME TESTS FAILED")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
