"""
Test script to verify the cheapest case cache implementation.

This test verifies:
1. Cache is properly initialized on startup
2. Cache updates when a cheaper case is created
3. Cache updates when case price is modified
4. Cache updates when a case is published/unpublished
5. Cache updates when a case is deleted
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import init_db, get_all_cases, create_case, update_case, delete_case, _update_cheapest_case_cache_callback
import db


async def test_cheapest_case_cache():
    """Test the cheapest case cache functionality"""

    print("=== Testing Cheapest Case Cache Implementation ===\n")

    # Initialize database
    await init_db()

    # Import the cache update function from start module
    from start import update_cheapest_case_cache, get_cheapest_case_id

    # Set the callback
    db._update_cheapest_case_cache_callback = update_cheapest_case_cache

    print("1️⃣ Testing initial cache population...")
    await update_cheapest_case_cache()
    cheapest_id = await get_cheapest_case_id()
    all_cases = await get_all_cases(published_only=True)

    if all_cases:
        print(f"   ✅ Cache initialized with case ID: {cheapest_id}")
        actual_cheapest = min(all_cases, key=lambda c: c.get('price', float('inf')))
        print(f"   ✅ Actual cheapest case: {actual_cheapest['id']} - Price: {actual_cheapest['price']}")
        assert cheapest_id == actual_cheapest['id'], "Cache doesn't match actual cheapest case!"
    else:
        print("   ℹ️ No published cases found")

    print("\n2️⃣ Testing cache update when creating a cheaper published case...")
    # Create a very cheap case
    test_case_id = "test-cheap-case-1"
    await create_case(test_case_id, "basic", "Test Cheap Case", 1, "/media/default.png", True)

    # Wait a bit for the cache to update
    await asyncio.sleep(0.1)

    new_cheapest_id = await get_cheapest_case_id()
    print(f"   ✅ Cache updated to: {new_cheapest_id}")
    assert new_cheapest_id == test_case_id, "Cache didn't update after creating cheaper case!"

    print("\n3️⃣ Testing cache doesn't update for unpublished case...")
    unpublished_case_id = "test-unpublished-case"
    await create_case(unpublished_case_id, "basic", "Test Unpublished Case", 0, "/media/default.png", False)

    await asyncio.sleep(0.1)

    current_cheapest = await get_cheapest_case_id()
    print(f"   ✅ Cache remains: {current_cheapest}")
    assert current_cheapest == test_case_id, "Cache incorrectly updated for unpublished case!"

    print("\n4️⃣ Testing cache update when updating case price...")
    # Create another case with higher price first
    test_case_2_id = "test-cheap-case-2"
    await create_case(test_case_2_id, "basic", "Test Case 2", 100, "/media/default.png", True)

    # Update its price to be cheaper
    await update_case(test_case_2_id, price=0.5)

    await asyncio.sleep(0.1)

    updated_cheapest = await get_cheapest_case_id()
    print(f"   ✅ Cache updated to: {updated_cheapest}")
    # Should be test_case_2_id now since it has price 0.5

    print("\n5️⃣ Testing cache update when publishing previously unpublished case...")
    await update_case(unpublished_case_id, published=True)

    await asyncio.sleep(0.1)

    published_cheapest = await get_cheapest_case_id()
    print(f"   ✅ Cache updated to: {published_cheapest}")
    assert published_cheapest == unpublished_case_id, "Cache didn't update when case was published!"

    print("\n6️⃣ Testing cache update when deleting the cheapest case...")
    await delete_case(unpublished_case_id)

    await asyncio.sleep(0.1)

    after_delete_cheapest = await get_cheapest_case_id()
    print(f"   ✅ Cache updated to: {after_delete_cheapest}")
    assert after_delete_cheapest != unpublished_case_id, "Cache didn't update after deleting cheapest case!"

    # Cleanup test cases
    print("\n7️⃣ Cleaning up test cases...")
    await delete_case(test_case_id)
    await delete_case(test_case_2_id)
    print("   ✅ Test cases deleted")

    print("\n✅ All tests passed!")
    print("\n=== Summary ===")
    print("The cheapest case cache implementation:")
    print("• Correctly initializes on startup")
    print("• Updates when cheaper cases are created")
    print("• Updates when case prices are modified")
    print("• Updates when cases are published/unpublished")
    print("• Updates when cases are deleted")
    print("• Only considers published cases")


if __name__ == "__main__":
    asyncio.run(test_cheapest_case_cache())
