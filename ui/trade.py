"""
Trade tab renderer.
- Open positions with leverage + optional Stop Loss / Take Profit
- Live position table with SL/TP editing
- Powerful Market Simulator (random walk, % bumps, multi-tick)
- Funding and manual close controls
"""

import streamlit as st
from typing import Any

from data.mock_data import get_default_price, get_volatility, get_all_symbols
from utils.price_simulator import (
    apply_percentage_move,
    random_walk_tick,
    batch_random_walk,
)
import random


def render_trade(sim: Any) -> None:
    st.markdown("### Open New Leveraged Position (with SL/TP)")

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        # Symbol with smart default price
        symbol = st.text_input("Symbol", value="NVDA").upper().strip()
        suggested = get_default_price(symbol)
        entry_price = st.number_input(
            "Entry / Mark Price",
            value=suggested,
            step=0.5,
            min_value=0.01
        )

        direction = st.selectbox("Direction", ["long", "short"])
        size_usd = st.number_input("Notional Size (USD)", value=2000.0, step=100.0, min_value=50.0)

        leverage = st.slider("Leverage (x)", 1, 50, 10, help="Higher leverage = lower margin but higher liquidation risk")

    with col2:
        st.markdown("**Optional Risk Orders**")
        use_sl = st.checkbox("Set Stop Loss", value=False)
        stop_loss = None
        if use_sl:
            default_sl = entry_price * 0.95 if direction == "long" else entry_price * 1.05
            stop_loss = st.number_input("Stop Loss Price", value=round(default_sl, 2), step=0.5)

        use_tp = st.checkbox("Set Take Profit", value=False)
        take_profit = None
        if use_tp:
            default_tp = entry_price * 1.10 if direction == "long" else entry_price * 0.90
            take_profit = st.number_input("Take Profit Price", value=round(default_tp, 2), step=0.5)

        # Margin preview (reused logic)
        required_margin = size_usd / leverage if leverage > 0 else size_usd
        st.markdown("**Margin Check**")
        st.write(f"Required Initial Margin: **${required_margin:,.2f}**")
        avail = sim.get_available_margin()
        st.write(f"Available now: **${avail:,.2f}**")

        can_open = required_margin <= avail and size_usd > 0

        if not can_open and size_usd > 0:
            st.error("Insufficient margin for this size/leverage combination.")
        elif size_usd > 0:
            st.success("Margin available.")

        if st.button("🚀 Open Position", use_container_width=True, disabled=not can_open):
            result = sim.open_position(
                symbol, direction, entry_price, size_usd,
                leverage=leverage,
                stop_loss=stop_loss if use_sl else None,
                take_profit=take_profit if use_tp else None
            )
            if "Opened" in str(result):
                st.success(result)
            else:
                st.error(result)
            st.rerun()

    st.divider()

    # === OPEN POSITIONS + EDIT SL/TP ===
    st.markdown("### Open Positions & Live Mark-to-Market")

    positions = sim.get_positions_list()

    if not positions:
        st.info("No open positions yet. Use the form above to open one.")
    else:
        from ui.components import render_positions_dataframe
        render_positions_dataframe(positions)

        # Per-position SL/TP editor
        st.markdown("**Adjust Stop Loss / Take Profit**")
        for pos in positions:
            sym = pos["symbol"]
            with st.expander(f"Modify {sym} SL/TP", expanded=False):
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_sl = st.number_input(
                        "New Stop Loss (blank = none)",
                        value=pos.get("stop_loss") or 0.0,
                        step=0.5,
                        key=f"sl_{sym}"
                    )
                with c2:
                    new_tp = st.number_input(
                        "New Take Profit (blank = none)",
                        value=pos.get("take_profit") or 0.0,
                        step=0.5,
                        key=f"tp_{sym}"
                    )
                with c3:
                    if st.button(f"Update {sym}", key=f"upd_{sym}"):
                        sl_val = new_sl if new_sl > 0 else None
                        tp_val = new_tp if new_tp > 0 else None
                        sim.positions[sym].set_sl_tp(sl_val, tp_val)
                        st.success(f"Updated SL/TP for {sym}")
                        st.rerun()

        # Quick single-symbol price update (legacy)
        st.markdown("**Quick Price Mark (single symbol)**")
        quick_sym = st.selectbox("Symbol to mark", list(sim.positions.keys()), key="quick_mark")
        new_price = st.number_input("New current price", value=float(sim.positions[quick_sym].current_price), step=0.5, key="quick_price")
        if st.button("Mark Price & Check SL/TP"):
            sim.update_position_price(quick_sym, new_price)
            st.rerun()

    st.divider()

    # === MARKET SIMULATOR (NEW) ===
    st.markdown("### 📡 Market Simulator — Random Walk & Price Shocks")
    st.caption("Practice risk management with realistic price movement. SL/TP orders will auto-execute when hit.")

    colm1, colm2 = st.columns(2)

    with colm1:
        st.markdown("**Global Controls**")
        vol = st.slider("Base Volatility per tick (%)", 0.2, 5.0, 2.0, 0.2) / 100.0
        drift = st.slider("Drift per tick (%)", -1.0, 1.0, 0.0, 0.1) / 100.0

        if st.button("🔄 Random Walk Tick (All Positions)", use_container_width=True):
            if sim.positions:
                updates = batch_random_walk(
                    {s: p.current_price for s, p in sim.positions.items()},
                    volatility=vol,
                    drift=drift,
                    per_symbol_vol={s: get_volatility(s) for s in sim.positions.keys()}
                )
                sim.batch_update_prices(updates)
                st.success("Random tick applied to all positions.")
                st.rerun()
            else:
                st.warning("Open positions first.")

        if st.button("▶️ Run 5 Random Ticks", use_container_width=True):
            if sim.positions:
                for _ in range(5):
                    updates = batch_random_walk(
                        {s: p.current_price for s, p in sim.positions.items()},
                        volatility=vol,
                        drift=drift
                    )
                    sim.batch_update_prices(updates)
                st.success("5 random ticks simulated.")
                st.rerun()

    with colm2:
        st.markdown("**Directional Shocks**")
        pct = st.number_input("Shock size (%)", value=2.0, step=0.5)
        shock_sym = st.selectbox("Apply shock to", ["ALL"] + list(sim.positions.keys()) if sim.positions else ["ALL"], key="shock_sym")

        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"📈 +{pct}% Move"):
                _apply_shock(sim, shock_sym, pct)
                st.rerun()
        with c2:
            if st.button(f"📉 {pct}% Move"):
                _apply_shock(sim, shock_sym, -pct)
                st.rerun()

        st.markdown("**Popular Symbols Quick Open**")
        popular = get_all_symbols()[:6]
        cols_pop = st.columns(3)
        for i, pop in enumerate(popular):
            with cols_pop[i % 3]:
                if st.button(f"+ {pop}", key=f"quick_{pop}"):
                    price = get_default_price(pop)
                    # open small long for demo
                    res = sim.open_position(pop, "long", price, 1500, leverage=8)
                    st.success(res)
                    st.rerun()

    st.divider()

    # === FUNDING & CLOSE ===
    st.markdown("### Funding & Close Positions")

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        if st.button("💸 Apply Funding (1h period)", use_container_width=True):
            if sim.positions:
                res = sim.apply_funding(1)
                st.success(res)
                st.rerun()
            else:
                st.warning("No positions open.")

    with fcol2:
        if sim.positions:
            to_close = st.selectbox("Close position", list(sim.positions.keys()), key="close_sym")
            exit_p = st.number_input("Exit price", value=sim.positions[to_close].current_price, step=0.5, key="manual_exit")
            if st.button("❌ Close Position Manually", use_container_width=True):
                res = sim.close_position(to_close, exit_p)
                st.success(res)
                st.rerun()
        else:
            st.info("No open positions to close.")


def _apply_shock(sim: Any, symbol_or_all: str, pct: float) -> None:
    """Internal helper to apply % shock and check triggers."""
    if not sim.positions:
        return
    if symbol_or_all == "ALL":
        targets = list(sim.positions.keys())
    else:
        targets = [symbol_or_all] if symbol_or_all in sim.positions else []

    updates = {}
    for sym in targets:
        curr = sim.positions[sym].current_price
        updates[sym] = apply_percentage_move(curr, pct)
    sim.batch_update_prices(updates)
