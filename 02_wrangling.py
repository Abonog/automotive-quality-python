"""
Step 2 — Wrangling

Combines the two cleaned quarters into one full-year dataset, joins in
part and supplier context, adds a derived risk column, and builds two
pivot table summaries. Each step prints a verification check rather than
assuming the previous step worked.

Output: data/processed/inspections_full.csv — one row per inspection,
        enriched with part_name, category, supplier_name, quantity_flag,
        and risk_level. This is the file scripts/03_visualization.py reads.
"""

import pandas as pd

IN_DIR = "data/processed"
RAW_DIR = "data"


def assess_risk(row) -> str:
    """Combine the quantity flag, result, and severity into one risk label."""
    if row["quantity_flag"] != "Valid":
        return "Data Issue"
    elif row["result"] == "Fail" and row["severity"] in ["High", "Critical"]:
        return "High Risk"
    elif row["result"] == "Fail":
        return "Moderate Risk"
    else:
        return "Low Risk"


def main():
    # --- Concat: stack Q1 and Q2 into one full-year dataset ---
    df_q1 = pd.read_csv(f"{IN_DIR}/inspections_q1_clean.csv")
    df_q2 = pd.read_csv(f"{IN_DIR}/inspections_q2_clean.csv")
    df_all = pd.concat([df_q1, df_q2], ignore_index=True)
    assert len(df_all) == len(df_q1) + len(df_q2), "concat row count mismatch"
    print(f"Concat: {len(df_q1)} + {len(df_q2)} = {len(df_all)} rows")

    # --- Merge: bring in part and supplier context ---
    parts = pd.read_csv(f"{RAW_DIR}/parts.csv")
    suppliers = pd.read_csv(f"{RAW_DIR}/suppliers.csv")
    df_merged = df_all.merge(parts, on="part_id", how="left").merge(
        suppliers, on="supplier_id", how="left"
    )
    print(f"Merge: {df_merged.shape[0]} rows, "
          f"missing part_name: {df_merged['part_name'].isna().sum()}, "
          f"missing supplier_name: {df_merged['supplier_name'].isna().sum()}")

    # --- Apply: derive a single risk_level column, row by row ---
    df_merged["risk_level"] = df_merged.apply(assess_risk, axis=1)
    print("Risk level breakdown:")
    print(df_merged["risk_level"].value_counts().to_string())

    # --- Explode: one row per individual defect type (used for the pivots below) ---
    df_exploded = df_merged.copy()
    df_exploded["defect_types"] = df_exploded["defect_types"].str.split(", ")
    df_exploded = df_exploded.explode("defect_types")
    print(f"\nExplode: {df_merged.shape[0]} inspections -> {df_exploded.shape[0]} "
          f"defect rows ({df_exploded['inspection_id'].nunique()} distinct "
          f"inspections, unchanged)")

    # --- Pivot 1: supplier x severity — inspection-level, must use df_merged ---
    # severity describes the whole inspection, not each individual defect;
    # pivoting it on the exploded table double-counts multi-defect inspections
    pivot_severity = pd.pivot_table(
        df_merged, index="supplier_name", columns="severity",
        values="inspection_id", aggfunc="count", fill_value=0,
    )
    print("\nSupplier x severity (df_merged, correct):")
    print(pivot_severity.to_string())

    # --- Pivot 2: category x month — also inspection-level ---
    df_merged["inspection_date"] = pd.to_datetime(df_merged["inspection_date"])
    df_merged["month"] = df_merged["inspection_date"].dt.month
    pivot_month = pd.pivot_table(
        df_merged, index="category", columns="month",
        values="inspection_id", aggfunc="count", fill_value=0,
    )
    print("\nCategory x month:")
    print(pivot_month.to_string())

    df_merged.to_csv(f"{IN_DIR}/inspections_full.csv", index=False)
    print(f"\nSaved: {IN_DIR}/inspections_full.csv ({len(df_merged)} rows)")


if __name__ == "__main__":
    main()
