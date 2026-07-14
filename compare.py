import pandas as pd
import sys

df_review = pd.read_excel('redaction_review_v5.xlsx')
df_reviewed = pd.read_excel('redaction_reviewed_v5.xlsx')

col_e = df_reviewed.columns[4]
df_reviewed[col_e] = df_reviewed[col_e].fillna('').astype(str).str.strip().str.lower()
edited_rows = df_reviewed[df_reviewed[col_e].isin(['e', 'edited'])]

diffs = []
for idx, row_reviewed in edited_rows.iterrows():
    # Attempt to find the corresponding row in df_review. We can match on Original Question
    orig_q = row_reviewed['Original Question']
    
    # find in df_review
    match = df_review[df_review['Original Question'] == orig_q]
    if not match.empty:
        old_redaction = match.iloc[0]['Redacted Question (v5)']
        new_redaction = row_reviewed['Redacted Question (v5)']
        if old_redaction != new_redaction:
            diffs.append({
                'Original': orig_q,
                'Old Redaction': old_redaction,
                'New Redaction': new_redaction
            })

print(f"Found {len(diffs)} edited rows with actual changes in the redaction.")
for i, d in enumerate(diffs[:20]):
    print(f"\n--- Change {i+1} ---")
    print(f"Original       : {d['Original']}")
    print(f"Old Redaction  : {d['Old Redaction']}")
    print(f"New Redaction  : {d['New Redaction']}")

