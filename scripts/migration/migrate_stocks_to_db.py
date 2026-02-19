#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script: stocks.json → botcut.db

Переносит блоки из data/stocks.json в единую БД BotCut/data/botcut.db
"""

import json
import os
import sys
from pathlib import Path

# Add BotCut to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "BotCut"))
from database import Database

ROOT = Path(__file__).parent
STOCKS_JSON = ROOT / "data" / "stocks.json"

def migrate():
    """Migrate stocks from JSON to SQLite database"""
    print(f"[MIGRATION] stocks.json -> botcut.db")
    print("=" * 60)

    # Read existing stocks from JSON
    if not STOCKS_JSON.exists():
        print(f"[ERROR] File {STOCKS_JSON} not found!")
        return

    with open(STOCKS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        stocks = data.get("stocks", [])

    print(f"[INFO] Found {len(stocks)} blocks in stocks.json")

    if not stocks:
        print("[WARN] No data to migrate")
        return

    # Initialize database
    db = Database()

    # Migrate each stock
    migrated = 0
    for stock in stocks:
        try:
            block_id = stock.get("id") or stock.get("BlockID") or ""
            grade = stock.get("grade") or stock.get("Grade") or stock.get("SteelGrade") or "plastic"
            x = float(stock.get("x") or stock.get("X") or 0)
            y = float(stock.get("y") or stock.get("Y") or 0)
            z = float(stock.get("z") or stock.get("Z") or 0)

            if not block_id or x <= 0 or y <= 0 or z <= 0:
                print(f"[SKIP] Invalid block: {stock}")
                continue

            db.add_stock(
                block_id=block_id,
                grade=grade,
                x=x,
                y=y,
                z=z,
                quantity=1,
                price=0.0,
                shape="block"
            )

            migrated += 1
            print(f"[OK] {migrated}. Migrated: {block_id} ({grade}, {x}x{y}x{z})")

        except Exception as e:
            print(f"[ERROR] Failed to migrate block {stock.get('id', '?')}: {e}")

    print("=" * 60)
    print(f"[SUCCESS] MIGRATION COMPLETE: {migrated}/{len(stocks)} blocks")

    # Verify
    warehouse = db.get_warehouse()
    print(f"[VERIFY] Database now contains {len(warehouse)} blocks")


if __name__ == "__main__":
    migrate()
