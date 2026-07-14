import pandas as pd
import sys

try:
    df_review = pd.read_excel('redaction_review_v5.xlsx')
    df_reviewed = pd.read_excel('redaction_reviewed_v5.xlsx')

    print("Columns in review:", df_review.columns.tolist())
    print("Columns in reviewed:", df_reviewed.columns.tolist())

    print("\nFirst few rows of reviewed where column E has 'e' or 'edited':")
    col_e = df_reviewed.columns[4]
    
    # Fill nan with empty string for string operations
    df_reviewed[col_e] = df_reviewed[col_e].fillna('').astype(str).str.strip().str.lower()
    edited_rows = df_reviewed[df_reviewed[col_e].isin(['e', 'edited'])]
    
    print(f"Found {len(edited_rows)} edited rows.")
    for idx, row in edited_rows.head(5).iterrows():
        print(f"\n--- Row {idx} ---")
        for k, v in row.to_dict().items():
            print(f"{k}: {v}")

except Exception as e:
    print(f"Error: {e}")
