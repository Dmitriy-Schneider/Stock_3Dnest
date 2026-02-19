#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция всех 493 элементов в базу данных:
- 351 БЛОКОВ для раскроя
- 118 КРУГОВ для бота
- 23 ЛИСТОВ/ПОЛОС для бота
"""
import json
import os
import sys
from pathlib import Path

# Add BotCut to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "BotCut"))
from database import Database

ROOT = Path(__file__).parent
JSON_FILE = ROOT / "excel_correct_all.json"

def migrate():
    print("[MIGRATION] excel_correct_all.json -> botcut.db")
    print("="*60)

    # Load extracted items
    if not JSON_FILE.exists():
        print(f"[ERROR] File {JSON_FILE} not found!")
        print("[INFO] Run extract_excel_correct.py first")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"[INFO] Found {len(items)} items in JSON file")

    # Статистика по типам
    blocks = [i for i in items if i['shape'] == 'block']
    plates = [i for i in items if i['shape'] == 'plate']
    rods = [i for i in items if i['shape'] == 'rod']

    print(f"[INFO] Categorization:")
    print(f"  - Blocks (for cutting): {len(blocks)}")
    print(f"  - Plates (for bot): {len(plates)}")
    print(f"  - Rods (for bot): {len(rods)}")

    if not items:
        print("[WARN] No data to migrate")
        return

    # Initialize database
    db = Database()

    # Очистить существующие данные (опционально)
    print("[INFO] Database will be updated with new stock...")

    # Migrate each item
    migrated = 0
    errors = 0
    by_type = {"block": 0, "plate": 0, "rod": 0}

    for item in items:
        try:
            grade = item.get("grade", "unknown")
            shape = item.get("shape", "block")
            shape_type = item.get("shape_type", "unknown")
            x = float(item.get("x", 0))
            y = float(item.get("y", 0))
            z = float(item.get("z", 0))
            quantity = int(item.get("quantity", 1))
            idx = item.get("index", migrated)

            if x <= 0 or y <= 0 or z <= 0:
                print(f"[SKIP] Invalid dimensions: {x}x{y}x{z}")
                errors += 1
                continue

            # Generate block_id
            block_id = f"{grade}_{int(x)}x{int(y)}x{int(z)}_row{idx}"

            # Add to database
            db.add_stock(
                block_id=block_id,
                grade=grade,
                x=x,
                y=y,
                z=z,
                quantity=quantity,
                price=0.0,
                shape=shape  # "block", "plate", "rod"
            )

            migrated += 1
            by_type[shape] = by_type.get(shape, 0) + 1

            if migrated % 100 == 0:
                print(f"[PROGRESS] Migrated {migrated}/{len(items)} items...")

        except Exception as e:
            print(f"[ERROR] Failed to migrate item {item.get('index', '?')}: {e}")
            errors += 1

    print("="*60)
    print(f"[SUCCESS] MIGRATION COMPLETE:")
    print(f"  - Total migrated: {migrated}")
    print(f"  - Blocks (cutting): {by_type.get('block', 0)}")
    print(f"  - Plates (bot): {by_type.get('plate', 0)}")
    print(f"  - Rods (bot): {by_type.get('rod', 0)}")
    print(f"  - Errors: {errors}")

    # Verify
    warehouse = db.get_warehouse()
    print(f"[VERIFY] Database now contains {len(warehouse)} items total")

    # Show samples by type
    print(f"\n[SAMPLES] First 3 blocks:")
    block_samples = [w for w in warehouse if w.get('shape') == 'block'][:3]
    for i, item in enumerate(block_samples):
        print(f"  {i+1}. {item.get('block_id')} - {item.get('grade')} " +
              f"{item.get('x')}x{item.get('y')}x{item.get('z')}")

    print(f"\n[SAMPLES] First 3 rods:")
    rod_samples = [w for w in warehouse if w.get('shape') == 'rod'][:3]
    for i, item in enumerate(rod_samples):
        print(f"  {i+1}. {item.get('block_id')} - {item.get('grade')} " +
              f"⌀{item.get('x')} x {item.get('z')}mm")

    print(f"\n[SAMPLES] First 3 plates:")
    plate_samples = [w for w in warehouse if w.get('shape') == 'plate'][:3]
    for i, item in enumerate(plate_samples):
        print(f"  {i+1}. {item.get('block_id')} - {item.get('grade')} " +
              f"{item.get('x')}x{item.get('y')}x{item.get('z')}")

    print("\n" + "="*60)
    print("[INFO] Database is ready for use!")
    print("  - Web interface can access all items")
    print("  - Telegram bot can search for plates and rods")
    print("  - 3D cutting optimizer uses blocks")


if __name__ == "__main__":
    migrate()
