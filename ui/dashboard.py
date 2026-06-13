"""
Dashboard tab renderer.
Shows equity, performance, advanced risk metrics (max DD, streaks, etc.),
equity curve + drawdown visualization, and position risk signals.
"""

import streamlit as st
from typing import Any, Dict

from ui.components import (
    render_equity_curve_chart,
    render_drawdown_chart,
    render_risk_metrics_cards,
    render_risk_signals,
)
from utils.risk_metrics import get_full_risk_stats


def render_dashboard(sim: Any) -> None:
    """Main dashboard content."""

    # --- KEY METRICS ---
    equity = sim.get_equity()
    available = sim.get_available_margin()
    used = sim.get_used_margin()
    unrealized_total = equity - sim.account.balance

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delta = equity - 10000.0
        st.metric("Total Equity", f"${equity:,.2f}", f"${delta:+,.2f}")
    with col2:
        st.metric("Available Margin", f"${available:,.2f}")
    with col3:
        st.metric("Used Margin", f"${used:,.2f}")
    with col4:
        color = "normal" if unrealized_total == 0 else ("inverse" if unrealized_total < 0 else "normal")
        st.metric("Unrealized PnL", f"${unrealized_total:,.2f}", delta_color=color)

    st.divider()

    # --- EQUITY CURVE + DRAWDOWN (advanced) ---
    st.markdown("### 📈 Equity Curve & Drawdown")
    equity_df = sim.get_equity_curve_df()

    render_equity_curve_chart(equity_df)
    render_drawdown_chart(equity_df)

    st.divider()

    # --- ADVANCED RISK METRICS ---
    st.markdown("### 🛡️ Advanced Risk Metrics")
    trade_df = sim.get_trade_history_df()
    risk_stats = get_full_risk_stats(equity_df, trade_df)
    render_risk_metrics_cards(risk_stats)

    with st.expander("How these metrics are calculated"):
        st.caption(
            "Max Drawdown = largest peak-to-trough decline on the equity curve. "
            "Current Drawdown = distance from the highest equity mark so far. "
            "Profit Factor = gross wins / gross losses. "
            "Streaks = consecutive winning or losing closed trades."
        )

    st.divider()

    # --- PERFORMANCE SUMMARY ---
    st.markdown("### Performance Summary (Closed Trades)")
    history = sim.get_trade_history()

    if history == "No trades yet.":
        st.info("No closed trades yet. Open and close positions (or trigger SL/TP) to build stats.")
    else:
        total_trades = len(history)
        winning = [t for t in history if t.get("realized_pnl", 0) > 0]
        losing = [t for t in history if t.get("realized_pnl", 0) < 0]

        win_rate = (len(winning) / total_trades * 100) if total_trades else 0
        total_pnl = sum(t.get("realized_pnl", 0) for t in history)
        avg_pnl = total_pnl / total_trades if total_trades else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Closed Trades", total_trades)
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col2:
            st.metric("Total Realized PnL", f"${total_pnl:,.2f}")
            st.metric("Avg PnL / Trade", f"${avg_pnl:,.2f}")
        with col3:
            bw = max((t["realized_pnl"] for t in winning), default=0)
            bl = min((t["realized_pnl"] for t in losing), default=0)
            st.metric("Biggest Winner", f"${bw:,.2f}" if winning else "—")
            st.metric("Biggest Loser", f"${bl:,.2f}" if losing else "—")

        with st.expander("More statistics"):
            st.write(f"Winning trades: **{len(winning)}** | Losing: **{len(losing)}**")
            if winning:
                st.write(f"Average win: **${sum(t['realized_pnl'] for t in winning)/len(winning):,.2f}**")
            if losing:
                st.write(f"Average loss: **${sum(t['realized_pnl'] for t in losing)/len(losing):,.2f}**")

    st.divider()

    # --- RISK SIGNALS ---
    st.markdown("### Risk & Position Signals (with SL/TP awareness)")
    positions = sim.get_positions_list()
    render_risk_signals(positions, equity)
