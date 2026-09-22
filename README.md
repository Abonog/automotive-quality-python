# Automotive Quality Data — Python (pandas & matplotlib) Analysis

A Python/pandas project built on the same realistic (synthetic) automotive manufacturing quality data as [`automotive-quality-sql`](../automotive-quality-sql) — supplier inspections and defects — this time cleaned, wrangled, and visualized end-to-end with pandas and matplotlib instead of SQL.

I currently work as a Quality Engineer in the automotive industry. This project takes the same kind of messy, real-world inspection data I work with and runs it through a full analyst workflow: clean it, combine it, join in context, derive a risk signal, and visualize it — while treating every chart and every summary statistic as something to verify, not just something to look at and trust.

## Contents

- **`data/`** — the four raw source files: two quarterly inspection files (`inspections_q1_2026.csv`, `inspections_q2_2026.csv`), `suppliers.csv`, and `parts.csv`. `data/processed/` holds the cleaned and merged outputs each script produces.
- **`scripts/01_cleaning.py`** — cleans Q1 and Q2 independently.
- **`scripts/02_wrangling.py`** — combines, joins, derives a risk column, and builds two pivot tables.
- **`scripts/03_visualization.py`** — builds all six charts below and saves them to `charts/`.
- **`charts/`** — the rendered PNG output of the visualization script.

Run in order: `python scripts/01_cleaning.py && python scripts/02_wrangling.py && python scripts/03_visualization.py`

## Part 1 — Cleaning

Both quarterly files have the same real-world problems, on purpose: inconsistent casing/whitespace in `plant` and `result` (dozens of spellings of the same 3 plants), missing `inspector_name` values (some true blanks, some placeholder text like `'unknown'`), `quantity_inspected` stored as text (`"473 units"`) in a handful of rows, a few exact duplicate rows, and — the one that mattered most for everything downstream — **invalid `quantity_defective` values**: negative counts, and counts that exceed the number of units actually inspected. Those are flagged with a `quantity_flag` column rather than silently dropped or corrected, because a real analyst needs to be able to trace and question a data quality issue, not have it disappear.

That decision to flag-not-delete turned out to matter a lot: two of those flagged rows (`quantity_defective` = 117 and 247) are extreme enough to distort nearly every summary statistic computed on the raw column later in this project.

## Part 2 — Wrangling

The cleaned quarters are concatenated into one 213-row full-year dataset, then joined to `parts` and `suppliers` so every inspection carries its part name, category, and supplier. A custom `assess_risk()` function is applied row-by-row to derive a single `risk_level` per inspection (combining the data-quality flag, the pass/fail result, and severity):

| Risk Level | Count |
|---|---|
| Low Risk | 160 |
| Moderate Risk | 22 |
| Data Issue | 18 |
| High Risk | 13 |

Two pivot tables summarize the data by supplier × severity and category × month — both built deliberately on the *inspection-level* table (one row per inspection), not the exploded *defect-level* table (one row per individual defect a multi-defect inspection has). That distinction matters: `severity` describes a whole inspection, so pivoting it on the exploded table double-counts any inspection with more than one defect type. Getting this wrong first, then catching and fixing it, showed OmegaFasteners and GammaPlastics are actually tied at 4 High/Critical-severity inspections each — not one clear standout, which a hastily-built version of this table had initially suggested.

## Part 3 — Visualization

Six charts, all built with an explicit colorblind-safe palette (Okabe-Ito) rather than matplotlib's default color cycle:

| Chart | File | What it shows |
|---|---|---|
| Bar | [`01_bar_risk_level.png`](charts/01_bar_risk_level.png) | Risk level counts — see table above. |
| Histogram | [`02_histogram_defects.png`](charts/02_histogram_defects.png) | Distribution of `quantity_defective`, zoomed to `range=(0, 30)`. Without the zoom, the two outlier rows (117, 247) stretch the bins so far that almost all 20 bins are empty and the real shape disappears. |
| Box plot | [`03_boxplot_supplier.png`](charts/03_boxplot_supplier.png) | `quantity_defective` by supplier. Every supplier's typical spread (box height / IQR) is similar — around 6.5 to 8.5 — despite AlphaMetal and OmegaFasteners visually dominating the chart with their outlier dots at 117 and 247. |
| Pie | [`04_piechart_severity.png`](charts/04_piechart_severity.png) | Severity share — but only of the 40 inspections that had a defect at all (`.value_counts()` silently drops the 173 rows with no `severity` set, since it's only assigned when there's a defect to rate). |
| Scatter | [`05_scatter_inspected_vs_defective.png`](charts/05_scatter_inspected_vs_defective.png) | `quantity_inspected` vs. `quantity_defective`. Correlation on the raw 213 rows is a near-zero 0.057 — which looks like "no relationship" — but excluding the two flagged outlier rows brings it to a real, moderate 0.534. The two numbers tell opposite stories; only the chart makes clear which one is true. |
| Dashboard | [`06_dashboard_subplots.png`](charts/06_dashboard_subplots.png) | Four of the above combined into one 2×2 figure — a single at-a-glance quality summary. |

## Lessons that came out of building this

- **A couple of outliers can flip a summary statistic's story entirely.** The quantity_inspected/quantity_defective correlation goes from "basically nothing" (0.057) to "a real relationship" (0.534) depending on whether two known-bad rows are included — a reminder to never trust a single number like a correlation coefficient without also looking at the chart it came from.
- **Row-level vs. group-level matters for which table you pivot on.** `severity` is one value per inspection; pivoting it on a defect-exploded table (one row per defect) inflates the count for any inspection with multiple defect types. The fix is choosing the right base table for the question being asked, not a chart-formatting fix.
- **`.value_counts()` and similar aggregations silently drop missing values.** A pie chart or count built this way only covers the rows that had something to count — worth stating explicitly in a title or caption, or the reader will assume it covers everything.
- **Flag data quality issues instead of deleting them.** Keeping the two invalid `quantity_defective` rows (rather than dropping them during cleaning) is what made it possible to trace their effect on every downstream statistic — deleting them early would have hidden a real, useful finding.

## Tech

Python 3, pandas, numpy, matplotlib. No dependencies beyond the standard data-science stack (`pip install pandas numpy matplotlib`).
