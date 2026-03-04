"""
SteadyGuard Pro — Custom Ticker Backtest
==========================================
Enter any tickers + weights. See how V3c regime signals
would have protected your specific portfolio.
"""
import numpy as np
import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="SteadyGuard Pro", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
    .stApp { background: #0a0e17; color: #e2e8f0; font-family: 'DM Sans', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 1200px;}
    .hero-title { font-size: 2.4rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; }
    .hero-sub { font-size: 1.05rem; color: #64748b; margin-top: 0.3rem; margin-bottom: 2rem; }
    .pro-badge { display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: #fff;
        font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 4px;
        letter-spacing: 0.08em; text-transform: uppercase; margin-left: 0.8rem; vertical-align: middle; }
    .metric-row { display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }
    .metric-card { flex: 1; min-width: 130px; background: #111827; border: 1px solid #1e293b;
        border-radius: 12px; padding: 1rem 1.1rem; text-align: center; }
    .metric-card.hl { border-color: #10b981; background: linear-gradient(180deg, #0f1f1a 0%, #111827 100%); }
    .metric-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 0.3rem; }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 500; color: #f1f5f9; }
    .metric-value.grn { color: #10b981; }
    .metric-delta { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64748b; margin-top: 0.15rem; }
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
    .regime-row { display: flex; gap: 0.5rem; margin: 0.6rem 0; flex-wrap: wrap; }
    .rc { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; padding: 0.3rem 0.7rem; border-radius: 6px; }
    .rc-l { background: #064e3b; color: #6ee7b7; }
    .rc-m { background: #713f12; color: #fcd34d; }
    .rc-h { background: #7c2d12; color: #fdba74; }
    .rc-c { background: #7f1d1d; color: #fca5a5; }
    .ref-note { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px;
        padding: 0.8rem 1rem; margin-top: 0.8rem; font-size: 0.78rem; color: #475569; line-height: 1.5; }
    .ref-note strong { color: #64748b; }
    .warn-box { background: #1c1917; border: 1px solid #78350f; border-radius: 8px;
        padding: 0.7rem 1rem; font-size: 0.8rem; color: #fbbf24; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

CL = {"static": "#6366f1", "sg": "#10b981",
      "sf": "rgba(99,102,241,0.15)", "sgf": "rgba(16,185,129,0.15)",
      "grid": "#1e293b", "bg": "#0a0e17", "paper": "#0a0e17", "txt": "#94a3b8"}


@st.cache_data
def load_signals():
    """Load V3c monthly signals."""
    for d in [Path("."), Path(__file__).parent, Path("/mnt/user-data/uploads")]:
        p = d / "monthly_data.json"
        if p.exists():
            with open(p) as f:
                return json.load(f)
    st.error("monthly_data.json not found.")
    st.stop()


@st.cache_data(ttl=3600)
def fetch_prices(tickers_str, bond_ticker):
    """Fetch daily price data via yfinance."""
    import yfinance as yf

    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
    all_tickers = list(set(tickers + [bond_ticker]))

    data = yf.download(all_tickers, start="1998-01-01", auto_adjust=True,
                       progress=False, threads=True)

    if data.empty:
        return None, "No data returned. Check ticker symbols."

    # Handle single vs multi ticker column format
    if len(all_tickers) == 1:
        closes = data[['Close']].copy()
        closes.columns = [all_tickers[0]]
    else:
        closes = data['Close'].copy()

    # Find common date range
    closes = closes.dropna()
    if len(closes) < 60:
        return None, f"Insufficient overlapping data ({len(closes)} days). Check tickers."

    return closes, None


def build_portfolio_returns(closes, tickers, weights, bond_ticker):
    """Compute daily portfolio + bond returns."""
    import pandas as pd

    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    weight_list = [float(w) / 100.0 for w in weights]

    # Normalize weights
    total_w = sum(weight_list)
    weight_list = [w / total_w for w in weight_list]

    # Daily returns
    rets = closes.pct_change().dropna()

    # Portfolio equity return = weighted sum
    port_ret = sum(rets[t] * w for t, w in zip(ticker_list, weight_list))
    bond_ret = rets[bond_ticker]

    # Align
    combined = pd.DataFrame({"equity": port_ret, "bond": bond_ret}).dropna()
    combined["ym"] = combined.index.to_period("M").astype(str)

    return combined


def run_daily_backtest(combined, signals_dict, eq_pct):
    """Daily backtest with monthly regime signals."""
    eq = eq_pct / 100.0
    vs = vg = 10000.0
    prev_scalar = 1.0
    prev_ym = None
    dates = []
    cs, cg = [10000.0], [10000.0]

    for date, row in combined.iterrows():
        ym = row["ym"]
        sig = signals_dict.get(ym)
        if sig is None:
            # No signal for this month — use LOW (scalar=1.0)
            scalar = 1.0
        else:
            scalar = sig["scalar"]

        rs = row["equity"]
        rb = row["bond"]

        # TX cost on regime change (first day of new month)
        if prev_ym is not None and ym != prev_ym:
            tx = 0.001 * abs(scalar - prev_scalar)
            vg *= (1 - tx)

        # Static
        vs *= (1 + eq * rs + (1 - eq) * rb)

        # SteadyGuard
        eq_adj = eq * scalar
        vg *= (1 + eq_adj * rs + (1 - eq_adj) * rb)

        dates.append(date)
        cs.append(vs)
        cg.append(vg)

        prev_scalar = scalar
        prev_ym = ym

    return dates, cs, cg


def metrics(curve, n_yr):
    a = np.array(curve)
    if a[0] == 0 or n_yr == 0:
        return {"CAGR": 0, "MaxDD": 0, "Vol": 0, "Sharpe": 0, "Calmar": 0, "Total": 0}
    cagr = (a[-1] / a[0]) ** (1 / n_yr) - 1
    r = np.diff(a) / a[:-1]
    vol = np.std(r, ddof=1) * np.sqrt(252)
    sharpe = cagr / vol if vol > 0 else 0
    pk = np.maximum.accumulate(a)
    dd = (a - pk) / pk
    mdd = dd.min()
    calmar = cagr / abs(mdd) if mdd != 0 else 0
    tot = a[-1] / a[0] - 1
    return {"CAGR": cagr, "MaxDD": mdd, "Vol": vol, "Sharpe": sharpe,
            "Calmar": calmar, "Total": tot}


# ── Load Signals ───────────────────────────────────────────────────────
mdata = load_signals()
signals_dict = {m["d"]: m for m in mdata}

# ── Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:0.5rem">
    <span class="hero-title">SteadyGuard</span><span class="pro-badge">Pro · Custom</span>
</div>
<div class="hero-sub">Backtest any portfolio with V3c regime protection</div>
""", unsafe_allow_html=True)

# ── Input Panel ────────────────────────────────────────────────────────
with st.container():
    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        tickers_input = st.text_input(
            "Equity Tickers (comma-separated)",
            value="SPY",
            help="Enter ticker symbols separated by commas. E.g.: QQQ, AAPL, MSFT",
            placeholder="SPY, QQQ, AAPL"
        )

    with c2:
        # Parse tickers to generate weight inputs
        ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        if len(ticker_list) == 1:
            weights_input = "100"
            st.text_input("Weights (%)", value="100", disabled=True)
        else:
            weights_input = st.text_input(
                "Weights (%)",
                value=", ".join(["" for _ in ticker_list]),
                help=f"Enter {len(ticker_list)} weights that sum to 100. E.g.: 50, 30, 20",
                placeholder=", ".join([str(round(100/len(ticker_list)))] * len(ticker_list))
            )

    with c3:
        bond_ticker = st.text_input("Bond Ticker", value="TLT",
                                     help="Bond/safe-haven asset for risk-off allocation")

# Parse weights
try:
    if len(ticker_list) == 1:
        weight_list = [100.0]
    else:
        weight_list = [float(w.strip()) for w in weights_input.split(",") if w.strip()]

    if len(weight_list) != len(ticker_list):
        weight_list = [100.0 / len(ticker_list)] * len(ticker_list)

    total_w = sum(weight_list)
    weight_list_norm = [w / total_w * 100 for w in weight_list]
except (ValueError, ZeroDivisionError):
    weight_list = [100.0 / len(ticker_list)] * len(ticker_list)
    weight_list_norm = weight_list

# Equity slider
c_slider, _, c_info = st.columns([2, 0.3, 1.5])
with c_slider:
    eq_pct = st.slider("Total Equity Allocation %", 0, 100, 100, 5,
                       help="% of portfolio in your equity tickers. Remainder goes to bonds.")
    bd_pct = 100 - eq_pct

    # Show allocation breakdown
    parts = " + ".join([f"{t} {w*eq_pct/100:.0f}%" for t, w in zip(ticker_list, weight_list_norm)])
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#94a3b8; margin:0.3rem 0 1rem 0;">
        {parts} + {bond_ticker} {bd_pct}%
    </div>
    """, unsafe_allow_html=True)

with c_info:
    rc = {}
    for m in mdata:
        rc[m['regime']] = rc.get(m['regime'], 0) + 1
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:0.8rem 1rem;margin-top:0.3rem">
        <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.4rem">
            V3c Signal History</div>
        <div class="regime-row">
            <span class="rc rc-l">LOW {rc.get('LOW',0)}</span>
            <span class="rc rc-m">MID {rc.get('MID',0)}</span>
            <span class="rc rc-h">HIGH {rc.get('HIGH',0)}</span>
            <span class="rc rc-c">CRISIS {rc.get('CRISIS',0)}</span>
        </div>
        <div style="font-size:0.72rem;color:#475569;margin-top:0.4rem">Signals: Jan 1998 – Jan 2026</div>
    </div>""", unsafe_allow_html=True)

# ── Caveat for non-SPY portfolios ──────────────────────────────────────
non_spy = any(t != "SPY" for t in ticker_list)
if non_spy:
    st.markdown("""
    <div class="warn-box">
        ⚠️ V3c signals are calibrated on S&P 500 (SPY) volatility and tail risk.
        Applied to other assets, protection may be stronger or weaker depending on
        correlation with SPY. Results are indicative, not validated.
    </div>
    """, unsafe_allow_html=True)

# ── Run Button ─────────────────────────────────────────────────────────
run_clicked = st.button("Run Backtest", type="primary", use_container_width=True)

if run_clicked or st.session_state.get("has_run", False):
    st.session_state["has_run"] = True

    all_tickers = list(set(ticker_list + [bond_ticker.strip().upper()]))
    all_tickers_str = ", ".join(all_tickers)

    with st.spinner(f"Fetching price data for {all_tickers_str}..."):
        closes, error = fetch_prices(", ".join(all_tickers), bond_ticker.strip().upper())

    if error:
        st.error(error)
        st.stop()

    # Build portfolio returns
    combined = build_portfolio_returns(closes, tickers_input, weight_list, bond_ticker.strip().upper())

    # Filter to signal period
    signal_months = set(signals_dict.keys())
    combined_filtered = combined[combined["ym"].isin(signal_months)]

    if len(combined_filtered) < 60:
        st.error(f"Only {len(combined_filtered)} trading days overlap with signal period (1998-2026). Need at least 60.")
        st.stop()

    start_date = combined_filtered.index.min()
    end_date = combined_filtered.index.max()
    n_years = (end_date - start_date).days / 365.25
    n_months = combined_filtered["ym"].nunique()

    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.82rem; color:#64748b; margin:0.5rem 0;">
        Data: {start_date.strftime('%b %Y')} — {end_date.strftime('%b %Y')} · {n_years:.1f} years · {len(combined_filtered):,} trading days
    </div>
    """, unsafe_allow_html=True)

    # ── Run Backtest ───────────────────────────────────────────────────
    dates, cs, cg = run_daily_backtest(combined_filtered, signals_dict, eq_pct)

    # Prepend start
    all_dates = [start_date] + dates
    sm = metrics(cs, n_years)
    gm = metrics(cg, n_years)

    # ── Metrics ────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">Results</div>', unsafe_allow_html=True)

    dd_better = gm['MaxDD'] > sm['MaxDD']
    cagr_better = gm['CAGR'] > sm['CAGR']

    def dh(sv, gv, fmt="pct"):
        d = gv - sv
        cls = "up" if d > 0 else "dn"
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

    # ── Chart ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">Equity Curve</div>', unsafe_allow_html=True)

    port_label = " + ".join(ticker_list) if len(ticker_list) <= 3 else f"{len(ticker_list)} tickers"

    fig = make_subplots(rows=2, cols=1, row_heights=[0.72, 0.28],
                        shared_xaxes=True, vertical_spacing=0.04)
    fig.add_trace(go.Scatter(x=all_dates, y=cs, name=f"Static ({port_label})",
                             line=dict(color=CL["static"], width=1.8), opacity=0.8), row=1, col=1)
    fig.add_trace(go.Scatter(x=all_dates, y=cg, name=f"SteadyGuard ({port_label})",
                             line=dict(color=CL["sg"], width=2.2)), row=1, col=1)

    for lbl, crv, clr, fl in [("_s", cs, CL["static"], CL["sf"]),
                                ("_g", cg, CL["sg"], CL["sgf"])]:
        a = np.array(crv)
        pk = np.maximum.accumulate(a)
        dd = (a - pk) / pk
        fig.add_trace(go.Scatter(x=all_dates, y=dd, name=lbl,
            line=dict(color=clr, width=0.8), fill="tozeroy", fillcolor=fl,
            showlegend=False), row=2, col=1)

    fig.update_layout(height=520, template="plotly_dark", paper_bgcolor=CL["paper"],
        plot_bgcolor=CL["bg"], font=dict(family="DM Sans", color=CL["txt"], size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=11)),
        margin=dict(l=60, r=20, t=40, b=40), hovermode="x unified")
    fig.update_yaxes(type="log", title="Growth of $10,000", gridcolor=CL["grid"],
                     gridwidth=0.5, row=1, col=1, tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(title="Drawdown", gridcolor=CL["grid"], gridwidth=0.5,
                     tickformat=".0%", row=2, col=1)
    fig.update_xaxes(gridcolor=CL["grid"], gridwidth=0.5)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Comparison Table ───────────────────────────────────────────────
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
        sg_wins = gv > sv if not lower_win else gv > sv
        sc = "win" if sg_wins else ""
        dc = "win" if sg_wins else "lose"
        trows += f'<tr><td>{label}</td><td>{ss}</td><td class="{sc}">{gs}</td><td class="{dc}">{ds}</td></tr>'

    st.markdown(f"""
    <table class="ct">
    <thead><tr><th>Metric</th><th>Static</th><th>SteadyGuard</th><th>Delta</th></tr></thead>
    <tbody>{trows}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # ── Methodology ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="ref-note">
        <strong>Methodology:</strong> Daily returns for {', '.join(ticker_list)} fetched from Yahoo Finance,
        weighted {'equally' if len(set(weight_list)) == 1 else 'as specified'} to form the equity component.
        V3c regime signals (calibrated on SPY) determine monthly equity exposure:
        LOW → 100%, MID → 80%, HIGH → 50%, CRISIS → 20%.
        Capital freed from equities moves to {bond_ticker}. Transaction cost of 10bps per regime change.
        {'<strong>Note:</strong> Signals are SPY-calibrated; effectiveness on other assets depends on correlation.' if non_spy else ''}
    </div>
    """, unsafe_allow_html=True)

else:
    # Show instructions when no backtest has been run
    st.markdown("""
    <div style="text-align:center; padding:3rem 2rem; color:#475569;">
        <div style="font-size:1.3rem; margin-bottom:0.5rem;">Enter your tickers and click <strong style="color:#10b981;">Run Backtest</strong></div>
        <div style="font-size:0.9rem;">Try SPY, QQQ, or any combination of tickers with custom weights.</div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="foot">
    SteadyGuard by Ben Vecchiarelli · Hypothetical backtest results — not financial advice.<br>
    Past performance does not guarantee future results.
</div>
""", unsafe_allow_html=True)
