"""
Price simulation utilities for realistic paper trading practice.

Implements:
- Simple geometric random walk (drift + volatility * gaussian noise)
- Percentage bump helpers
- Batch simulation helpers

Designed to be called from the Simulator and Trade UI tab.
No external dependencies beyond stdlib.
"""

import random
from typing import Dict, List, Optional


def random_walk_tick(
    current_price: float,
    volatility: float = 0.02,
    drift: float = 0.0,
    seed: Optional[int] = None
) -> float:
    """
    Advance price by one 'tick' using a simple geometric Brownian motion approximation.

    Args:
        current_price: Last mark price
        volatility: Std dev of return per tick (e.g. 0.02 = 2%)
        drift: Expected return per tick (small positive or negative)
        seed: Optional random seed for reproducibility in tests

    Returns:
        New price rounded to 2 decimals
    """
    if seed is not None:
        random.seed(seed)

    # Gaussian noise ~ N(0,1)
    noise = random.gauss(0, 1)
    # Relative change
    change = drift + volatility * noise
    new_price = current_price * (1 + change)

    # Guardrails: never go to zero or negative in paper sim
    return max(round(new_price, 2), 0.01)


def apply_percentage_move(current_price: float, pct_change: float) -> float:
    """
    Apply a deterministic percentage move (e.g. +2.5 or -1.8).
    Useful for 'bullish tick' / 'bearish tick' buttons.
    """
    new_price = current_price * (1 + pct_change / 100.0)
    return max(round(new_price, 2), 0.01)


def simulate_multiple_ticks(
    current_price: float,
    n_ticks: int = 5,
    volatility: float = 0.02,
    drift: float = 0.0,
    seed: Optional[int] = None
) -> List[float]:
    """Generate a sequence of n prices starting from current."""
    prices = [current_price]
    price = current_price
    for _ in range(n_ticks):
        price = random_walk_tick(price, volatility, drift, seed)
        prices.append(price)
    return prices[1:]  # return the new prices


def batch_random_walk(
    current_prices: Dict[str, float],
    volatility: float = 0.02,
    drift: float = 0.0,
    per_symbol_vol: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Apply one random walk tick to many symbols at once.
    Optionally pass per-symbol volatility overrides.
    """
    per_symbol_vol = per_symbol_vol or {}
    updates: Dict[str, float] = {}
    for symbol, price in current_prices.items():
        vol = per_symbol_vol.get(symbol, volatility)
        updates[symbol] = random_walk_tick(price, vol, drift)
    return updates
