"""
Jon's Hyperliquid Trading App - Main Streamlit entrypoint (thin orchestrator).

All heavy UI logic has been extracted to the ui/ package for better modularity.
Core engine lives in core/.
Price simulation + risk calculations live in utils/ + data/.
"""

import streamlit as st
from core.simulator import Simulator

# Modular UI
from ui import (
    render_dashboard,
    render_trade,
    render_history,
    render_ai_insights,
)

# Optional: ensure data / utils are importable (side effect of package inits)
import data.mock_data  # noqa
import utils.price_simulator  # noqa
import utils.risk_metrics  # noqa

# =====================
# PAGE CONFIG + THEME
# =====================
st.set_page_config(
    page_title="Jon's Hyperliquid Trading App",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional dark theme (kept here for the thin entrypoint)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    h1, h2, h3 { color: #00d4ff; font-family: 'Segoe UI', system-ui, sans-serif; font-weight: 600; }
    .stMetricValue { font-size: 1.65rem; font-weight: 700; }
    .stMetricLabel { font-size: 0.85rem; color: #888; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e222a; border-radius: 8px 8px 0 0; padding: 10px 18px; color: #aaaaaa; }
    .stTabs [aria-selected="true"] { background-color: #00d4ff; color: #0e1117; font-weight: 700; }
    .positive { color: #00c853 !important; font-weight: 600; }
    .negative { color: #ff5252 !important; font-weight: 600; }
    .stDataFrame { font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# =====================
# HEADER
# =====================
st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
        <div style="font-size: 42px;">🌊</div>
        <div>
            <h1 style="margin: 0; color: #00d4ff;">Jon's Hyperliquid Trading App</h1>
            <p style="margin: 0; color: #888888; font-size: 1.1rem;">Equity Perps Paper Trading Platform</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# =====================
# SESSION
# =====================
if "sim" not in st.session_state:
    st.session_state.sim = Simulator(starting_balance=10000.0)

sim = st.session_state.sim

# =====================
# SIDEBAR
# =====================
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    if st.button("🔄 Reset Paper Account", use_container_width=True):
        msg = sim.reset(10000.0)
        st.success(msg)
        st.rerun()

    st.divider()
    st.markdown("**Live Session**")
    st.write(f"**Equity:** ${sim.get_equity():,.2f}")
    st.write(f"**Open Positions:** {len(sim.positions)}")
    st.write(f"**Total Notional:** ${sim.get_total_notional():,.0f}")

    st.divider()
    st.caption("Modular Architecture\nHyperliquid Perps • Leverage • SL/TP • Random Walk • Advanced Risk Metrics")

# =====================
# TABS (delegated to ui package)
# =====================
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Trade", "History", "AI Insights"])

with tab1:
    render_dashboard(sim)

with tab2:
    render_trade(sim)

with tab3:
    render_history(sim)

with tab4:
    render_ai_insights(sim)

st.caption("Modular • Dark Professional Theme • Hyperliquid Perps Paper Trading • SL/TP Auto-Execution • Random Walk Market Simulator • Full Risk Metrics")