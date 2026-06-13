"""
History tab renderer.
Shows closed trades in a rich table, cumulative PnL chart,
full equity curve, and CSV export.
"""

import streamlit as st
from typing import Any

from ui.components import (
    render_positions_dataframe,
    render_cumulative_pnl_chart,
    render_equity_curve_chart,
)


def render_history(sim: Any) -> None:
    st.markdown("### Trade History & Performance Charts")

    trade_df = sim.get_trade_history_df()

    if trade_df.empty:
        st.info("No trades recorded yet. Close positions (manually or via SL/TP) to populate history.")
        return

    # Rich table
    st.dataframe(
        trade_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "realized_pnl": st.column_config.NumberColumn("Realized PnL", format="$%.2f"),
            "cumulative_pnl": st.column_config.NumberColumn("Cumulative PnL", format="$%.2f"),
            "size_usd": st.column_config.NumberColumn("Notional", format="$%.0f"),
            "leverage": st.column_config.NumberColumn("Leverage", format="%d x"),
        }
    )

    st.divider()

    st.markdown("#### Cumulative Realized PnL")
    render_cumulative_pnl_chart(trade_df)

    st.markdown("#### Full Account Equity Curve (includes unrealized + funding + SL/TP closes)")
    equity_df = sim.get_equity_curve_df()
    render_equity_curve_chart(equity_df, height=260)

    st.divider()

    if st.button("📥 Export Trade History to CSV", use_container_width=True):
        csv = trade_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download trade_history.csv",
            data=csv,
            file_name="trade_history.csv",
            mime="text/csv",
            use_container_width=True
        )
