import streamlit as st
import pandas as pd
from core.simulator import Simulator

# =====================
# PAGE CONFIG + PROFESSIONAL THEME
# =====================
st.set_page_config(
    page_title="Jon's Hyperliquid Trading App",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional trading platform look
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    h1 {
        color: #00d4ff;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    .stMetricValue {
        font-size: 1.6rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e222a;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #aaaaaa;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00d4ff;
        color: black;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# =====================
# HEADER / LOGO
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
# INITIALIZE SIMULATOR
# =====================
if "sim" not in st.session_state:
    st.session_state.sim = Simulator(starting_balance=10000.0)

sim = st.session_state.sim

# =====================
# TABS
# =====================
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Trade", "History", "AI Insights"])

# =====================
# TAB 1: DASHBOARD
# =====================
with tab1:
    st.write("### Account Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Account Equity", f"${sim.account.equity:,.2f}")
    with col2:
        st.metric("Available Margin", f"${sim.account.available_margin:,.2f}")
    with col3:
        st.metric("Used Margin", f"${sim.account.used_margin:,.2f}")

    st.divider()
    st.write("### Performance Summary")

    history = sim.get_trade_history()
    if history == "No trades yet.":
        st.info("No trades yet. Complete some trades to see performance stats.")
    else:
        total_trades = len(history)
        winning_trades = [t for t in history if t['realized_pnl'] > 0]
        losing_trades = [t for t in history if t['realized_pnl'] < 0]

        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t['realized_pnl'] for t in history)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

        avg_win = sum(t['realized_pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['realized_pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        biggest_winner = max(history, key=lambda x: x['realized_pnl'])
        biggest_loser = min(history, key=lambda x: x['realized_pnl'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", total_trades)
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col2:
            st.metric("Total Realized PnL", f"${total_pnl:,.2f}")
            st.metric("Average PnL per Trade", f"${avg_pnl:,.2f}")
        with col3:
            st.metric("Biggest Winner", f"${biggest_winner['realized_pnl']:,.2f}")
            st.metric("Biggest Loser", f"${biggest_loser['realized_pnl']:,.2f}")

        st.write("**Additional Stats**")
        st.write(f"- Winning Trades: {len(winning_trades)}")
        st.write(f"- Losing Trades: {len(losing_trades)}")
        st.write(f"- Average Win: ${avg_win:,.2f}")
        st.write(f"- Average Loss: ${avg_loss:,.2f}")

    st.divider()
    st.write("### Risk & Signals")

    if not sim.positions:
        st.info("No open positions. Signals will appear here when you have active trades.")
    else:
        for symbol, position in sim.positions.items():
            unrealized = position.unrealized_pnl()
            pnl_percent = (unrealized / position.size_usd) * 100 if position.size_usd != 0 else 0

            signals = []

            if pnl_percent <= -8:
                signals.append("🔴 **High Risk**: Position is down more than 8%. Strongly consider reviewing or reducing size.")
            elif pnl_percent <= -3:
                signals.append("🟠 **Caution**: Position is down. Monitor closely.")

            if pnl_percent >= 15:
                signals.append("🟢 **Strong Gain**: Position up over 15%. Consider taking partial profits.")
            elif pnl_percent >= 8:
                signals.append("🟢 **Good Gain**: Solid unrealized profit. Think about risk management.")

            position_risk = (position.size_usd / sim.account.equity) * 100 if sim.account.equity > 0 else 0
            if position_risk > 40:
                signals.append(f"🟡 **Concentration Risk**: This position is {position_risk:.0f}% of your equity. High single-position risk.")
            elif position_risk > 25:
                signals.append(f"🟡 **Moderate Risk**: Position size is {position_risk:.0f}% of equity.")

            st.write(f"**{symbol} ({position.direction.upper()})** — Unrealized: ${unrealized:,.2f} ({pnl_percent:.1f}%)")

            if signals:
                for signal in signals:
                    st.write(signal)
            else:
                st.write("✅ No major signals at the moment.")

            st.write("---")

# =====================
# TAB 2: TRADE
# =====================
with tab2:
    st.write("### Open New Position")
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Symbol", value="NVDA").upper()
        direction = st.selectbox("Direction", ["long", "short"])
        entry_price = st.number_input("Entry Price", value=120.0, step=0.5)
        size_usd = st.number_input("Position Size (USD)", value=2000.0, step=100.0)
    with col2:
        if st.button("Open Position", use_container_width=True):
            result = sim.open_position(symbol, direction, entry_price, size_usd)
            st.success(result)
            st.rerun()

    st.divider()
    st.write("### Open Positions")
    positions_text = sim.get_positions()
    if positions_text == "No open positions.":
        st.info("No open positions currently.")
    else:
        st.text(positions_text)

    st.divider()
    st.write("### Funding & Close Position")
    if st.button("Apply Funding to Open Positions", use_container_width=True):
        if sim.positions:
            before = sim.account.equity
            result = sim.apply_funding()
            after = sim.account.equity
            st.success(result)
            st.write(f"**Change:** ${after - before:,.2f}")
            st.rerun()
        else:
            st.warning("No open positions.")

    if sim.positions:
        symbol_to_close = st.selectbox("Select position to close", list(sim.positions.keys()))
        exit_price = st.number_input("Exit Price", value=125.0, step=0.5, key="exit_price")
        if st.button("Close Position", use_container_width=True):
            result = sim.close_position(symbol_to_close, exit_price)
            st.success(result)
            st.rerun()

# =====================
# TAB 3: HISTORY
# =====================
with tab3:
    st.write("### Trade History")
    history = sim.get_trade_history()
    if history == "No trades yet.":
        st.info("No trades recorded yet.")
    else:
        for i, trade in enumerate(reversed(history), 1):
            st.write(f"**Trade #{i}** — {trade['timestamp']}")
            st.write(f"{trade['direction'].upper()} {trade['symbol']} | Entry: ${trade['entry_price']:,.2f} → Exit: ${trade['exit_price']:,.2f}")
            st.write(f"Size: ${trade['size_usd']:,.2f} | Realized PnL: ${trade['realized_pnl']:,.2f}")
            st.divider()

        st.divider()
        if st.button("Export Trade History to CSV", use_container_width=True):
            df = pd.DataFrame(history)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="trade_history.csv",
                mime="text/csv",
                use_container_width=True
            )

# =====================
# TAB 4: AI INSIGHTS
# =====================
with tab4:
    st.write("### AI Trading Insights")
    history = sim.get_trade_history()
    if history == "No trades yet.":
        st.info("Complete some trades to get AI insights.")
    else:
        total_trades = len(history)
        winning_trades = len([t for t in history if t['realized_pnl'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t['realized_pnl'] for t in history)

        st.write("**Quick Stats**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", total_trades)
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            st.metric("Total PnL", f"${total_pnl:,.2f}")

        st.divider()
        st.write("**Ask a Custom Question**")
        user_question = st.text_area(
            "What would you like to know about your trading?",
            placeholder="e.g. What’s my biggest weakness? How should I adjust my position sizing?",
            height=80
        )

        if st.button("Generate AI Prompt", use_container_width=True):
            if user_question.strip() == "":
                st.warning("Please enter a question.")
            else:
                prompt = f"""You are an expert trading coach analyzing my paper trading performance.

**My Stats:**
- Total Trades: {total_trades}
- Win Rate: {win_rate:.1f}%
- Total Realized PnL: ${total_pnl:,.2f}
- Current Equity: ${sim.account.equity:,.2f}

**Trade History:**
"""
                for trade in history:
                    prompt += f"- {trade['timestamp']}: {trade['direction'].upper()} {trade['symbol']} | Entry: ${trade['entry_price']:.2f} → Exit: ${trade['exit_price']:.2f} | PnL: ${trade['realized_pnl']:.2f}\n"

                prompt += f"""
**My Question:**
{user_question}

Please give a clear, honest, and constructive analysis with specific suggestions."""

                st.write("**Copy and paste this prompt to me (Grok):**")
                st.code(prompt, language="markdown")

        st.divider()
        if st.button("Analyze My Overall Performance", use_container_width=True):
            prompt = f"""You are an expert trading coach. Analyze my paper trading performance:

**Stats:**
- Total Trades: {total_trades}
- Win Rate: {win_rate:.1f}%
- Total Realized PnL: ${total_pnl:,.2f}
- Current Equity: ${sim.account.equity:,.2f}

**Trade History:**
"""
            for trade in history:
                prompt += f"- {trade['timestamp']}: {trade['direction'].upper()} {trade['symbol']} | PnL: ${trade['realized_pnl']:.2f}\n"

            prompt += """
Please provide:
1. Overall performance assessment
2. Key patterns or behaviors you notice
3. Specific suggestions for improvement
4. Any risk management observations

Be honest and constructive."""

            st.write("**Copy and paste this prompt to me (Grok):**")
            st.code(prompt, language="markdown")

st.caption("Modular Design • Professional Trading Platform • Funding + Trade History + AI Insights")