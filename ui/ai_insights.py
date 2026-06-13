"""
AI Insights tab.
Generates high-quality copy-paste prompts for Grok (or any LLM) that include
leverage, SL/TP, drawdown, streaks, and full trade context.
"""

import streamlit as st
from typing import Any


def render_ai_insights(sim: Any) -> None:
    st.markdown("### AI Trading Coach Prompts")

    history = sim.get_trade_history()
    equity = sim.get_equity()

    if history == "No trades yet.":
        st.info("Close at least a few trades (including some via SL or TP) to generate meaningful coaching prompts.")
        return

    total_trades = len(history)
    winning = [t for t in history if t.get("realized_pnl", 0) > 0]
    win_rate = (len(winning) / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum(t.get("realized_pnl", 0) for t in history)

    # Quick stats row
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Closed Trades", total_trades)
    with c2: st.metric("Win Rate", f"{win_rate:.1f}%")
    with c3: st.metric("Total Realized PnL", f"${total_pnl:,.2f}")
    with c4: st.metric("Current Equity", f"${equity:,.2f}")

    st.divider()

    # Custom question
    st.markdown("**Generate a targeted coaching prompt**")
    question = st.text_area(
        "Your question for the coach",
        placeholder="Should I be using higher leverage on low-vol names like AAPL? How do my SL/TP placements look?",
        height=80
    )

    if st.button("🧠 Generate Custom Prompt", use_container_width=True):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            prompt = _build_custom_prompt(sim, history, equity, question)
            st.code(prompt, language="markdown")

    st.divider()

    # One-click comprehensive review
    if st.button("📋 Generate Full Performance + Risk Review Prompt", use_container_width=True):
        prompt = _build_full_review_prompt(sim, history, equity, total_trades, win_rate, total_pnl)
        st.code(prompt, language="markdown")


def _build_custom_prompt(sim, history, equity, question: str) -> str:
    prompt = f"""You are an expert Hyperliquid perps trading coach and risk manager.

**Current Account State**
- Equity: ${equity:,.2f}
- Open Positions: {len(sim.positions)}
- Total Notional Risk: ${sim.get_total_notional():,.0f}

**Trade History Summary**
- Closed Trades: {len(history)}
- Win Rate: {(len([t for t in history if t.get('realized_pnl',0)>0])/len(history)*100):.1f}% if history else 0
- Total Realized PnL: ${sum(t.get('realized_pnl',0) for t in history):,.2f}

**Recent Trades (last 10):**
"""
    for t in history[-10:]:
        note = t.get("note", "")
        lev = t.get("leverage", "?")
        prompt += f"- {t['direction'].upper()} {t['symbol']} @ {lev}x | PnL ${t['realized_pnl']:.2f} {note}\n"

    prompt += f"""
**My Question:**
{question}

Please give honest, specific, and actionable advice. Reference my actual leverage usage, any SL/TP triggers, and risk concentration where relevant.
"""
    return prompt


def _build_full_review_prompt(sim, history, equity, total_trades, win_rate, total_pnl) -> str:
    prompt = f"""You are a professional trading coach who specializes in leveraged perpetual futures (Hyperliquid style).

Please perform a thorough review of my paper trading performance.

**Account Snapshot**
- Current Equity: ${equity:,.2f}
- Open Positions: {len(sim.positions)}

**Performance Stats**
- Closed Trades: {total_trades}
- Win Rate: {win_rate:.1f}%
- Total Realized PnL: ${total_pnl:,.2f}

**Full Trade Log** (most recent first, limit 15):
"""
    for t in reversed(history[-15:]):
        note = t.get("note", "")
        lev = t.get("leverage", "?")
        sltp = ""
        if "stop_loss" in t or "take_profit" in t:
            sltp = f" (SL/TP used)"
        prompt += f"- {t['timestamp']}: {t['direction'].upper()} {t['symbol']} {lev}x | ${t['size_usd']:,.0f} | PnL ${t['realized_pnl']:.2f} {note}{sltp}\n"

    prompt += """
**Please provide a structured report with these sections:**
1. Overall verdict (brutally honest)
2. Key patterns you observe (leverage, holding time, symbol choice, SL/TP usage)
3. Specific recommendations for position sizing and risk management
4. How my use of stops and take-profits is affecting results
5. One concrete rule or drill I should follow for the next 20 trades
6. Any observations about drawdowns or streaks (if data supports it)

Keep feedback constructive but direct. Use concrete numbers from my journal.
"""
    return prompt
