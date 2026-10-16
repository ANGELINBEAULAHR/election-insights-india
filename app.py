
from pathlib import Path
from datetime import datetime
from html import escape
from html import unescape
import re

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

try:
    import feedparser
except ImportError:
    feedparser = None


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

st.set_page_config(
    page_title="Election Insights | India",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. SESSION STATE AND RESET BUTTON
# ============================================================

DEFAULTS = {
    "year_filter": "All years",
    "state_filter": "All states",
    "region_search": "",
    "main_navigation": "Overview",
    "explorer_search": "",
    "sample_seed": 42,
    "news_refresh": 0,
}

# Initialise state before rendering widgets.
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_dashboard():
    """Reset all dashboard controls before Streamlit reruns."""
    for key, value in DEFAULTS.items():
        st.session_state[key] = value

    # Sampling size is dynamic, so calculate its default
    # later after the selected dataset has been loaded.


# ============================================================
# 3. PREMIUM DARK THEME
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #080d1b;
    --panel: #111a2e;
    --line: rgba(164,190,255,.18);
    --text: #f4f7ff;
    --muted: #a8b6cf;
    --blue: #7189ff;
    --cyan: #53e0e0;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    color: var(--text);
    background:
        radial-gradient(ellipse at 5% 0%, rgba(55,86,190,.22), transparent 35%),
        radial-gradient(ellipse at 95% 10%, rgba(42,190,199,.12), transparent 30%),
        var(--bg);
}

header[data-testid="stHeader"] {
    background: rgba(8,13,27,.96) !important;
    border-bottom: 1px solid var(--line);
    backdrop-filter: blur(16px);
}

[data-testid="stDecoration"] {
    background: linear-gradient(90deg, #7189ff, #53e0e0, #a78bfa);
    height: 3px;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}

#MainMenu, footer {
    visibility: hidden;
}

h1, h2, h3, h4 {
    color: var(--text) !important;
    letter-spacing: -.035em;
}

p {
    color: #c4d0e5;
    line-height: 1.7;
}

.topline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
    padding: 12px 4px 20px;
    border-bottom: 1px solid var(--line);
    margin-bottom: 20px;
}

.brand {
    font-family: 'Manrope', sans-serif;
    font-size: 1.2rem;
    font-weight: 800;
    color: white;
}

.brand span {
    color: #8fa3ff;
}

.live-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #5ce3bb;
    border-radius: 50%;
    margin-right: 8px;
    box-shadow: 0 0 12px #5ce3bb;
}

.hero {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(142,166,255,.30);
    border-radius: 26px;
    padding: 42px;
    margin: 12px 0 30px;
    background: linear-gradient(115deg, #111f3c, #1b2f5e 55%, #1c4c68);
    animation: rise .7s ease both;
}

.hero:before {
    content: "";
    position: absolute;
    width: 250px;
    height: 250px;
    right: -65px;
    top: -130px;
    border: 1px solid rgba(143,177,255,.35);
    border-radius: 50%;
    box-shadow: 0 0 0 35px rgba(143,177,255,.05),
                0 0 0 70px rgba(143,177,255,.035);
    animation: float 7s ease-in-out infinite;
    pointer-events: none;
}

.hero-tag, .tag {
    display: inline-block;
    border: 1px solid rgba(142,166,255,.35);
    border-radius: 30px;
    padding: 6px 11px;
    color: #c2ceff;
    background: rgba(102,135,255,.12);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.4px;
}

.hero h1 {
    position: relative;
    font-family: 'Manrope', sans-serif;
    font-size: clamp(2.1rem, 5vw, 3.8rem);
    font-weight: 800;
    line-height: 1.08;
    margin: 20px 0 14px;
    max-width: 850px;
}

.hero p {
    position: relative;
    max-width: 720px;
    color: #d0dcf5;
}

.section-head {
    margin: 30px 0 16px;
    animation: rise .45s ease both;
}

.kicker {
    color: #8da4ff;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 6px;
}

.section-title {
    color: white;
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: -.7px;
}

.subtle {
    color: var(--muted);
    line-height: 1.7;
    margin-top: 5px;
}

.panel, .news-card {
    background: linear-gradient(145deg, #111b2f, #0c1424);
    border: 1px solid var(--line);
    border-radius: 19px;
    padding: 22px;
    margin-bottom: 14px;
    transition: transform .25s ease, border-color .25s ease,
                box-shadow .25s ease;
    animation: rise .5s ease both;
}

.panel:hover, .news-card:hover {
    transform: translateY(-4px);
    border-color: rgba(112,143,255,.7);
    box-shadow: 0 14px 35px rgba(0,0,0,.22);
}

.panel h3, .news-card h3 {
    color: white;
    font-size: 1.05rem;
    margin: 12px 0;
}

.panel p, .news-card p {
    color: #a9b8d0;
    font-size: .92rem;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #142038, #0d1526);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 20px;
    transition: transform .25s ease, border-color .25s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    border-color: var(--blue);
}

[data-testid="stMetricLabel"] {
    color: #a7b6d2 !important;
}

[data-testid="stMetricValue"] {
    color: white !important;
    font-weight: 800 !important;
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 12px;
    border: 1px solid rgba(120,151,255,.45);
    background: linear-gradient(115deg, #496bf1, #7468f7);
    color: white;
    font-weight: 700;
    transition: all .22s ease;
    min-height: 42px;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.12);
    box-shadow: 0 10px 25px rgba(73,107,241,.3);
    border-color: #a7b6ff;
}

.stButton > button:active {
    transform: scale(.98);
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: #101a2e !important;
    color: white !important;
    border-color: var(--line) !important;
    border-radius: 11px !important;
}

[data-testid="stSelectbox"] > div {
    background: #101a2e !important;
    border-radius: 11px !important;
}

[data-testid="stRadio"] > div {
    gap: 8px;
    flex-wrap: wrap;
}

[data-testid="stRadio"] label {
    background: #131d32;
    border: 1px solid var(--line);
    padding: 8px 12px;
    border-radius: 11px;
    transition: all .2s ease;
}

[data-testid="stRadio"] label:hover {
    border-color: var(--blue);
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 13px;
    overflow: hidden;
}

.news-date {
    color: var(--cyan);
    font-size: 11px;
    letter-spacing: 1px;
    font-weight: 800;
}

.news-link {
    color: #9eafff !important;
    font-weight: 700;
    text-decoration: none;
}

.news-link:hover {
    color: var(--cyan) !important;
}

.news-hero {
    padding: 28px;
    border-radius: 22px;
    border: 1px solid rgba(120,151,255,.32);
    background: linear-gradient(115deg, #142548, #183e55);
    margin: 18px 0 25px;
}

.footer {
    margin-top: 38px;
    padding-top: 20px;
    border-top: 1px solid var(--line);
    color: #8191ad;
    font-size: 12px;
    line-height: 1.8;
}

hr {
    border-color: var(--line) !important;
    margin: 1.5rem 0;
}

@keyframes rise {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(13px); }
}

@media (max-width: 800px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 26px 21px;
    }

    .hero:before {
        right: -200px;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *:before, *:after {
        animation: none !important;
        transition: none !important;
    }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

@st.cache_data
def read_csv(filename):
    path = DATA / filename

    if not path.exists():
        return pd.DataFrame()

    try:
        frame = pd.read_csv(path, low_memory=False)
    except (UnicodeDecodeError, pd.errors.ParserError, OSError):
        try:
            frame = pd.read_csv(
                path, encoding="latin-1", low_memory=False
            )
        except Exception:
            return pd.DataFrame()

    frame.columns = frame.columns.astype(str).str.strip()
    return frame


def num(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )


def section(kicker, title, description=None):
    desc = (
        f'<div class="subtle">{escape(str(description))}</div>'
        if description else ""
    )

    st.markdown(
        f"""
        <div class="section-head">
            <div class="kicker">{escape(str(kicker))}</div>
            <div class="section-title">{escape(str(title))}</div>
            {desc}
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(tag, title, description):
    st.markdown(
        f"""
        <div class="panel">
            <span class="tag">{escape(str(tag))}</span>
            <h3>{escape(str(title))}</h3>
            <p>{escape(str(description))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_theme(fig, ax):
    fig.patch.set_facecolor("#10182b")

    for item in np.atleast_1d(ax):
        item.set_facecolor("#10182b")
        item.tick_params(colors="#a7b6d2", labelsize=9)
        item.xaxis.label.set_color("#a7b6d2")
        item.yaxis.label.set_color("#a7b6d2")
        item.title.set_color("#f4f7ff")

        for spine in item.spines.values():
            spine.set_color("#273651")

        item.grid(
            axis="y",
            color="#34425c",
            alpha=.45,
            linewidth=.7,
        )
        item.set_axisbelow(True)

    fig.tight_layout(pad=2)


def show_fig(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ============================================================
# 5. LOAD DATA
# ============================================================

df_raw = read_csv("dataset1.csv")
candidates = read_csv("dataset2.csv")
expenses = read_csv("dataset3.csv")


# ============================================================
# 6. BRAND AND HERO
# ============================================================

st.markdown("""
<div class="topline">
    <div class="brand">
        ELECTION<span>INSIGHTS</span>
        <span style="color:#8090aa;font-size:10px;letter-spacing:1.8px">
            / INDIA
        </span>
    </div>
    <div style="color:#d0def4;font-size:12px;letter-spacing:1px">
        <span class="live-dot"></span>
        DATA EXPLORER · ACADEMIC PROJECT
    </div>
</div>

<div class="hero">
    <div class="hero-tag">INDIA · ELECTION DATA LAB</div>
    <h1>Understanding the<br>power of every vote.</h1>
    <p>
        Explore participation patterns, compare turnout across regions,
        analyse gender differences, and experiment with sampling
        probability using historical election records.
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 7. VALIDATE AND CLEAN DATA
# ============================================================

if df_raw.empty:
    st.error(
        "dataset1.csv is missing or could not be read. "
        "Place it inside the data folder beside app.py."
    )
    st.code(
        "Election-Polling-Vote-Estimation/\n"
        "├── app.py\n"
        "├── requirements.txt\n"
        "└── data/\n"
        "    ├── dataset1.csv\n"
        "    ├── dataset2.csv\n"
        "    └── dataset3.csv"
    )
    st.stop()

required = [
    "Year", "State",
    "Male_Electors", "Female_Electors", "Total_Electors",
    "Male_Voters", "Female_Voters", "Total_Voters",
]

missing = [column for column in required if column not in df_raw.columns]

if missing:
    st.error(f"Required columns missing from dataset1.csv: {missing}")
    st.write("Columns found:", df_raw.columns.tolist())
    st.stop()

df = df_raw.copy()
rows_before = len(df)

for column in required:
    if column != "State":
        df[column] = num(df[column])

df["State"] = df["State"].fillna("").astype(str).str.strip()

df = df.dropna(
    subset=["Year", "Total_Electors", "Total_Voters"]
)

df = df[
    (df["Total_Electors"] > 0)
    & (df["State"] != "")
].copy()

df["Year"] = df["Year"].astype(int)

df["Turnout (%)"] = (
    df["Total_Voters"] / df["Total_Electors"] * 100
).clip(0, 100)

if df.empty:
    st.error("No valid records remain after data cleaning.")
    st.stop()


# ============================================================
# 8. FILTERS AND FUNCTIONAL RESET
# ============================================================

section(
    "EXPLORE THE DATA",
    "Set your view",
    "Select an election year or region. Use Reset to clear your filters.",
)

f1, f2, f3, f4 = st.columns([1.15, 1.15, 1.5, .8])

year_options = ["All years"] + sorted(df["Year"].unique().tolist())
state_options = ["All states"] + sorted(df["State"].unique().tolist())

# Protect selectboxes if a previous selection no longer exists.
if st.session_state.year_filter not in year_options:
    st.session_state.year_filter = "All years"

if st.session_state.state_filter not in state_options:
    st.session_state.state_filter = "All states"

with f1:
    st.selectbox(
        "Election year",
        year_options,
        key="year_filter",
    )

with f2:
    st.selectbox(
        "State / region",
        state_options,
        key="state_filter",
    )

with f3:
    st.text_input(
        "Search region",
        placeholder="Type a state name...",
        key="region_search",
    )

with f4:
    st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)

    st.button(
        "↺ Reset all",
        on_click=reset_dashboard,
        use_container_width=True,
        help="Clear all filters and return to the Overview page.",
    )

year_choice = st.session_state.year_filter
state_choice = st.session_state.state_filter
search = st.session_state.region_search

view = df.copy()

if year_choice != "All years":
    view = view[view["Year"] == year_choice]

if state_choice != "All states":
    view = view[view["State"] == state_choice]

if search.strip():
    view = view[
        view["State"].str.contains(
            search.strip(), case=False, na=False, regex=False
        )
    ]

if view.empty:
    st.warning(
        "No records match your filters. Change your selection "
        "or click Reset all."
    )
    st.stop()


# ============================================================
# 9. SUMMARY METRICS
# ============================================================

electors = float(view["Total_Electors"].sum())
voters = float(view["Total_Voters"].sum())
non_voters = max(electors - voters, 0)
turnout = voters / electors * 100 if electors else 0

section(
    "THE NUMBERS",
    "Election snapshot",
    f"{len(view):,} valid records · {year_choice} · {state_choice}",
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Records selected", f"{len(view):,}")
m2.metric("Total electors", f"{electors:,.0f}")
m3.metric("Votes recorded", f"{voters:,.0f}")
m4.metric("Weighted turnout", f"{turnout:.2f}%")


# ============================================================
# 10. DASHBOARD NAVIGATION
# ============================================================

section(
    "DASHBOARD",
    "Explore every angle",
    "Choose a section to explore the data.",
)

pages = [
    "Overview",
    "Gender Analysis",
    "Sampling Experiment",
    "Candidates & Expenditure",
    "Data Explorer",
    "Voting & News",
]

st.radio(
    "Dashboard sections",
    pages,
    horizontal=True,
    label_visibility="collapsed",
    key="main_navigation",
)

page = st.session_state.main_navigation
st.markdown("---")


# ============================================================
# 11. OVERVIEW
# ============================================================

if page == "Overview":
    section(
        "01 / OVERVIEW",
        "The participation picture",
        "Explore historical turnout and regional differences.",
    )

    left, right = st.columns([1.35, 1])

    yearly = df.groupby("Year", as_index=False).agg(
        Electors=("Total_Electors", "sum"),
        Voters=("Total_Voters", "sum"),
    )
    yearly["Turnout (%)"] = (
        yearly["Voters"] / yearly["Electors"] * 100
    )

    with left:
        st.markdown("#### Turnout across election years")

        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(
            yearly["Year"],
            yearly["Turnout (%)"],
            marker="o",
            linewidth=3,
            markersize=6,
            color="#7d91ff",
            markerfacecolor="#53e0e0",
        )
        ax.fill_between(
            yearly["Year"],
            yearly["Turnout (%)"],
            alpha=.12,
            color="#7d91ff",
        )
        ax.set_title(
            "Weighted voter turnout by year",
            loc="left",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel("Election year")
        ax.set_ylabel("Turnout (%)")
        chart_theme(fig, ax)
        show_fig(fig)

    with right:
        st.markdown("#### Participation split")

        fig, ax = plt.subplots(figsize=(6, 4))
        if electors > 0:
            ax.pie(
                [voters, non_voters],
                labels=["Votes recorded", "Remaining electors"],
                autopct="%1.1f%%",
                startangle=90,
                colors=["#7189ff", "#263752"],
                textprops={"color": "#e7edff", "fontsize": 9},
                wedgeprops={
                    "width": .38,
                    "edgecolor": "#10182b",
                    "linewidth": 3,
                },
                pctdistance=.78,
            )
        ax.set_title(
            "Voters vs remaining electors",
            loc="left",
            fontsize=13,
            fontweight="bold",
            color="#f4f7ff",
        )
        chart_theme(fig, ax)
        show_fig(fig)

    section("REGIONAL COMPARISON", "Where turnout stands")

    region = view.groupby("State", as_index=False).agg(
        Electors=("Total_Electors", "sum"),
        Voters=("Total_Voters", "sum"),
    )
    region["Turnout (%)"] = (
        region["Voters"] / region["Electors"] * 100
    )

    region = region.sort_values("Turnout (%)", ascending=False)
    top = region.head(15).sort_values("Turnout (%)")

    fig, ax = plt.subplots(figsize=(10, max(4, len(top) * .32)))
    ax.barh(
        top["State"],
        top["Turnout (%)"],
        color="#7189ff",
        height=.68,
    )
    ax.set_xlabel("Turnout (%)")
    ax.set_title(
        "Top regions by turnout",
        loc="left",
        fontsize=13,
        fontweight="bold",
    )
    chart_theme(fig, ax)
    show_fig(fig)

    with st.expander("View regional figures"):
        st.dataframe(region, use_container_width=True, hide_index=True)

    a, b, c = st.columns(3)

    with a:
        card(
            "DATA CLEANING",
            "Reliable inputs",
            f"{rows_before - len(df):,} rows removed during basic validation.",
        )

    with b:
        card(
            "PARTICIPATION",
            "Weighted turnout",
            f"The selected records have a weighted turnout of {turnout:.2f}%.",
        )

    with c:
        card(
            "INTERPRETATION",
            "Historical data",
            "The charts describe supplied historical records, not live vote "
            "counts or election predictions.",
        )


# ============================================================
# 12. GENDER ANALYSIS
# ============================================================

elif page == "Gender Analysis":
    section(
        "02 / GENDER ANALYSIS",
        "Participation by gender",
        "Compare registered electors, voters, and turnout rates.",
    )

    me = float(view["Male_Electors"].sum())
    fe = float(view["Female_Electors"].sum())
    mv = float(view["Male_Voters"].sum())
    fv = float(view["Female_Voters"].sum())

    mr = mv / me * 100 if me else 0
    fr = fv / fe * 100 if fe else 0

    a, b, c = st.columns(3)
    a.metric("Male turnout", f"{mr:.2f}%")
    b.metric("Female turnout", f"{fr:.2f}%")
    c.metric("Turnout gap", f"{abs(mr - fr):.2f} pp")

    left, right = st.columns(2)

    with left:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(
            ["Male", "Female"],
            [me, fe],
            color=["#7189ff", "#53d8d3"],
            width=.55,
        )
        ax.set_title(
            "Registered electors",
            loc="left",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel("Electors")
        chart_theme(fig, ax)
        show_fig(fig)

    with right:
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(
            ["Male", "Female"],
            [mr, fr],
            color=["#7189ff", "#53d8d3"],
            width=.55,
        )
        ax.set_title(
            "Turnout rate by gender",
            loc="left",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel("Turnout (%)")

        for bar, val in zip(bars, [mr, fr]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + .5,
                f"{val:.1f}%",
                ha="center",
                color="#f4f7ff",
                fontweight="bold",
            )

        chart_theme(fig, ax)
        show_fig(fig)

    gender_table = pd.DataFrame({
        "Group": ["Male", "Female"],
        "Electors": [me, fe],
        "Voters": [mv, fv],
        "Turnout (%)": [mr, fr],
    })
    st.dataframe(
        gender_table, use_container_width=True, hide_index=True
    )


# ============================================================
# 13. SAMPLING EXPERIMENT
# ============================================================

elif page == "Sampling Experiment":
    section(
        "03 / PROBABILITY LAB",
        "Sampling experiment",
        "Compare a random subset of records with the selected dataset.",
    )

    card(
        "HOW IT WORKS",
        "From population to sample",
        "A random sample selects a subset of records. Its weighted turnout "
        "is compared with the full filtered dataset.",
    )

    st.warning(
        "Voting is necessary!!!"
    )

    sampleable = view.dropna(
        subset=["Total_Electors", "Total_Voters"]
    ).copy()
    sampleable = sampleable[sampleable["Total_Electors"] > 0]

    if len(sampleable) < 2:
        st.info("At least two valid records are needed for sampling.")

    else:
        max_size = len(sampleable)
        default_size = max(1, max_size // 2)

        # Keep the sample slider in range if the dataset changes.
        if (
            "sample_size" not in st.session_state
            or not isinstance(st.session_state.sample_size, int)
            or not 1 <= st.session_state.sample_size <= max_size
        ):
            st.session_state.sample_size = default_size

        c1, c2 = st.columns([1.2, 1])

        with c1:
            sample_size = st.slider(
                "Number of records to sample",
                min_value=1,
                max_value=max_size,
                key="sample_size",
            )

        with c2:
            seed = st.number_input(
                "Random seed",
                min_value=0,
                max_value=999999,
                step=1,
                key="sample_seed",
            )

        sample = sampleable.sample(
            n=int(sample_size),
            random_state=int(seed),
        )

        sample_electors = float(sample["Total_Electors"].sum())
        sample_voters = float(sample["Total_Voters"].sum())
        full_electors = float(sampleable["Total_Electors"].sum())
        full_voters = float(sampleable["Total_Voters"].sum())

        sample_rate = (
            sample_voters / sample_electors * 100
            if sample_electors else 0
        )
        benchmark = (
            full_voters / full_electors * 100
            if full_electors else 0
        )
        error = abs(sample_rate - benchmark)

        x, y, z = st.columns(3)
        x.metric("Records sampled", f"{len(sample):,} / {len(sampleable):,}")
        y.metric("Sample turnout", f"{sample_rate:.2f}%")
        z.metric("Full dataset turnout", f"{benchmark:.2f}%")

        fig, ax = plt.subplots(figsize=(9, 4))
        bars = ax.bar(
            ["Full dataset", "Random sample"],
            [benchmark, sample_rate],
            color=["#53d8d3", "#7189ff"],
            width=.5,
        )
        ax.set_ylabel("Turnout (%)")
        ax.set_title(
            "Sample estimate vs dataset benchmark",
            loc="left",
            fontsize=13,
            fontweight="bold",
        )

        for bar, val in zip(bars, [benchmark, sample_rate]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + .5,
                f"{val:.2f}%",
                ha="center",
                color="#f4f7ff",
                fontweight="bold",
            )

        chart_theme(fig, ax)
        show_fig(fig)

        card(
            "INTERPRETATION",
            "What does the result mean?",
            f"The sample contains {len(sample):,} of {len(sampleable):,} "
            f"records. Its turnout differs from the dataset benchmark by "
            f"{error:.2f} percentage points. Change the sample size or "
            "random seed to see how the estimate changes.",
        )

        section("SAMPLE RECORDS", "Inspect or export the sample")
        st.dataframe(sample, use_container_width=True, hide_index=True)

        st.download_button(
            "↓ Download sampled records",
            sample.to_csv(index=False).encode("utf-8"),
            "election_sample.csv",
            "text/csv",
        )


# ============================================================
# 14. CANDIDATES AND EXPENDITURE
# ============================================================

elif page == "Candidates & Expenditure":
    section(
        "04 / ELECTION DETAILS",
        "Candidates, winners & expenditure",
        "Explore additional source files when available.",
    )

    if candidates.empty:
        st.info("dataset2.csv is missing or could not be read.")

    else:
        cand_view = candidates.copy()

        if "Year" in cand_view.columns and year_choice != "All years":
            cand_view = cand_view[
                num(cand_view["Year"]) == year_choice
            ]

        if "State" in cand_view.columns and state_choice != "All states":
            cand_view = cand_view[
                cand_view["State"].astype(str).str.casefold()
                == state_choice.casefold()
            ]

        if "State" in cand_view.columns and search.strip():
            cand_view = cand_view[
                cand_view["State"].astype(str).str.contains(
                    search.strip(), case=False, na=False, regex=False
                )
            ]

        winner_cols = [
            col for col in ["Male_Winner", "Female_Winner"]
            if col in cand_view.columns
        ]

        if winner_cols:
            cols = st.columns(len(winner_cols))
            for ui, col in zip(cols, winner_cols):
                ui.metric(
                    col.replace("_", " "),
                    f"{num(cand_view[col]).sum():,.0f}",
                )

        st.markdown("#### Candidate records")
        st.caption(
            f"{len(cand_view):,} rows · {len(cand_view.columns)} columns"
        )
        st.dataframe(
            cand_view, use_container_width=True, hide_index=True
        )

        st.download_button(
            "↓ Download candidate data",
            cand_view.to_csv(index=False).encode("utf-8"),
            "election_candidates.csv",
            "text/csv",
        )

    st.markdown("---")

    if expenses.empty:
        st.info("dataset3.csv is missing or could not be read.")

    else:
        st.markdown("#### Historical expenditure records")
        st.dataframe(
            expenses, use_container_width=True, hide_index=True
        )

        year_col = next(
            (
                col for col in expenses.columns
                if col.lower().strip() in ["year", "election_year"]
            ),
            None,
        )

        exp_col = next(
            (
                col for col in expenses.columns
                if col.lower().strip() in [
                    "gove_expense", "govt_expense",
                    "government_expense", "expenditure",
                    "expense", "total_expenditure",
                ]
            ),
            None,
        )

        if year_col and exp_col:
            ex = expenses.copy()
            ex[year_col] = num(ex[year_col])
            ex[exp_col] = num(ex[exp_col])
            ex = ex.dropna(
                subset=[year_col, exp_col]
            ).sort_values(year_col)

            if not ex.empty:
                fig, ax = plt.subplots(figsize=(9, 4))
                ax.plot(
                    ex[year_col],
                    ex[exp_col],
                    marker="o",
                    linewidth=3,
                    color="#53d8d3",
                )
                ax.set_title(
                    "Reported expenditure by year",
                    loc="left",
                    fontsize=13,
                    fontweight="bold",
                )
                ax.set_xlabel("Year")
                ax.set_ylabel("Expenditure")
                chart_theme(fig, ax)
                show_fig(fig)
        else:
            st.caption(
                "An expenditure chart needs a year column and a recognised "
                "expenditure column."
            )


# ============================================================
# 15. DATA EXPLORER
# ============================================================

elif page == "Data Explorer":
    section(
        "05 / DATA EXPLORER",
        "Inspect the source records",
        "Search, review missing values, and export filtered data.",
    )

    st.text_input(
        "Search all visible columns",
        placeholder="Search a state, year or value...",
        key="explorer_search",
    )

    query = st.session_state.explorer_search
    explore = view.copy()

    if query.strip():
        mask = explore.astype(str).apply(
            lambda col: col.str.contains(
                query.strip(),
                case=False,
                na=False,
                regex=False,
            )
        ).any(axis=1)
        explore = explore[mask]

    st.caption(f"{len(explore):,} matching rows")
    st.dataframe(
        explore, use_container_width=True, hide_index=True
    )

    st.download_button(
        "↓ Download filtered data",
        explore.to_csv(index=False).encode("utf-8"),
        "election_filtered_data.csv",
        "text/csv",
    )

    section("DATA QUALITY", "Missing values & types")

    quality = pd.DataFrame({
        "Column": df_raw.columns,
        "Missing values": df_raw.isna().sum().values,
        "Missing (%)": (df_raw.isna().mean().values * 100).round(2),
        "Data type": df_raw.dtypes.astype(str).values,
    })

    st.dataframe(
        quality, use_container_width=True, hide_index=True
    )

    with st.expander("View source file details"):
        for label, data in [
            ("Dataset 1 — Electors and voters", df_raw),
            ("Dataset 2 — Candidates and winners", candidates),
            ("Dataset 3 — Expenditure", expenses),
        ]:
            st.markdown(
                f"**{label}** · {len(data):,} rows · "
                f"{len(data.columns)} columns"
            )
            if not data.empty:
                st.write(data.columns.tolist())


# ============================================================
# 16. VOTING AWARENESS AND NEWS
# ============================================================

elif page == "Voting & News":
    section(
        "06 / CITIZEN PARTICIPATION",
        "Voting awareness & resources",
        "Explore voter awareness visuals and official election portals.",
    )

    st.markdown("""
    <div class="news-hero">
        <span class="tag">YOUR VOICE MATTERS</span>
        <h2 style="color:white">Democracy is powered by people.</h2>
        <p>
            Participation data helps us understand how communities
            engage with elections. Check official sources for current
            election information.
        </p>
    </div>
    """, unsafe_allow_html=True)

    section("VOTING GALLERY", "The power of participation")

    image_specs = [
        (
            ["voting-india-map.png", "voting-india-map.jpg"],
            "India & democracy",
            "A visual reminder of participation across India.",
        ),
        (
            ["voter-inked-finger.png", "voter-inked-finger.jpg"],
            "Your vote matters",
            "The ink mark represents participation in democracy.",
        ),
        (
            ["electoral-roll.png", "electoral-roll.jpg"],
            "Election day",
            "Election materials help voters complete the process.",
        ),
    ]

    roots = [BASE / "assets", BASE / "voting"]
    gallery = st.columns(3, gap="large")

    for col, (names, title, description) in zip(gallery, image_specs):
        found = None

        for root in roots:
            if root.exists():
                for path in root.rglob("*"):
                    if path.is_file() and path.name.casefold() in [
                        name.casefold() for name in names
                    ]:
                        found = path
                        break
            if found:
                break

        with col:
            if found:
                st.image(
                    str(found),
                    caption=description,
                    use_container_width=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="panel">
                        <span class="tag">VOTER AWARENESS</span>
                        <h3>{escape(title)}</h3>
                        <p>{escape(description)}</p>
                        <p style="font-size:12px">
                            Add an image to the assets folder to display it.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    section("LIVE NEWS", "Latest election headlines")

    st.caption(
        "Headlines come from Google News RSS. Internet access is required."
    )

    news_url = (
        "https://news.google.com/rss/search?"
        "q=India+elections+OR+Election+Commission+India"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    )

    st.button(
        "↻ Refresh election news",
        on_click=lambda: st.session_state.update(
            news_refresh=st.session_state.news_refresh + 1
        ),
    )

    @st.cache_data(ttl=900, show_spinner=False)
    def get_election_news(url, refresh_token):
        if feedparser is None:
            return []

        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:12]:
            summary = re.sub(
                r"<[^>]+>", " ", entry.get("summary", "")
            )
            summary = unescape(summary).strip()

            articles.append({
                "title": entry.get("title", "Election news update"),
                "link": entry.get("link", ""),
                "summary": summary[:450],
                "published": entry.get(
                    "published", "Publication date unavailable"
                ),
            })

        return articles

    if feedparser is None:
        st.warning(
            "Install feedparser to enable live headlines: "
            "pip install feedparser"
        )
    else:
        try:
            with st.spinner("Loading election headlines..."):
                articles = get_election_news(
                    news_url, st.session_state.news_refresh
                )

            if articles:
                for article in articles:
                    title = escape(article["title"])
                    summary = escape(
                        article["summary"]
                        or "Open the article for further details."
                    )
                    published = escape(article["published"])
                    link = article["link"]

                    # Accept only HTTP(S) article links.
                    if not link.startswith(("https://", "http://")):
                        continue

                    safe_link = escape(link, quote=True)

                    st.markdown(
                        f"""
                        <div class="news-card">
                            <div class="news-date">
                                NEWS UPDATE · {published}
                            </div>
                            <h3>{title}</h3>
                            <p>{summary}</p>
                            <a class="news-link"
                               href="{safe_link}"
                               target="_blank"
                               rel="noopener noreferrer">
                                Read full article ↗
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info(
                    "No headlines are available. Check the official "
                    "election resources below."
                )

        except Exception:
            st.warning(
                "The news feed could not be loaded. "
                "You can still visit the official portals below."
            )

    section("WHAT TO WATCH", "Future election updates")

    future_items = [
        (
            "01 · ELECTION SCHEDULES",
            "Upcoming polls and by-elections",
            "Check official notifications for polling dates, nominations, "
            "counting dates and constituency details.",
            "https://www.eci.gov.in/",
        ),
        (
            "02 · VOTER REGISTRATION",
            "Electoral roll revisions",
            "Check announcements about new voter registration, corrections "
            "and checking your name on the electoral roll.",
            "https://voters.eci.gov.in/",
        ),
        (
            "03 · RESULTS & COUNTING",
            "Official results updates",
            "Use the Election Commission results portal for published "
            "counting updates and final results.",
            "https://results.eci.gov.in/",
        ),
        (
            "04 · DIGITAL ELECTIONS",
            "Technology and voter services",
            "Follow official announcements about voter services and "
            "election administration.",
            "https://www.eci.gov.in/",
        ),
    ]

    future_cols = st.columns(2, gap="large")

    for index, item in enumerate(future_items):
        tag, title, description, link = item

        with future_cols[index % 2]:
            st.markdown(
                f"""
                <div class="news-card">
                    <div class="news-date">{escape(tag)}</div>
                    <h3>{escape(title)}</h3>
                    <p>{escape(description)}</p>
                    <a class="news-link"
                       href="{escape(link, quote=True)}"
                       target="_blank"
                       rel="noopener noreferrer">
                        Check official updates ↗
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )

    section("VERIFIED SOURCES", "Official election portals")

    official = [
        (
            "ELECTION COMMISSION",
            "ECI announcements",
            "Official announcements and notifications.",
            "https://www.eci.gov.in/",
        ),
        (
            "VOTER SERVICES",
            "Voter services",
            "Registration and electoral roll services.",
            "https://voters.eci.gov.in/",
        ),
        (
            "RESULTS PORTAL",
            "Election results",
            "Published results and counting information.",
            "https://results.eci.gov.in/",
        ),
    ]

    cols = st.columns(3, gap="large")

    for col, item in zip(cols, official):
        tag, title, description, link = item

        with col:
            st.markdown(
                f"""
                <div class="panel">
                    <span class="tag">{escape(tag)}</span>
                    <h3>{escape(title)}</h3>
                    <p>{escape(description)}</p>
                    <a class="news-link"
                       href="{escape(link, quote=True)}"
                       target="_blank"
                       rel="noopener noreferrer">
                        Open official portal ↗
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption("Election Insights · India")


# ============================================================
# 17. FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <b style="color:#cbd7ef">ELECTION INSIGHTS · INDIA</b><br>
    <span style="color:#596a87">
        Built for exploration, transparency and learning.
    </span>
</div>
""", unsafe_allow_html=True)