#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРАВИЛЬНЫЙ парсер для StockHPM.xlsx:
- БЛОКИ: col0="Марка Блок", col1="X × Y × Z"
- КРУГИ: col0="Марка Круг D", col1=длина
- ПОЛОСЫ: col0="Марка Полоса NxM", col1=длина
"""
import pandas as pd
import re
import json

df = pd.read_excel('data/StockHPM.xlsx')

items = []
skipped = 0
stats = {}
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

        # Извлечь марку стали
        grade_match = re.match(r'^([^\s]+)', col0)
        grade = grade_match.group(1).strip() if grade_match else "unknown"

        col0_lower = col0.lower()
        x, y, z = None, None, None
        shape = None
        shape_type = None

        # ==========================================
        # 1. БЛОКИ (block) - размеры в col1!
        # ==========================================
        if "блок" in col0_lower:
            shape = "block"
            shape_type = "Блок"

            # ВАЖНО: размеры в col1, формат "X × Y × Z"
            if col1 and col1 != "nan":
                # Ищем паттерн "число × число × число"
                size3d = re.search(r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)', col1)
                if size3d:
                    x = float(size3d.group(1))
                    y = float(size3d.group(2))
                    z = float(size3d.group(3))
                else:
                    skipped += 1
                    skip_reasons["block_no_dims_in_col1"] = skip_reasons.get("block_no_dims_in_col1", 0) + 1
                    continue
            else:
                skipped += 1
                skip_reasons["block_empty_col1"] = skip_reasons.get("block_empty_col1", 0) + 1
                continue

        # ==========================================
        # 2. ЛИСТЫ/ПЛИТЫ (plate)
        # ==========================================
        elif "плита" in col0_lower or "лист" in col0_lower:
            shape = "plate"
            shape_type = "Плита" if "плита" in col0_lower else "Лист"

            # Размеры могут быть в col0 или col1
            size2d_col1 = re.search(r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)', col1) if col1 and col1 != "nan" else None
            size2d_col0 = re.search(r'(\d+)\s*[×x]\s*(\d+)', col0)

            if size2d_col1:
                # Если в col1 есть 2D размеры
                x = float(size2d_col1.group(1))
                y = float(size2d_col1.group(2))
                z = 1000.0  # Стандартная длина листа
            elif size2d_col0:
                x = float(size2d_col0.group(1))
                y = float(size2d_col0.group(2))
                # Попытка извлечь длину из col1
                try:
                    z = float(col1.replace(',', '')) if col1 and col1 != "nan" else 1000.0
                except:
                    z = 1000.0
            else:
                skipped += 1
                skip_reasons["plate_no_dims"] = skip_reasons.get("plate_no_dims", 0) + 1
                continue

        # ==========================================
        # 3. ПОЛОСЫ (strip)
        # ==========================================
        elif "полоса" in col0_lower:
            shape = "plate"
            shape_type = "Полоса"

            # Сечение в col0, длина в col1
            size2d = re.search(r'(\d+)\s*[×x]\s*(\d+)', col0)
            if size2d:
                x = float(size2d.group(1))
                y = float(size2d.group(2))
                try:
                    z = float(col1.replace(',', '')) if col1 and col1 != "nan" else 2000.0
                except:
                    z = 2000.0
            else:
                skipped += 1
                skip_reasons["strip_no_dims"] = skip_reasons.get("strip_no_dims", 0) + 1
                continue

        # ==========================================
        # 4. КРУГИ/ПРУТКИ (rod)
        # ==========================================
        elif "круг" in col0_lower or "кругл" in col0_lower or "пруток" in col0_lower:
            shape = "rod"
            shape_type = "Круг"

            # Диаметр в col0, длина в col1
            # Паттерн: "Круг 4,13" или "Круг 18"
            diam_match = re.search(r'(круг|кругл|пруток)[^\d]*([\d,\.]+)', col0_lower)
            if diam_match:
                diam_str = diam_match.group(2).replace(',', '.')
                diameter = float(diam_str)

                # Длина из col1
                try:
                    z = float(col1.replace(',', '')) if col1 and col1 != "nan" else 3000.0
                except:
                    z = 3000.0

                # Для БД храним как квадрат
                x = diameter
                y = diameter
            else:
                skipped += 1
                skip_reasons["rod_no_diameter"] = skip_reasons.get("rod_no_diameter", 0) + 1
                continue

        # ==========================================
        # 5. КВАДРАТЫ
        # ==========================================
        elif "квадрат" in col0_lower:
            shape = "block"
            shape_type = "Квадрат"

            sq_match = re.search(r'квадр[^\d]*([\d,\.]+)', col0_lower)
            if sq_match:
                size = float(sq_match.group(1).replace(',', '.'))
                try:
                    z = float(col1.replace(',', '')) if col1 and col1 != "nan" else 3000.0
                except:
                    z = 3000.0
                x = size
                y = size
            else:
                skipped += 1
                skip_reasons["square_no_size"] = skip_reasons.get("square_no_size", 0) + 1
                continue

        # ==========================================
        # 6. ШЕСТИГРАННИКИ
        # ==========================================
        elif "шестигр" in col0_lower:
            shape = "rod"
            shape_type = "Шестигранник"

            hex_match = re.search(r'шестигр[^\d]*([\d,\.]+)', col0_lower)
            if hex_match:
                size = float(hex_match.group(1).replace(',', '.'))
                try:
                    z = float(col1.replace(',', '')) if col1 and col1 != "nan" else 3000.0
                except:
                    z = 3000.0
                x = size
                y = size
            else:
                skipped += 1
                skip_reasons["hex_no_size"] = skip_reasons.get("hex_no_size", 0) + 1
                continue
        else:
            # Неизвестный тип
            skipped += 1
            skip_reasons["unknown_type"] = skip_reasons.get("unknown_type", 0) + 1
            continue

        # Валидация
        if x is None or y is None or z is None:
            skipped += 1
            skip_reasons["no_dimensions"] = skip_reasons.get("no_dimensions", 0) + 1
            continue

        if x <= 0 or y <= 0 or z <= 0:
            skipped += 1
            skip_reasons["invalid_dimensions"] = skip_reasons.get("invalid_dimensions", 0) + 1
            continue

        quantity = int(col3) if col3 >= 1 else 1

        item = {
            "index": idx,
            "grade": grade,
            "shape": shape,
            "shape_type": shape_type,
            "col0": col0[:70],
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "quantity": quantity
        }
        items.append(item)
        stats[shape_type] = stats.get(shape_type, 0) + 1

    except Exception as e:
        skipped += 1
        skip_reasons[f"error_{str(e)[:30]}"] = skip_reasons.get(f"error_{str(e)[:30]}", 0) + 1

print(f"Extracted {len(items)} items, skipped {skipped}")
print(f"\nShape statistics:")
for shape_type, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  {shape_type}: {count}")

print(f"\nSkip reasons:")
for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1])[:10]:
    print(f"  {reason}: {count}")

# Сохранить
with open('excel_correct_all.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"\nSaved ALL {len(items)} items to excel_correct_all.json")

# Статистика
blocks = [i for i in items if i['shape'] == 'block']
plates = [i for i in items if i['shape'] == 'plate']
rods = [i for i in items if i['shape'] == 'rod']

print(f"\nDatabase categorization:")
print(f"  Blocks (for 3D cutting): {len(blocks)}")
print(f"  Plates (for bot): {len(plates)}")
print(f"  Rods (for bot): {len(rods)}")

if items:
    print(f"\nDimension ranges:")
    xs = [i['x'] for i in items]
    ys = [i['y'] for i in items]
    zs = [i['z'] for i in items]
    print(f"  X: {min(xs):.1f} - {max(xs):.1f} mm")
    print(f"  Y: {min(ys):.1f} - {max(ys):.1f} mm")
    print(f"  Z: {min(zs):.1f} - {max(zs):.1f} mm")

print(f"\nREADY FOR MIGRATION!")
