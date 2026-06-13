"""
Advanced risk and performance metrics for the paper trading journal.

Computes:
- Maximum drawdown (peak-to-trough)
- Current drawdown from running peak
- Win / loss streaks
- Enhanced profit factor
- Overall stats dict suitable for UI cards

All functions accept the DataFrames produced by Simulator:
- equity_df from get_equity_curve_df()
- trade_df from get_trade_history_df()
"""

from __future__ import annotations
import pandas as pd
from typing import Dict, Any


def calculate_max_drawdown(equity_series: pd.Series) -> float:
    """
    Maximum historical drawdown as percentage (positive number).
    """
    if equity_series.empty:
        return 0.0
    peak = equity_series.cummax()
    drawdown = (peak - equity_series) / peak
    max_dd = drawdown.max()
    return round(float(max_dd) * 100, 2)


def calculate_current_drawdown(equity_series: pd.Series) -> float:
    """
    Drawdown from the highest peak seen so far (current unrealized pain).
    """
    if equity_series.empty:
        return 0.0
    peak = equity_series.cummax().iloc[-1]
    current = equity_series.iloc[-1]
    if peak <= 0:
        return 0.0
    dd = (peak - current) / peak
    return round(float(dd) * 100, 2)


def _extract_pnl_series(trade_df: pd.DataFrame) -> pd.Series:
    if trade_df.empty or "realized_pnl" not in trade_df.columns:
        return pd.Series([], dtype=float)
    return trade_df["realized_pnl"].fillna(0)


def compute_streaks(trade_df: pd.DataFrame) -> Dict[str, int]:
    """
    Longest current and historical win/loss streaks.
    Returns dict with: current_streak, current_type ('win'/'loss'/'flat'), max_win_streak, max_loss_streak
    """
    pnls = _extract_pnl_series(trade_df)
    if pnls.empty:
        return {"current_streak": 0, "current_type": "flat", "max_win_streak": 0, "max_loss_streak": 0}

    current_streak = 0
    current_type = "flat"
    max_win = 0
    max_loss = 0

    streak = 0
    last_was_win = None

    for pnl in pnls:
        is_win = pnl > 0
        is_loss = pnl < 0

        if is_win:
            if last_was_win is True:
                streak += 1
            else:
                streak = 1
            last_was_win = True
            max_win = max(max_win, streak)
        elif is_loss:
            if last_was_win is False:
                streak += 1
            else:
                streak = 1
            last_was_win = False
            max_loss = max(max_loss, streak)
        else:
            # breakeven trade resets?
            streak = 0
            last_was_win = None

    # Current streak is the final run
    current_streak = streak if last_was_win is not None else 0
    current_type = "win" if last_was_win is True else ("loss" if last_was_win is False else "flat")

    return {
        "current_streak": int(current_streak),
        "current_type": current_type,
        "max_win_streak": int(max_win),
        "max_loss_streak": int(max_loss),
    }


def compute_profit_factor(trade_df: pd.DataFrame) -> float:
    """
    Gross profit / gross loss. Classic risk metric.
    > 1.0 is good. Returns inf or large number if no losing trades.
    """
    pnls = _extract_pnl_series(trade_df)
    if pnls.empty:
        return 0.0

    gross_profit = pnls[pnls > 0].sum()
    gross_loss = abs(pnls[pnls < 0].sum())

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return round(gross_profit / gross_loss, 2)


def get_full_risk_stats(equity_df: pd.DataFrame, trade_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Bundle of advanced metrics for display in Dashboard.
    Safe to call even with empty data.
    """
    if "equity" not in equity_df.columns:
        equity_series = pd.Series([], dtype=float)
    else:
        equity_series = equity_df["equity"].astype(float)

    stats: Dict[str, Any] = {
        "max_drawdown_pct": calculate_max_drawdown(equity_series),
        "current_drawdown_pct": calculate_current_drawdown(equity_series),
        "profit_factor": compute_profit_factor(trade_df),
    }

    streaks = compute_streaks(trade_df)
    stats.update(streaks)

    # Bonus simple expectancy (average pnl per trade, already in UI but useful here)
    if not trade_df.empty and "realized_pnl" in trade_df.columns:
        pnls = trade_df["realized_pnl"].fillna(0)
        stats["expectancy"] = round(float(pnls.mean()), 2)
        stats["total_trades"] = int(len(pnls))
    else:
        stats["expectancy"] = 0.0
        stats["total_trades"] = 0

    return stats
