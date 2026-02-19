#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script: StockHPM.xlsx → botcut.db

Переносит ВСЕ блоки из data/StockHPM.xlsx в единую БД BotCut/data/botcut.db
"""

import os
import sys
from pathlib import Path
import pandas as pd

# Add BotCut to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "BotCut"))
from database import Database

ROOT = Path(__file__).parent
EXCEL_FILE = ROOT / "data" / "StockHPM.xlsx"

def migrate():
    """Migrate stocks from Excel to SQLite database"""
    print(f"[MIGRATION] StockHPM.xlsx -> botcut.db")
    print("=" * 60)

    # Read Excel file
    if not EXCEL_FILE.exists():
        print(f"[ERROR] File {EXCEL_FILE} not found!")
        return

    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"[INFO] Found {len(df)} rows in Excel")
        print(f"[INFO] Columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to read Excel: {e}")
        return

    # Initialize database
    db = Database()

    # Migrate each row
    migrated = 0
    skipped = 0

    for idx, row in df.iterrows():
        try:
            # Parse dimensions from "Размер блока" column (format: "X x Y x Z" or "X×Y×Z")
            size_str = str(row.iloc[0]) if len(row) > 0 else ""  # First column

            # Try different separators
            parts = None
            for sep in ['×', 'x', 'X', '*']:
                if sep in size_str:
                    parts = size_str.split(sep)
                    break

            if not parts or len(parts) < 3:
                print(f"[SKIP] Row {idx}: Invalid size format '{size_str}'")
                skipped += 1
                continue

            # Parse dimensions
            try:
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                z = float(parts[2].strip())
            except:
                print(f"[SKIP] Row {idx}: Cannot parse dimensions from '{size_str}'")
                skipped += 1
                continue

            # Get grade (column 1 or 2)
            grade = str(row.iloc[1]) if len(row) > 1 else "unknown"
            if pd.isna(grade) or grade == "nan":
                grade = "unknown"

            # Get quantity (column 3 or last)
            quantity = 1
            if len(row) > 3:
                try:
                    quantity = int(row.iloc[3])
                except:
                    quantity = 1

            # Generate block_id
            block_id = f"{grade}_{int(x)}x{int(y)}x{int(z)}_{idx}"

            # Add to database
            db.add_stock(
                block_id=block_id,
                grade=grade,
                x=x,
                y=y,
                z=z,
                quantity=quantity,
                price=0.0,
                shape="block"
            )

            migrated += 1
            if migrated % 50 == 0:
                print(f"[PROGRESS] Migrated {migrated} blocks...")

        except Exception as e:
            print(f"[ERROR] Row {idx}: {e}")
            skipped += 1

    print("=" * 60)
    print(f"[SUCCESS] MIGRATION COMPLETE:")
    print(f"  - Migrated: {migrated}")
    print(f"  - Skipped: {skipped}")
    print(f"  - Total: {len(df)}")

    # Verify
    warehouse = db.get_warehouse()
    print(f"[VERIFY] Database now contains {len(warehouse)} blocks")


if __name__ == "__main__":
    migrate()
