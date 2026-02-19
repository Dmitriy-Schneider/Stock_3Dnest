"""
Warehouse Excel Parser
Parses warehouse Excel files (Склад НН.xlsx format) into standardized format
Handles grouped data structure: Grade header → Detail items
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class WarehouseParser:
    """Parse warehouse Excel files with grouped structure"""

    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

    @staticmethod
    def parse_grade_and_type(text: str) -> Tuple[str, str, Optional[float]]:
        """
        Parse steel grade, material type, and embedded dimension.

        Examples:
            "1.2311 Блок" → ("1.2311", "block", None)
            "1.3343 ESR Круг 18" → ("1.3343 ESR", "circle", 18.0)
            "BG 42 Лист 3,5" → ("BG 42", "sheet", 3.5)
            "1.1730 Полоса 50x15" → ("1.1730", "strip", None)

        Returns:
            (grade, type, embedded_dimension)
        """
        text = str(text).strip()

        # Determine material type
        material_type = "block"  # default
        if "Блок" in text:
            material_type = "block"
        elif "Круг" in text:
            material_type = "circle"
        elif "Лист" in text or "Bleche" in text:
            material_type = "sheet"
        elif "Полоса" in text:
            material_type = "strip"
        elif "Пруток" in text:
            material_type = "circle"
        elif "Квадрат" in text:
            material_type = "square"
        elif "Диск" in text:
            material_type = "block"

        # Extract embedded dimension
        embedded_dim = None

        # For circles: "Круг 18" → diameter 18
        if material_type == "circle":
            match = re.search(r'Круг\s+(\d+(?:[.,]\d+)?)', text)
            if match:
                embedded_dim = float(match.group(1).replace(',', '.'))

        # For sheets: "Лист 3,5" → thickness 3.5
        elif material_type == "sheet":
            match = re.search(r'(?:Лист|Bleche)\s+(\d+(?:[.,]\d+)?)', text)
            if match:
                embedded_dim = float(match.group(1).replace(',', '.'))

        # For strips: "Полоса 50x15" → width 50mm x thickness 15mm
        elif material_type == "strip":
            # Extract width × thickness from name (e.g., "50x15")
            match = re.search(r'(\d+(?:[.,]\d+)?)\s*[xх×]\s*(\d+(?:[.,]\d+)?)', text)
            if match:
                # Return as tuple (width, thickness) for later use
                width = float(match.group(1).replace(',', '.'))
                thickness = float(match.group(2).replace(',', '.'))
                embedded_dim = (width, thickness)  # Store both dimensions

        # Extract grade name (everything before type keyword)
        grade = text
        for keyword in ["Блок", "Полоса", "Круг", "Лист", "Пруток", "Квадрат", "Диск", "Bleche"]:
            if keyword in grade:
                grade = grade.split(keyword)[0].strip()
                break

        # Clean up grade name
        if 'x' in grade.lower():
            grade = re.sub(r'\s+\d+(?:[.,]\d+)?(?:x\d+(?:[.,]\d+)?)+$', '', grade).strip()

        return grade, material_type, embedded_dim

    @staticmethod
    def parse_dimensions(size_text: str, material_type: str, embedded_dim: Optional[float] = None) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Parse dimensions based on material type.

        Returns:
            (x, y, z) tuple where:
            - block: (length, width, height)
            - circle: (length, 0, diameter)
            - sheet: (length, width, thickness)
            - strip: (length, width, thickness)
        """
        if not size_text or pd.isna(size_text):
            return None, None, embedded_dim if embedded_dim else None

        text = str(size_text).strip()

        # Normalize separators: Х → ×, comma → dot
        text = text.replace('Х', '×').replace('х', '×').replace(',', '.')

        # Extract all numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        numbers = [float(n) for n in numbers]

        if not numbers:
            return None, None, embedded_dim if embedded_dim else None

        # Parse based on material type
        if material_type == "block":
            # "332 × 232 × 27" → (332, 232, 27)
            if len(numbers) >= 3:
                return numbers[0], numbers[1], numbers[2]
            elif len(numbers) == 2:
                return numbers[0], numbers[1], None
            elif len(numbers) == 1:
                return numbers[0], None, None

        elif material_type == "circle":
            # "3800" → length=3800, diameter from embedded_dim
            if len(numbers) >= 1:
                return numbers[0], 0, embedded_dim  # length, 0, diameter

        elif material_type == "sheet":
            # "700 × 100" → length × width, thickness from embedded_dim
            if len(numbers) >= 2:
                return numbers[0], numbers[1], embedded_dim  # length, width, thickness
            elif len(numbers) == 1:
                return numbers[0], None, embedded_dim

        elif material_type == "strip":
            # "2050" → length, width and thickness from embedded_dim tuple
            # embedded_dim = (width, thickness) from "Полоса 50x15"
            if len(numbers) >= 1:
                length = numbers[0]
                if embedded_dim and isinstance(embedded_dim, tuple):
                    width, thickness = embedded_dim
                    return length, width, thickness
                else:
                    return length, None, None

        return numbers[0] if numbers else None, None, embedded_dim

    @staticmethod
    def format_size_text(x: Optional[float], y: Optional[float], z: Optional[float], material_type: str) -> str:
        """
        Format dimensions into readable size text.

        Examples:
            block: "332 × 232 × 27"
            circle: "3800" (length, diameter in type)
            sheet: "700 × 100"
        """
        if material_type == "block":
            if x and y and z:
                return f"{int(x)} × {int(y)} × {int(z)}"
            elif x and y:
                return f"{int(x)} × {int(y)}"
            elif x:
                return str(int(x))

        elif material_type == "circle":
            if x:
                return str(int(x))  # Just length

        elif material_type == "sheet":
            if x and y:
                return f"{int(x)} × {int(y)}"
            elif x:
                return str(int(x))

        elif material_type == "strip":
            # For strips: show only length (width/thickness already in grade name)
            if x:
                return str(int(x))

        return ""

    def parse(self) -> List[Dict]:
        """
        Parse Excel file into standardized warehouse items.

        Structure of source file:
        - Header row: Марка + размеры (Номенклатура, Unnamed: 1, Вес, Количество)
        - Group header: "1.2311 Блок", nan, 2700.7, 5.0 (total weight/quantity)
        - Detail items: "БП-00000637-11", "332 Х 232 Х 27", 15.2, 1.0

        Returns:
            List of standardized items with format:
            {
                'grade': '1.2311',
                'type': 'block',
                'size_text': '332 × 232 × 27',
                'x': 332, 'y': 232, 'z': 27,
                'weight': 15.2,
                'quantity': 1,
                'full_name': '1.2311 Блок'
            }
        """
        logger.info(f"Parsing warehouse file: {self.excel_path}")

        # Read Excel file without headers to detect format
        df_raw = pd.read_excel(self.excel_path, header=None)
        logger.info(f"Loaded {len(df_raw)} rows")

        # Find header row (contains 'Номенклатура')
        header_row = None
        for idx, row in df_raw.iterrows():
            if any('Номенклатура' in str(cell) for cell in row.values if pd.notna(cell)):
                header_row = idx
                logger.info(f"Found header row at index {header_row}")
                break

        if header_row is None:
            logger.error("Header row with 'Номенклатура' not found")
            return []

        # Re-read with proper header
        df = pd.read_excel(self.excel_path, header=header_row)
        logger.info(f"Data rows: {len(df)}")

        # Detect column positions
        nom_col = 'Номенклатура' if 'Номенклатура' in df.columns else df.columns[0]

        # Find size column (usually Unnamed: 1 or Unnamed: 3)
        size_col_name = None
        for col in df.columns:
            if 'Unnamed' in str(col) and df.columns.get_loc(col) in [1, 3]:
                # Check if this column has dimension data
                sample = df[col].dropna().head(5).astype(str)
                if any('x' in s.lower() or 'х' in s.lower() or s.replace('.','').isdigit() for s in sample):
                    size_col_name = col
                    break

        if size_col_name is None:
            size_col_name = df.columns[1] if len(df.columns) > 1 else None

        # Find weight and quantity columns
        weight_col = 'Вес' if 'Вес' in df.columns else None
        if weight_col is None:
            for col in df.columns:
                if 'вес' in str(col).lower() or 'остаток' in str(col).lower():
                    weight_col = col
                    break

        quantity_col = 'Количество' if 'Количество' in df.columns else None
        if quantity_col is None:
            for col in df.columns:
                if 'количество' in str(col).lower() or 'кол' in str(col).lower():
                    quantity_col = col
                    break

        logger.info(f"Columns detected: nom={nom_col}, size={size_col_name}, weight={weight_col}, quantity={quantity_col}")

        items = []
        current_grade = None
        current_type = None
        current_embedded_dim = None
        current_full_name = None

        for idx, row in df.iterrows():
            # Skip completely empty rows
            if pd.isna(row[nom_col]):
                continue

            nomenclature = str(row[nom_col]).strip()
            size_col = row[size_col_name] if size_col_name else None
            weight = row[weight_col] if weight_col and weight_col in row.index else None
            quantity = row[quantity_col] if quantity_col and quantity_col in row.index else None

            # Check if this is a header row (group header)
            # Headers have grade/type in Номенклатура and nan in Unnamed: 1
            is_header = pd.isna(size_col) or (nomenclature and not nomenclature.startswith('БП-'))

            if is_header:
                # This is a group header - extract grade and type
                grade, mat_type, embedded = self.parse_grade_and_type(nomenclature)
                current_grade = grade
                current_type = mat_type
                current_embedded_dim = embedded
                current_full_name = nomenclature
                logger.debug(f"Header: {nomenclature} → grade={grade}, type={mat_type}, embedded={embedded}")
            else:
                # This is a detail item - use current grade/type
                if not current_grade:
                    logger.warning(f"Row {idx}: Detail without header: {nomenclature}")
                    continue

                # Parse dimensions
                x, y, z = self.parse_dimensions(size_col, current_type, current_embedded_dim)

                # Format size text
                size_text = self.format_size_text(x, y, z, current_type)

                # Create item
                item = {
                    'grade': current_grade,
                    'type': current_type,
                    'full_name': current_full_name,
                    'size_text': size_text,
                    'x': x,
                    'y': y,
                    'z': z,
                    'weight': float(weight) if not pd.isna(weight) else 0.0,
                    'quantity': int(quantity) if not pd.isna(quantity) else 1,
                    'item_code': nomenclature  # БП-00000637-11
                }

                items.append(item)
                logger.debug(f"Item: {nomenclature} → {size_text} ({current_type})")

        logger.info(f"Parsed {len(items)} warehouse items")
        return items

    def to_dataframe(self) -> pd.DataFrame:
        """Parse and return as pandas DataFrame"""
        items = self.parse()
        return pd.DataFrame(items)


def parse_warehouse_file(excel_path: str) -> List[Dict]:
    """
    Convenience function to parse warehouse Excel file.

    Args:
        excel_path: Path to Excel file

    Returns:
        List of warehouse items
    """
    parser = WarehouseParser(excel_path)
    return parser.parse()


if __name__ == "__main__":
    # Test parser
    logging.basicConfig(level=logging.INFO)

    test_file = "Склад НН.xlsx"
    if Path(test_file).exists():
        print(f"\n=== Testing parser with {test_file} ===\n")
        parser = WarehouseParser(test_file)
        items = parser.parse()

        print(f"Total items: {len(items)}")
        print("\nFirst 10 items:")
        for item in items[:10]:
            print(f"{item['full_name']:30} | {item['size_text']:20} | {item['weight']:8.1f} | {item['quantity']}")

        print("\nItems by type:")
        df = pd.DataFrame(items)
        print(df.groupby('type').size())
