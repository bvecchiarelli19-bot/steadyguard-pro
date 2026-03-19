"""
SteadyGuard Pro — Custom Ticker Backtest
==========================================
Production frontend matching the SteadyGuard site aesthetic.
"""
import numpy as np
import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(page_title="SteadyGuard Pro — Custom Backtest",
                   page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# ── CSS: Match the SteadyGuard site aesthetic ──────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ── Base ── */
    :root {
        --bg-primary: #080c14;
        --bg-card: #0f1520;
        --bg-card-hover: #131a28;
        --bg-input: #111827;
        --border: #1a2235;
        --border-hover: #243049;
        --text-primary: #f0f4f8;
        --text-secondary: #8494a7;
        --text-muted: #4a5568;
        --accent: #10b981;
        --accent-dim: #059669;
        --accent-glow: rgba(16, 185, 129, 0.15);
        --red: #ef4444;
        --yellow: #f59e0b;
        --blue: #3b82f6;
        --mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
        --sans: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
        font-family: var(--sans);
    }

    #MainMenu, footer, header, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
        visibility: hidden !important;
        display: none !important;
    }

    .block-container {
        padding: 2.5rem 3rem 4rem 3rem;
        max-width: 1100px;
    }

    /* ── Streamlit Widget Overrides ── */
    .stTextInput > div > div > input {
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: var(--mono) !important;
        font-size: 0.88rem !important;
        padding: 0.65rem 0.9rem !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent-glow) !important;
    }
    .stTextInput label {
        font-family: var(--sans) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* Slider */
    .stSlider label {
        font-family: var(--sans) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    .stSlider [data-baseweb="slider"] {
        margin-top: 0.3rem !important;
    }
    [data-testid="stThumbValue"] {
        font-family: var(--mono) !important;
        font-weight: 600 !important;
        color: var(--accent) !important;
    }

    /* Button */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent), var(--accent-dim)) !important;
        color: #fff !important;
        font-family: var(--sans) !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.03em !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.7rem 2rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 25px rgba(16, 185, 129, 0.35) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-family: var(--sans) !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }

    /* Tooltip / help icon */
    [data-testid="stTooltipIcon"] {
        color: var(--text-muted) !important;
    }

    /* ── Custom Classes ── */
    .sg-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.4rem;
    }
    .sg-logo {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .sg-logo-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, var(--accent), #059669);
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
    }
    .sg-wordmark {
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.03em;
    }
    .sg-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: linear-gradient(135deg, var(--accent), var(--accent-dim));
        color: #fff;
        font-size: 0.62rem;
        font-weight: 700;
        padding: 0.2rem 0.55rem;
        border-radius: 4px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-left: 0.6rem;
    }
    .sg-tagline {
        font-size: 1rem;
        color: var(--text-muted);
        font-weight: 400;
        margin: 0.3rem 0 2rem 0;
        letter-spacing: 0.01em;
    }
    .sg-divider {
        height: 1px;
        background: var(--border);
        margin: 2rem 0;
    }
    .sg-section-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 1rem;
    }

    /* Metric Cards */
    .m-row { display: flex; gap: 0.8rem; margin: 1.2rem 0; flex-wrap: wrap; }
    .m-card {
        flex: 1; min-width: 135px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.1rem 1rem;
        text-align: center;
        transition: border-color 0.2s ease, background 0.2s ease;
    }
    .m-card:hover { border-color: var(--border-hover); background: var(--bg-card-hover); }
    .m-card.active {
        border-color: rgba(16, 185, 129, 0.4);
        background: linear-gradient(180deg, rgba(16,185,129,0.06) 0%, var(--bg-card) 100%);
    }
    .m-lbl {
        font-size: 0.65rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 0.4rem;
    }
    .m-val {
        font-family: var(--mono);
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .m-val.g { color: var(--accent); }
    .m-delta {
        font-family: var(--mono);
        font-size: 0.72rem;
        margin-top: 0.25rem;
        color: var(--text-muted);
    }
    .m-delta.up { color: var(--accent); }
    .m-delta.dn { color: var(--red); }

    /* Allocation bar */
    .alloc-wrap {
        display: flex; align-items: center; gap: 0.6rem;
        margin: 0.3rem 0 0.8rem 0;
    }
    .alloc-bar { flex: 1; height: 6px; border-radius: 3px; overflow: hidden; display: flex; }
    .alloc-eq { background: var(--blue); }
    .alloc-bd { background: var(--yellow); }
    .alloc-tag {
        font-family: var(--mono);
        font-size: 0.72rem;
        color: var(--text-muted);
        white-space: nowrap;
    }

    /* Regime chips */
    .r-row { display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .r-chip {
        font-family: var(--mono); font-size: 0.68rem; font-weight: 600;
        padding: 0.25rem 0.6rem; border-radius: 5px;
    }
    .r-low { background: rgba(16,185,129,0.12); color: #6ee7b7; }
    .r-mid { background: rgba(250,204,21,0.12); color: #fcd34d; }
    .r-high { background: rgba(249,115,22,0.12); color: #fdba74; }
    .r-crisis { background: rgba(239,68,68,0.12); color: #fca5a5; }

    /* Comparison table */
    .cmp { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    .cmp th {
        font-family: var(--sans);
        color: var(--text-muted);
        font-weight: 600;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        text-align: right;
        padding: 0.7rem 1rem;
        border-bottom: 1px solid var(--border);
    }
    .cmp th:first-child { text-align: left; }
    .cmp td {
        font-family: var(--mono);
        padding: 0.65rem 1rem;
        text-align: right;
        color: var(--text-secondary);
        border-bottom: 1px solid rgba(26,34,53,0.5);
        font-size: 0.85rem;
    }
    .cmp td:first-child {
        text-align: left;
        font-family: var(--sans);
        font-weight: 500;
        color: var(--text-secondary);
    }
    .cmp tr:hover td { background: rgba(255,255,255,0.015); }
    .cmp .w { color: var(--accent); font-weight: 600; }
    .cmp .l { color: var(--red); }

    /* Warning box */
    .sg-warn {
        background: rgba(245,158,11,0.06);
        border: 1px solid rgba(245,158,11,0.2);
        border-radius: 8px;
        padding: 0.65rem 1rem;
        font-size: 0.8rem;
        color: #fbbf24;
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        line-height: 1.5;
    }

    /* Data info line */
    .sg-data-info {
        font-family: var(--mono);
        font-size: 0.78rem;
        color: var(--text-muted);
        padding: 0.5rem 0;
    }

    /* Methodology note */
    .sg-method {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-size: 0.78rem;
        color: var(--text-muted);
        line-height: 1.65;
        margin-top: 1rem;
    }
    .sg-method strong { color: var(--text-secondary); }

    /* Footer */
    .sg-foot {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.7rem;
        margin-top: 3.5rem;
        padding: 1.5rem 0;
        border-top: 1px solid var(--border);
        letter-spacing: 0.01em;
    }

    /* Info card */
    .sg-info-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
    }
    .sg-info-label {
        font-size: 0.65rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 0.5rem;
    }

    /* Instructions placeholder */
    .sg-placeholder {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--text-muted);
    }
    .sg-placeholder-icon {
        font-size: 2.5rem;
        margin-bottom: 0.8rem;
        opacity: 0.4;
    }
    .sg-placeholder-text {
        font-size: 1.1rem;
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: 0.3rem;
    }
    .sg-placeholder-sub {
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

CL = {"static": "#6366f1", "sg": "#10b981",
      "sf": "rgba(99,102,241,0.12)", "sgf": "rgba(16,185,129,0.12)",
      "grid": "#1a2235", "bg": "#080c14", "paper": "#080c14", "txt": "#8494a7"}


@st.cache_data
def load_signals():
    for d in [Path("."), Path(__file__).parent, Path("/mnt/user-data/uploads")]:
        p = d / "monthly_data.json"
        if p.exists():
            with open(p) as f:
                return json.load(f)
    st.error("monthly_data.json not found.")
    st.stop()


@st.cache_data(ttl=3600)
def fetch_prices(tickers_str, bond_ticker):
    import yfinance as yf
    import pandas as pd
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
    all_tickers = list(set(tickers + [bond_ticker]))

    data = yf.download(all_tickers, start="1998-01-01", auto_adjust=True,
                       progress=False, threads=True)
    if data.empty:
        return None, "No data returned. Check ticker symbols."

    # Handle yfinance column formats (varies by version and ticker count)
    if isinstance(data.columns, pd.MultiIndex):
        # Multi-ticker: columns are ('Close', 'AAPL'), ('Close', 'AMZN'), etc.
        if 'Close' in data.columns.get_level_values(0):
            closes = data['Close'].copy()
        elif 'close' in [c.lower() for c in data.columns.get_level_values(0)]:
            lvl0 = data.columns.get_level_values(0)
            close_label = [c for c in lvl0 if c.lower() == 'close'][0]
            closes = data[close_label].copy()
        else:
            # Try first level
            closes = data.iloc[:, :len(all_tickers)].copy()
            closes.columns = all_tickers
    else:
        # Single ticker
        if 'Close' in data.columns:
            closes = data[['Close']].copy()
            closes.columns = [all_tickers[0]]
        else:
            closes = data.iloc[:, [0]].copy()
            closes.columns = [all_tickers[0]]

    # Ensure all requested tickers are present
    missing = [t for t in all_tickers if t not in closes.columns]
    if missing:
        return None, f"Could not find data for: {', '.join(missing)}"

    # Drop rows where ALL equity tickers are NaN (keep partial data)
    # Only require that all tickers have data (dropna on the full set)
    closes = closes.dropna()

    if len(closes) < 20:
        return None, f"Insufficient overlapping data ({len(closes)} days). Some tickers may have limited history."
    return closes, None


def build_portfolio_returns(closes, tickers, weights, bond_ticker):
    import pandas as pd
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    weight_list = [float(w) / 100.0 for w in weights]
    total_w = sum(weight_list)
    weight_list = [w / total_w for w in weight_list]
    rets = closes.pct_change().dropna()
    port_ret = sum(rets[t] * w for t, w in zip(ticker_list, weight_list))
    bond_ret = rets[bond_ticker]
    combined = pd.DataFrame({"equity": port_ret, "bond": bond_ret}).dropna()
    combined["ym"] = combined.index.to_period("M").astype(str)
    return combined


def run_daily_backtest(combined, signals_dict, eq_pct):
    eq = eq_pct / 100.0
    vs = vg = 10000.0
    prev_scalar = 1.0
    prev_ym = None
    dates, cs, cg = [], [10000.0], [10000.0]
    for date, row in combined.iterrows():
        ym = row["ym"]
        sig = signals_dict.get(ym)
        scalar = sig["scalar"] if sig else 1.0
        rs, rb = row["equity"], row["bond"]
        if prev_ym is not None and ym != prev_ym:
            vg *= (1 - 0.001 * abs(scalar - prev_scalar))
        vs *= (1 + eq * rs + (1 - eq) * rb)
        eq_adj = eq * scalar
        vg *= (1 + eq_adj * rs + (1 - eq_adj) * rb)
        dates.append(date)
        cs.append(vs)
        cg.append(vg)
        prev_scalar = scalar
        prev_ym = ym
    return dates, cs, cg


def calc_metrics(curve, n_yr):
    a = np.array(curve)
    if a[0] == 0 or n_yr == 0:
        return {k: 0 for k in ["CAGR","MaxDD","Vol","Sharpe","Calmar","Total"]}
    cagr = (a[-1] / a[0]) ** (1 / n_yr) - 1
    r = np.diff(a) / a[:-1]
    vol = np.std(r, ddof=1) * np.sqrt(252)
    sharpe = cagr / vol if vol > 0 else 0
    pk = np.maximum.accumulate(a)
    mdd = ((a - pk) / pk).min()
    calmar = cagr / abs(mdd) if mdd != 0 else 0
    return {"CAGR": cagr, "MaxDD": mdd, "Vol": vol, "Sharpe": sharpe,
            "Calmar": calmar, "Total": a[-1]/a[0] - 1}


# ── Load ───────────────────────────────────────────────────────────────
mdata = load_signals()
signals_dict = {m["d"]: m for m in mdata}
rc = {}
for m in mdata:
    rc[m['regime']] = rc.get(m['regime'], 0) + 1

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="sg-header">
    <div class="sg-logo">
        <div class="sg-logo-icon">🛡️</div>
        <span class="sg-wordmark">SteadyGuard</span>
        <span class="sg-badge">PRO · CUSTOM</span>
    </div>
</div>
<div class="sg-tagline">Backtest any portfolio with V3c regime protection</div>
""", unsafe_allow_html=True)

# ── Input Section ──────────────────────────────────────────────────────
st.markdown('<div class="sg-section-label">Portfolio Configuration</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([2.2, 1, 0.8])
with c1:
    tickers_input = st.text_input("Equity Tickers", value="SPY",
        help="Comma-separated ticker symbols (e.g. QQQ, AAPL, MSFT)",
        placeholder="SPY, QQQ, AAPL")
with c2:
    ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    if len(ticker_list) == 1:
        weights_input = "100"
        st.text_input("Weights (%)", value="100", disabled=True)
    else:
        weights_input = st.text_input("Weights (%)",
            value=", ".join([str(round(100/len(ticker_list)))] * len(ticker_list)),
            help=f"Enter {len(ticker_list)} weights summing to 100",
            placeholder="50, 30, 20")
with c3:
    bond_ticker = st.text_input("Bond ETF", value="TLT",
        help="Safe-haven asset for risk-off periods")

# Parse weights
try:
    if len(ticker_list) == 1:
        weight_list = [100.0]
    else:
        weight_list = [float(w.strip()) for w in weights_input.split(",") if w.strip()]
    if len(weight_list) != len(ticker_list):
        weight_list = [100.0 / len(ticker_list)] * len(ticker_list)
    total_w = sum(weight_list)
    wn = [w / total_w * 100 for w in weight_list]
except:
    weight_list = [100.0 / len(ticker_list)] * len(ticker_list)
    wn = weight_list

# Slider + Info
c_sl, _, c_nfo = st.columns([2.2, 0.2, 1.3])
with c_sl:
    eq_pct = st.slider("Total Equity Allocation", 0, 100, 100, 5,
                       help="% in equities. Remainder goes to bonds.")
    bd_pct = 100 - eq_pct
    parts = " + ".join([f"**{t}** {w*eq_pct/100:.0f}%" for t, w in zip(ticker_list, wn)])
    bond_part = f"**{bond_ticker.strip().upper()}** {bd_pct}%"

    st.markdown(f"""
    <div class="alloc-wrap">
        <span class="alloc-tag" style="color:var(--blue)">{eq_pct}% equity</span>
        <div class="alloc-bar">
            <div class="alloc-eq" style="width:{eq_pct}%"></div>
            <div class="alloc-bd" style="width:{bd_pct}%"></div>
        </div>
        <span class="alloc-tag" style="color:var(--yellow)">{bd_pct}% bonds</span>
    </div>
    """, unsafe_allow_html=True)

    from datetime import date as _date
    start_date_input = st.date_input("Backtest Start Date (optional)",
                               value=None,
                               min_value=_date(1998, 1, 1),
                               max_value=_date(2026, 1, 31),
                               help="Leave blank to use all available data, or set a date to simulate when you built your portfolio.")

with c_nfo:
    st.markdown(f"""
    <div class="sg-info-card">
        <div class="sg-info-label">V3c Signal Coverage</div>
        <div style="font-family:var(--mono);font-size:0.88rem;color:var(--text-primary);margin-bottom:0.3rem">
            Jan 1998 — Jan 2026</div>
        <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.5rem">337 months</div>
        <div class="r-row">
            <span class="r-chip r-low">LOW {rc.get('LOW',0)}</span>
            <span class="r-chip r-mid">MID {rc.get('MID',0)}</span>
            <span class="r-chip r-high">HIGH {rc.get('HIGH',0)}</span>
            <span class="r-chip r-crisis">CRISIS {rc.get('CRISIS',0)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Caveat
non_spy = any(t != "SPY" for t in ticker_list)
if non_spy:
    st.markdown(f"""
    <div class="sg-warn">
        <span>⚠️</span>
        <span>V3c signals are calibrated on S&P 500 (SPY). Applied to other assets, protection
        effectiveness depends on correlation with SPY. Results are indicative, not validated.</span>
    </div>
    """, unsafe_allow_html=True)

# ── Run ────────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
run_clicked = st.button("Run Backtest", type="primary", use_container_width=True)

if run_clicked or st.session_state.get("has_run", False):
    st.session_state["has_run"] = True

    all_tickers = list(set(ticker_list + [bond_ticker.strip().upper()]))
    with st.spinner(f"Fetching data for {', '.join(all_tickers)}..."):
        closes, error = fetch_prices(", ".join(all_tickers), bond_ticker.strip().upper())

    if error:
        st.error(error)
        st.stop()

    combined = build_portfolio_returns(closes, tickers_input, weight_list, bond_ticker.strip().upper())
    combined_f = combined[combined["ym"].isin(signals_dict.keys())]

    # Apply user's start date if provided
    if start_date_input is not None:
        import pandas as pd
        combined_f = combined_f[combined_f.index >= pd.Timestamp(start_date_input)]

    if len(combined_f) < 20:
        st.error(f"Only {len(combined_f)} trading days in the selected period. Need at least 20.")
        st.stop()

    start_d = combined_f.index.min()
    end_d = combined_f.index.max()
    n_years = (end_d - start_d).days / 365.25

    st.markdown(f"""
    <div class="sg-data-info">
        {start_d.strftime('%b %Y')} — {end_d.strftime('%b %Y')} · {n_years:.1f} years · {len(combined_f):,} trading days
    </div>
    """, unsafe_allow_html=True)

    dates, cs, cg = run_daily_backtest(combined_f, signals_dict, eq_pct)
    all_dates = [start_d] + dates
    sm = calc_metrics(cs, n_years)
    gm = calc_metrics(cg, n_years)

    # ── Metrics ────────────────────────────────────────────────────────
    st.markdown('<div class="sg-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sg-section-label">Results</div>', unsafe_allow_html=True)

    dd_ok = gm['MaxDD'] > sm['MaxDD']
    cagr_ok = gm['CAGR'] > sm['CAGR']

    def dh(sv, gv, fmt="pct"):
        d = gv - sv
        c = "up" if d > 0 else "dn"
        if fmt == "num":
            return f'<div class="m-delta {c}">{"+" if d>0 else ""}{d:.2f} vs static</div>'
        return f'<div class="m-delta {c}">{"+" if d>0 else ""}{d:.2%} vs static</div>'

    st.markdown(f"""
    <div class="m-row">
        <div class="m-card {'active' if cagr_ok else ''}">
            <div class="m-lbl">CAGR</div>
            <div class="m-val {'g' if cagr_ok else ''}">{gm['CAGR']:.2%}</div>
            {dh(sm['CAGR'], gm['CAGR'])}
        </div>
        <div class="m-card {'active' if dd_ok else ''}">
            <div class="m-lbl">Max Drawdown</div>
            <div class="m-val {'g' if dd_ok else ''}">{gm['MaxDD']:.2%}</div>
            {dh(sm['MaxDD'], gm['MaxDD'])}
        </div>
        <div class="m-card active">
            <div class="m-lbl">Sharpe Ratio</div>
            <div class="m-val g">{gm['Sharpe']:.2f}</div>
            {dh(sm['Sharpe'], gm['Sharpe'], fmt="num")}
        </div>
        <div class="m-card">
            <div class="m-lbl">Growth of $10k</div>
            <div class="m-val">${cg[-1]:,.0f}</div>
            <div class="m-delta {'up' if cg[-1]>cs[-1] else 'dn'}">${cg[-1]-cs[-1]:+,.0f} vs static</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Chart ──────────────────────────────────────────────────────────
    st.markdown('<div class="sg-section-label" style="margin-top:1.5rem">Equity Curve</div>',
                unsafe_allow_html=True)

    port_lbl = " + ".join(ticker_list) if len(ticker_list) <= 3 else f"{len(ticker_list)} tickers"

    fig = make_subplots(rows=2, cols=1, row_heights=[0.72, 0.28],
                        shared_xaxes=True, vertical_spacing=0.04)
    fig.add_trace(go.Scatter(x=all_dates, y=cs, name=f"Static ({port_lbl})",
        line=dict(color=CL["static"], width=1.6), opacity=0.75), row=1, col=1)
    fig.add_trace(go.Scatter(x=all_dates, y=cg, name=f"SteadyGuard ({port_lbl})",
        line=dict(color=CL["sg"], width=2.2)), row=1, col=1)

    for lbl, crv, clr, fl in [("_s", cs, CL["static"], CL["sf"]),
                                ("_g", cg, CL["sg"], CL["sgf"])]:
        a = np.array(crv)
        pk = np.maximum.accumulate(a)
        dd = (a - pk) / pk
        fig.add_trace(go.Scatter(x=all_dates, y=dd, name=lbl,
            line=dict(color=clr, width=0.7), fill="tozeroy", fillcolor=fl,
            showlegend=False), row=2, col=1)

    fig.update_layout(
        height=500, template="plotly_dark",
        paper_bgcolor=CL["paper"], plot_bgcolor=CL["bg"],
        font=dict(family="Plus Jakarta Sans, sans-serif", color=CL["txt"], size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=55, r=15, t=35, b=35),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#131a28", bordercolor="#1a2235",
                        font=dict(family="JetBrains Mono", size=11)),
    )
    fig.update_yaxes(type="log", title=None, gridcolor=CL["grid"], gridwidth=0.5,
                     row=1, col=1, tickprefix="$", tickformat=",.0f",
                     zeroline=False)
    fig.update_yaxes(title=None, gridcolor=CL["grid"], gridwidth=0.5,
                     tickformat=".0%", row=2, col=1, zeroline=False)
    fig.update_xaxes(gridcolor=CL["grid"], gridwidth=0.5, zeroline=False)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Comparison Table ───────────────────────────────────────────────
    st.markdown('<div class="sg-section-label">Full Comparison</div>', unsafe_allow_html=True)

    rows_data = [
        ("CAGR", "CAGR", "pct", False), ("Max Drawdown", "MaxDD", "pct", True),
        ("Annualized Vol", "Vol", "pct", True), ("Sharpe Ratio", "Sharpe", "num", False),
        ("Calmar Ratio", "Calmar", "num", False), ("Total Return", "Total", "pct", False),
    ]
    trows = ""
    for label, key, fmt, lower_win in rows_data:
        sv, gv = sm[key], gm[key]
        d = gv - sv
        if fmt == "pct":
            ss, gs, ds = f"{sv:.2%}", f"{gv:.2%}", f"{'+'if d>0 else''}{d:.2%}"
        else:
            ss, gs, ds = f"{sv:.2f}", f"{gv:.2f}", f"{'+'if d>0 else''}{d:.2f}"
        sg_wins = gv > sv
        sc = "w" if sg_wins else ""
        dc = "w" if sg_wins else "l"
        trows += f'<tr><td>{label}</td><td>{ss}</td><td class="{sc}">{gs}</td><td class="{dc}">{ds}</td></tr>'

    st.markdown(f"""
    <table class="cmp">
    <thead><tr><th>Metric</th><th>Static</th><th>SteadyGuard</th><th>Delta</th></tr></thead>
    <tbody>{trows}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # ── Methodology ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sg-method">
        <strong>Methodology</strong> — Daily returns for {', '.join(ticker_list)} from Yahoo Finance,
        weighted to form the equity component. V3c regime signals (calibrated on SPY) set monthly
        equity exposure: LOW → 100%, MID → 80%, HIGH → 50%, CRISIS → 20%.
        Freed capital rotates to {bond_ticker.strip().upper()}. 10bps transaction cost per regime change.
        {'<br><strong>Note:</strong> Signals are SPY-calibrated; effectiveness on non-SPY assets depends on correlation.' if non_spy else ''}
    </div>
    """, unsafe_allow_html=True)

else:
    # Placeholder
    st.markdown("""
    <div class="sg-divider"></div>
    <div class="sg-placeholder">
        <div class="sg-placeholder-icon">📊</div>
        <div class="sg-placeholder-text">Configure your portfolio above</div>
        <div class="sg-placeholder-sub">Enter tickers, set your allocation, and hit Run Backtest</div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="sg-foot">
    SteadyGuard by Ben Vecchiarelli · Hypothetical backtest results · Not financial advice<br>
    Past performance does not guarantee future results
</div>
""", unsafe_allow_html=True)
