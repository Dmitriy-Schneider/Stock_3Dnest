#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASTAPI-BASED SERVER FOR GUILLOTINE CUTTING ALGORITHM
=====================================================

This server replaces SimpleHTTPRequestHandler with FastAPI for:
- Proper HTTP routing and method discrimination
- Async support for concurrent requests
- Better performance and stability
- Built-in API documentation (Swagger UI at /docs)
- Pydantic validation for request/response data

The GuillotineCutter algorithm is imported from server.py.
"""

import json
import os
import logging
import copy
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Union

# Import the algorithm classes from server.py
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import GuillotineCutter, Part, Block, ensure_dirs, solve_with_all_orientations, optimize_block_size

# Import unified database from BotCut
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "BotCut"))
from database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HPMCut - 3D Guillotine Cutting API",
    description="API для оптимизации 3D раскроя блоков",
    version="2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(ROOT, "static")
DATA_DIR = os.path.join(ROOT, "data")

# Initialize unified database
db = Database()


def grades_match(target_grade: str, item_grade: str) -> bool:
    """
    Check if grades match with flexible matching.

    CRITICAL: Dots and hyphens are PART of steel grade numbers (1.2343, 1.2311)
    Split ONLY by spaces to avoid false matches.

    Examples:
        "1.2343", "1.2343" -> True (exact match)
        "1.2343", "1.2343 ESR" -> True (first word matches)
        "1.2343", "1.2311" -> False (different grades!)
        "K110", "K110 Regulit" -> True (first word matches)
    """
    if not target_grade and not item_grade:
        return True
    if not target_grade or not item_grade:
        return False

    target_str = str(target_grade).strip().lower()
    item_str = str(item_grade).strip().lower()

    # Exact match
    if target_str == item_str:
        return True

    # Split ONLY by spaces (dots and hyphens are part of grade numbers!)
    target_words = target_str.split()
    item_words = item_str.split()

    # Check if target is the first word in item (flexible match)
    if len(target_words) > 0 and len(item_words) > 0:
        if target_words[0] == item_words[0]:
            return True

    # Check if all target words are present in item words
    if len(target_words) > 1 and all(tw in item_words for tw in target_words):
        return True

    return False


# Adapter functions for format conversion (JSON ↔ SQLite)
def read_stocks():
    """
    Read stocks from unified database (SQLite).
    Returns list in JSON format for compatibility with existing code.

    JSON format: {"id": "Stock1", "x": 500, "y": 400, "z": 300, "kerf": 2.0, "grade": "steel"}
    DB format: {"block_id": "Stock1", "x": 500, "grade": "steel", "quantity": 1, "available": 1}
    """
    warehouse_items = db.get_warehouse()  # All items

    stocks = []
    for item in warehouse_items:
        stock = {
            "id": item.get("block_id", ""),
            "x": item.get("x", 0),
            "y": item.get("y", 0),
            "z": item.get("z", 0),
            "kerf": 5.0,  # Default kerf
            "grade": item.get("grade", "plastic"),
            "shape": item.get("shape", "block")  # Include shape for filtering
        }
        stocks.append(stock)

    return stocks

def write_stocks(stocks_data):
    """
    Write stocks to unified database (SQLite).
    Accepts list in JSON format and converts to DB format.

    JSON format: {"id": "Stock1", "x": 500, "y": 400, "z": 300, "kerf": 2.0, "grade": "steel"}
    DB format: block_id, grade, x, y, z, quantity, price
    """
    for stock in stocks_data:
        block_id = stock.get("id") or stock.get("BlockID") or f"Block_{len(stocks_data)}"
        grade = stock.get("grade") or stock.get("Grade") or stock.get("SteelGrade") or "plastic"
        x = float(stock.get("x") or stock.get("X") or 0)
        y = float(stock.get("y") or stock.get("Y") or 0)
        z = float(stock.get("z") or stock.get("Z") or 0)

        db.add_stock(
            block_id=block_id,
            grade=grade,
            x=x,
            y=y,
            z=z,
            quantity=1,  # Web interface doesn't track quantity, always 1
            price=0.0,
            shape="block"
        )

    logger.info(f"Saved {len(stocks_data)} stocks to unified database")


# ============= Pydantic Models for validation =============

class PartModel(BaseModel):
    id: Union[str, None] = Field(default=None, validation_alias='PartID')
    x: Union[float, None] = Field(default=None, validation_alias='X')
    y: Union[float, None] = Field(default=None, validation_alias='Y')
    z: Union[float, None] = Field(default=None, validation_alias='Z')
    quantity: Union[int, None] = Field(default=None, validation_alias='Quantity')
    grade: Optional[str] = Field(default=None, validation_alias='Grade')

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "Part1",
                "x": 100,
                "y": 80,
                "z": 60,
                "quantity": 5,
                "grade": "plastic"
            }
        }


class BlockModel(BaseModel):
    id: Union[str, None] = Field(default=None, validation_alias='BlockID')
    x: Union[float, None] = Field(default=None, validation_alias='X')
    y: Union[float, None] = Field(default=None, validation_alias='Y')
    z: Union[float, None] = Field(default=None, validation_alias='Z')
    kerf: Optional[float] = Field(default=0.0, validation_alias='Kerf')
    grade: Optional[str] = Field(default=None, validation_alias='Grade')
    steelgrade: Optional[str] = Field(default=None, validation_alias='SteelGrade')

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "Stock1",
                "x": 500,
                "y": 400,
                "z": 300,
                "kerf": 2.0,
                "grade": "steel"
            }
        }


class SolveRequest(BaseModel):
    parts: List[PartModel]
    stocks: List[BlockModel]
    iterations: int = 100
    try_all_orientations: bool = False  # ОТКАТ: опционально, не по умолчанию


class AutoSelectRequest(BaseModel):
    parts: List[PartModel]
    iterations: Optional[int] = 10
    try_all_orientations: bool = False  # ОТКАТ: опционально, не по умолчанию


class StocksRequest(BaseModel):
    stocks: List[BlockModel]


class OptimizeBlockSizeRequest(BaseModel):
    parts: List[PartModel]
    max_x: float
    max_y: float
    max_z: float
    step: Optional[float] = 10.0
    iterations: Optional[int] = 50  # Увеличено с 10 до 50 для лучшей оптимизации
    kerf: Optional[float] = 5.0
    grade: Optional[str] = "plastic"


# ============= Routes =============

@app.get('/')
async def root():
    """Serve main HTML page"""
    html_path = os.path.join(STATIC_DIR, 'index.html')
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type='text/html')
    return {"error": "Frontend not found"}


@app.get('/health')
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "ok",
        "service": "HPMCut Guillotine Cutting API",
        "version": "v27"
    }


@app.get('/api/stocks')
async def get_stocks():
    """Get all stocks from database"""
    try:
        stocks = read_stocks()
        return {"stocks": stocks}
    except Exception as e:
        logger.error(f"Error in GET /api/stocks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/stocks')
async def save_stocks(request: StocksRequest):
    """Save stocks to database"""
    try:
        stocks_data = [dict(item) for item in request.stocks]
        write_stocks(stocks_data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error in POST /api/stocks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/solve')
async def solve_cutting(request: SolveRequest):
    """Solve cutting problem with given parts and stocks"""
    try:
        # Convert Pydantic models to domain classes
        parts = [
            Part(
                p.id,
                p.x,
                p.y,
                p.z,
                p.quantity,
                grade=p.grade
            )
            for p in request.parts
        ]

        stocks = [
            Block(
                s.id,
                s.x,
                s.y,
                s.z,
                kerf=s.kerf,
                grade=s.grade
            )
            for s in request.stocks
        ]

        iterations = request.iterations
        try_all_orientations = request.try_all_orientations

        # Log input
        logger.info("=" * 60)
        logger.info("API /solve REQUEST")
        logger.info(f"Parts: {len(parts)} (total qty: {sum(p.quantity for p in parts)})")
        logger.info(f"Stocks: {len(stocks)}")
        for i, s in enumerate(stocks):
            logger.info(f"  Stock{i}: {s.id} {s.x}x{s.y}x{s.z} (vol={s.volume})")
        logger.info(f"Iterations: {iterations}")
        logger.info(f"Try all orientations: {try_all_orientations}")
        logger.info("=" * 60)

        # Run algorithm
        start_time = time.time()
        if try_all_orientations:
            result = solve_with_all_orientations(parts, stocks, iterations=iterations)
        else:
            cutter = GuillotineCutter(parts, stocks)
            result = cutter.run(iterations=iterations)
        elapsed = time.time() - start_time

        # Log result
        placed = len(result['placements'])
        util = result['summary']['overall_utilization']
        logger.info("=" * 60)
        logger.info("API /solve RESULT")
        logger.info(f"Placed: {placed} parts")
        logger.info(f"Utilization: {util:.2f}%")
        logger.info(f"Best iteration: {result.get('best_iteration', '?')}")
        logger.info(f"Time: {elapsed:.2f}s")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.error(f"Error in /api/solve: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/auto-select-stocks')
async def auto_select_stocks(request: AutoSelectRequest):
    """Auto-select optimal blocks from warehouse database by grade"""
    try:
        if not request.parts:
            logger.warning("Auto-select: No parts provided")
            raise HTTPException(status_code=400, detail="No parts provided")

        # Convert parts
        parts = [
            Part(
                p.id,
                p.x,
                p.y,
                p.z,
                p.quantity,
                grade=p.grade
            )
            for p in request.parts
        ]

        # Get target grade
        target_grade = parts[0].grade or "plastic"
        logger.info(f"Auto-select: Looking for blocks with grade '{target_grade}'")

        # Get stocks from latest warehouse database
        from warehouse_parser import parse_warehouse_file

        warehouse_dir = Path(__file__).parent / "data" / "warehouse"
        excel_files = list(warehouse_dir.glob("*.xlsx"))

        if not excel_files:
            logger.warning("Auto-select: No warehouse databases found")
            return {
                "variants": [],
                "stocks": [],
                "count": 0,
                "remaining_parts": sum(p.quantity for p in parts),
                "message": "Нет файлов базы данных склада"
            }

        # Get latest warehouse file
        latest_db = max([f.name for f in excel_files], key=extract_date_from_filename)
        warehouse_path = warehouse_dir / latest_db

        logger.info(f"Auto-select: Using warehouse database: {latest_db}")

        # Parse warehouse file
        warehouse_items = parse_warehouse_file(str(warehouse_path))

        # Convert warehouse items to stock format
        # Filter only blocks (type='block')
        blocks_only = [
            item for item in warehouse_items
            if item.get("type") == "block"
        ]

        logger.info(f"Auto-select: Found {len(blocks_only)} blocks in warehouse")

        # Use grades_match() for flexible grade matching (handles "1.2343" vs "1.2343 ESR")
        matching = [
            item for item in blocks_only
            if grades_match(target_grade, item.get("grade", ""))
        ]

        logger.info(f"Auto-select: Found {len(matching)} matching blocks with grade '{target_grade}'")

        if not matching:
            logger.warning(f"Auto-select: No blocks found with grade {target_grade}")
            # Возвращаем пустой результат вместо 404
            return {
                "variants": [],
                "stocks": [],
                "count": 0,
                "remaining_parts": sum(p.quantity for p in parts),
                "message": f"Нет блоков с маркой '{target_grade}' в базе данных"
            }

        logger.info(f"Auto-select: Testing {len(matching)} blocks with all parts...")

        # NEW ALGORITHM: Test ALL blocks and show TOP-N with best utilization
        # This allows users to choose blocks with maximum utilization even if not all parts fit
        block_results = []
        tested_count = 0
        placed_count = 0

        for stock_raw in matching:
            try:
                # Convert warehouse item to Block format
                # Warehouse format: {grade, type, x, y, z, weight, quantity, item_code, full_name, size_text}
                stock = Block(
                    stock_raw.get("item_code", "Unknown"),  # БП-00000637-11
                    stock_raw.get("x", 0),
                    stock_raw.get("y", 0),
                    stock_raw.get("z", 0),
                    kerf=5,  # Default kerf
                    grade=stock_raw.get("grade", "")
                )
                tested_count += 1

                # Debug logging
                if stock.id and "910" in str(stock.id):
                    logger.info(f"  DEBUG: Testing large block {stock.id}")
                    logger.info(f"    Stock dimensions: {stock.x}x{stock.y}x{stock.z}")
                    logger.info(f"    Parts to place: {len(parts)}")
                    for p in parts:
                        logger.info(f"      - {p.id}: {p.x}x{p.y}x{p.z} qty={p.quantity}")

                # Quick cutting with 30 iterations for better accuracy
                if request.try_all_orientations:
                    result = solve_with_all_orientations(parts, [stock], iterations=30)
                else:
                    cutter = GuillotineCutter(parts, [stock])
                    result = cutter.run(iterations=30)

                placed = len(result["placements"])
                util = result["summary"]["overall_utilization"]

                # Log ALL blocks for debugging
                if placed > 0:
                    logger.info(f"  ✓ Block {stock.id}: {placed} parts, {util:.1f}% utilization")
                    placed_count += 1
                else:
                    logger.debug(f"  ✗ Block {stock.id}: 0 parts placed")

                if placed > 0:  # Only consider blocks where at least one part fits

                    # Collect placement info
                    placed_parts_info = []
                    for placement in result["placements"]:
                        part_id = placement["part_id"]
                        original_part = next((p for p in parts if p.id == part_id), None)
                        dimensions = [original_part.x, original_part.y, original_part.z] if original_part else placement.get("dimensions", [0, 0, 0])

                        placed_parts_info.append({
                            "part_id": part_id,
                            "position": placement.get("position", [0, 0, 0]),
                            "dimensions": dimensions
                        })

                    block_results.append({
                        "stock_id": stock_raw.get("id"),
                        "stock": stock_raw,
                        "placed_count": placed,
                        "utilization": util,
                        "total_cuts": result.get("summary", {}).get("total_cuts", 0),
                        "placements": placed_parts_info,
                        "steps": result.get("steps", []),
                        "waste_percentage": 100 - util
                    })

            except Exception as e:
                logger.debug(f"Error testing block {stock_raw.get('id')}: {e}")
                continue

        # Sort by utilization (highest first), then by parts placed
        block_results.sort(key=lambda x: (-x["utilization"], -x["placed_count"]))

        # Return TOP 10 best blocks
        variants = block_results[:10]
        selected = [v["stock"] for v in variants]

        total_parts = sum(p.quantity for p in parts)
        remaining_parts = total_parts

        logger.info(f"Auto-select: Tested {tested_count} blocks, {placed_count} could place parts")
        logger.info(f"Auto-select: Found {len(variants)} suitable blocks (showing top 10 by utilization)")

        if not selected:
            logger.warning("Auto-select: Could not select any blocks")
            # Возвращаем пустой результат вместо ошибки
            return {
                "variants": [],
                "stocks": [],
                "count": 0,
                "remaining_parts": total_parts,
                "message": "Не удалось подобрать подходящие блоки для размещения деталей"
            }

        # Calculate how many parts can be placed in the best block
        best_placed = variants[0]["placed_count"] if variants else 0

        resp = {
            "variants": variants,
            "stocks": selected,
            "count": len(selected),
            "remaining_parts": max(0, total_parts - best_placed),
            "message": f"Найдено {len(variants)} вариантов блоков (отсортированы по утилизации)"
        }

        logger.info(f"Auto-select: Success! Selected {len(selected)} blocks")
        return resp

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-select ERROR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/optimize-block-size')
async def optimize_block_size_endpoint(request: OptimizeBlockSizeRequest):
    """Optimize block size to fit all parts with maximum utilization"""
    try:
        if not request.parts:
            logger.warning("Optimize block size: No parts provided")
            raise HTTPException(status_code=400, detail="No parts provided")

        # Convert parts
        parts = [
            Part(
                p.id,
                p.x,
                p.y,
                p.z,
                p.quantity,
                grade=p.grade
            )
            for p in request.parts
        ]

        logger.info(f"Optimize block size: {len(parts)} parts, max {request.max_x}×{request.max_y}×{request.max_z}, step={request.step}")

        # Run optimizer
        result = optimize_block_size(
            parts,
            max_x=request.max_x,
            max_y=request.max_y,
            max_z=request.max_z,
            step=request.step,
            iterations=request.iterations,
            kerf=request.kerf,
            grade=request.grade
        )

        logger.info(f"Optimize block size: Success! Block {result['best_block']['x']}×{result['best_block']['y']}×{result['best_block']['z']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimize block size ERROR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/docs')
async def swagger_docs():
    """Interactive API documentation"""
    pass


# Mount static files (CSS, JS, images)
@app.post("/api/generate-html-report")
async def generate_html_report_api(request: dict):
    """
    Generate interactive Three.js HTML report
    Used by Telegram bot to get interactive 3D reports
    """
    try:
        # Import PDF generator from BotCut
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "BotCut"))
        from pdf_generator import pdf_generator

        # Generate interactive Three.js HTML report
        html_path = pdf_generator.generate_threejs_html(
            request,
            user_info=request.get("user_info", {})
        )

        if not html_path or not os.path.exists(html_path):
            raise HTTPException(status_code=500, detail="Failed to generate HTML report")

        # Return the file
        return FileResponse(
            html_path,
            media_type="text/html",
            filename="botcut_3d_interactive.html"
        )

    except Exception as e:
        logger.error(f"Error generating HTML report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WAREHOUSE API ENDPOINTS
# ============================================================================

def extract_date_from_filename(filename: str) -> int:
    """
    Extract date from warehouse filename for sorting.
    Returns timestamp (higher = newer).

    Examples:
        "Склад на 30.12.25.xlsx" -> 2025-12-30
        "Склад 14.08.25.xlsx" -> 2025-08-14
        "Склад НН.xlsx" -> very old (2000-01-01)
    """
    import re
    from datetime import datetime

    date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', filename)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3))

        # Convert 2-digit year to 4-digit
        if year < 100:
            year += 2000

        return int(datetime(year, month, day).timestamp())

    # Files without date go to the end (very old)
    return int(datetime(2000, 1, 1).timestamp())


@app.get('/api/warehouse/databases')
async def get_warehouse_databases():
    """Get list of available warehouse Excel files"""
    try:
        warehouse_dir = Path(__file__).parent / "data" / "warehouse"
        if not warehouse_dir.exists():
            return {"databases": []}

        # Find all Excel files
        excel_files = list(warehouse_dir.glob("*.xlsx"))
        databases = [f.name for f in excel_files]

        logger.info(f"Found {len(databases)} warehouse databases")
        return {"databases": sorted(databases)}

    except Exception as e:
        logger.error(f"Error getting warehouse databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/warehouse/latest')
async def get_latest_warehouse_database():
    """Get the newest warehouse database filename based on date in filename"""
    try:
        warehouse_dir = Path(__file__).parent / "data" / "warehouse"
        if not warehouse_dir.exists():
            return {"latest": None}

        # Find all Excel files
        excel_files = list(warehouse_dir.glob("*.xlsx"))
        if not excel_files:
            return {"latest": None}

        # Sort by date (newest first)
        databases = [f.name for f in excel_files]
        latest = max(databases, key=extract_date_from_filename)

        logger.info(f"Latest warehouse database: {latest}")
        return {"latest": latest}

    except Exception as e:
        logger.error(f"Error getting latest warehouse database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/warehouse/stocks')
async def get_warehouse_stocks(db: str = "Склад НН.xlsx"):
    """
    Get warehouse stocks from specified database.
    Automatically parses Excel file into standardized format.

    Args:
        db: Database filename (e.g., "Склад НН.xlsx")

    Returns:
        List of warehouse items with structure:
        {
            grade: str,
            type: str (block/circle/sheet/strip),
            full_name: str,
            size_text: str,
            x, y, z: float,
            weight: float,
            quantity: int
        }
    """
    try:
        from warehouse_parser import parse_warehouse_file

        warehouse_dir = Path(__file__).parent / "data" / "warehouse"
        excel_path = warehouse_dir / db

        if not excel_path.exists():
            raise HTTPException(status_code=404, detail=f"Database not found: {db}")

        # Parse Excel file
        items = parse_warehouse_file(str(excel_path))

        logger.info(f"Loaded {len(items)} items from {db}")
        return {"items": items, "count": len(items)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading warehouse stocks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/warehouse/search')
async def search_warehouse(request: dict):
    """
    Smart search/filter warehouse items.

    Request body:
    {
        "db": "Склад НН.xlsx",          # Optional, database name
        "grade": "1.2311",               # Optional, steel grade filter
        "type": "block|circle|sheet",    # Optional, material type filter
        "minDimensions": {               # Optional, minimum dimensions for blocks
            "x": 200,
            "y": 600,
            "z": 500
        },
        "diameter": 18,                  # Optional, for circles
        "tolerance": 5                   # Optional, tolerance in mm (default 5)
    }

    Returns:
        Filtered list of items that match criteria
    """
    try:
        from warehouse_parser import parse_warehouse_file

        # Get database name
        db = request.get('db', 'Склад НН.xlsx')
        warehouse_dir = Path(__file__).parent / "data" / "warehouse"
        excel_path = warehouse_dir / db

        if not excel_path.exists():
            raise HTTPException(status_code=404, detail=f"Database not found: {db}")

        # Parse Excel file
        items = parse_warehouse_file(str(excel_path))

        # Apply filters
        filtered = items

        # Filter by grade
        if 'grade' in request and request['grade']:
            grade_filter = request['grade'].strip().lower()
            filtered = [item for item in filtered
                       if grade_filter in item['grade'].lower()]

        # Filter by type
        if 'type' in request and request['type']:
            type_filter = request['type'].lower()
            filtered = [item for item in filtered
                       if item['type'] == type_filter]

        # Filter by dimensions (for blocks)
        if 'minDimensions' in request:
            min_dims = request['minDimensions']
            min_x = min_dims.get('x', 0)
            min_y = min_dims.get('y', 0)
            min_z = min_dims.get('z', 0)

            # Check if detail can fit in stock (any orientation)
            def can_fit(item):
                if item['type'] != 'block':
                    return True

                # Get stock dimensions
                stock_dims = []
                if item['x']: stock_dims.append(item['x'])
                if item['y']: stock_dims.append(item['y'])
                if item['z']: stock_dims.append(item['z'])

                if len(stock_dims) < 3:
                    return False

                # Sort both dimensions for orientation-independent comparison
                detail_sorted = sorted([min_x, min_y, min_z])
                stock_sorted = sorted(stock_dims)

                # All detail dimensions must fit in stock
                return all(d <= s for d, s in zip(detail_sorted, stock_sorted))

            filtered = [item for item in filtered if can_fit(item)]

        # Filter by diameter (for circles)
        if 'diameter' in request and request['diameter']:
            target_diameter = float(request['diameter'])
            tolerance = float(request.get('tolerance', 5))

            def diameter_match(item):
                if item['type'] != 'circle':
                    return True

                if not item['z']:  # Diameter stored in z
                    return False

                # Check if within tolerance
                return abs(item['z'] - target_diameter) <= tolerance

            filtered = [item for item in filtered if diameter_match(item)]

        # Filter sheets by thickness only (like circles by diameter)
        if 'sheetThickness' in request and request['sheetThickness']:
            target_thickness = float(request['sheetThickness'])
            tolerance = float(request.get('sheetTolerance', 0.5))  # Default 0.5mm

            logger.info(f"Sheet filter: thickness={target_thickness}, tolerance={tolerance}")

            def sheet_thickness_match(item):
                if item['type'] != 'sheet':
                    return False

                if not item['z']:  # Thickness stored in z
                    return False

                # Check if within tolerance
                matches = abs(item['z'] - target_thickness) <= tolerance
                if not matches:
                    logger.debug(f"Sheet rejected: {item['full_name']} thickness={item['z']} (target={target_thickness}±{tolerance})")
                return matches

            filtered = [item for item in filtered if sheet_thickness_match(item)]
            logger.info(f"After sheet thickness filter: {len(filtered)} items")

        # Filter strips by thickness only (like circles by diameter)
        if 'stripThickness' in request and request['stripThickness']:
            target_thickness = float(request['stripThickness'])
            tolerance = float(request.get('stripTolerance', 0.5))  # Default 0.5mm

            logger.info(f"Strip filter: thickness={target_thickness}, tolerance={tolerance}")

            def strip_thickness_match(item):
                if item['type'] != 'strip':
                    return False

                if not item['z']:  # Thickness stored in z
                    return False

                # Check if within tolerance
                matches = abs(item['z'] - target_thickness) <= tolerance
                if not matches:
                    logger.debug(f"Strip rejected: {item['full_name']} thickness={item['z']} (target={target_thickness}±{tolerance})")
                return matches

            filtered = [item for item in filtered if strip_thickness_match(item)]
            logger.info(f"After strip thickness filter: {len(filtered)} items")

        logger.info(f"Search: {len(items)} total → {len(filtered)} filtered")
        return {
            "items": filtered,
            "count": len(filtered),
            "total": len(items)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching warehouse: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


try:
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    ensure_dirs()
    logger.info("FastAPI server initialized")


if __name__ == '__main__':
    import uvicorn

    ensure_dirs()
    logger.info("Starting FastAPI server on http://127.0.0.1:3001")
    print("FastAPI server starting on http://127.0.0.1:3001")
    print("API docs available at http://127.0.0.1:3001/docs")
    print("ReDoc docs available at http://127.0.0.1:3001/redoc")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3001,
        log_level="info"
    )
