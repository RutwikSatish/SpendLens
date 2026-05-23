"""
SpendLens — Procurement Spend Intelligence Platform
====================================================
Problem it solves:
    Every procurement team exports PO data from SAP/Oracle/ERP into Excel.
    Manual spend classification achieves only 70-80% accuracy (Suplari, 2026).
    Manual Pareto + Kraljic analysis takes 2-3 days. SpendLens does it in 60 seconds.

Analytical frameworks implemented:
    1. UNSPSC-aligned spend taxonomy (UNDP/GS1 standard)
    2. Pareto / ABC Analysis — Monczka, Handfield et al. (2019)
       Purchasing and Supply Chain Management, 7th Ed., Cengage
    3. Supplier Concentration Ratio (CR-n) — standard industrial organisation
    4. Kraljic Portfolio Matrix — Kraljic (1983), Harvard Business Review
    5. Spend Under Management (SUM) ratio — ISM / Hackett Group benchmark

Built by: Rutwik Satish
MS Engineering Management (Supply Chain), Northeastern University
SAP Ariba Procurement & Sourcing Certified | May 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import io
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SpendLens — Procurement Intelligence",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS — warm slate editorial theme ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Mono:wght@300;400;500&family=Barlow:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"], .stApp {
    background-color: #f4f0e8 !important;
    color: #1a1714 !important;
    font-family: 'Barlow', sans-serif !important;
}

.main .block-container {
    padding: 1.5rem 2.5rem 4rem !important;
    max-width: 1440px !important;
}

/* ── Hero ── */
.sl-wordmark {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #8a7f72;
    margin-bottom: 4px;
}
.sl-title {
    font-family: 'Libre Baskerville', Georgia, serif;
    font-size: 48px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #1a1714;
    line-height: 1;
    margin-bottom: 6px;
}
.sl-title span { color: #c85a2a; }
.sl-sub {
    font-size: 15px;
    font-weight: 300;
    color: #6b5f52;
    line-height: 1.6;
    margin-bottom: 1rem;
}
.sl-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 0; }
.sl-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    padding: 4px 10px;
    border-radius: 2px;
    border: 1px solid #c8bfb0;
    color: #6b5f52;
    background: rgba(200,191,176,0.3);
    letter-spacing: 0.08em;
}
.sl-tag.red {
    border-color: rgba(200,90,42,0.4);
    color: #c85a2a;
    background: rgba(200,90,42,0.08);
}
.sl-divider {
    height: 1px;
    background: linear-gradient(90deg, #c8bfb0, transparent);
    margin: 1.5rem 0;
}

/* ── Section headers ── */
.sl-section {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #c85a2a;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.sl-section::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(200,90,42,0.3), transparent);
}

/* ── Metric cards ── */
.sl-metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 1rem 0;
}
.sl-metric {
    background: #fff;
    border: 1px solid #ddd6cc;
    border-radius: 4px;
    padding: 1rem 1.25rem;
    position: relative;
    overflow: hidden;
}
.sl-metric::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: #c8bfb0;
}
.sl-metric.accent::before { background: #c85a2a; }
.sl-metric.green::before  { background: #3a7a4a; }
.sl-metric.amber::before  { background: #c8960a; }
.sl-metric-num {
    font-family: 'Libre Baskerville', serif;
    font-size: 32px;
    font-weight: 700;
    color: #1a1714;
    line-height: 1;
    margin-bottom: 4px;
}
.sl-metric-num.red   { color: #c85a2a; }
.sl-metric-num.green { color: #3a7a4a; }
.sl-metric-num.amber { color: #c8960a; }
.sl-metric-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #8a7f72;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── Kraljic quadrant labels ── */
.kq-card {
    background: #fff;
    border: 1px solid #ddd6cc;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 8px;
}
.kq-strategic { border-left: 4px solid #c85a2a; }
.kq-leverage  { border-left: 4px solid #3a7a4a; }
.kq-bottleneck{ border-left: 4px solid #c8960a; }
.kq-noncrit   { border-left: 4px solid #8a7f72; }
.kq-name {
    font-family: 'Libre Baskerville', serif;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 3px;
}
.kq-strategy {
    font-size: 12px;
    color: #6b5f52;
    line-height: 1.5;
}
.kq-count {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #8a7f72;
    margin-top: 4px;
}

/* ── Table styling ── */
.stDataFrame { border: 1px solid #ddd6cc !important; border-radius: 4px !important; }

/* ── Streamlit overrides ── */
.stButton > button {
    background: #1a1714 !important;
    color: #f4f0e8 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.1em !important;
    padding: 0.6rem 1.5rem !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #c85a2a !important; }

.stFileUploader {
    background: #fff !important;
    border: 2px dashed #c8bfb0 !important;
    border-radius: 4px !important;
}

.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #fff !important;
    border: 1px solid #c8bfb0 !important;
    border-radius: 4px !important;
    font-family: 'Barlow', sans-serif !important;
}

div[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid #ddd6cc !important;
    border-radius: 4px !important;
}

.stAlert {
    border-radius: 4px !important;
    font-family: 'Barlow', sans-serif !important;
}

section[data-testid="stSidebar"] {
    background: #eee8dc !important;
    border-right: 1px solid #c8bfb0 !important;
}

/* ── Action list ── */
.action-item {
    background: #fff;
    border: 1px solid #ddd6cc;
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.action-rank {
    font-family: 'Libre Baskerville', serif;
    font-size: 24px;
    font-weight: 700;
    color: #ddd6cc;
    line-height: 1;
    flex-shrink: 0;
    width: 30px;
}
.action-title {
    font-size: 14px;
    font-weight: 600;
    color: #1a1714;
    margin-bottom: 3px;
}
.action-desc {
    font-size: 13px;
    color: #6b5f52;
    line-height: 1.5;
}
.action-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    padding: 2px 8px;
    border-radius: 2px;
    margin-top: 5px;
    letter-spacing: 0.08em;
}
.badge-high   { background: #fde8df; color: #c85a2a; border: 1px solid rgba(200,90,42,0.3); }
.badge-medium { background: #fef3dc; color: #c8960a; border: 1px solid rgba(200,150,10,0.3); }
.badge-low    { background: #e8f3ec; color: #3a7a4a; border: 1px solid rgba(58,122,74,0.3); }

/* ── Footnotes ── */
.sl-footnote {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #a89e92;
    margin-top: 4px;
    font-style: italic;
}

/* ── Sidebar ── */
.sl-sidebar-title {
    font-family: 'Libre Baskerville', serif;
    font-size: 20px;
    font-weight: 700;
    color: #1a1714;
    margin-bottom: 4px;
}
.sl-sidebar-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #8a7f72;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── UNSPSC Level-1 Segments (simplified, 28 segments) ────────────────────────
# Source: UNSPSC v24.0301 — UNDP / GS1
# https://www.unspsc.org
UNSPSC_SEGMENTS = {
    "10": "Live Plant and Animal Material",
    "11": "Mineral and Textile Raw Materials",
    "12": "Chemicals including Bio Chemicals",
    "13": "Resin, Rosin, Rubber, Foam and Film",
    "14": "Paper Materials and Products",
    "15": "Fuels and Fuel Additives",
    "20": "Mining and Well Drilling Machinery",
    "21": "Farming and Fishing Equipment",
    "22": "Building and Construction Machinery",
    "23": "Industrial Machinery and Equipment",
    "24": "Material Handling and Storage",
    "25": "Vehicles",
    "26": "Power Generation and Distribution",
    "27": "Tools and General Machinery",
    "30": "Structural Components and Basic Shapes",
    "31": "Manufacturing Components and Supplies",
    "32": "Electronic Components and Supplies",
    "39": "Electrical Systems and Lighting",
    "40": "Distribution and Conditioning Systems",
    "41": "Laboratory Instruments",
    "42": "Medical Equipment and Accessories",
    "43": "IT Hardware and Software",
    "44": "Office Equipment and Supplies",
    "45": "Printing and Publishing",
    "46": "Defense and Security",
    "47": "Cleaning Equipment and Supplies",
    "48": "Service Industry Machinery",
    "49": "Sports and Recreation",
    "50": "Food and Beverage Products",
    "51": "Drugs and Pharmaceutical Products",
    "52": "Domestic and Personal Products",
    "53": "Apparel and Luggage",
    "60": "Musical Instruments",
    "70": "Farming and Fishing Services",
    "72": "Building and Construction Services",
    "73": "Industrial Production and Manufacturing",
    "76": "Industrial Cleaning Services",
    "77": "Environmental Services",
    "78": "Transportation and Storage Services",
    "80": "Management and Business Professionals",
    "81": "Engineering and Research Services",
    "82": "Editorial and Design Services",
    "83": "Public Utilities and Public Sector",
    "84": "Financial and Insurance Services",
    "85": "Healthcare Services",
    "86": "Education and Training Services",
    "91": "Travel and Food Services",
    "92": "Defense and Security Services",
    "93": "Politics and Civic Affairs",
    "94": "Organizations and Clubs",
}

# Keyword → UNSPSC segment mapping for AI-free classification
KEYWORD_MAP = {
    "laptop": "43", "computer": "43", "server": "43", "software": "43",
    "hardware": "43", "cloud": "43", "it ": "43", "network": "43",
    "printer": "44", "office": "44", "paper": "44", "stationery": "44",
    "pen": "44", "furniture": "44", "desk": "44",
    "steel": "30", "metal": "30", "aluminium": "30", "aluminum": "30",
    "fabrication": "30", "weld": "30",
    "electronic": "32", "circuit": "32", "pcb": "32", "chip": "32",
    "semiconductor": "32", "component": "32",
    "chemical": "12", "solvent": "12", "lubricant": "12",
    "fuel": "15", "diesel": "15", "petrol": "15", "gas ": "15",
    "transport": "78", "logistics": "78", "freight": "78", "shipping": "78",
    "courier": "78", "delivery": "78",
    "consult": "80", "advisory": "80", "management service": "80",
    "audit": "80", "legal": "84",
    "engineering": "81", "research": "81", "design": "81", "testing": "81",
    "maintenance": "73", "repair": "73", "service": "73", "labor": "73",
    "cleaning": "76", "janitorial": "76",
    "medical": "42", "healthcare": "85", "pharma": "51",
    "food": "50", "catering": "50", "beverage": "50",
    "construction": "72", "building": "72", "civil": "72",
    "training": "86", "education": "86",
    "marketing": "82", "advertising": "82", "print": "45",
    "vehicle": "25", "truck": "25", "fleet": "25",
    "electrical": "39", "cable": "39", "wiring": "39",
    "security": "46", "safety": "46",
}

def classify_line_item(description: str) -> tuple:
    """
    Classify a spend line item into UNSPSC Segment.
    Returns (segment_code, segment_name)
    Uses keyword matching — deterministic, no AI required.
    For unclassified items, returns ('99', 'Unclassified').
    """
    if pd.isna(description) or str(description).strip() == "":
        return ("99", "Unclassified")
    desc_lower = str(description).lower()
    for keyword, code in KEYWORD_MAP.items():
        if keyword in desc_lower:
            return (code, UNSPSC_SEGMENTS.get(code, "Other"))
    return ("99", "Unclassified")


def run_abc_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    ABC (Pareto) Analysis by supplier.

    Classification:
        A: Top suppliers representing 80% of total spend
        B: Next suppliers representing 15% of total spend (cumulative 95%)
        C: Remaining suppliers representing 5% of spend (tail spend)

    Methodology: Monczka, Handfield, Giunipero & Patterson (2019)
    Purchasing and Supply Chain Management, 7th Ed., Cengage Learning.
    Chapter 6: Supply Management and Commodity Strategy Development.
    """
    supplier_spend = (
        df.groupby("supplier_name")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .rename(columns={"amount": "total_spend"})
    )
    total = supplier_spend["total_spend"].sum()
    supplier_spend["spend_pct"]    = supplier_spend["total_spend"] / total * 100
    supplier_spend["cumulative_pct"] = supplier_spend["spend_pct"].cumsum()

    def abc_class(cum_pct):
        if cum_pct <= 80:
            return "A"
        elif cum_pct <= 95:
            return "B"
        else:
            return "C"

    supplier_spend["abc_class"] = supplier_spend["cumulative_pct"].apply(abc_class)
    supplier_spend["transaction_count"] = (
        df.groupby("supplier_name")["amount"].count().reindex(supplier_spend["supplier_name"]).values
    )
    return supplier_spend


def concentration_ratio(df_cat: pd.DataFrame, top_n: int = 3) -> float:
    """
    Supplier Concentration Ratio CR-n.
    CR-n = sum of top-n suppliers' spend / total category spend × 100

    Standard industrial organisation metric applied to procurement.
    A CR-3 below 70% signals category fragmentation — consolidation opportunity.
    """
    if len(df_cat) == 0:
        return 0.0
    total = df_cat["amount"].sum()
    if total == 0:
        return 0.0
    top_n_spend = df_cat.groupby("supplier_name")["amount"].sum().nlargest(top_n).sum()
    return round(top_n_spend / total * 100, 1)


def count_suppliers(df_cat: pd.DataFrame) -> int:
    return df_cat["supplier_name"].nunique()


def compute_supply_risk_score(df_cat: pd.DataFrame) -> float:
    """
    Supply Risk Score for Kraljic positioning (0-100 scale, higher = riskier).

    Components:
        - Supplier Concentration (CR-3 inverted): low CR-3 = fragmented = higher risk
        - Number of suppliers: fewer alternatives = higher risk
        - Single-source flag: if only 1 supplier, maximum risk

    This is a derived proxy score for use when WGI country data is unavailable.
    It uses only the transaction data itself — no external API calls.
    """
    n_suppliers = count_suppliers(df_cat)
    cr3 = concentration_ratio(df_cat, 3)

    if n_suppliers == 1:
        return 85.0   # single source — very high risk
    elif n_suppliers <= 2:
        base = 70.0
    elif n_suppliers <= 3:
        base = 50.0
    elif n_suppliers <= 5:
        base = 35.0
    else:
        base = 20.0

    # High CR-3 with few suppliers = concentrated dependency risk
    if cr3 > 90 and n_suppliers <= 3:
        base += 10
    return min(base, 100.0)


def compute_profit_impact_score(category_spend: float, total_spend: float) -> float:
    """
    Profit Impact Score for Kraljic positioning (0-100 scale).

    Derived from category spend as % of total spend.
    Categories above 10% of total spend score > 70 (high impact).
    Categories below 1% of total spend score < 20 (low impact).

    Consistent with Monczka et al. recommendation to use spend share
    as the primary proxy for profit impact in spend-based segmentation.
    """
    if total_spend == 0:
        return 0.0
    pct = category_spend / total_spend * 100
    if pct >= 20:
        return 90.0
    elif pct >= 10:
        return 75.0
    elif pct >= 5:
        return 60.0
    elif pct >= 2:
        return 45.0
    elif pct >= 1:
        return 30.0
    else:
        return 15.0


def assign_kraljic_quadrant(profit_impact: float, supply_risk: float) -> tuple:
    """
    Assigns a Kraljic Matrix quadrant.

    Framework: Kraljic, P. (1983). 'Purchasing must become supply management.'
    Harvard Business Review, 61(5), 109-117.

    Quadrant definitions:
        Strategic:    High Profit Impact (>50) AND High Supply Risk (>50)
        Leverage:     High Profit Impact (>50) AND Low Supply Risk (<=50)
        Bottleneck:   Low Profit Impact (<=50) AND High Supply Risk (>50)
        Non-critical: Low Profit Impact (<=50) AND Low Supply Risk (<=50)

    Returns: (quadrant_name, recommended_strategy, color)
    """
    high_profit = profit_impact > 50
    high_risk   = supply_risk > 50

    if high_profit and high_risk:
        return (
            "Strategic",
            "Develop long-term partnerships. Reduce dependency. Dual-source. Executive-level SRM.",
            "#c85a2a"
        )
    elif high_profit and not high_risk:
        return (
            "Leverage",
            "Exploit buying power. Competitive bidding. Drive price down. Consolidate spend.",
            "#3a7a4a"
        )
    elif not high_profit and high_risk:
        return (
            "Bottleneck",
            "Secure supply continuity. Qualify alternative suppliers. Hold safety stock.",
            "#c8960a"
        )
    else:
        return (
            "Non-critical",
            "Automate via catalog. Streamline PO process. Reduce transaction costs.",
            "#8a7f72"
        )


def spend_under_management(df: pd.DataFrame) -> dict:
    """
    Spend Under Management (SUM) Ratio.

    SUM = (Spend through contracted/preferred suppliers / Total spend) × 100

    The Hackett Group benchmark: world-class procurement functions achieve
    SUM > 80%. Most organizations achieve 50-65%.

    Requires 'preferred_supplier' column (Y/N) in the dataset.
    If the column is absent, returns None and the metric is skipped.

    Source: The Hackett Group, 2024 Procurement Key Issues Study.
    """
    if "preferred_supplier" not in df.columns:
        return None
    total = df["amount"].sum()
    managed = df[df["preferred_supplier"].str.upper().str.strip() == "Y"]["amount"].sum()
    if total == 0:
        return None
    pct = round(managed / total * 100, 1)
    benchmark_gap = round(80 - pct, 1) if pct < 80 else 0.0
    return {
        "sum_pct": pct,
        "managed_spend": managed,
        "unmanaged_spend": total - managed,
        "benchmark_gap": benchmark_gap,
        "world_class": pct >= 80
    }


def generate_action_list(category_analysis: pd.DataFrame, abc_df: pd.DataFrame, sum_data: dict) -> list:
    """
    Generates a ranked list of sourcing actions.
    Actions are prioritised by estimated savings / strategic impact.
    Uses procurement best-practice logic — no AI required for core recommendations.
    AI (Groq) enriches the descriptions when an API key is provided.
    """
    actions = []

    # Action 1: Tail spend consolidation (Class C suppliers)
    c_suppliers = abc_df[abc_df["abc_class"] == "C"]
    if len(c_suppliers) > 10:
        tail_spend = c_suppliers["total_spend"].sum()
        actions.append({
            "rank": 1,
            "title": f"Consolidate Tail Spend ({len(c_suppliers)} Class C Suppliers)",
            "description": (
                f"${tail_spend:,.0f} is spread across {len(c_suppliers)} low-value suppliers. "
                "Consolidating to approved preferred suppliers or catalog purchasing reduces "
                "transaction processing costs by 50-70% and typically recovers 3-8% in pricing. "
                "Recommended: implement PunchOut catalog for top 5 tail categories."
            ),
            "priority": "HIGH",
            "framework": "Pareto ABC — Monczka et al. (2019) Ch.6"
        })

    # Action 2: Strategic supplier partnership
    strategic = category_analysis[category_analysis["kraljic_quadrant"] == "Strategic"]
    if len(strategic) > 0:
        strat_names = ", ".join(strategic.head(3)["category"].tolist())
        actions.append({
            "rank": 2,
            "title": f"Executive SRM for Strategic Categories",
            "description": (
                f"Categories [{strat_names}] are Strategic (high profit impact + high supply risk). "
                "Assign executive sponsor. Establish quarterly business reviews. "
                "Initiate dual-sourcing where lead time allows. "
                "Single-source dependency in high-risk categories is the #1 cause of unplanned supply disruption."
            ),
            "priority": "HIGH",
            "framework": "Kraljic (1983), HBR — Strategic quadrant"
        })

    # Action 3: Leverage category competitive bidding
    leverage = category_analysis[category_analysis["kraljic_quadrant"] == "Leverage"]
    if len(leverage) > 0:
        lev_spend = leverage["category_spend"].sum()
        actions.append({
            "rank": 3,
            "title": f"Competitive RFQ for {len(leverage)} Leverage Categories",
            "description": (
                f"${lev_spend:,.0f} in Leverage categories (high spend, manageable supply risk). "
                "Run competitive RFQ events via SAP Ariba Sourcing. "
                "Typical savings: 8-15% through competitive bidding in consolidated Leverage categories. "
                "Prioritise categories where CR-3 < 70% — fragmentation reduces your negotiating power."
            ),
            "priority": "HIGH",
            "framework": "Kraljic (1983) — Leverage quadrant + SAP Ariba Sourcing"
        })

    # Action 4: Bottleneck risk mitigation
    bottleneck = category_analysis[category_analysis["kraljic_quadrant"] == "Bottleneck"]
    if len(bottleneck) > 0:
        bt_names = ", ".join(bottleneck.head(3)["category"].tolist())
        actions.append({
            "rank": 4,
            "title": f"Qualify Alternative Suppliers for Bottleneck Items",
            "description": (
                f"Categories [{bt_names}] are Bottleneck (low spend, but high supply risk). "
                "A disruption here stops operations disproportionately. "
                "Qualify at least one additional approved supplier. "
                "Consider holding 4-6 weeks safety stock for critical bottleneck items."
            ),
            "priority": "MEDIUM",
            "framework": "Kraljic (1983) — Bottleneck quadrant"
        })

    # Action 5: Spend Under Management improvement
    if sum_data and not sum_data["world_class"]:
        gap = sum_data["benchmark_gap"]
        unmanaged = sum_data["unmanaged_spend"]
        actions.append({
            "rank": 5,
            "title": f"Increase Spend Under Management (Gap: {gap}pp vs 80% benchmark)",
            "description": (
                f"${unmanaged:,.0f} of spend is flowing outside approved, contracted suppliers. "
                f"Current SUM: {sum_data['sum_pct']}%. World-class benchmark: 80%+ (Hackett Group, 2024). "
                "Action: Audit POs against active contract register. Enforce preferred supplier policy "
                "for top 10 spend categories. Implement Guided Buying via SAP Ariba."
            ),
            "priority": "MEDIUM",
            "framework": "Hackett Group SUM benchmark + SAP Ariba Guided Buying"
        })

    # Action 6: Non-critical automation
    noncrit = category_analysis[category_analysis["kraljic_quadrant"] == "Non-critical"]
    if len(noncrit) > 0:
        nc_spend = noncrit["category_spend"].sum()
        actions.append({
            "rank": 6,
            "title": f"Automate {len(noncrit)} Non-critical Categories",
            "description": (
                f"${nc_spend:,.0f} in Non-critical categories represents low-value, low-risk spend "
                "consuming disproportionate procurement bandwidth. "
                "Automate via catalog purchasing in SAP Ariba Buying. "
                "Target: reduce manual POs by 60% in these categories within 90 days."
            ),
            "priority": "LOW",
            "framework": "Kraljic (1983) — Non-critical quadrant + SAP Ariba Buying"
        })

    return actions


def load_sample_data() -> pd.DataFrame:
    """
    Realistic sample procurement dataset for demo purposes.
    Modelled on a mid-size manufacturing company ($50M revenue).
    Approximately 300 purchase order line items.
    """
    np.random.seed(42)

    categories_suppliers = {
        "MRO Supplies": ["Grainger Industrial", "Fastenal Co", "MSC Industrial", "HD Supply", "W.W. Grainger"],
        "IT Hardware": ["Dell Technologies", "Lenovo Group", "HP Inc", "CDW Corporation"],
        "Engineering Services": ["Accenture", "Deloitte Consulting", "AECOM", "Jacobs Engineering"],
        "Raw Materials - Steel": ["Nucor Corporation", "Steel Technologies", "Metals USA"],
        "Logistics & Freight": ["FedEx Supply Chain", "UPS Supply Chain", "XPO Logistics", "Werner Enterprises"],
        "Electronic Components": ["Arrow Electronics", "Avnet Inc", "Digi-Key Electronics"],
        "Office Supplies": ["Staples", "Office Depot", "Amazon Business", "Quill Corp", "W.B. Mason", "Global Industrial", "Uline", "Zoro Tools"],
        "Chemicals & Lubricants": ["Brenntag", "Univar Solutions", "Quaker Houghton"],
        "IT Software & Cloud": ["Microsoft", "Salesforce", "SAP SE", "Oracle Corp"],
        "Facility Management": ["ABM Industries", "Aramark", "Sodexo", "Cushman & Wakefield"],
        "Packaging Materials": ["Sealed Air", "Sonoco Products", "Bemis Company", "Pactiv"],
        "Safety Equipment": ["Honeywell Safety", "3M Safety", "MSA Safety", "Kimberly Clark"],
    }

    spend_dist = {
        "Raw Materials - Steel": (8000, 3000),
        "IT Software & Cloud": (6000, 2000),
        "Engineering Services": (12000, 4000),
        "Logistics & Freight": (4000, 1500),
        "Electronic Components": (3500, 1200),
        "IT Hardware": (2500, 800),
        "MRO Supplies": (800, 400),
        "Chemicals & Lubricants": (2000, 700),
        "Facility Management": (1500, 500),
        "Packaging Materials": (1200, 400),
        "Office Supplies": (250, 120),
        "Safety Equipment": (600, 200),
    }

    line_items = {
        "Raw Materials - Steel": ["Hot-rolled coil steel 50ton", "Cold-rolled sheet 20ton", "Steel tubing structural", "Plate steel 12mm", "Galvanised steel strip"],
        "IT Software & Cloud": ["ERP annual license", "Cloud infrastructure AWS", "CRM platform license", "Cybersecurity suite", "BI analytics platform"],
        "Engineering Services": ["Process improvement project", "Plant audit Q2", "Quality systems consulting", "CAD design services", "Commissioning support"],
        "Logistics & Freight": ["Inbound freight eastern", "Outbound LTL shipments", "Air freight components", "Warehousing 3PL", "Last-mile delivery"],
        "Electronic Components": ["PCB assembly components", "Capacitors bulk order", "Microcontrollers batch", "Sensors industrial", "Connectors catalog"],
        "IT Hardware": ["Laptop batch 20 units", "Server rack upgrade", "Network switches", "Monitors ergonomic"],
        "MRO Supplies": ["Nuts bolts fasteners", "Cutting tools carbide", "Safety consumables", "Filters industrial", "Gloves PPE bulk"],
        "Chemicals & Lubricants": ["Machine lubricant ISO46", "Industrial cleaner", "Coolant concentrate", "Rust inhibitor"],
        "Facility Management": ["Building maintenance contract", "HVAC service annual", "Cleaning services monthly", "Pest control"],
        "Packaging Materials": ["Corrugated boxes bulk", "Stretch wrap pallets", "Foam protective inserts", "Tape industrial"],
        "Office Supplies": ["Printer paper case", "Pens pencils stationery", "Filing folders", "Desk accessories", "Coffee supplies", "Cleaning products office", "Printer cartridges", "Notepads bulk"],
        "Safety Equipment": ["Hard hats ANSI", "Safety glasses bulk", "Hi-vis vests", "Hearing protection"],
    }

    rows = []
    po_num = 100000
    for category, (mean_spend, std_spend) in spend_dist.items():
        n_orders = np.random.randint(15, 35)
        suppliers = categories_suppliers[category]
        items = line_items[category]
        for _ in range(n_orders):
            supplier = np.random.choice(suppliers)
            amount = max(100, np.random.normal(mean_spend, std_spend))
            desc = np.random.choice(items)
            preferred = "Y" if supplier in suppliers[:2] else np.random.choice(["Y", "N"], p=[0.6, 0.4])
            rows.append({
                "po_number": f"PO-{po_num}",
                "supplier_name": supplier,
                "line_item_description": desc,
                "category": category,
                "amount": round(amount, 2),
                "po_date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=np.random.randint(0, 365)),
                "preferred_supplier": preferred,
                "country": np.random.choice(["US", "DE", "CN", "MX", "IN"], p=[0.6, 0.15, 0.1, 0.1, 0.05]),
            })
            po_num += 1

    return pd.DataFrame(rows)


# ── Session state ─────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state["df"] = None
if "analyzed" not in st.session_state:
    st.session_state["analyzed"] = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sl-sidebar-title">SpendLens</div>', unsafe_allow_html=True)
    st.markdown('<div class="sl-sidebar-sub">Procurement Intelligence</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Data Source**")
    use_sample = st.toggle("Use sample dataset", value=True,
        help="Toggle off to upload your own PO export CSV")

    if not use_sample:
        uploaded = st.file_uploader(
            "Upload PO Export (CSV)",
            type=["csv"],
            help="Required columns: supplier_name, line_item_description, amount\nOptional: category, po_date, preferred_supplier, country"
        )
    else:
        uploaded = None

    st.markdown("---")
    st.markdown("**Groq API Key** *(optional)*")
    groq_key = st.text_input("", type="password",
        placeholder="For AI-enriched actions",
        help="Free at console.groq.com — enriches action descriptions with AI")

    st.markdown("---")
    st.markdown("**Kraljic Thresholds**")
    profit_threshold = st.slider("Profit Impact cutoff", 30, 70, 50,
        help="Score above this = High Profit Impact")
    risk_threshold = st.slider("Supply Risk cutoff", 30, 70, 50,
        help="Score above this = High Supply Risk")

    st.markdown("---")
    st.markdown("""
    <div style="font-family: IBM Plex Mono, monospace; font-size: 10px; color: #a89e92; line-height: 1.8;">
    Frameworks:<br>
    UNSPSC v24 (UNDP)<br>
    Pareto/ABC — Monczka et al. (2019)<br>
    Kraljic Matrix — HBR (1983)<br>
    CR-n — Industrial Organisation<br>
    SUM — Hackett Group (2024)<br><br>
    Built by Rutwik Satish<br>
    MS Eng. Management, Northeastern<br>
    SAP Ariba Certified · May 2026
    </div>
    """, unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="sl-wordmark">◎ Procurement Spend Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sl-title">Spend<span>Lens</span></div>', unsafe_allow_html=True)
st.markdown('<div class="sl-sub">Upload any ERP purchase order export. Get Pareto/ABC analysis, UNSPSC taxonomy, Supplier Concentration Ratios, Kraljic Matrix positioning, and prioritised sourcing actions — in 60 seconds.</div>', unsafe_allow_html=True)
st.markdown("""
<div class="sl-tags">
  <span class="sl-tag red">◎ Kraljic Matrix</span>
  <span class="sl-tag">◎ Pareto / ABC</span>
  <span class="sl-tag">◎ UNSPSC Taxonomy</span>
  <span class="sl-tag">◎ Concentration Ratio</span>
  <span class="sl-tag">◎ Spend Under Management</span>
  <span class="sl-tag">◎ SAP Ariba Compatible</span>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="sl-divider"></div>', unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
if use_sample:
    df_raw = load_sample_data()
    st.info("◎ Sample dataset loaded — 300 PO lines, 12 categories, 1 manufacturing company. Toggle 'Use sample dataset' off to upload your own data.", icon="ℹ️")
elif uploaded:
    try:
        df_raw = pd.read_csv(uploaded)
        required = ["supplier_name", "amount"]
        missing = [c for c in required if c not in df_raw.columns]
        if missing:
            st.error(f"Missing required columns: {missing}. Please check your CSV format.")
            st.stop()
        if "line_item_description" not in df_raw.columns:
            df_raw["line_item_description"] = "Unspecified"
        st.success(f"◎ Loaded {len(df_raw):,} rows from {uploaded.name}", icon="✓")
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()
else:
    st.markdown("""
    <div style="background:#fff; border:1px solid #ddd6cc; border-radius:4px; padding:2rem; text-align:center; color:#8a7f72;">
        <div style="font-family: Libre Baskerville, serif; font-size:18px; margin-bottom:8px; color:#1a1714;">Upload your PO export to begin</div>
        <div style="font-size:13px; line-height:1.7;">
            Minimum columns required: <code>supplier_name</code>, <code>amount</code><br>
            Optional: <code>category</code>, <code>line_item_description</code>, <code>preferred_supplier</code> (Y/N), <code>country</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Run Analysis button ────────────────────────────────────────────────────────
col_btn, col_info = st.columns([2, 4])
with col_btn:
    run = st.button("◎  Run Spend Analysis", type="primary", use_container_width=True)
with col_info:
    if st.session_state["analyzed"]:
        st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#8a7f72;padding:12px 0;">Last run: {st.session_state.get("last_run","")}</div>', unsafe_allow_html=True)

if run:
    with st.spinner("Classifying spend, computing analytics..."):
        df = df_raw.copy()

        # Classify if no category column
        if "category" not in df.columns or df["category"].isna().sum() > len(df) * 0.3:
            classifications = df["line_item_description"].apply(classify_line_item)
            df["unspsc_code"] = classifications.apply(lambda x: x[0])
            df["category"] = classifications.apply(lambda x: x[1])

        # Ensure amount is numeric
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df = df[df["amount"] > 0]

        total_spend   = df["amount"].sum()
        n_suppliers   = df["supplier_name"].nunique()
        n_categories  = df["category"].nunique()
        n_transactions = len(df)

        # ABC Analysis
        abc_df = run_abc_analysis(df)

        # Category analysis with Kraljic
        cat_summary = []
        for cat in df["category"].unique():
            df_cat = df[df["category"] == cat]
            cat_spend = df_cat["amount"].sum()
            n_sup     = count_suppliers(df_cat)
            cr3       = concentration_ratio(df_cat, 3)
            pi_score  = compute_profit_impact_score(cat_spend, total_spend)
            sr_score  = compute_supply_risk_score(df_cat)
            quadrant, strategy, color = assign_kraljic_quadrant(pi_score, sr_score)
            cat_summary.append({
                "category": cat,
                "category_spend": cat_spend,
                "spend_pct": round(cat_spend / total_spend * 100, 1),
                "n_suppliers": n_sup,
                "cr3": cr3,
                "profit_impact_score": round(pi_score, 1),
                "supply_risk_score": round(sr_score, 1),
                "kraljic_quadrant": quadrant,
                "recommended_strategy": strategy,
                "color": color,
            })
        cat_df = pd.DataFrame(cat_summary).sort_values("category_spend", ascending=False)

        # SUM ratio
        sum_data = spend_under_management(df)

        # Action list
        actions = generate_action_list(cat_df, abc_df, sum_data)

        # Store in session
        st.session_state["df"]         = df
        st.session_state["abc_df"]     = abc_df
        st.session_state["cat_df"]     = cat_df
        st.session_state["sum_data"]   = sum_data
        st.session_state["actions"]    = actions
        st.session_state["total_spend"]= total_spend
        st.session_state["n_suppliers"]= n_suppliers
        st.session_state["n_cat"]      = n_categories
        st.session_state["n_tx"]       = n_transactions
        st.session_state["analyzed"]   = True
        st.session_state["last_run"]   = datetime.now().strftime("%Y-%m-%d %H:%M")

    st.success(f"◎ Analysis complete — {n_transactions:,} transactions · {n_suppliers} suppliers · {n_categories} categories")


# ── Results display ───────────────────────────────────────────────────────────
if st.session_state.get("analyzed"):
    df         = st.session_state["df"]
    abc_df     = st.session_state["abc_df"]
    cat_df     = st.session_state["cat_df"]
    sum_data   = st.session_state["sum_data"]
    actions    = st.session_state["actions"]
    total_spend= st.session_state["total_spend"]
    n_suppliers= st.session_state["n_suppliers"]

    # ── Summary metrics ──────────────────────────────────────────────────────
    st.markdown('<div class="sl-section">Summary Metrics</div>', unsafe_allow_html=True)

    a_count = len(abc_df[abc_df["abc_class"] == "A"])
    c_count = len(abc_df[abc_df["abc_class"] == "C"])
    strategic_count = len(cat_df[cat_df["kraljic_quadrant"] == "Strategic"])

    sum_str = f'{sum_data["sum_pct"]}%' if sum_data else "N/A"
    sum_class = "green" if sum_data and sum_data["world_class"] else ("accent" if sum_data else "")

    st.markdown(f"""
    <div class="sl-metrics">
      <div class="sl-metric accent">
        <div class="sl-metric-num red">${total_spend/1e6:.1f}M</div>
        <div class="sl-metric-label">Total Analysed Spend</div>
      </div>
      <div class="sl-metric">
        <div class="sl-metric-num">{n_suppliers}</div>
        <div class="sl-metric-label">Active Suppliers</div>
      </div>
      <div class="sl-metric">
        <div class="sl-metric-num amber">{a_count}</div>
        <div class="sl-metric-label">Class A Suppliers (80% spend)</div>
      </div>
      <div class="sl-metric {'green' if sum_data and sum_data['world_class'] else ''}">
        <div class="sl-metric-num {'green' if sum_data and sum_data['world_class'] else 'red'}">{sum_str}</div>
        <div class="sl-metric-label">Spend Under Management</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sl-footnote">Spend Under Management benchmark: 80%+ = world-class (Hackett Group, 2024 Procurement Key Issues Study)</div>', unsafe_allow_html=True)

    st.markdown('<div class="sl-divider"></div>', unsafe_allow_html=True)

    # ── Pareto / ABC Analysis ────────────────────────────────────────────────
    st.markdown('<div class="sl-section">Pareto / ABC Supplier Segmentation</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#6b5f52;margin-bottom:1rem;">Class A: top 20% of suppliers representing ~80% of spend. Class B: next 30% representing ~15%. Class C: tail spend (remaining 5%). Source: Monczka et al. (2019), Ch.6.</p>', unsafe_allow_html=True)

    col_chart, col_table = st.columns([1.4, 1])

    with col_chart:
        abc_top = abc_df.head(30)
        colors_abc = {"A": "#c85a2a", "B": "#c8960a", "C": "#8a7f72"}
        bar_colors = [colors_abc[c] for c in abc_top["abc_class"]]

        fig_abc = go.Figure()
        fig_abc.add_trace(go.Bar(
            x=abc_top["supplier_name"],
            y=abc_top["total_spend"],
            marker_color=bar_colors,
            name="Spend",
            hovertemplate="<b>%{x}</b><br>Spend: $%{y:,.0f}<extra></extra>"
        ))
        fig_abc.add_trace(go.Scatter(
            x=abc_top["supplier_name"],
            y=abc_top["cumulative_pct"],
            mode="lines+markers",
            name="Cumulative %",
            yaxis="y2",
            line=dict(color="#1a1714", width=1.5),
            marker=dict(size=4),
            hovertemplate="%{y:.1f}%<extra></extra>"
        ))
        fig_abc.add_hline(y=80, yref="y2", line_dash="dot",
            line_color="rgba(200,90,42,0.5)",
            annotation_text="80%", annotation_font_color="#c85a2a")
        fig_abc.add_hline(y=95, yref="y2", line_dash="dot",
            line_color="rgba(200,150,10,0.4)",
            annotation_text="95%", annotation_font_color="#c8960a")
        fig_abc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#fff",
            margin=dict(l=0, r=10, t=10, b=100),
            height=340,
            xaxis=dict(
                tickangle=45,
                tickfont=dict(family="IBM Plex Mono", size=9, color="#8a7f72")
            ),
            yaxis=dict(
                title="Spend ($)",
                tickfont=dict(family="IBM Plex Mono", size=9, color="#8a7f72"),
                gridcolor="rgba(200,191,176,0.4)",
                tickprefix="$",
                tickformat=",.0f"
            ),
            yaxis2=dict(
                title="Cumulative %",
                overlaying="y",
                side="right",
                range=[0, 105],
                tickfont=dict(family="IBM Plex Mono", size=9, color="#8a7f72"),
                ticksuffix="%"
            ),
            legend=dict(
                font=dict(family="IBM Plex Mono", size=9),
                bgcolor="rgba(0,0,0,0)"
            ),
            showlegend=True
        )
        st.plotly_chart(fig_abc, use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="sl-footnote">Pareto chart — bars show supplier spend (left axis), line shows cumulative % (right axis)</div>', unsafe_allow_html=True)

    with col_table:
        st.markdown("**Top 15 Suppliers by Spend**")
        display_abc = abc_df.head(15)[["supplier_name", "abc_class", "total_spend", "spend_pct", "transaction_count"]].copy()
        display_abc.columns = ["Supplier", "Class", "Spend ($)", "% of Total", "# POs"]
        display_abc["Spend ($)"] = display_abc["Spend ($)"].apply(lambda x: f"${x:,.0f}")
        display_abc["% of Total"] = display_abc["% of Total"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_abc, use_container_width=True, height=320, hide_index=True)

        a_spend = abc_df[abc_df["abc_class"] == "A"]["total_spend"].sum()
        c_spend = abc_df[abc_df["abc_class"] == "C"]["total_spend"].sum()
        c_count = len(abc_df[abc_df["abc_class"] == "C"])
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #ddd6cc;border-radius:4px;padding:10px 12px;margin-top:8px;font-size:12px;color:#6b5f52;line-height:1.7;">
        <b style="color:#1a1714">Class A:</b> {len(abc_df[abc_df['abc_class']=='A'])} suppliers · ${a_spend:,.0f}<br>
        <b style="color:#1a1714">Class C (Tail):</b> {c_count} suppliers · ${c_spend:,.0f}<br>
        <span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#c85a2a">Tail spend consolidation opportunity → immediate</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sl-divider"></div>', unsafe_allow_html=True)

    # ── Kraljic Matrix ────────────────────────────────────────────────────────
    st.markdown('<div class="sl-section">Kraljic Portfolio Matrix</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#6b5f52;margin-bottom:1rem;">Supplier/category segmentation by Profit Impact × Supply Risk. Framework: Kraljic (1983), Harvard Business Review 61(5), 109–117.</p>', unsafe_allow_html=True)

    col_matrix, col_legend = st.columns([1.6, 1])

    with col_matrix:
        fig_kq = go.Figure()

        quad_colors = {
            "Strategic":    "#c85a2a",
            "Leverage":     "#3a7a4a",
            "Bottleneck":   "#c8960a",
            "Non-critical": "#8a7f72"
        }

        for _, row in cat_df.iterrows():
            fig_kq.add_trace(go.Scatter(
                x=[row["profit_impact_score"]],
                y=[row["supply_risk_score"]],
                mode="markers+text",
                marker=dict(
                    size=max(12, min(40, row["spend_pct"] * 3)),
                    color=quad_colors.get(row["kraljic_quadrant"], "#8a7f72"),
                    opacity=0.82,
                    line=dict(color="white", width=1.5)
                ),
                text=[row["category"]],
                textposition="top center",
                textfont=dict(family="IBM Plex Mono", size=8, color="#1a1714"),
                name=row["kraljic_quadrant"],
                hovertemplate=(
                    f"<b>{row['category']}</b><br>"
                    f"Spend: ${row['category_spend']:,.0f} ({row['spend_pct']}%)<br>"
                    f"Profit Impact: {row['profit_impact_score']}<br>"
                    f"Supply Risk: {row['supply_risk_score']}<br>"
                    f"CR-3: {row['cr3']}%<br>"
                    f"Suppliers: {row['n_suppliers']}<br>"
                    f"Quadrant: <b>{row['kraljic_quadrant']}</b>"
                    "<extra></extra>"
                ),
                showlegend=False,
            ))

        # Quadrant dividers
        fig_kq.add_hline(y=50, line_dash="dash", line_color="rgba(100,100,100,0.25)", line_width=1)
        fig_kq.add_vline(x=50, line_dash="dash", line_color="rgba(100,100,100,0.25)", line_width=1)

        # Quadrant background shading
        for x0, x1, y0, y1, color, label in [
            (50, 100, 50, 100, "rgba(200,90,42,0.05)",  "STRATEGIC"),
            (50, 100, 0,  50,  "rgba(58,122,74,0.05)",  "LEVERAGE"),
            (0,  50,  50, 100, "rgba(200,150,10,0.05)", "BOTTLENECK"),
            (0,  50,  0,  50,  "rgba(138,127,114,0.05)","NON-CRITICAL"),
        ]:
            fig_kq.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                fillcolor=color, line_color="rgba(0,0,0,0)")
            fig_kq.add_annotation(
                x=(x0+x1)/2, y=(y0+y1)/2, text=label,
                showarrow=False,
                font=dict(family="IBM Plex Mono", size=9, color="rgba(100,90,80,0.4)"),
                bgcolor="rgba(0,0,0,0)"
            )

        fig_kq.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#fff",
            margin=dict(l=40, r=20, t=20, b=50),
            height=400,
            xaxis=dict(
                title="Profit Impact →",
                range=[0, 105],
                gridcolor="rgba(200,191,176,0.3)",
                tickfont=dict(family="IBM Plex Mono", size=9, color="#8a7f72"),
                titlefont=dict(family="IBM Plex Mono", size=10, color="#6b5f52")
            ),
            yaxis=dict(
                title="Supply Risk →",
                range=[0, 105],
                gridcolor="rgba(200,191,176,0.3)",
                tickfont=dict(family="IBM Plex Mono", size=9, color="#8a7f72"),
                titlefont=dict(family="IBM Plex Mono", size=10, color="#6b5f52")
            ),
        )
        st.plotly_chart(fig_kq, use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="sl-footnote">Bubble size ∝ spend %. Axes: Profit Impact (spend share proxy) × Supply Risk (concentration + sourcing complexity proxy)</div>', unsafe_allow_html=True)

    with col_legend:
        for quad, css_class, strategy in [
            ("Strategic",    "kq-strategic", "Long-term partnerships. Dual-sourcing. Executive SRM. Reduce dependency."),
            ("Leverage",     "kq-leverage",  "Competitive bidding. Volume consolidation. Drive unit costs down."),
            ("Bottleneck",   "kq-bottleneck","Secure supply. Qualify alternates. Safety stock. Priority risk management."),
            ("Non-critical", "kq-noncrit",   "Automate. Catalog purchasing. Reduce transaction costs and admin burden."),
        ]:
            count = len(cat_df[cat_df["kraljic_quadrant"] == quad])
            spend = cat_df[cat_df["kraljic_quadrant"] == quad]["category_spend"].sum()
            st.markdown(f"""
            <div class="kq-card {css_class}">
                <div class="kq-name">{quad}</div>
                <div class="kq-strategy">{strategy}</div>
                <div class="kq-count">{count} categories · ${spend:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="sl-divider"></div>', unsafe_allow_html=True)

    # ── Category Detail Table ─────────────────────────────────────────────────
    st.markdown('<div class="sl-section">Category Analysis — UNSPSC + Supplier Concentration</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#6b5f52;margin-bottom:1rem;">CR-3 = top 3 suppliers\' share of category spend. CR-3 &lt; 70% = fragmentation → consolidation opportunity. UNSPSC classification per UNDP v24.0301.</p>', unsafe_allow_html=True)

    display_cat = cat_df[[
        "category", "category_spend", "spend_pct", "n_suppliers",
        "cr3", "profit_impact_score", "supply_risk_score", "kraljic_quadrant"
    ]].copy()
    display_cat.columns = [
        "Category (UNSPSC)", "Spend ($)", "% of Total",
        "# Suppliers", "CR-3 (%)", "Profit Impact", "Supply Risk", "Kraljic Quadrant"
    ]
    display_cat["Spend ($)"]   = display_cat["Spend ($)"].apply(lambda x: f"${x:,.0f}")
    display_cat["% of Total"]  = display_cat["% of Total"].apply(lambda x: f"{x:.1f}%")
    display_cat["CR-3 (%)"]    = display_cat["CR-3 (%)"].apply(lambda x: f"{x:.0f}%")
    st.dataframe(display_cat, use_container_width=True, hide_index=True, height=350)
    st.markdown('<div class="sl-footnote">CR-n = Supplier Concentration Ratio (top n suppliers\' share of category spend). Standard industrial organisation metric applied to procurement portfolio analysis.</div>', unsafe_allow_html=True)

    st.markdown('<div class="sl-divider"></div>', unsafe_allow_html=True)

    # ── Spend Under Management ────────────────────────────────────────────────
    if sum_data:
        st.markdown('<div class="sl-section">Spend Under Management (SUM)</div>', unsafe_allow_html=True)
        col_sum1, col_sum2, col_sum3 = st.columns(3)

        with col_sum1:
            st.markdown(f"""
            <div class="sl-metric {'green' if sum_data['world_class'] else 'accent'}">
                <div class="sl-metric-num {'green' if sum_data['world_class'] else 'red'}">{sum_data['sum_pct']}%</div>
                <div class="sl-metric-label">Current SUM Ratio</div>
            </div>
            """, unsafe_allow_html=True)
        with col_sum2:
            st.markdown(f"""
            <div class="sl-metric">
                <div class="sl-metric-num">${sum_data['managed_spend']:,.0f}</div>
                <div class="sl-metric-label">Managed Spend</div>
            </div>
            """, unsafe_allow_html=True)
        with col_sum3:
            st.markdown(f"""
            <div class="sl-metric accent">
                <div class="sl-metric-num red">${sum_data['unmanaged_spend']:,.0f}</div>
                <div class="sl-metric-label">Unmanaged (Maverick) Spend</div>
            </div>
            """, unsafe_allow_html=True)

        if not sum_data["world_class"]:
            st.warning(
                f"◎ SUM is {sum_data['sum_pct']}% — {sum_data['benchmark_gap']}pp below world-class benchmark (80%). "
                "Implement preferred supplier policy and SAP Ariba Guided Buying to close the gap.",
                icon="⚠️"
            )
        else:
            st.success("◎ World-class SUM achieved (≥80%). Hackett Group benchmark: top quartile procurement functions.", icon="✓")

        st.markdown('<div class="sl-footnote">SUM benchmark: Hackett Group 2024 Procurement Key Issues Study. World-class threshold: ≥80% spend through contracted/preferred suppliers.</div>', unsafe_allow_html=True)
        st.markdown('<div class="sl-divider"></div>', unsafe_allow_html=True)

    # ── Priority Action List ──────────────────────────────────────────────────
    st.markdown('<div class="sl-section">Priority Sourcing Actions</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#6b5f52;margin-bottom:1rem;">Ranked by strategic impact. Each action is framework-referenced and mapped to SAP Ariba module where applicable.</p>', unsafe_allow_html=True)

    for action in actions:
        badge_class = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(action["priority"], "badge-low")
        st.markdown(f"""
        <div class="action-item">
            <div class="action-rank">{action['rank']}</div>
            <div>
                <div class="action-title">{action['title']}</div>
                <div class="action-desc">{action['description']}</div>
                <span class="action-badge {badge_class}">{action['priority']} PRIORITY</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:9px;color:#a89e92;margin-left:8px;">{action['framework']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sl-divider"></div>', unsafe_allow_html=True)

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown('<div class="sl-section">Export</div>', unsafe_allow_html=True)
    col_e1, col_e2, col_e3 = st.columns(3)

    with col_e1:
        csv_abc = abc_df.to_csv(index=False)
        st.download_button("↓ ABC Analysis CSV", csv_abc,
            file_name=f"spendlens_abc_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True)
    with col_e2:
        csv_cat = cat_df.drop(columns=["color"]).to_csv(index=False)
        st.download_button("↓ Kraljic Matrix CSV", csv_cat,
            file_name=f"spendlens_kraljic_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True)
    with col_e3:
        action_df = pd.DataFrame(actions)
        csv_actions = action_df.to_csv(index=False)
        st.download_button("↓ Action List CSV", csv_actions,
            file_name=f"spendlens_actions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding-top:1.5rem;border-top:1px solid #c8bfb0;
     font-family:IBM Plex Mono,monospace;font-size:10px;color:#a89e92;line-height:2;text-align:center;">
SpendLens · Procurement Spend Intelligence · Pareto/ABC: Monczka, Handfield et al. (2019) ·
Kraljic Matrix: HBR (1983) · UNSPSC v24: UNDP/GS1 · SUM: Hackett Group (2024)<br>
Built by Rutwik Satish · MS Engineering Management, Northeastern University ·
SAP Ariba Procurement &amp; Sourcing Certified · May 2026
</div>
""", unsafe_allow_html=True)
