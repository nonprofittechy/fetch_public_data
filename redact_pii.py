import csv
import random
import re
import sys

from faker import Faker
from opf._api import OPF

# Oregon cities list
oregon_cities = [
    "Eugene", "Salem", "Gresham", "Hillsboro", "Beaverton", "Bend", 
    "Medford", "Springfield", "Corvallis", "Albany", "Tigard", "Lake Oswego", 
    "Keizer", "Grants Pass", "Oregon City", "McMinnville", "Redmond", 
    "Tualatin", "West Linn", "Woodburn", "Newberg", "Roseburg", "Forest Grove",
    "Klamath Falls", "Milwaukie", "Ashland", "Wilsonville", "Sherwood", 
    "Central Point", "Hermiston", "Pendleton", "Coos Bay", "Troutdale"
]

faker = Faker('en_US')
faker.seed_instance(42)
random.seed(42)

opf = OPF(output_text_only=False, device='cpu')

def is_business_name(text):
    text = text.lower()
    business_keywords = ['llc', 'inc', 'co', 'corp', 'corporation', 'company', 'clinic', 'hospital', 'center', 'restaurant', 'bank', 'store', 'shop', 'services', 'agency', 'associates', 'group', 'partners']
    return any(keyword in text for keyword in business_keywords)

def get_business_suffix(text):
    text = text.lower()
    if 'clinic' in text: return 'Clinic'
    if 'hospital' in text: return 'Hospital'
    if 'center' in text: return 'Center'
    if 'restaurant' in text: return 'Restaurant'
    if 'bank' in text: return 'Bank'
    if 'llc' in text: return 'LLC'
    if 'inc' in text: return 'Inc'
    return ''

def replace_span(span):
    label = span.label
    text = span.text

    if label == 'private_person':
        if is_business_name(text):
            suffix = get_business_suffix(text)
            fake_company = faker.company()
            if suffix and not is_business_name(fake_company):
                fake_company += ' ' + suffix
            return fake_company
        else:
            return faker.name()
    elif label == 'private_address':
        if 'portland' in text.lower():
            if any(char.isdigit() for char in text):
                return f"{faker.street_address()}, Portland, OR {faker.postcode()}"
            else:
                return "Portland"
        else:
            if any(char.isdigit() for char in text):
                city = random.choice(oregon_cities)
                return f"{faker.street_address()}, {city}, OR {faker.postcode()}"
            else:
                return random.choice(oregon_cities)
    elif label == 'private_phone':
        return faker.phone_number()
    elif label == 'private_email':
        return faker.email()
    elif label == 'private_url':
        return faker.url()
    elif label == 'private_date':
        return faker.date()
    elif label in ['account_number', 'secret']:
        return faker.bban()
    else:
        return "***REDACTED***"

rows = []
with open('combined_deduplicated.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for i, row in enumerate(reader):
        question = row['question']
        try:
            result = opf.redact(question)
            spans = result.detected_spans
            if spans:
                redacted_q = list(question)
                for span in sorted(spans, key=lambda s: s.start, reverse=True):
                    replacement = replace_span(span)
                    redacted_q[span.start:span.end] = list(replacement)
                row['question'] = "".join(redacted_q)
        except Exception as e:
            print(f"Error redacting row {i}: {e}", file=sys.stderr)
        rows.append(row)

with open('combined_deduplicated_redacted.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Successfully redacted {len(rows)} rows.")
