# SpendLens — Procurement Spend Intelligence Platform

> *Upload any ERP PO export. Get Pareto/ABC, UNSPSC taxonomy, Supplier Concentration Ratios, Kraljic Matrix positioning, and prioritised sourcing actions — in 60 seconds.*

---

## The Problem It Solves

Every procurement team exports PO data from SAP/Oracle/ERP into Excel and spends 2-3 days manually:
1. Cleaning and categorising line items
2. Running Pareto analysis on suppliers
3. Plotting the Kraljic Matrix in PowerPoint
4. Writing action recommendations

**Manual spend classification achieves only 70–80% accuracy** and degrades over time (Suplari, 2026). SpendLens automates the entire workflow deterministically — no black-box AI, every formula is documented and citable.

---

## Analytical Frameworks Implemented

| Framework | Source | How SpendLens applies it |
|---|---|---|
| **Pareto / ABC Analysis** | Monczka, Handfield et al. (2019) *Purchasing and Supply Chain Management*, 7th Ed., Cengage | Class A/B/C supplier segmentation by cumulative spend |
| **UNSPSC Taxonomy** | UNDP/GS1 — UNSPSC v24.0301 | Automatic line-item classification into spend segments |
| **Supplier Concentration Ratio (CR-n)** | Standard industrial organisation economics | CR-3 per category to detect fragmentation and consolidation opportunity |
| **Kraljic Portfolio Matrix** | Kraljic, P. (1983). *HBR*, 61(5), 109–117 | 2×2 matrix: Profit Impact × Supply Risk → quadrant + recommended strategy |
| **Spend Under Management (SUM)** | Hackett Group (2024) Procurement Key Issues Study | % of spend through contracted/preferred suppliers vs. 80% world-class benchmark |

---

## Setup

```bash
# 1. Clone or download
cd spendlens

# 2. Install
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

---

## Datasets to Download

### Option A — Kaggle (easiest, no account needed for some)

| Dataset | URL | Why useful |
|---|---|---|
| Procurement KPI Analysis | https://www.kaggle.com/datasets/shahriarkabir/procurement-kpi-analysis-dataset | Supplier performance + spend KPIs |
| Company Purchasing Dataset | https://www.kaggle.com/datasets/shahriarkabir/company-purchasing-dataset | Purchase orders with categories |
| Spend Analytics | https://www.kaggle.com/datasets/mukeshmanral/spend-analytics | Raw spend data for analysis |
| SF Purchasing Commodity | https://www.kaggle.com/san-francisco/sf-purchasing-commodity-data | Real government procurement data |
| Government Procurement 2015-2021 | https://www.kaggle.com/datasets/shivamb/government-procurement-dataset | Multi-year PO history |

### Option B — USASpending.gov (real federal procurement data, public domain)

1. Go to: **https://www.usaspending.gov/download_center/award_data_archive**
2. Select: Award Type = **Contracts**
3. Select: Fiscal Year = **2024**
4. Select: Agency = e.g., **Department of Defense** or **General Services Administration**
5. Download CSV (free, no account required)
6. Relevant columns: `recipient_name`, `award_amount`, `naics_description`, `primary_place_of_performance_country_code`

Map to SpendLens format:
```
recipient_name        → supplier_name
award_amount          → amount  
naics_description     → line_item_description
```

### Option C — Built-in sample data
The app includes a realistic 300-row sample dataset for a mid-size manufacturer.
Toggle "Use sample dataset" ON in the sidebar — no file upload needed.

---

## CSV Format (your own data)

**Required columns:**
```
supplier_name          | string  | Supplier/vendor name
amount                 | numeric | PO line item amount (USD or any currency)
```

**Optional columns (enrich the analysis):**
```
line_item_description  | string  | Item description (used for UNSPSC classification)
category               | string  | Pre-existing category (skips UNSPSC classification)
preferred_supplier     | Y/N     | Enables Spend Under Management calculation
po_date                | date    | Purchase order date
country                | string  | ISO 2-letter country code (supplier country)
```

---


## References

- Kraljic, P. (1983). Purchasing must become supply management. *Harvard Business Review*, 61(5), 109–117.
- Monczka, R., Handfield, R., Giunipero, L. & Patterson, J. (2019). *Purchasing and Supply Chain Management* (7th ed.). Cengage Learning.
- UNDP/GS1. (2024). *UNSPSC v24.0301 — United Nations Standard Products and Services Code*. unspsc.org
- The Hackett Group. (2024). *Procurement Key Issues Study*. thehackettgroup.com
- Suplari. (2026). *Spend Analysis Explained*. suplari.com

---

**Built by Rutwik Satish** · MS Engineering Management, Northeastern University · May 2026  
[linkedin.com/in/rutwiksatish](https://linkedin.com/in/rutwiksatish)
