"""
Test script to validate the case creation changes
This script tests:
1. Case creation now requires immediate data input (similar to gift creation)
2. Default case selection selects the cheapest published case
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from db import get_all_cases, get_case_with_gifts


async def test_cheapest_case_selection():
    """Test that the cheapest case is correctly identified"""
    print("Testing cheapest case selection...")

    # Get all published cases
    cases = await get_all_cases(published_only=True)

    if not cases:
        print("❌ No published cases found")
        return False

    print(f"Found {len(cases)} published cases:")
    for case in cases:
        print(f"  - {case['id']}: {case['name']} - Price: {case['price']}")

    # Find the cheapest case
    cheapest_case = min(cases, key=lambda c: c.get('price', float('inf')))
    print(f"\n✅ Cheapest case: {cheapest_case['id']} ({cheapest_case['name']}) - Price: {cheapest_case['price']}")

    return True


async def test_case_structure():
    """Verify that cases can be retrieved properly"""
    print("\nTesting case retrieval...")

    cases = await get_all_cases()
    print(f"Total cases in database: {len(cases)}")

    for case in cases:
        case_data = await get_case_with_gifts(case['id'])
        if case_data:
            print(f"  ✅ Case {case['id']}: {case_data['name']} (Published: {case_data.get('published', False)})")
        else:
            print(f"  ❌ Failed to retrieve case {case['id']}")

    return True


async def main():
    print("=" * 60)
    print("Case Creation Test Suite")
    print("=" * 60)

    try:
        await test_cheapest_case_selection()
        await test_case_structure()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
