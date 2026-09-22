"""
Step 3 — Visualization

Six matplotlib charts built on the wrangled data, using a colorblind-safe
(Okabe-Ito) palette throughout instead of matplotlib's default color cycle.
Each chart is saved to charts/ and most are paired with a printed number
that either confirms or complicates what the chart seems to show — several
of these charts are only trustworthy once you know that two specific rows
(the flagged business-rule violations, quantity_defective = 117 and 247)
are extreme outliers that distort anything computed on the raw column.

Run after 02_wrangling.py.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

IN_DIR = "data/processed"
OUT_DIR = "charts"
OKABE_ITO = ["#0072B2", "#E69F00", "#D55E00", "#56B4E9", "#009E73", "#CC79A7"]


def main():
    df = pd.read_csv(f"{IN_DIR}/inspections_full.csv")

    # --- 1. Bar chart: inspections by risk level ---
    counts = df["risk_level"].value_counts()
    plt.figure(figsize=(8, 5))
    plt.bar(counts.index, counts.values, color=OKABE_ITO[:4])
    plt.title("Inspections by Risk Level")
    plt.xlabel("Risk Level")
    plt.ylabel("Number of Inspections")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/01_bar_risk_level.png", dpi=120)
    plt.close()

    # --- 2. Histogram: distribution of quantity_defective, zoomed to the real range ---
    print(f"quantity_defective range: {df['quantity_defective'].min()} to "
          f"{df['quantity_defective'].max()} — two extreme outliers force a "
          f"zoomed range=(0, 30) to see the real shape")
    plt.figure(figsize=(8, 5))
    plt.hist(df["quantity_defective"], bins=20, range=(0, 30),
              color=OKABE_ITO[0], edgecolor="white")
    plt.title("Distribution of Defective Quantities (0-30 range)")
    plt.xlabel("Quantity Defective")
    plt.ylabel("Number of Inspections")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/02_histogram_defects.png", dpi=120)
    plt.close()

    # --- 3. Box plot: quantity_defective by supplier ---
    suppliers_list = sorted(df["supplier_name"].dropna().unique())
    data_by_supplier = [df[df["supplier_name"] == s]["quantity_defective"]
                         for s in suppliers_list]
    iqr_by_supplier = {
        s: (d.quantile(0.75) - d.quantile(0.25)) for s, d in zip(suppliers_list, data_by_supplier)
    }
    print(f"IQR by supplier (box height, the robust consistency measure): {iqr_by_supplier}")
    plt.figure(figsize=(9, 5))
    plt.boxplot(data_by_supplier, tick_labels=suppliers_list)
    plt.title("Defective Quantity by Supplier")
    plt.xlabel("Supplier")
    plt.ylabel("Quantity Defective")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/03_boxplot_supplier.png", dpi=120)
    plt.close()

    # --- 4. Pie chart: severity share (of inspections that had a defect) ---
    sev_counts = df["severity"].value_counts()
    print(f"severity pie covers {sev_counts.sum()} of {len(df)} inspections — "
          f".value_counts() drops the {len(df) - sev_counts.sum()} rows with no "
          f"defect (severity is only set when there's a defect to rate)")
    plt.figure(figsize=(7, 7))
    plt.pie(sev_counts.values, labels=sev_counts.index, autopct="%1.1f%%",
            colors=OKABE_ITO[:4])
    plt.title("Defect Severity Share (of flagged defects, not all inspections)")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/04_piechart_severity.png", dpi=120)
    plt.close()

    # --- 5. Scatter: quantity_inspected vs quantity_defective, with correlation ---
    corr_all = df["quantity_inspected"].corr(df["quantity_defective"])
    clean = df[
        (df["quantity_defective"] >= 0)
        & (df["quantity_defective"] <= df["quantity_inspected"])
    ]
    corr_clean = clean["quantity_inspected"].corr(clean["quantity_defective"])
    print(f"correlation (all 213 rows): {corr_all:.3f}  |  "
          f"correlation (195 rows, flagged outliers excluded): {corr_clean:.3f}")
    plt.figure(figsize=(8, 5))
    plt.scatter(df["quantity_inspected"], df["quantity_defective"],
                color=OKABE_ITO[0], alpha=0.6)
    plt.title("Quantity Defective vs. Quantity Inspected")
    plt.xlabel("Quantity Inspected")
    plt.ylabel("Quantity Defective")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/05_scatter_inspected_vs_defective.png", dpi=120)
    plt.close()

    # --- 6. Capstone dashboard: four of the above combined into one figure ---
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    axes[0, 0].bar(counts.index, counts.values, color=OKABE_ITO[:4])
    axes[0, 0].set_title("Inspections by Risk Level")
    axes[0, 0].set_ylabel("Number of Inspections")
    axes[0, 0].tick_params(axis="x", rotation=20)

    axes[0, 1].hist(df["quantity_defective"], bins=20, range=(0, 30),
                     color=OKABE_ITO[0], edgecolor="white")
    axes[0, 1].set_title("Distribution of Defective Quantities (0-30)")
    axes[0, 1].set_xlabel("Quantity Defective")
    axes[0, 1].set_ylabel("Number of Inspections")

    axes[1, 0].boxplot(data_by_supplier, tick_labels=suppliers_list)
    axes[1, 0].set_title("Defective Quantity by Supplier")
    axes[1, 0].set_ylabel("Quantity Defective")
    axes[1, 0].tick_params(axis="x", rotation=30)

    axes[1, 1].pie(sev_counts.values, labels=sev_counts.index, autopct="%1.1f%%",
                    colors=OKABE_ITO[:4])
    axes[1, 1].set_title("Defect Severity Share (of flagged defects)")

    fig.suptitle("Q1-Q2 2026 Quality Inspection Dashboard", fontsize=16)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/06_dashboard_subplots.png", dpi=120)
    plt.close()

    print(f"\nSaved 6 charts to {OUT_DIR}/")


if __name__ == "__main__":
    main()
