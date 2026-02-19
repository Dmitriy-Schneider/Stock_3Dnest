"""
Database module for BotCut
Handles all SQLite database operations
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Try to import Config, but make it optional for web server
try:
    from config import Config
    DEFAULT_DB_PATH = Config.DB_PATH
except ImportError:
    # Fallback for web server (no config.py available)
    DEFAULT_DB_PATH = os.getenv("DB_PATH", "/app/data/botcut.db")

logger = logging.getLogger(__name__)


class Database:
    """SQLite Database handler"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_tables()

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        """Create tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Calculation history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                calculation_type TEXT NOT NULL,
                input_data TEXT NOT NULL,
                result_data TEXT NOT NULL,
                utilization REAL,
                waste_percent REAL,
                num_cuts INTEGER,
                num_remnants INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Warehouse/Stocks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warehouse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_id TEXT UNIQUE,
                grade TEXT,
                shape TEXT DEFAULT 'block',
                x REAL,
                y REAL,
                z REAL,
                weight REAL,
                quantity INTEGER DEFAULT 1,
                price REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrate existing table to add new columns if they don't exist
        try:
            # Check existing columns
            cursor.execute("PRAGMA table_info(warehouse)")
            columns = [row[1] for row in cursor.fetchall()]

            # Add missing columns
            if 'shape' not in columns:
                cursor.execute("ALTER TABLE warehouse ADD COLUMN shape TEXT DEFAULT 'block'")
                logger.info("Added 'shape' column to warehouse")

            if 'weight' not in columns:
                cursor.execute("ALTER TABLE warehouse ADD COLUMN weight REAL")
                logger.info("Added 'weight' column to warehouse")

            conn.commit()
        except Exception as e:
            logger.warning(f"Migration warning: {e}")

        # User's saved parts library
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                part_name TEXT,
                grade TEXT,
                x REAL,
                y REAL,
                z REAL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # User's saved blocks library
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                block_name TEXT,
                grade TEXT,
                x REAL,
                y REAL,
                z REAL,
                kerf REAL DEFAULT 5.0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database tables ensured")

    # ============ USER MANAGEMENT ============

    def add_or_update_user(self, user_id: int, first_name: str = None,
                          last_name: str = None, username: str = None):
        """Add or update user"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (user_id, first_name, last_name, username, last_activity)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = COALESCE(?, first_name),
                last_name = COALESCE(?, last_name),
                username = COALESCE(?, username),
                last_activity = CURRENT_TIMESTAMP
        """, (user_id, first_name, last_name, username, first_name, last_name, username))

        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user info"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    # ============ CALCULATIONS ============

    def save_calculation(self, user_id: int, calc_type: str,
                        input_data: Dict, result_data: Dict) -> int:
        """Save calculation result"""
        conn = self._get_connection()
        cursor = conn.cursor()

        result = result_data.get("summary", {})
        utilization = result.get("overall_utilization", 0)
        waste = 100 - utilization if utilization else 0

        cursor.execute("""
            INSERT INTO calculations
            (user_id, calculation_type, input_data, result_data,
             utilization, waste_percent, num_cuts, num_remnants)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            calc_type,
            json.dumps(input_data, ensure_ascii=False),
            json.dumps(result_data, ensure_ascii=False),
            utilization,
            waste,
            len(result_data.get("steps", [])),
            result.get("remaining_quantity", 0)
        ))

        calc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return calc_id

    def get_calculation(self, calc_id: int) -> Optional[Dict]:
        """Get specific calculation"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM calculations WHERE id = ?", (calc_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        result = dict(row)
        result["input_data"] = json.loads(result["input_data"])
        result["result_data"] = json.loads(result["result_data"])
        return result

    def get_user_calculations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's calculation history"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, calculation_type, created_at, utilization, waste_percent, num_cuts
            FROM calculations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ============ WAREHOUSE ============

    def add_stock(self, block_id: str, grade: str, x: float, y: float, z: float,
                 quantity: int, price: float = 0, shape: str = "block",
                 weight: float = None) -> bool:
        """
        Add stock to warehouse

        Args:
            block_id: Unique identifier
            grade: Steel grade
            x, y, z: Dimensions in mm
            quantity: Number of items
            price: Price per unit
            shape: "block", "circle", or "sheet"
            weight: Weight in kg
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO warehouse
                (block_id, grade, x, y, z, quantity, price, shape, weight, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (block_id, grade, x, y, z, quantity, price, shape, weight))

            conn.commit()
            logger.info(f"Stock {block_id} ({shape}) added/updated")
            return True
        except Exception as e:
            logger.error(f"Error adding stock: {e}")
            return False
        finally:
            conn.close()

    def get_warehouse(self, grade: str = None) -> List[Dict]:
        """Get warehouse items, optionally filtered by grade"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if grade:
            cursor.execute("""
                SELECT * FROM warehouse
                WHERE grade = ? AND quantity > 0
                ORDER BY block_id
            """, (grade,))
        else:
            cursor.execute("""
                SELECT * FROM warehouse
                WHERE quantity > 0
                ORDER BY grade, block_id
            """)

        rows = cursor.fetchall()
        conn.close()

        # CRITICAL FIX: Explicitly build dicts to remove SQLite Row metadata
        result = []
        for row in rows:
            # Build clean dict with explicit keys - NO metadata
            clean_row = {
                "block_id": str(row["block_id"]) if row["block_id"] else "",
                "grade": str(row["grade"]) if row["grade"] else "",
                "x": float(row["x"]) if row["x"] is not None else 0.0,
                "y": float(row["y"]) if row["y"] is not None else 0.0,
                "z": float(row["z"]) if row["z"] is not None else 0.0,
                "quantity": int(row["quantity"]) if row["quantity"] is not None else 0,
            }

            # Add shape field with default
            try:
                clean_row["shape"] = str(row["shape"]) if "shape" in row.keys() and row["shape"] else "block"
            except:
                clean_row["shape"] = "block"

            # Add optional fields if present
            try:
                if "weight" in row.keys() and row["weight"] is not None:
                    clean_row["weight"] = float(row["weight"])
            except:
                pass

            result.append(clean_row)

        return result

    def update_stock_quantity(self, block_id: str, quantity_used: int) -> bool:
        """Update stock quantity after use"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE warehouse
                SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
                WHERE block_id = ?
            """, (quantity_used, block_id))

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            return False
        finally:
            conn.close()

    # ============ USER LIBRARIES ============

    def save_part_template(self, user_id: int, name: str, grade: str,
                          x: float, y: float, z: float, description: str = "") -> int:
        """Save part template"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_parts (user_id, part_name, grade, x, y, z, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, grade, x, y, z, description))

        part_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return part_id

    def get_user_parts(self, user_id: int) -> List[Dict]:
        """Get user's saved parts"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, part_name, grade, x, y, z
            FROM user_parts
            WHERE user_id = ?
            ORDER BY part_name
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def save_block_template(self, user_id: int, name: str, grade: str,
                           x: float, y: float, z: float, kerf: float = 5.0,
                           description: str = "") -> int:
        """Save block template"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_blocks (user_id, block_name, grade, x, y, z, kerf, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, grade, x, y, z, kerf, description))

        block_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return block_id

    def get_user_blocks(self, user_id: int) -> List[Dict]:
        """Get user's saved blocks"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, block_name, grade, x, y, z, kerf
            FROM user_blocks
            WHERE user_id = ?
            ORDER BY block_name
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]


# Global database instance
db = Database()
