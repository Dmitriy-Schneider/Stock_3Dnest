#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final migration: excel_aggressive.json → botcut.db
Migrates all 125 extracted blocks to the unified database
"""
import json
import os
import sys
from pathlib import Path

# Add BotCut to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "BotCut"))
from database import Database

ROOT = Path(__file__).parent
JSON_FILE = ROOT / "excel_aggressive.json"

def migrate():
    print("[MIGRATION] excel_aggressive.json -> botcut.db")
    print("="*60)

    # Load extracted blocks
    if not JSON_FILE.exists():
        print(f"[ERROR] File {JSON_FILE} not found!")
        print("[INFO] Run extract_excel_aggressive.py first")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    print(f"[INFO] Found {len(blocks)} blocks in JSON file")

    if not blocks:
        print("[WARN] No data to migrate")
        return

    # Initialize database
    db = Database()

    # Clear existing stocks first (optional - comment out to keep existing data)
    print("[INFO] Clearing existing stock data...")
    # db.clear_all_stocks()  # Uncomment if Database has this method

    # Migrate each block
    migrated = 0
    errors = 0

    for block in blocks:
        try:
            # Generate unique block_id
            grade = block.get("grade", "unknown")
            x = float(block.get("x", 0))
            y = float(block.get("y", 0))
            z = float(block.get("z", 0))
            quantity = int(block.get("quantity", 1))
            shape = block.get("shape_type", "unknown")
            idx = block.get("index", migrated)

            if x <= 0 or y <= 0 or z <= 0:
                print(f"[SKIP] Invalid dimensions: {x}x{y}x{z}")
                errors += 1
                continue

            # Create block_id: grade_XxYxZ_index
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
                shape=shape[:20]  # Limit shape length
            )

            migrated += 1
            if migrated % 25 == 0:
                print(f"[PROGRESS] Migrated {migrated}/{len(blocks)} blocks...")

        except Exception as e:
            print(f"[ERROR] Failed to migrate block {block.get('index', '?')}: {e}")
            errors += 1

    print("="*60)
    print(f"[SUCCESS] MIGRATION COMPLETE:")
    print(f"  - Migrated: {migrated}")
    print(f"  - Errors: {errors}")
    print(f"  - Total: {len(blocks)}")

    # Verify
    warehouse = db.get_warehouse()
    print(f"[VERIFY] Database now contains {len(warehouse)} blocks")

    # Show sample
    print(f"\n[SAMPLE] First 5 blocks in database:")
    for i, item in enumerate(warehouse[:5]):
        print(f"  {i+1}. {item.get('block_id')} - {item.get('grade')} " +
              f"{item.get('x')}x{item.get('y')}x{item.get('z')}")


if __name__ == "__main__":
    migrate()
