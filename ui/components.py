"""
Reusable Streamlit UI components for the Hyperliquid paper trading app.

All components respect the dark professional theme.
They encapsulate charts, tables, badges, and metric cards.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Dict, Any, Optional


def render_pnl_badge(pnl: float, pct: Optional[float] = None) -> None:
    """Render a colored PnL value."""
    css_class = "positive" if pnl >= 0 else "negative"
    text = f"${pnl:,.2f}"
    if pct is not None:
        text += f" ({pct:+.1f}%)"
    st.markdown(f'<span class="{css_class}">{text}</span>', unsafe_allow_html=True)


def render_positions_dataframe(positions: List[Dict[str, Any]]) -> None:
    """Professional dataframe for open positions including SL/TP and risk."""
    if not positions:
        st.info("No open positions.")
        return

    df = pd.DataFrame(positions)

    # Nice column selection + formatting
    cols = [
        "symbol", "direction", "leverage", "entry_price", "current_price",
        "size_usd", "initial_margin", "unrealized_pnl", "unrealized_pnl_pct",
        "est_liquidation_price", "risk_pct_equity"
    ]
    # Add optional SL/TP if present
    extra = []
    if "stop_loss" in df.columns:
        extra.append("stop_loss")
    if "take_profit" in df.columns:
        extra.append("take_profit")

    display_cols = [c for c in cols + extra if c in df.columns]

    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "unrealized_pnl": st.column_config.NumberColumn("Unrealized PnL", format="$%.2f"),
            "unrealized_pnl_pct": st.column_config.NumberColumn("PnL %", format="%.2f%%"),
            "est_liquidation_price": st.column_config.NumberColumn("Est. Liq", format="$%.2f"),
            "risk_pct_equity": st.column_config.NumberColumn("Risk % Eq", format="%.1f%%"),
            "stop_loss": st.column_config.NumberColumn("Stop Loss", format="$%.2f"),
            "take_profit": st.column_config.NumberColumn("Take Profit", format="$%.2f"),
            "size_usd": st.column_config.NumberColumn("Notional", format="$%.0f"),
            "initial_margin": st.column_config.NumberColumn("Margin", format="$%.0f"),
        }
    )


def render_equity_curve_chart(equity_df: pd.DataFrame, height: int = 340) -> None:
    """Interactive equity curve with starting balance reference line."""
    if equity_df.empty or len(equity_df) < 2:
        st.info("Equity curve will populate after trading activity.")
        return

    fig = px.line(
        equity_df,
        x="timestamp",
        y="equity",
        title="Account Equity Over Time",
        markers=True,
        hover_data=["event", "positions"]
    )
    fig.update_traces(line=dict(color="#00d4ff", width=3), marker=dict(size=6))
    fig.update_layout(
        height=height,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
        xaxis=dict(title="Time", gridcolor="#2a2f38"),
        yaxis=dict(title="Equity (USD)", gridcolor="#2a2f38"),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.add_hline(y=10000, line_dash="dot", line_color="#888", annotation_text="Starting Balance")
    st.plotly_chart(fig, use_container_width=True)


def render_drawdown_chart(equity_df: pd.DataFrame, height: int = 180) -> None:
    """Drawdown % chart (area) under the equity curve for risk visualization."""
    if equity_df.empty or len(equity_df) < 2 or "equity" not in equity_df.columns:
        return

    eq = equity_df["equity"].astype(float)
    peak = eq.cummax()
    dd = (peak - eq) / peak * 100

    dd_df = pd.DataFrame({
        "timestamp": equity_df["timestamp"],
        "drawdown_pct": dd
    })

    fig = px.area(
        dd_df,
        x="timestamp",
        y="drawdown_pct",
        title="Drawdown % from Peak",
        color_discrete_sequence=["#ff5252"]
    )
    fig.update_layout(
        height=height,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa", size=11),
        xaxis=dict(gridcolor="#2a2f38", title=""),
        yaxis=dict(gridcolor="#2a2f38", title="Drawdown %"),
        margin=dict(l=20, r=20, t=30, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)


def render_cumulative_pnl_chart(trade_df: pd.DataFrame, height: int = 260) -> None:
    """Cumulative realized PnL line chart."""
    if trade_df.empty or "cumulative_pnl" not in trade_df.columns:
        st.info("Close some trades to see cumulative PnL.")
        return

    fig = px.line(
        trade_df,
        x="timestamp",
        y="cumulative_pnl",
        markers=True,
        title="Cumulative Realized PnL"
    )
    fig.update_traces(line=dict(color="#00c853", width=3))
    fig.update_layout(
        height=height,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
        xaxis=dict(gridcolor="#2a2f38"),
        yaxis=dict(gridcolor="#2a2f38"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_risk_metrics_cards(metrics: Dict[str, Any]) -> None:
    """Display advanced risk metrics in a clean 4-column grid."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Max Drawdown", f"{metrics.get('max_drawdown_pct', 0):.2f}%")
        st.metric("Current Drawdown", f"{metrics.get('current_drawdown_pct', 0):.2f}%")

    with col2:
        pf = metrics.get('profit_factor', 0)
        pf_display = "∞" if pf == float("inf") else f"{pf:.2f}"
        st.metric("Profit Factor", pf_display)
        st.metric("Expectancy / Trade", f"${metrics.get('expectancy', 0):,.2f}")

    with col3:
        ctype = metrics.get("current_type", "flat")
        cstreak = metrics.get("current_streak", 0)
        streak_label = f"{cstreak} {ctype.capitalize()}" if cstreak > 0 else "—"
        st.metric("Current Streak", streak_label)

    with col4:
        st.metric("Longest Win Streak", metrics.get("max_win_streak", 0))
        st.metric("Longest Loss Streak", metrics.get("max_loss_streak", 0))


def render_risk_signals(positions: List[Dict], total_equity: float) -> None:
    """Render the dynamic risk & liquidation signals (moved from original Dashboard)."""
    if not positions:
        st.info("No open positions. Risk signals will appear here when you have active trades.")
        return

    for pos in positions:
        symbol = pos["symbol"]
        direction = pos["direction"].upper()
        lev = pos.get("leverage", 1)
        unrealized = pos["unrealized_pnl"]
        pnl_pct = pos["unrealized_pnl_pct"]
        liq = pos["est_liquidation_price"]
        risk_pct = pos.get("risk_pct_equity", 0)

        css = "positive" if unrealized >= 0 else "negative"
        st.markdown(
            f"**{symbol} ({direction} @ {lev}x)** — "
            f'<span class="{css}">Unrealized: ${unrealized:,.2f} ({pnl_pct:+.1f}%)</span> | '
            f"Liq ≈ ${liq:,.2f}",
            unsafe_allow_html=True
        )

        signals = []

        if pnl_pct <= -12:
            signals.append("🔴 **HIGH RISK** — Down >12%. Consider closing or hedging.")
        elif pnl_pct <= -5:
            signals.append("🟠 **Caution** — Material unrealized loss. Watch closely.")

        if pnl_pct >= 18:
            signals.append("🟢 **Strong Gain** — >18% unrealized. Consider scaling out.")
        elif pnl_pct >= 9:
            signals.append("🟢 **Good Gain** — Solid profit. Tighten risk or take partials.")

        if risk_pct > 45:
            signals.append(f"🟡 **CONCENTRATION RISK** — {risk_pct:.0f}% of total equity.")
        elif risk_pct > 28:
            signals.append(f"🟡 **Moderate Concentration** — {risk_pct:.0f}% of equity.")

        # SL/TP proximity hints
        if pos.get("stop_loss"):
            sl = pos["stop_loss"]
            dist_sl = abs((pos["current_price"] - sl) / pos["entry_price"] * 100)
            if dist_sl < 3:
                signals.append(f"⚠️ Very close to Stop Loss (${sl:,.2f})")

        if pos.get("take_profit"):
            tp = pos["take_profit"]
            dist_tp = abs((pos["current_price"] - tp) / pos["entry_price"] * 100)
            if dist_tp < 2.5:
                signals.append(f"🎯 Approaching Take Profit (${tp:,.2f})")

        entry = pos["entry_price"]
        current = pos["current_price"]
        dist_liq = abs((current - liq) / entry * 100) if entry else 0
        if dist_liq < 4:
            signals.append(f"⚠️ **Close to liquidation** — only ~{dist_liq:.1f}% away.")

        for s in signals:
            st.write(s)
        if not signals:
            st.write("✅ No urgent signals.")
        st.markdown("---")
