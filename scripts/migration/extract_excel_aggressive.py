#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggressive extraction: try to extract ANY valid dimensions from ANY column
"""
import pandas as pd
import re
import json

df = pd.read_excel('data/StockHPM.xlsx')

blocks = []
skipped = 0
skip_reasons = {}

for idx, row in df.iterrows():
    try:
        col0 = str(row.iloc[0]) if len(row) > 0 and not pd.isna(row.iloc[0]) else ""
        col1 = str(row.iloc[1]) if len(row) > 1 and not pd.isna(row.iloc[1]) else ""
        col2 = str(row.iloc[2]) if len(row) > 2 and not pd.isna(row.iloc[2]) else ""
        col3 = float(row.iloc[3]) if len(row) > 3 and not pd.isna(row.iloc[3]) else 1.0

        if not col0 or col0 == "nan":
            skipped += 1
            skip_reasons["empty_col0"] = skip_reasons.get("empty_col0", 0) + 1
            continue

        # Extract grade
        grade_match = re.match(r'^([\d\.]+)', col0)
        grade = grade_match.group(1) if grade_match else "unknown"

        x, y, z = None, None, None
        shape_type = "unknown"
        col0_lower = col0.lower()

        # Try to extract dimensions from col0
        # Pattern: "NxM" or "N×M"
        size2d_col0 = re.search(r'(\d+)\s*[x×]\s*(\d+)', col0)

        # Try to extract length from col1
        length = None
        if col1 and col1 != "nan":
            try:
                length = float(col1.replace(',', ''))
                if length > 10000:  # Suspiciously large
                    length = None
            except:
                pass

        # Try to extract alternative dimensions from col2
        alt_dim = None
        if col2 and col2 != "nan":
            try:
                # Remove comma (might be thousands or decimal separator)
                col2_clean = col2.replace(',', '')
                alt_val = float(col2_clean)
                # Only use if it looks like a dimension (not weight)
                if 1 < alt_val < 10000:
                    alt_dim = alt_val
            except:
                pass

        # Strategy 1: Shape keywords with dimensions
        if "полоса" in col0_lower:
            shape_type = "Полоса"
            if size2d_col0 and length:
                x, y, z = float(size2d_col0.group(1)), float(size2d_col0.group(2)), length
            elif size2d_col0 and alt_dim:
                x, y, z = float(size2d_col0.group(1)), float(size2d_col0.group(2)), alt_dim
            else:
                # Single dimension + length
                single_match = re.search(r'полоса\s+(\d+)', col0_lower)
                if single_match and length:
                    x, y, z = float(single_match.group(1)), 10.0, length

        elif "плита" in col0_lower:
            shape_type = "Плита"
            if size2d_col0 and length:
                x, y, z = float(size2d_col0.group(1)), float(size2d_col0.group(2)), length
            elif size2d_col0 and alt_dim:
                x, y, z = float(size2d_col0.group(1)), float(size2d_col0.group(2)), alt_dim

        elif "круг" in col0_lower:
            shape_type = "Круг"
            diam_match = re.search(r'круг[^\d]*(\d+)', col0_lower)
            if diam_match and length:
                diam = float(diam_match.group(1))
                x, y, z = diam, diam, length
            elif diam_match and alt_dim:
                diam = float(diam_match.group(1))
                x, y, z = diam, diam, alt_dim

        elif "квадрат" in col0_lower:
            shape_type = "Квадрат"
            sq_match = re.search(r'квадр[^\d]*(\d+)', col0_lower)
            if sq_match and length:
                size = float(sq_match.group(1))
                x, y, z = size, size, length

        elif "шестигр" in col0_lower:
            shape_type = "Шестигранник"
            hex_match = re.search(r'шестигр[^\d]*(\d+)', col0_lower)
            if hex_match and length:
                size = float(hex_match.group(1))
                x, y, z = size, size, length

        # Strategy 2: If no shape keyword but has dimensions
        elif size2d_col0 and length:
            shape_type = "Неизвестная форма"
            x, y, z = float(size2d_col0.group(1)), float(size2d_col0.group(2)), length

        # Strategy 3: Extract single dimension + guess others
        if x is None and length and length > 10:
            # Try to find ANY number in col0
            any_num = re.search(r'\s(\d+)\s*$', col0)  # Number at end
            if any_num:
                num = float(any_num.group(1))
                if 1 < num < 1000:
                    shape_type = "Автоопределение"
                    x, y, z = num, num, length

        # Validate
        if x is None or y is None or z is None:
            reason = "no_dimensions"
            if not length:
                reason = "no_length"
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            skipped += 1
            continue

        if x <= 0 or y <= 0 or z <= 0:
            skip_reasons["invalid_dimensions"] = skip_reasons.get("invalid_dimensions", 0) + 1
            skipped += 1
            continue

        quantity = int(col3) if col3 >= 1 else 1

        blocks.append({
            "index": idx,
            "grade": grade,
            "shape_type": shape_type,
            "col0": col0[:70],
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "quantity": quantity
        })

    except Exception as e:
        skipped += 1
        skip_reasons["error"] = skip_reasons.get("error", 0) + 1

print(f"Extracted {len(blocks)} blocks, skipped {skipped}")
print(f"\nSkip reasons:")
for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
    print(f"  {reason}: {count}")

# Save
with open('excel_aggressive.json', 'w', encoding='utf-8') as f:
    json.dump(blocks, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(blocks)} blocks to excel_aggressive.json")
print(f"Ready for database migration!")

if blocks:
    xs = [b['x'] for b in blocks]
    ys = [b['y'] for b in blocks]
    zs = [b['z'] for b in blocks]
    print(f"\nDimension ranges:")
    print(f"  X: {min(xs):.1f} - {max(xs):.1f} mm")
    print(f"  Y: {min(ys):.1f} - {max(ys):.1f} mm")
    print(f"  Z: {min(zs):.1f} - {max(zs):.1f} mm")
