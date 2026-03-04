"""
SteadyGuard Pro — Custom Portfolio Backtest
============================================
Uses the site's monthly returns/regime data (Jan 1998 - Jan 2026).
28 years. Monthly rebalancing. Same formula as the public site.
"""
import numpy as np
import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(page_title="SteadyGuard Pro", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# ── CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
    .stApp { background: #0a0e17; color: #e2e8f0; font-family: 'DM Sans', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 1100px;}
    .hero-title { font-size: 2.4rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; }
    .hero-sub { font-size: 1.05rem; color: #64748b; margin-top: 0.3rem; margin-bottom: 2rem; }
    .pro-badge { display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: #fff;
        font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 4px;
        letter-spacing: 0.08em; text-transform: uppercase; margin-left: 0.8rem; vertical-align: middle; }
    .metric-row { display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }
    .metric-card { flex: 1; min-width: 140px; background: #111827; border: 1px solid #1e293b;
        border-radius: 12px; padding: 1.1rem 1.2rem; text-align: center; }
    .metric-card.hl { border-color: #10b981; background: linear-gradient(180deg, #0f1f1a 0%, #111827 100%); }
    .metric-label { font-size: 0.72rem; color: #64748b; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 0.35rem; }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 500; color: #f1f5f9; }
    .metric-value.grn { color: #10b981; }
    .metric-delta { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #64748b; margin-top: 0.15rem; }
    .metric-delta.up { color: #10b981; }
    .metric-delta.dn { color: #ef4444; }
    .section-hdr { font-size: 1.05rem; font-weight: 600; color: #94a3b8; text-transform: uppercase;
        letter-spacing: 0.05em; margin: 2rem 0 0.8rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #1e293b; }
    .ct { width: 100%; border-collapse: collapse; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
    .ct th { color: #64748b; font-weight: 500; text-align: right; padding: 0.6rem 1rem;
        border-bottom: 1px solid #1e293b; font-size: 0.72rem; text-transform: uppercase; }
    .ct th:first-child { text-align: left; }
    .ct td { padding: 0.6rem 1rem; text-align: right; border-bottom: 1px solid #0f172a; color: #cbd5e1; }
    .ct td:first-child { text-align: left; color: #94a3b8; font-family: 'DM Sans', sans-serif; font-weight: 500; }
    .win { color: #10b981; font-weight: 600; }
    .lose { color: #ef4444; }
    .foot { text-align: center; color: #334155; font-size: 0.72rem; margin-top: 3rem;
        padding: 1.5rem 0; border-top: 1px solid #1e293b; }
    .alloc-display { display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0 1.5rem 0; }
    .alloc-bar { flex: 1; height: 8px; border-radius: 4px; overflow: hidden; display: flex; }
    .alloc-eq { background: #3b82f6; height: 100%; }
    .alloc-bd { background: #f59e0b; height: 100%; }
    .alloc-lbl { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #94a3b8; white-space: nowrap; }
    .regime-row { display: flex; gap: 0.5rem; margin: 0.6rem 0; flex-wrap: wrap; }
    .rc { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; padding: 0.3rem 0.7rem; border-radius: 6px; }
    .rc-l { background: #064e3b; color: #6ee7b7; }
    .rc-m { background: #713f12; color: #fcd34d; }
    .rc-h { background: #7c2d12; color: #fdba74; }
    .rc-c { background: #7f1d1d; color: #fca5a5; }
    .ref-note { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px;
        padding: 0.8rem 1rem; margin-top: 1rem; font-size: 0.8rem; color: #64748b; }
    .ref-note strong { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

CL = {
    "static": "#6366f1", "sg": "#10b981",
    "sf": "rgba(99,102,241,0.15)", "sgf": "rgba(16,185,129,0.15)",
    "grid": "#1e293b", "bg": "#0a0e17", "paper": "#0a0e17", "txt": "#94a3b8",
}


@st.cache_data
def load_data():
    for d in [Path("."), Path(__file__).parent, Path("/mnt/user-data/uploads")]:
        p = d / "monthly_data.json"
        if p.exists():
            with open(p) as f:
                return json.load(f)
    st.error("monthly_data.json not found.")
    st.stop()


def run_bt(data, eq_pct):
    eq = eq_pct / 100.0
    vs = vg = 10000.0
    prev = 1.0
    cs, cg, dates = [10000.0], [10000.0], []
    scalars_used = []

    for m in data:
        s, b, sc = m['s'], m['b'], m['scalar']
        vs *= (1 + eq * s + (1 - eq) * b)
        eq_adj = eq * sc
        vg *= (1 + eq_adj * s + (1 - eq_adj) * b - 0.001 * abs(sc - prev))
        prev = sc
        dates.append(m['d'])
        cs.append(vs)
        cg.append(vg)
        scalars_used.append(sc)

    return dates, cs, cg, scalars_used


def metrics(curve, n_yr):
    a = np.array(curve)
    cagr = (a[-1] / a[0]) ** (1 / n_yr) - 1
    r = np.diff(a) / a[:-1]
    vol = np.std(r, ddof=1) * np.sqrt(12)
    sharpe = cagr / vol if vol > 0 else 0
    pk = np.maximum.accumulate(a)
    dd = (a - pk) / pk
    mdd = dd.min()
    calmar = cagr / abs(mdd) if mdd != 0 else 0
    tot = a[-1] / a[0] - 1
    return {"CAGR": cagr, "MaxDD": mdd, "Vol": vol, "Sharpe": sharpe, "Calmar": calmar, "Total": tot}


# ── Load ───────────────────────────────────────────────────────────────
data = load_data()
n_years = len(data) / 12.0
rc = {}
for m in data:
    rc[m['regime']] = rc.get(m['regime'], 0) + 1

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:0.5rem">
    <span class="hero-title">SteadyGuard</span><span class="pro-badge">Pro</span>
</div>
<div class="hero-sub">Custom portfolio backtest — see how V3c protects your allocation over 28 years</div>
""", unsafe_allow_html=True)

# ── Inputs ─────────────────────────────────────────────────────────────
c1, _, c2 = st.columns([2, 0.3, 1.5])
with c1:
    eq = st.slider("Equity Allocation %", 0, 100, 70, 5,
                   help="% allocated to stocks (SPY). Rest goes to bonds (VUSTX/TLT).")
    bd = 100 - eq
    st.markdown(f"""
    <div class="alloc-display">
        <span class="alloc-lbl" style="color:#3b82f6">SPY {eq}%</span>
        <div class="alloc-bar"><div class="alloc-eq" style="width:{eq}%"></div>
            <div class="alloc-bd" style="width:{bd}%"></div></div>
        <span class="alloc-lbl" style="color:#f59e0b">Bonds {bd}%</span>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:1rem 1.2rem;margin-top:0.3rem">
        <div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem">
            Backtest Window</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;color:#e2e8f0">
            Jan 1998 — Jan 2026</div>
        <div style="font-size:0.8rem;color:#64748b;margin-top:0.15rem">{n_years:.1f} years · {len(data)} months</div>
        <div class="regime-row" style="margin-top:0.6rem">
            <span class="rc rc-l">LOW {rc.get('LOW',0)}</span>
            <span class="rc rc-m">MID {rc.get('MID',0)}</span>
            <span class="rc rc-h">HIGH {rc.get('HIGH',0)}</span>
            <span class="rc rc-c">CRISIS {rc.get('CRISIS',0)}</span>
        </div>
    </div>""", unsafe_allow_html=True)

# ── Run ────────────────────────────────────────────────────────────────
dates, cs, cg, scalars = run_bt(data, eq)
all_dates = [data[0]['d']] + dates
sm = metrics(cs, n_years)
gm = metrics(cg, n_years)

# ── Metric Cards ───────────────────────────────────────────────────────
st.markdown('<div class="section-hdr">SteadyGuard Results</div>', unsafe_allow_html=True)

def dh(sv, gv, fmt="pct"):
    d = gv - sv
    cls = "up" if d > 0 else "dn"
    if fmt == "num":
        return f'<span class="metric-delta {cls}">{"+" if d>0 else ""}{d:.2f} vs static</span>'
    return f'<span class="metric-delta {cls}">{"+" if d>0 else ""}{d:.2%} vs static</span>'

dd_better = gm['MaxDD'] > sm['MaxDD']
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card hl">
        <div class="metric-label">CAGR</div>
        <div class="metric-value grn">{gm['CAGR']:.2%}</div>
        {dh(sm['CAGR'], gm['CAGR'])}
    </div>
    <div class="metric-card hl">
        <div class="metric-label">Max Drawdown</div>
        <div class="metric-value {'grn' if dd_better else ''}">{gm['MaxDD']:.2%}</div>
        {dh(sm['MaxDD'], gm['MaxDD'])}
    </div>
    <div class="metric-card hl">
        <div class="metric-label">Sharpe Ratio</div>
        <div class="metric-value grn">{gm['Sharpe']:.2f}</div>
        {dh(sm['Sharpe'], gm['Sharpe'], fmt="num")}
    </div>
    <div class="metric-card">
        <div class="metric-label">Growth of $10k</div>
        <div class="metric-value">${cg[-1]:,.0f}</div>
        <span class="metric-delta {'up' if cg[-1]>cs[-1] else 'dn'}">${cg[-1]-cs[-1]:+,.0f} vs static</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Chart ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-hdr">Equity Curve</div>', unsafe_allow_html=True)

fig = make_subplots(rows=2, cols=1, row_heights=[0.72, 0.28], shared_xaxes=True, vertical_spacing=0.04)
fig.add_trace(go.Scatter(x=all_dates, y=cs, name=f"Static {eq}/{bd}",
    line=dict(color=CL["static"], width=1.8), opacity=0.8), row=1, col=1)
fig.add_trace(go.Scatter(x=all_dates, y=cg, name=f"SteadyGuard {eq}/{bd}",
    line=dict(color=CL["sg"], width=2.2)), row=1, col=1)

# Drawdown panel
for lbl, crv, clr, fl in [("_dd_s", cs, CL["static"], CL["sf"]), ("_dd_g", cg, CL["sg"], CL["sgf"])]:
    a = np.array(crv)
    pk = np.maximum.accumulate(a)
    dd = (a - pk) / pk
    fig.add_trace(go.Scatter(x=all_dates, y=dd, name=lbl,
        line=dict(color=clr, width=0.8), fill="tozeroy", fillcolor=fl, showlegend=False), row=2, col=1)

# Regime background bands
regime_colors = {"LOW": "rgba(16,185,129,0.04)", "MID": "rgba(250,204,21,0.06)",
                 "HIGH": "rgba(249,115,22,0.08)", "CRISIS": "rgba(239,68,68,0.1)"}
i = 0
while i < len(data):
    r = data[i]['regime']
    j = i
    while j < len(data) and data[j]['regime'] == r:
        j += 1
    if r != "LOW":
        fig.add_vrect(x0=data[i]['d'], x1=data[min(j, len(data)-1)]['d'],
            fillcolor=regime_colors.get(r, "rgba(0,0,0,0)"), line_width=0, row=1, col=1)
    i = j

fig.update_layout(height=520, template="plotly_dark", paper_bgcolor=CL["paper"],
    plot_bgcolor=CL["bg"], font=dict(family="DM Sans", color=CL["txt"], size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
    margin=dict(l=60, r=20, t=40, b=40), hovermode="x unified")
fig.update_yaxes(type="log", title="Growth of $10,000", gridcolor=CL["grid"], gridwidth=0.5,
    row=1, col=1, tickprefix="$", tickformat=",.0f")
fig.update_yaxes(title="Drawdown", gridcolor=CL["grid"], gridwidth=0.5, tickformat=".0%", row=2, col=1)
fig.update_xaxes(gridcolor=CL["grid"], gridwidth=0.5)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Comparison Table ───────────────────────────────────────────────────
st.markdown('<div class="section-hdr">Full Comparison</div>', unsafe_allow_html=True)

rows_data = [
    ("CAGR", "CAGR", "pct", False),
    ("Max Drawdown", "MaxDD", "pct", True),
    ("Annualized Vol", "Vol", "pct", True),
    ("Sharpe Ratio", "Sharpe", "num", False),
    ("Calmar Ratio", "Calmar", "num", False),
    ("Total Return", "Total", "pct", False),
]

trows = ""
for label, key, fmt, lower_win in rows_data:
    sv, gv = sm[key], gm[key]
    d = gv - sv
    if fmt == "pct":
        ss, gs, ds = f"{sv:.2%}", f"{gv:.2%}", f"{'+'if d>0 else''}{d:.2%}"
    else:
        ss, gs, ds = f"{sv:.2f}", f"{gv:.2f}", f"{'+'if d>0 else''}{d:.2f}"
    if lower_win:
        sg_wins = gv < sv if key != "MaxDD" else gv > sv
    else:
        sg_wins = gv > sv
    sc = "win" if sg_wins else ""
    dc = "win" if sg_wins else "lose"
    trows += f'<tr><td>{label}</td><td>{ss}</td><td class="{sc}">{gs}</td><td class="{dc}">{ds}</td></tr>'

st.markdown(f"""
<table class="ct">
<thead><tr><th>Metric</th><th>Static {eq}/{bd}</th><th>SteadyGuard</th><th>Delta</th></tr></thead>
<tbody>{trows}</tbody>
</table>
""", unsafe_allow_html=True)

# ── Reference Note ─────────────────────────────────────────────────────
st.markdown(f"""
<div class="ref-note">
    <strong>Methodology note:</strong> This tool uses the same monthly returns and V3c regime signals
    as the main SteadyGuard site. Results reflect monthly rebalancing with a 0.1% transaction cost
    per regime change. The flagship site metrics (8.81% CAGR, -20.57% MaxDD at 100% equity) are
    derived from a daily-frequency production model; this monthly approximation captures the same
    regime shifts but may differ slightly in absolute levels due to intra-month price movements.
    Relative comparisons between static and SteadyGuard allocations are accurate.
</div>
""", unsafe_allow_html=True)

# ── How It Works ───────────────────────────────────────────────────────
with st.expander("How SteadyGuard works", expanded=False):
    st.markdown(f"""
**V3c classifies market conditions monthly** using volatility percentile, Hill tail risk,
and Hurst trend persistence into four regimes:

| Regime | Scalar | Your {eq}% Equity Becomes |
|--------|--------|--------------------------|
| **LOW** (Calm) | 1.0× | **{eq}%** SPY |
| **MID** (Cautious) | 0.8× | **{int(eq*0.8)}%** SPY |
| **HIGH** (Elevated) | 0.5× | **{int(eq*0.5)}%** SPY |
| **CRISIS** | 0.2× | **{int(eq*0.2)}%** SPY |

Capital freed from equities moves to bonds (VUSTX/TLT), then returns when conditions improve.

**Period:** Jan 1998 – Jan 2026 ({n_years:.0f} years) covering the dot-com crash, GFC,
COVID crash, and 2022 bear market.
    """)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="foot">
    SteadyGuard by Ben Vecchiarelli · Hypothetical backtest results — not financial advice.<br>
    Past performance does not guarantee future results.
</div>
""", unsafe_allow_html=True)
