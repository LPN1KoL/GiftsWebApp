#!/usr/bin/env python3
"""
Test script to verify the case ID generation fix.

This test simulates the scenario described in issue #29:
1. Create multiple cases
2. Delete a case in the middle
3. Create a new case and verify no duplicate key error occurs
"""

async def test_case_id_generation():
    """Test that case ID generation correctly handles deleted cases"""

    # Simulate existing cases after some deletions
    test_cases = [
        [
            {'id': 'case-1', 'name': 'Case 1'},
            {'id': 'case-2', 'name': 'Case 2'},
            {'id': 'case-3', 'name': 'Case 3'},
        ],
        [
            {'id': 'case-1', 'name': 'Case 1'},
            {'id': 'case-3', 'name': 'Case 3'},  # case-2 deleted
        ],
        [
            {'id': 'case-1', 'name': 'Case 1'},
            {'id': 'case-2', 'name': 'Case 2'},
            {'id': 'case-4', 'name': 'Case 4'},  # case-3 deleted, case-4 created
        ],
        [
            {'id': 'case-5', 'name': 'Case 5'},  # All previous deleted, only case-5 remains
        ],
        [],  # All cases deleted
    ]

    print("Testing case ID generation logic...")
    print("=" * 60)

    for idx, cases in enumerate(test_cases):
        print(f"\nTest scenario {idx + 1}:")
        print(f"Existing cases: {[c['id'] for c in cases]}")

        # Replicate the fix logic
        max_case_num = 0
        for case in cases:
            case_id = case.get('id', '')
            if case_id.startswith('case-'):
                try:
                    case_num = int(case_id.split('-')[1])
                    max_case_num = max(max_case_num, case_num)
                except (ValueError, IndexError):
                    pass

        new_case_num = max_case_num + 1
        new_case_id = f"case-{new_case_num}"

        # Check for duplicates
        existing_ids = [c['id'] for c in cases]
        is_duplicate = new_case_id in existing_ids

        status = "❌ DUPLICATE!" if is_duplicate else "✅ UNIQUE"
        print(f"Generated ID: {new_case_id} {status}")

        # Also show what the old logic would have generated
        old_case_id = f"case-{len(cases) + 1}"
        old_is_duplicate = old_case_id in existing_ids
        old_status = "❌ DUPLICATE!" if old_is_duplicate else "✅ UNIQUE"
        print(f"Old logic would generate: {old_case_id} {old_status}")

    print("\n" + "=" * 60)
    print("✅ All test scenarios completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_case_id_generation())
