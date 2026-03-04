"""
SteadyGuard Pro — Custom Portfolio Backtest
============================================
Streamlit app for Pro tier ($29/mo).
User selects equity allocation, sees backtest results instantly.

Deploy: streamlit run app.py
Requires: spy_prices.csv, tlt_prices.csv, drivers_timeseries*.csv in same directory

Author: Ben Vecchiarelli | SteadyGuard
"""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ── Page Config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SteadyGuard Pro — Custom Backtest",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {
        background: #0a0e17;
        color: #e2e8f0;
        font-family: 'DM Sans', sans-serif;
    }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 1100px;}

    .hero-title {
        font-size: 2.4rem; font-weight: 700; color: #f8fafc;
        letter-spacing: -0.02em; margin-bottom: 0; line-height: 1.2;
    }
    .hero-sub {
        font-size: 1.05rem; color: #64748b;
        margin-top: 0.3rem; margin-bottom: 2rem;
    }
    .pro-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10b981, #059669);
        color: #fff; font-size: 0.7rem; font-weight: 700;
        padding: 0.2rem 0.6rem; border-radius: 4px;
        letter-spacing: 0.08em; text-transform: uppercase;
        margin-left: 0.8rem; vertical-align: middle;
    }

    .metric-row { display: flex; gap: 1rem; margin: 1.5rem 0; }
    .metric-card {
        flex: 1; background: #111827; border: 1px solid #1e293b;
        border-radius: 12px; padding: 1.2rem 1.4rem; text-align: center;
    }
    .metric-card.highlight {
        border-color: #10b981;
        background: linear-gradient(180deg, #0f1f1a 0%, #111827 100%);
    }
    .metric-label {
        font-size: 0.75rem; color: #64748b;
        text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.4rem;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem; font-weight: 500; color: #f1f5f9;
    }
    .metric-value.green { color: #10b981; }
    .metric-value.red { color: #ef4444; }
    .metric-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;
    }
    .metric-delta.better { color: #10b981; }
    .metric-delta.worse { color: #ef4444; }

    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 0.05em;
        margin: 2rem 0 0.8rem 0; padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e293b;
    }

    .comp-table {
        width: 100%; border-collapse: collapse;
        font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;
    }
    .comp-table th {
        color: #64748b; font-weight: 500; text-align: right;
        padding: 0.6rem 1rem; border-bottom: 1px solid #1e293b;
        font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em;
    }
    .comp-table th:first-child { text-align: left; }
    .comp-table td {
        padding: 0.6rem 1rem; text-align: right;
        border-bottom: 1px solid #0f172a; color: #cbd5e1;
    }
    .comp-table td:first-child {
        text-align: left; color: #94a3b8;
        font-family: 'DM Sans', sans-serif; font-weight: 500;
    }
    .comp-table tr:hover { background: #1e293b20; }
    .win { color: #10b981; font-weight: 600; }
    .lose { color: #ef4444; }

    .sg-footer {
        text-align: center; color: #334155; font-size: 0.75rem;
        margin-top: 3rem; padding: 1.5rem 0; border-top: 1px solid #1e293b;
    }

    .alloc-display { display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0 1.5rem 0; }
    .alloc-bar { flex: 1; height: 8px; border-radius: 4px; overflow: hidden; display: flex; }
    .alloc-eq { background: #3b82f6; height: 100%; }
    .alloc-bd { background: #f59e0b; height: 100%; }
    .alloc-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem; color: #94a3b8; white-space: nowrap;
    }

    .regime-row { display: flex; gap: 0.6rem; margin: 0.8rem 0; }
    .regime-chip {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem; padding: 0.35rem 0.8rem; border-radius: 6px; text-align: center;
    }
    .regime-low { background: #064e3b; color: #6ee7b7; }
    .regime-mid { background: #713f12; color: #fcd34d; }
    .regime-high { background: #7c2d12; color: #fdba74; }
    .regime-crisis { background: #7f1d1d; color: #fca5a5; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────
TRADING_DAYS = 252
COLORS = {
    "static": "#6366f1", "steadyguard": "#10b981",
    "static_fill": "rgba(99,102,241,0.15)", "sg_fill": "rgba(16,185,129,0.15)",
    "grid": "#1e293b", "bg": "#0a0e17", "paper": "#0a0e17", "text": "#94a3b8",
}


# ── Data Loading (cached) ─────────────────────────────────────────────
@st.cache_data
def load_data():
    """Load real SPY/TLT prices and V3c signals."""
    search = [Path("."), Path("/mnt/user-data/uploads"), Path(__file__).parent]

    def find(names):
        for d in search:
            for n in names:
                if (d / n).exists():
                    return d / n
        return None

    spy_path = find(["spy_prices.csv"])
    tlt_path = find(["tlt_prices.csv"])
    dr_path = find(["drivers_timeseries (2).csv", "drivers_timeseries__2_.csv", "drivers_timeseries.csv"])

    if not spy_path or not tlt_path or not dr_path:
        missing = []
        if not spy_path: missing.append("spy_prices.csv")
        if not tlt_path: missing.append("tlt_prices.csv")
        if not dr_path: missing.append("drivers_timeseries.csv")
        st.error(f"Missing data files: {', '.join(missing)}")
        st.stop()

    # Load prices — handle yfinance multi-row header
    def load_prices(path, col_name):
        raw = pd.read_csv(path, skiprows=2, header=None, names=['date', 'close'])
        raw = raw[raw['date'].str.match(r'^\d{4}-\d{2}-\d{2}', na=False)].copy()
        raw['date'] = pd.to_datetime(raw['date'])
        raw['close'] = raw['close'].astype(float)
        raw = raw.sort_values('date').reset_index(drop=True)
        raw[col_name] = raw['close'].pct_change()
        return raw[['date', col_name]]

    spy = load_prices(spy_path, 'spy_ret')
    tlt = load_prices(tlt_path, 'tlt_ret')

    merged = spy.merge(tlt, on='date', how='inner').sort_values('date').reset_index(drop=True)
    merged['month'] = merged['date'].dt.to_period('M')

    dr = pd.read_csv(dr_path, parse_dates=['date'])
    dr['month'] = dr['date'].dt.to_period('M')
    scalar_lookup = dict(zip(dr['month'], dr['scalar']))
    regime_counts = dr['risk_state'].value_counts().to_dict()

    # Filter to signal period
    first_signal_month = dr['month'].min()
    merged = merged[merged['month'] >= first_signal_month].reset_index(drop=True)

    return merged, scalar_lookup, regime_counts


def run_backtest(data, scalars, eq_pct):
    eq = eq_pct / 100.0
    bd = 1.0 - eq
    static_c, sg_c = [1.0], [1.0]
    st_ws, st_wt = eq, bd
    prev_m = data["month"].iloc[0]
    sc = scalars.get(prev_m, 1.0)
    sg_ws, sg_wt = eq * sc, 1.0 - eq * sc

    for i in range(1, len(data)):
        sr, tr, m = data["spy_ret"].iat[i], data["tlt_ret"].iat[i], data["month"].iat[i]
        if pd.isna(sr) or pd.isna(tr):
            static_c.append(static_c[-1]); sg_c.append(sg_c[-1]); prev_m = m; continue
        if m != prev_m:
            st_ws, st_wt = eq, bd
            sc = scalars.get(m, 1.0)
            sg_ws, sg_wt = eq * sc, 1.0 - eq * sc
        st_r = st_ws * sr + st_wt * tr
        static_c.append(static_c[-1] * (1 + st_r))
        if (1 + st_r) != 0: st_ws = st_ws * (1 + sr) / (1 + st_r); st_wt = 1 - st_ws
        sg_r = sg_ws * sr + sg_wt * tr
        sg_c.append(sg_c[-1] * (1 + sg_r))
        if (1 + sg_r) != 0: sg_ws = sg_ws * (1 + sr) / (1 + sg_r); sg_wt = 1 - sg_ws
        prev_m = m

    return pd.DataFrame({"date": data["date"].values, "static": static_c, "steadyguard": sg_c})


def calc_metrics(curve, dates):
    arr = np.array(curve)
    yrs = (dates.iloc[-1] - dates.iloc[0]).days / 365.25
    cagr = (arr[-1] / arr[0]) ** (1 / yrs) - 1
    rets = np.diff(arr) / arr[:-1]
    vol = np.std(rets, ddof=1) * np.sqrt(TRADING_DAYS)
    sharpe = cagr / vol if vol > 0 else 0
    peak = np.maximum.accumulate(arr)
    dd = (arr - peak) / peak
    maxdd = dd.min()
    calmar = cagr / abs(maxdd) if maxdd != 0 else 0
    total = arr[-1] / arr[0] - 1
    return {"CAGR": cagr, "Max Drawdown": maxdd, "Volatility": vol,
            "Sharpe": sharpe, "Calmar": calmar, "Total Return": total}


# ── Load & Run ─────────────────────────────────────────────────────────
data, scalars, regime_counts = load_data()

st.markdown("""
<div style="margin-bottom: 0.5rem;">
    <span class="hero-title">SteadyGuard</span>
    <span class="pro-badge">Pro</span>
</div>
<div class="hero-sub">Custom portfolio backtest — see how V3c protects your allocation</div>
""", unsafe_allow_html=True)

col_input, col_spacer, col_info = st.columns([2, 0.3, 1.5])

with col_input:
    equity_pct = st.slider("Equity Allocation %", 0, 100, 70, 5,
                           help="Percentage allocated to stocks (SPY). Remainder goes to bonds (TLT).")
    bond_pct = 100 - equity_pct
    st.markdown(f"""
    <div class="alloc-display">
        <span class="alloc-label" style="color:#3b82f6;">SPY {equity_pct}%</span>
        <div class="alloc-bar">
            <div class="alloc-eq" style="width:{equity_pct}%;"></div>
            <div class="alloc-bd" style="width:{bond_pct}%;"></div>
        </div>
        <span class="alloc-label" style="color:#f59e0b;">TLT {bond_pct}%</span>
    </div>
    """, unsafe_allow_html=True)

with col_info:
    start_str = data["date"].iloc[0].strftime("%b %Y")
    end_str = data["date"].iloc[-1].strftime("%b %Y")
    n_years = (data["date"].iloc[-1] - data["date"].iloc[0]).days / 365.25
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1e293b; border-radius:10px;
                padding:1rem 1.2rem; margin-top:0.3rem;">
        <div style="font-size:0.72rem; color:#64748b; text-transform:uppercase;
                    letter-spacing:0.05em; margin-bottom:0.6rem;">Backtest Window</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.95rem; color:#e2e8f0;">
            {start_str} — {end_str}</div>
        <div style="font-size:0.8rem; color:#64748b; margin-top:0.2rem;">
            {n_years:.1f} years · {len(data):,} trading days</div>
        <div style="margin-top:0.8rem;">
            <div class="regime-row">
                <span class="regime-chip regime-low">LOW {regime_counts.get('LOW',0)}</span>
                <span class="regime-chip regime-mid">MID {regime_counts.get('MID',0)}</span>
                <span class="regime-chip regime-high">HIGH {regime_counts.get('HIGH',0)}</span>
                <span class="regime-chip regime-crisis">CRISIS {regime_counts.get('CRISIS',0)}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

results = run_backtest(data, scalars, equity_pct)
sm = calc_metrics(results["static"], results["date"])
sgm = calc_metrics(results["steadyguard"], results["date"])

# ── Metric Cards ───────────────────────────────────────────────────────
def delta_html(sv, sgv, fmt="pct"):
    d = sgv - sv
    better = d > 0
    if fmt != "pct":
        cls = "better" if better else "worse"
        return f'<span class="metric-delta {cls}">{"+" if d>0 else ""}{d:.2f} vs static</span>'
    cls = "better" if better else "worse"
    return f'<span class="metric-delta {cls}">{"+" if d>0 else ""}{d:.2%} vs static</span>'

st.markdown('<div class="section-header">SteadyGuard Results</div>', unsafe_allow_html=True)

dd_better = sgm['Max Drawdown'] > sm['Max Drawdown']
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card highlight">
        <div class="metric-label">CAGR</div>
        <div class="metric-value green">{sgm['CAGR']:.2%}</div>
        {delta_html(sm['CAGR'], sgm['CAGR'])}
    </div>
    <div class="metric-card highlight">
        <div class="metric-label">Max Drawdown</div>
        <div class="metric-value {'green' if dd_better else 'red'}">{sgm['Max Drawdown']:.2%}</div>
        {delta_html(sm['Max Drawdown'], sgm['Max Drawdown'])}
    </div>
    <div class="metric-card highlight">
        <div class="metric-label">Sharpe Ratio</div>
        <div class="metric-value green">{sgm['Sharpe']:.2f}</div>
        {delta_html(sm['Sharpe'], sgm['Sharpe'], fmt="num")}
    </div>
    <div class="metric-card">
        <div class="metric-label">Total Return</div>
        <div class="metric-value">{sgm['Total Return']:.0%}</div>
        {delta_html(sm['Total Return'], sgm['Total Return'])}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Chart ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Equity Curve</div>', unsafe_allow_html=True)

fig = make_subplots(rows=2, cols=1, row_heights=[0.72, 0.28], shared_xaxes=True, vertical_spacing=0.04)
fig.add_trace(go.Scatter(x=results["date"], y=results["static"], name=f"Static {equity_pct}/{bond_pct}",
    line=dict(color=COLORS["static"], width=1.8), opacity=0.8), row=1, col=1)
fig.add_trace(go.Scatter(x=results["date"], y=results["steadyguard"], name=f"SteadyGuard {equity_pct}/{bond_pct}",
    line=dict(color=COLORS["steadyguard"], width=2), opacity=0.95), row=1, col=1)

for label, col, color, fill in [
    ("Static DD", "static", COLORS["static"], COLORS["static_fill"]),
    ("SteadyGuard DD", "steadyguard", COLORS["steadyguard"], COLORS["sg_fill"]),
]:
    c = results[col].values
    p = np.maximum.accumulate(c)
    dd = (c - p) / p
    fig.add_trace(go.Scatter(x=results["date"], y=dd, name=label,
        line=dict(color=color, width=0.8), fill="tozeroy", fillcolor=fill, showlegend=False), row=2, col=1)

fig.update_layout(height=520, template="plotly_dark", paper_bgcolor=COLORS["paper"],
    plot_bgcolor=COLORS["bg"], font=dict(family="DM Sans, sans-serif", color=COLORS["text"], size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
    margin=dict(l=60, r=20, t=40, b=40), hovermode="x unified")
fig.update_yaxes(type="log", title="Growth of $1", gridcolor=COLORS["grid"], gridwidth=0.5,
    row=1, col=1, tickprefix="$", tickformat=".1f")
fig.update_yaxes(title="Drawdown", gridcolor=COLORS["grid"], gridwidth=0.5, tickformat=".0%", row=2, col=1)
fig.update_xaxes(gridcolor=COLORS["grid"], gridwidth=0.5)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Table ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Full Comparison</div>', unsafe_allow_html=True)

metrics_list = [
    ("CAGR", "CAGR", "pct", False), ("Max Drawdown", "Max Drawdown", "pct", True),
    ("Annualized Vol", "Volatility", "pct", True), ("Sharpe Ratio", "Sharpe", "num", False),
    ("Calmar Ratio", "Calmar", "num", False), ("Total Return", "Total Return", "pct", False),
]

table_rows = ""
for label, key, fmt, lower_better in metrics_list:
    sv, sgv = sm[key], sgm[key]
    d = sgv - sv
    if fmt == "pct":
        sv_s, sgv_s, d_s = f"{sv:.2%}", f"{sgv:.2%}", f"{'+'if d>0 else ''}{d:.2%}"
    else:
        sv_s, sgv_s, d_s = f"{sv:.2f}", f"{sgv:.2f}", f"{'+'if d>0 else ''}{d:.2f}"
    if lower_better:
        sg_wins = sgv < sv if key != "Max Drawdown" else sgv > sv
    else:
        sg_wins = sgv > sv
    table_rows += f'<tr><td>{label}</td><td class="{"" if sg_wins else "win"}">{sv_s}</td>' \
                  f'<td class="{"win" if sg_wins else ""}">{sgv_s}</td>' \
                  f'<td class="{"win" if sg_wins else "lose"}">{d_s}</td></tr>'

st.markdown(f"""
<table class="comp-table">
    <thead><tr><th>Metric</th><th>Static {equity_pct}/{bond_pct}</th><th>SteadyGuard</th><th>Delta</th></tr></thead>
    <tbody>{table_rows}</tbody>
</table>
""", unsafe_allow_html=True)

# ── How It Works ───────────────────────────────────────────────────────
with st.expander("How SteadyGuard works", expanded=False):
    st.markdown(f"""
    **SteadyGuard's V3c model** classifies market conditions each month into one of four regimes
    based on volatility, tail risk, and trend persistence:

    | Regime | Signal | Your Equity Allocation |
    |--------|--------|----------------------|
    | **LOW** (Calm) | 1.0× | {equity_pct}% → **{equity_pct}%** SPY |
    | **MID** (Cautious) | 0.8× | {equity_pct}% → **{int(equity_pct*0.8)}%** SPY |
    | **HIGH** (Risky) | 0.5× | {equity_pct}% → **{int(equity_pct*0.5)}%** SPY |
    | **CRISIS** | 0.2× | {equity_pct}% → **{int(equity_pct*0.2)}%** SPY |

    The freed-up capital moves to bonds (TLT), then returns to equities when conditions improve.
    Rebalancing occurs monthly based on end-of-month signals.
    """)

st.markdown("""
<div class="sg-footer">
    SteadyGuard by Ben Vecchiarelli · Backtest results are hypothetical and do not guarantee future performance.<br>
    Past performance is not indicative of future results. Not financial advice.
</div>
""", unsafe_allow_html=True)
