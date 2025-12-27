#!/usr/bin/env python3
"""
Test script to verify case creation and database persistence.
This script tests if cases are properly saved to the database and appear on the cases page.

Issue #35: Cases are created but not saved to database
Fix: Changed default published value from False to True so cases appear immediately on /cases page
"""
import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import create_case, get_case, get_all_cases, delete_case, init_db


async def test_case_creation():
    """Test case creation and retrieval"""
    print("=== Testing Case Creation (Issue #35) ===\n")

    # Initialize database
    print("1. Initializing database...")
    try:
        await init_db()
        print("   ✓ Database initialized\n")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}\n")
        return False

    # Create a test case with published=True (as per the fix)
    test_case_id = "test-case-999"
    test_category = "basic"
    test_name = "Test Case"
    test_price = 100
    test_logo = "/media/test.png"
    test_published = True  # Changed to True to match the fix

    print("2. Creating test case...")
    print(f"   ID: {test_case_id}")
    print(f"   Name: {test_name}")
    print(f"   Price: {test_price}")
    print(f"   Category: {test_category}")
    print(f"   Published: {test_published}")

    try:
        await create_case(test_case_id, test_category, test_name, test_price, test_logo, test_published)
        print("   ✓ create_case() completed without errors\n")
    except Exception as e:
        print(f"   ✗ create_case() failed: {e}\n")
        return False

    # Retrieve the case immediately
    print("3. Retrieving case from database...")
    try:
        case = await get_case(test_case_id)
        if case:
            print("   ✓ Case found in database!")
            print(f"   Retrieved data: {case}\n")
        else:
            print("   ✗ Case NOT found in database!")
            print("   This indicates the case was not saved.\n")
            return False
    except Exception as e:
        print(f"   ✗ get_case() failed: {e}\n")
        return False

    # Verify data integrity
    print("4. Verifying data integrity...")
    issues = []
    if case.get('id') != test_case_id:
        issues.append(f"ID mismatch: expected {test_case_id}, got {case.get('id')}")
    if case.get('category') != test_category:
        issues.append(f"Category mismatch: expected {test_category}, got {case.get('category')}")
    if case.get('name') != test_name:
        issues.append(f"Name mismatch: expected {test_name}, got {case.get('name')}")
    if case.get('price') != test_price:
        issues.append(f"Price mismatch: expected {test_price}, got {case.get('price')}")
    if case.get('published') != test_published:
        issues.append(f"Published mismatch: expected {test_published}, got {case.get('published')}")

    if issues:
        print("   ✗ Data integrity issues found:")
        for issue in issues:
            print(f"     - {issue}")
        print()
        return False
    else:
        print("   ✓ All data matches expected values\n")

    # List all cases
    print("5. Listing all cases...")
    try:
        all_cases = await get_all_cases()
        print(f"   Total cases in database: {len(all_cases)}")
        for c in all_cases:
            status = "✅ published" if c.get('published') else "❌ unpublished"
            print(f"     - {c['id']}: {c['name']} ({c['price']}₽) [{status}]")
        print()
    except Exception as e:
        print(f"   ✗ get_all_cases() failed: {e}\n")

    # Verify case appears in published cases list
    print("6. Verifying case appears in published cases list...")
    try:
        published_cases = await get_all_cases(published_only=True)
        found_in_published = any(c['id'] == test_case_id for c in published_cases)
        if found_in_published:
            print("   ✓ Test case found in published cases list (will appear on /cases page)\n")
        else:
            print("   ✗ Test case NOT found in published cases list (won't appear on /cases page)\n")
            return False
    except Exception as e:
        print(f"   ✗ get_all_cases(published_only=True) failed: {e}\n")
        return False

    # Clean up - delete test case
    print("7. Cleaning up test case...")
    try:
        await delete_case(test_case_id)
        print("   ✓ Test case deleted\n")
    except Exception as e:
        print(f"   ✗ delete_case() failed: {e}\n")

    # Verify deletion
    print("8. Verifying deletion...")
    try:
        case = await get_case(test_case_id)
        if case:
            print("   ✗ Case still exists after deletion!\n")
            return False
        else:
            print("   ✓ Case successfully deleted\n")
    except Exception as e:
        print(f"   ✗ Verification failed: {e}\n")
        return False

    print("=== All tests passed! ===\n")
    return True


async def main():
    try:
        success = await test_case_creation()
        if success:
            print("Result: SUCCESS - Cases are being saved correctly")
            sys.exit(0)
        else:
            print("Result: FAILURE - Cases are NOT being saved correctly")
            sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
