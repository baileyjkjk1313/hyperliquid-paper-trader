"""
Mock market data for the paper trading simulator.
Provides realistic starting prices and typical per-tick volatilities
for common symbols (crypto + equities) to make random walk simulation feel natural.
"""

# Base prices and approximate per-tick volatility (for random walk simulation)
# Volatility here is rough std dev of returns per "tick" / simulation step.
# Higher for individual stocks, lower for major crypto or indices.
SYMBOL_DEFAULTS = {
    "BTC":  {"price": 65000.0, "vol": 0.012},
    "ETH":  {"price": 2500.0,  "vol": 0.018},
    "SOL":  {"price": 140.0,   "vol": 0.025},
    "NVDA": {"price": 120.0,   "vol": 0.028},
    "AAPL": {"price": 195.0,   "vol": 0.012},
    "TSLA": {"price": 280.0,   "vol": 0.035},
    "MSFT": {"price": 420.0,   "vol": 0.011},
    "META": {"price": 510.0,   "vol": 0.022},
    "AMD":  {"price": 155.0,   "vol": 0.032},
    "SPY":  {"price": 580.0,   "vol": 0.007},
}

DEFAULT_VOL = 0.02
DEFAULT_PRICE = 100.0

def get_default_price(symbol: str) -> float:
    """Return a sensible starting/entry price for a symbol (case-insensitive)."""
    sym = symbol.upper().strip()
    return SYMBOL_DEFAULTS.get(sym, {}).get("price", DEFAULT_PRICE)

def get_volatility(symbol: str, default: float = DEFAULT_VOL) -> float:
    """Return typical simulation volatility for the symbol."""
    sym = symbol.upper().strip()
    return SYMBOL_DEFAULTS.get(sym, {}).get("vol", default)

def get_all_symbols() -> list[str]:
    return list(SYMBOL_DEFAULTS.keys())

def suggest_price_for_symbol(symbol: str) -> float:
    """Convenience for UI autofill."""
    return get_default_price(symbol)
