import csv
import re
import difflib
import random
from datetime import datetime, timedelta
from faker import Faker
import spacy

nlp = spacy.load('en_core_web_sm')
fake = Faker()

with open("combined_deduplicated.csv", "r", encoding="utf-8") as f:
    orig_rows = list(csv.DictReader(f))

with open("combined_deduplicated_redacted.csv", "r", encoding="utf-8") as f:
    red_rows = list(csv.DictReader(f))

oregon_cities = [
    "Portland", "Eugene", "Salem", "Gresham", "Hillsboro", "Bend",
    "Beaverton", "Medford", "Springfield", "Corvallis", "Albany",
    "Tigard", "Lake Oswego", "Keizer", "Grants Pass", "Oregon City",
    "McMinnville", "Redmond", "Tualatin", "West Linn"
]

bad_orgs = {"llc", "inc", "inc.", "corp", "corp.", "company", "co.", "co", "ltd", "ltd.", "llp", "pllc"}

def format_fake_date_like(original_str):
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2026, 12, 31)
    fake_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    
    orig = original_str.strip()
    is_lower = orig.islower()
    is_upper = orig.isupper()
    
    if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', orig):
        if '/' in orig:
            if re.search(r'\d{4}', orig):
                res = fake_date.strftime("%m/%d/%Y")
            else:
                res = fake_date.strftime("%m/%d/%y")
        elif '-' in orig:
            if re.search(r'\d{4}', orig):
                res = fake_date.strftime("%m-%d-%Y")
            else:
                res = fake_date.strftime("%m-%d-%y")
        else:
            res = fake_date.strftime("%m/%d/%Y")
            
        if not re.search(r'0\d', orig):
            res = re.sub(r'(^|/)0', r'\1', res)
            res = re.sub(r'(^|-)0', r'\1', res)
        return res

    month_names = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
    month_abbrs = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    
    orig_lower = orig.lower()
    has_full_month = any(m in orig_lower for m in month_names)
    has_abbr_month = any(m in orig_lower for m in month_abbrs)
    has_year = bool(re.search(r'\d{4}', orig))
    has_day = bool(re.search(r'\d{1,2}', re.sub(r'\d{4}', '', orig)))
    
    fmt = ""
    if has_full_month:
        fmt += "%B "
    elif has_abbr_month:
        fmt += "%b "
        
    if has_day:
        fmt += "%d"
        if ',' in orig:
            fmt += ", "
        else:
            fmt += " "
            
    if has_year:
        fmt += "%Y"
        
    if not fmt:
        return fake_date.strftime("%Y-%m-%d")
        
    res = fake_date.strftime(fmt.strip())
    res = res.replace(' 0', ' ')
    
    if re.search(r'\d+(st|nd|rd|th)', orig_lower):
        day = fake_date.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suf = "th"
        else:
            suf = ["st", "nd", "rd"][day % 10 - 1]
        res = re.sub(r'(\d+)', r'\1' + suf, res, count=1)
        
    if is_lower:
        res = res.lower()
    elif is_upper:
        res = res.upper()
    else:
        if any(c.isupper() for c in orig):
            res = res.title()
            
    return res

output_rows = []
for orig, red in zip(orig_rows, red_rows):
    orig_q = orig['question']
    red_q = red['question']
    
    tokens_orig = [t for t in re.split(r'(\s+)', orig_q) if t]
    tokens_red = [t for t in re.split(r'(\s+)', red_q) if t]
    
    sm = difflib.SequenceMatcher(None, tokens_orig, tokens_red, autojunk=False)
    
    new_tokens_red = []
    
    for opcode, i1, i2, j1, j2 in sm.get_opcodes():
        orig_segment = "".join(tokens_orig[i1:i2])
        red_segment = "".join(tokens_red[j1:j2])
        
        if opcode == 'replace' and re.search(r'\d{4}-\d{2}-\d{2}', red_segment):
            new_date = format_fake_date_like(orig_segment)
            new_seg = re.sub(r'\d{4}-\d{2}-\d{2}', new_date, red_segment)
            new_tokens_red.append(new_seg)
        elif opcode in ['equal', 'insert', 'replace']:
            new_tokens_red.append(red_segment)
            
    red_q_fixed_dates = "".join(new_tokens_red)
    
    doc = nlp(red_q_fixed_dates)
    entities = [(ent.start_char, ent.end_char, ent.label_, ent.text) for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE', 'LOC']]
    
    red_final = red_q_fixed_dates
    for start, end, label, text in reversed(entities):
        if text in oregon_cities:
            continue
            
        if label == 'ORG' and text.lower().strip() in bad_orgs:
            continue
            
        if label == 'PERSON':
            repl = fake.name()
        elif label == 'ORG':
            repl = fake.company()
        elif label in ['GPE', 'LOC']:
            repl = random.choice(oregon_cities)
        else:
            repl = text
            
        red_final = red_final[:start] + repl + red_final[end:]
        
    out_row = red.copy()
    out_row['question'] = red_final
    output_rows.append(out_row)

with open('combined_deduplicated_redacted_v4.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=orig_rows[0].keys())
    writer.writeheader()
    writer.writerows(output_rows)

print("Created combined_deduplicated_redacted_v4.csv")
