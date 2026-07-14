import csv
import difflib
import xlsxwriter
import re

with open("combined_deduplicated.csv", "r", encoding="utf-8") as f:
    orig_rows = list(csv.DictReader(f))

with open("combined_deduplicated_redacted_v4.csv", "r", encoding="utf-8") as f:
    red_rows = list(csv.DictReader(f))

workbook = xlsxwriter.Workbook('redaction_review_v4.xlsx')
worksheet = workbook.add_worksheet()

red_format = workbook.add_format({'font_color': 'red', 'bold': True, 'font_strikeout': True})
green_format = workbook.add_format({'font_color': 'green', 'bold': True})
wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})

worksheet.set_column('A:B', 15)
worksheet.set_column('C:D', 65)

headers = ["Category", "Subcategory", "Original Question", "Redacted Question (v4)"]
header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
for col, h in enumerate(headers):
    worksheet.write(0, col, h, header_format)

def clean_rich(rich_list):
    if not rich_list: return ""
    merged = []
    for item in rich_list:
        if isinstance(item, str):
            if merged and isinstance(merged[-1], str):
                merged[-1] += item
            else:
                merged.append(item)
        else:
            merged.append(item)
            
    if len(merged) == 1 and isinstance(merged[0], str):
        return merged[0]
    if len(merged) == 2 and not isinstance(merged[0], str) and isinstance(merged[1], str):
        merged.append("")
    return merged

for i, (orig, red) in enumerate(zip(orig_rows, red_rows)):
    row_idx = i + 1
    worksheet.write(row_idx, 0, orig['category'], wrap_format)
    worksheet.write(row_idx, 1, orig['subcategory'], wrap_format)

    orig_q = orig['question']
    red_q = red['question']

    if orig_q == red_q:
        worksheet.write(row_idx, 2, orig_q, wrap_format)
        worksheet.write(row_idx, 3, red_q, wrap_format)
        continue

    # Word level diff with autojunk=False
    tokens_orig = [t for t in re.split(r'(\s+)', orig_q) if t]
    tokens_red = [t for t in re.split(r'(\s+)', red_q) if t]

    sm = difflib.SequenceMatcher(None, tokens_orig, tokens_red, autojunk=False)

    orig_rich = []
    red_rich = []

    for opcode, i1, i2, j1, j2 in sm.get_opcodes():
        orig_segment = "".join(tokens_orig[i1:i2])
        red_segment = "".join(tokens_red[j1:j2])
        
        if opcode == 'replace' and orig_segment == red_segment:
            opcode = 'equal'

        if opcode == 'equal':
            if orig_segment: orig_rich.append(orig_segment)
            if red_segment: red_rich.append(red_segment)
        elif opcode == 'replace':
            if orig_segment: orig_rich.extend([red_format, orig_segment])
            if red_segment: red_rich.extend([green_format, red_segment])
        elif opcode == 'delete':
            if orig_segment: orig_rich.extend([red_format, orig_segment])
        elif opcode == 'insert':
            if red_segment: red_rich.extend([green_format, red_segment])

    orig_cleaned = clean_rich(orig_rich)
    if isinstance(orig_cleaned, str):
        worksheet.write(row_idx, 2, orig_cleaned, wrap_format)
    else:
        worksheet.write_rich_string(row_idx, 2, *orig_cleaned, wrap_format)
        
    red_cleaned = clean_rich(red_rich)
    if isinstance(red_cleaned, str):
        worksheet.write(row_idx, 3, red_cleaned, wrap_format)
    else:
        worksheet.write_rich_string(row_idx, 3, *red_cleaned, wrap_format)

workbook.close()
print("Created redaction_review_v4.xlsx")
