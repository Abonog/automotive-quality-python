"""
Step 1 — Cleaning

Cleans the two raw quarterly inspection files independently (Q1 and Q2),
before they're ever combined. Each file has the same five real-world data
quality problems, deliberately built in:

  - inconsistent casing/whitespace in `plant` and `result`
    (e.g. 'Plant_De1', '  PLANT_TR1 ', 'plant_de1' are all the same plant)
  - missing `inspector_name` values, some true blanks, some placeholder
    text ('N/A', 'unknown')
  - `quantity_inspected` stored as a number in most rows, but as text
    like "473 units" in a few — a classic pandas dtype problem
  - invalid `quantity_defective` values: negative, or exceeding the
    quantity inspected (physically impossible, flagged not deleted)
  - a handful of exact duplicate rows

Output: data/processed/inspections_q1_clean.csv,
        data/processed/inspections_q2_clean.csv
"""

import numpy as np
import pandas as pd

RAW_DIR = "data"
OUT_DIR = "data/processed"


def clean_inspections(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- Consistency: standardize plant and result text ---
    df["plant"] = df["plant"].str.strip().str.upper()
    df["plant"] = df["plant"].replace(
        {"PLANT_DE1": "Plant_DE1", "PLANT_TR1": "Plant_TR1", "PLANT_HU1": "Plant_HU1"}
    )
    df["result"] = df["result"].str.strip().str.upper().map(
        {"PASS": "Pass", "FAIL": "Fail"}
    )

    # --- Completeness: turn placeholder text into real missing values ---
    df["inspector_name"] = df["inspector_name"].replace(
        ["N/A", "n/a", "NA", "unknown", "-", ""], pd.NA
    )

    # --- Validity / dtype: quantity_inspected sometimes has " units" text ---
    df["quantity_inspected"] = pd.to_numeric(
        df["quantity_inspected"].astype(str).str.replace(" units", "", regex=False),
        errors="coerce",
    )

    # --- Validity: flag (don't silently drop) physically impossible defect counts ---
    conditions = [
        df["quantity_defective"] < 0,
        df["quantity_defective"] > df["quantity_inspected"],
    ]
    choices = ["Negative defective quantity", "Defective exceeds inspected"]
    df["quantity_flag"] = np.select(conditions, choices, default="Valid")

    # --- Uniqueness: drop exact duplicate rows ---
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)

    print(f"  rows in: {before}, duplicates dropped: {dropped}, rows out: {len(df)}")
    print(f"  quantity_inspected dtype: {df['quantity_inspected'].dtype} "
          f"(missing after coercion: {df['quantity_inspected'].isna().sum()})")
    print(f"  inspector_name missing: {df['inspector_name'].isna().sum()}")
    print(f"  quantity_flag counts:\n{df['quantity_flag'].value_counts().to_string()}")

    return df


def main():
    print("Cleaning Q1...")
    df_q1 = clean_inspections(pd.read_csv(f"{RAW_DIR}/inspections_q1_2026.csv"))
    df_q1.to_csv(f"{OUT_DIR}/inspections_q1_clean.csv", index=False)

    print("\nCleaning Q2...")
    df_q2 = clean_inspections(pd.read_csv(f"{RAW_DIR}/inspections_q2_2026.csv"))
    df_q2.to_csv(f"{OUT_DIR}/inspections_q2_clean.csv", index=False)

    print(f"\nSaved: {OUT_DIR}/inspections_q1_clean.csv ({len(df_q1)} rows), "
          f"{OUT_DIR}/inspections_q2_clean.csv ({len(df_q2)} rows)")


if __name__ == "__main__":
    main()
