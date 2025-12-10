#!/usr/bin/env python3
"""
Migration script to import cases.json data into the database.
Run this script once to migrate existing data from cases.json to PostgreSQL.
"""
import json
import asyncio
from db import init_db, create_case, create_gift, get_case_with_gifts

async def migrate_cases():
    """Migrate cases from JSON file to database"""
    print("🔄 Starting migration from cases.json to database...")

    # Initialize database tables
    print("📊 Initializing database tables...")
    await init_db()
    print("✅ Database tables initialized")

    # Load cases from JSON file
    try:
        with open("data/cases.json", "r", encoding="utf-8") as f:
            cases = json.load(f)
        print(f"📂 Loaded {len(cases)} cases from data/cases.json")
    except FileNotFoundError:
        print("❌ Error: data/cases.json not found")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return

    # Migrate each case
    migrated_cases = 0
    migrated_gifts = 0

    for case in cases:
        case_id = case.get('id')

        # Check if case already exists
        existing_case = await get_case_with_gifts(case_id)
        if existing_case:
            print(f"⚠️  Case {case_id} already exists, skipping...")
            continue

        # Create case
        try:
            await create_case(
                case_id,
                case.get('category', 'basic'),
                case.get('name', 'Unnamed Case'),
                case.get('price', 0),
                case.get('logo'),
                case.get('published', False)
            )
            print(f"✅ Migrated case: {case_id} - {case.get('name')}")
            migrated_cases += 1

            # Migrate gifts for this case
            for gift in case.get('gifts', []):
                try:
                    await create_gift(
                        gift.get('id'),
                        case_id,
                        gift.get('name', 'Unnamed Gift'),
                        gift.get('link'),
                        gift.get('img'),
                        gift.get('chance', 0.0),
                        gift.get('fake_chance', gift.get('chance', 0.0)),
                        gift.get('price', 0)
                    )
                    migrated_gifts += 1
                except Exception as e:
                    print(f"❌ Error migrating gift {gift.get('id')}: {e}")

        except Exception as e:
            print(f"❌ Error migrating case {case_id}: {e}")

    print("\n" + "="*50)
    print(f"✅ Migration complete!")
    print(f"📦 Migrated {migrated_cases} cases")
    print(f"🎁 Migrated {migrated_gifts} gifts")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(migrate_cases())
