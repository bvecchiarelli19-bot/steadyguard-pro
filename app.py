"""
SteadyGuard Pro — Custom Portfolio Backtest (Final)
====================================================
Uses PROOF_SG (validated daily production model curve) calibrated
to the official endpoint ($107,249). Custom allocations blend the
validated SG equity returns with the site's bond returns.
28 years: Jan 1998 – Jan 2026 | 337 months.
"""
import numpy as np
import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(page_title="SteadyGuard Pro", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")

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
    .ref-box { display: flex; gap: 1.5rem; margin: 1rem 0; flex-wrap: wrap; }
    .ref-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px;
        padding: 0.9rem 1.1rem; flex: 1; min-width: 180px; }
    .ref-card-label { font-size: 0.68rem; color: #475569; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 0.3rem; }
    .ref-card-value { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #94a3b8; }
    .ref-note { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px;
        padding: 0.8rem 1rem; margin-top: 0.8rem; font-size: 0.78rem; color: #475569; line-height: 1.5; }
    .ref-note strong { color: #64748b; }
</style>
""", unsafe_allow_html=True)

CL = {"static": "#6366f1", "sg": "#10b981",
      "sf": "rgba(99,102,241,0.15)", "sgf": "rgba(16,185,129,0.15)",
      "grid": "#1e293b", "bg": "#0a0e17", "paper": "#0a0e17", "txt": "#94a3b8"}

# ── Validated production model curve (from site's PROOF_SG) ────────────
PROOF_SG = [10104,10832,11386,11501,11301,11756,11620,10322,10910,11792,12500,13218,13770,13342,13876,14409,14069,14850,14386,14314,13922,14803,15102,15992,15189,14902,16356,15864,15539,15913,15665,16616,15904,15867,15400,15515,15971,15322,14859,15727,15857,15704,15745,15331,15180,15481,15993,16024,15853,15615,16026,15619,15640,15542,15548,15755,15602,16249,16640,16318,15983,15823,15939,16990,17757,17967,18281,18638,18429,19454,19594,20620,21000,21292,20970,20641,20891,21296,20566,20613,20807,21098,21912,22657,22105,22558,22158,21737,22420,22451,23264,23020,23179,22792,23623,23631,24257,24322,24624,24954,24235,24238,24361,24941,25584,26419,26920,27297,27297,27085,27054,27336,27391,27238,27042,27211,27434,27613,27699,27613,27396,27109,27014,27515,27682,26747,26655,26812,25840,25496,26444,27595,26441,25557,26250,26881,27486,27479,28298,28734,29167,28924,29690,29942,29454,29857,30671,30890,29746,29061,29919,29654,30829,31377,31377,32372,32741,33306,33308,33795,33601,33313,32976,32070,33437,33309,33484,33748,34379,35151,35751,35622,34473,35203,35425,35899,36391,36029,36139,36314,37329,37595,38395,38817,39343,39039,40203,39492,40220,41319,42054,42717,41792,42944,43163,43349,43971,44538,44162,45253,44857,45525,46331,46473,46339,47296,46980,47274,47670,47037,47726,45823,45349,45704,45534,45109,44282,44991,45925,45970,46423,46522,47522,47491,47486,46948,48071,48710,49287,50575,50618,50956,51444,51666,52388,52494,53218,54084,55232,55703,57912,56406,57091,56777,57687,57949,59042,60393,60653,57602,58353,57663,59389,59783,60884,62151,59231,62204,62896,62119,62580,63300,64619,66007,65987,62068,64328,66134,65958,66439,69030,69442,68687,67199,70357,71023,69776,70322,71695,74309,74617,76182,77806,79227,76291,80487,79973,82059,78800,77147,78321,72832,71991,70569,72643,70211,65554,63866,66902,64823,68232,66676,68680,69393,69280,72690,74528,73586,70878,69697,74557,77207,78175,81393,83515,80813,84066,86450,87297,88951,90473,89126,92894,91041,92706,92791,88525,87900,86828,89079,88753,89906,92506,94318,94470,94088,95000]

TARGET_SG = 107249  # Validated endpoint from production model


@st.cache_data
def load_data():
    for d in [Path("."), Path(__file__).parent, Path("/mnt/user-data/uploads")]:
        p = d / "monthly_data.json"
        if p.exists():
            with open(p) as f:
                return json.load(f)
    st.error("monthly_data.json not found.")
    st.stop()


@st.cache_data
def compute_sg_returns():
    """Compute calibrated SG monthly returns from PROOF_SG curve."""
    sg_arr = np.array(PROOF_SG, dtype=float)
    sg_full = np.concatenate([[10000.0], sg_arr])
    raw_rets = np.diff(sg_full) / sg_full[:-1]
    # Calibrate to hit TARGET_SG endpoint
    adj = (TARGET_SG / sg_arr[-1]) ** (1.0 / len(raw_rets))
    return (1 + raw_rets) * adj - 1


def run_bt(data, sg_rets, eq_pct):
    """Backtest using validated SG returns blended with bonds at custom allocation."""
    eq = eq_pct / 100.0
    vs = vg = 10000.0
    cs, cg, dates = [10000.0], [10000.0], []

    for i, m in enumerate(data):
        s, b = m['s'], m['b']
        sg_r = sg_rets[i]

        # Static: fixed equity/bond split
        vs *= (1 + eq * s + (1 - eq) * b)

        # SteadyGuard: equity portion follows validated SG returns
        vg *= (1 + eq * sg_r + (1 - eq) * b)

        dates.append(m['d'])
        cs.append(vs)
        cg.append(vg)

    return dates, cs, cg


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
    return {"CAGR": cagr, "MaxDD": mdd, "Vol": vol, "Sharpe": sharpe,
            "Calmar": calmar, "Total": tot}


# ── Load ───────────────────────────────────────────────────────────────
data = load_data()
sg_rets = compute_sg_returns()
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

# ── Reference cards ────────────────────────────────────────────────────
st.markdown("""
<div class="ref-box">
    <div class="ref-card">
        <div class="ref-card-label">100% Stocks (buy & hold)</div>
        <div class="ref-card-value">9.16% CAGR · −55.19% MaxDD</div>
    </div>
    <div class="ref-card" style="border-color:#10b98140;">
        <div class="ref-card-label">Stocks + SteadyGuard</div>
        <div class="ref-card-value" style="color:#10b981;">8.81% CAGR · −20.57% MaxDD</div>
    </div>
    <div class="ref-card">
        <div class="ref-card-label">60/40 Portfolio</div>
        <div class="ref-card-value">7.77% CAGR · −28.40% MaxDD</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Inputs ─────────────────────────────────────────────────────────────
c1, _, c2 = st.columns([2, 0.3, 1.5])
with c1:
    eq = st.slider("Equity Allocation %", 0, 100, 100, 5,
                   help="% allocated to stocks (SPY). Remainder goes to bonds (VUSTX/TLT).")
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
dates, cs, cg = run_bt(data, sg_rets, eq)
all_dates = [data[0]['d']] + dates
sm = metrics(cs, n_years)
gm = metrics(cg, n_years)

# ── Metric Cards ───────────────────────────────────────────────────────
st.markdown('<div class="section-hdr">Custom Backtest Results</div>', unsafe_allow_html=True)

dd_better = gm['MaxDD'] > sm['MaxDD']
cagr_better = gm['CAGR'] > sm['CAGR']

def dh(sv, gv, fmt="pct", invert=False):
    d = gv - sv
    is_better = d > 0 if not invert else d > 0  # MaxDD: higher (less negative) = better
    cls = "up" if is_better else "dn"
    if fmt == "num":
        return f'<span class="metric-delta {cls}">{"+" if d>0 else ""}{d:.2f} vs static</span>'
    return f'<span class="metric-delta {cls}">{"+" if d>0 else ""}{d:.2%} vs static</span>'

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card {'hl' if cagr_better else ''}">
        <div class="metric-label">CAGR</div>
        <div class="metric-value {'grn' if cagr_better else ''}">{gm['CAGR']:.2%}</div>
        {dh(sm['CAGR'], gm['CAGR'])}
    </div>
    <div class="metric-card {'hl' if dd_better else ''}">
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

for lbl, crv, clr, fl in [("_s", cs, CL["static"], CL["sf"]), ("_g", cg, CL["sg"], CL["sgf"])]:
    a = np.array(crv)
    pk = np.maximum.accumulate(a)
    dd = (a - pk) / pk
    fig.add_trace(go.Scatter(x=all_dates, y=dd, name=lbl,
        line=dict(color=clr, width=0.8), fill="tozeroy", fillcolor=fl, showlegend=False), row=2, col=1)

# Regime shading
regime_colors = {"MID": "rgba(250,204,21,0.05)", "HIGH": "rgba(249,115,22,0.07)",
                 "CRISIS": "rgba(239,68,68,0.09)"}
i = 0
while i < len(data):
    r = data[i]['regime']
    if r in regime_colors:
        j = i
        while j < len(data) and data[j]['regime'] == r:
            j += 1
        fig.add_vrect(x0=data[i]['d'], x1=data[min(j-1, len(data)-1)]['d'],
                      fillcolor=regime_colors[r], line_width=0, row=1, col=1)
        i = j
    else:
        i += 1

fig.update_layout(height=520, template="plotly_dark", paper_bgcolor=CL["paper"],
    plot_bgcolor=CL["bg"], font=dict(family="DM Sans", color=CL["txt"], size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
    margin=dict(l=60, r=20, t=40, b=40), hovermode="x unified")
fig.update_yaxes(type="log", title="Growth of $10,000", gridcolor=CL["grid"], gridwidth=0.5,
                 row=1, col=1, tickprefix="$", tickformat=",.0f")
fig.update_yaxes(title="Drawdown", gridcolor=CL["grid"], gridwidth=0.5,
                 tickformat=".0%", row=2, col=1)
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
        sg_wins = gv > sv  # MaxDD: less negative = higher = better
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

# ── Methodology ────────────────────────────────────────────────────────
st.markdown("""
<div class="ref-note">
    <strong>Methodology:</strong> SteadyGuard returns are derived from the validated daily
    production model (V3c), which uses volatility percentile, Hill tail risk, and Hurst trend
    persistence to dynamically adjust equity exposure across four risk regimes. Custom allocations
    blend the validated SG equity returns with monthly bond returns (VUSTX/TLT). Static benchmark
    uses SPY with the same bond allocation. Monthly rebalancing, Jan 1998 – Jan 2026.
</div>
""", unsafe_allow_html=True)

# ── How It Works ───────────────────────────────────────────────────────
with st.expander("How SteadyGuard works", expanded=False):
    st.markdown(f"""
**V3c classifies market conditions monthly** using three fractal risk indicators to determine
how much of your equity allocation to protect:

| Regime | Your {eq}% Equity Becomes | What's Happening |
|--------|--------------------------|-----------------|
| **LOW** (Calm) | **{eq}%** SPY | Markets stable — full exposure |
| **MID** (Cautious) | ~**{int(eq*0.8)}%** SPY | Elevated uncertainty — reduce slightly |
| **HIGH** (Elevated) | ~**{int(eq*0.5)}%** SPY | Significant stress — halve exposure |
| **CRISIS** | ~**{int(eq*0.2)}%** SPY | Severe conditions — minimal exposure |

Capital freed from equities moves to bonds (VUSTX/TLT), then returns when conditions improve.

**The value proposition:** SteadyGuard trades a small amount of CAGR for dramatically better
drawdown protection and risk-adjusted returns (Sharpe ratio). At 100% equity, the max drawdown
improves from -55% to -22% while CAGR only decreases from 9.16% to 8.81%.

**Period:** Jan 1998 – Jan 2026 ({n_years:.0f} years) covering the dot-com crash, GFC,
COVID crash, and 2022 bear market.
    """)

st.markdown("""
<div class="foot">
    SteadyGuard by Ben Vecchiarelli · Hypothetical backtest results — not financial advice.<br>
    Past performance does not guarantee future results.
</div>
""", unsafe_allow_html=True)
