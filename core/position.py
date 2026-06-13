class Position:
    """
    Represents a single open perpetual futures position (Long or Short).
    Designed for Hyperliquid-style paper trading with leverage support.

    Key Hyperliquid concepts modeled:
    - size_usd = notional value of the position
    - leverage = user-selected leverage (affects margin requirement)
    - initial_margin = collateral posted to open the position (size_usd / leverage)
    - Unrealized PnL is marked-to-market
    - Estimated liquidation price (simplified model)
    """

    def __init__(self, symbol: str, direction: str, entry_price: float, size_usd: float, leverage: int = 10,
                 stop_loss: float | None = None, take_profit: float | None = None):
        """
        Initialize a new leveraged position.

        Args:
            symbol: Trading pair (e.g. 'BTC', 'NVDA', 'ETH')
            direction: 'long' or 'short'
            entry_price: Entry mark price
            size_usd: Notional position size in USD (value of the position)
            leverage: Chosen leverage multiplier (1-50x typical for perps)
            stop_loss: Optional price at which to auto-close (paper simulation)
            take_profit: Optional price at which to auto-close for profit
        """
        self.symbol = symbol.upper()
        self.direction = direction.lower()
        self.entry_price = float(entry_price)
        self.size_usd = float(size_usd)
        self.leverage = int(leverage)
        self.current_price = self.entry_price

        # Margin & risk
        self.initial_margin = self.size_usd / self.leverage if self.leverage > 0 else self.size_usd

        # Risk orders (paper trading only)
        self.stop_loss = float(stop_loss) if stop_loss is not None else None
        self.take_profit = float(take_profit) if take_profit is not None else None

    def mark_to_market(self, new_price: float):
        """Update current price (mark-to-market). Called when user simulates price moves."""
        self.current_price = float(new_price)

    def set_sl_tp(self, stop_loss: float | None = None, take_profit: float | None = None):
        """Update or clear SL/TP levels after the position is open."""
        if stop_loss is not None:
            self.stop_loss = float(stop_loss)
        if take_profit is not None:
            self.take_profit = float(take_profit)

    def check_trigger(self, price: float | None = None) -> str | None:
        """
        Return 'sl' or 'tp' if the given (or current) price has breached the order.
        Longs: SL below entry, TP above entry.
        Shorts: SL above entry, TP below entry.
        """
        p = price if price is not None else self.current_price
        if p is None:
            return None

        if self.stop_loss is not None:
            if self.direction == "long" and p <= self.stop_loss:
                return "sl"
            if self.direction == "short" and p >= self.stop_loss:
                return "sl"

        if self.take_profit is not None:
            if self.direction == "long" and p >= self.take_profit:
                return "tp"
            if self.direction == "short" and p <= self.take_profit:
                return "tp"

        return None

    def unrealized_pnl(self) -> float:
        """
        Return current unrealized PnL in USD.
        Formula for linear perps: PnL = direction * (exit - entry) / entry * notional
        """
        if self.direction == "long":
            pnl = (self.current_price - self.entry_price) / self.entry_price * self.size_usd
        else:
            pnl = (self.entry_price - self.current_price) / self.entry_price * self.size_usd
        return round(pnl, 2)

    def unrealized_pnl_pct(self) -> float:
        """Unrealized PnL as percentage of notional size."""
        if self.size_usd == 0:
            return 0.0
        return round((self.unrealized_pnl() / self.size_usd) * 100, 2)

    def maintenance_margin_rate(self) -> float:
        """Simplified maintenance margin (typical 0.5% or 0.005 for many perps)."""
        return 0.005

    def estimated_liquidation_price(self) -> float:
        """
        Very simplified liquidation price estimate.
        Real Hyperliquid uses more sophisticated formula with funding + fees.
        Approx: Longs get liquidated when loss ≈ initial_margin * 0.9 (buffer)
        """
        mm = self.maintenance_margin_rate()
        buffer = 0.1  # safety buffer
        effective_loss_pct = (self.initial_margin / self.size_usd) * (1 - buffer)

        if self.direction == "long":
            liq_price = self.entry_price * (1 - effective_loss_pct)
        else:
            liq_price = self.entry_price * (1 + effective_loss_pct)

        return round(max(liq_price, 0.01), 2)

    def margin_used(self) -> float:
        """Current margin posted for this position (initial for now; could be dynamic)."""
        return self.initial_margin

    def notional_value(self) -> float:
        return self.size_usd

    def risk_pct_of_equity(self, total_equity: float) -> float:
        """What % of total account equity is this position's notional."""
        if total_equity <= 0:
            return 0.0
        return round((self.size_usd / total_equity) * 100, 1)

    def __str__(self):
        pnl = self.unrealized_pnl()
        pnl_pct = self.unrealized_pnl_pct()
        extra = ""
        if self.stop_loss:
            extra += f" | SL ${self.stop_loss:,.2f}"
        if self.take_profit:
            extra += f" | TP ${self.take_profit:,.2f}"
        return (f"{self.direction.upper()} {self.symbol} @ {self.leverage}x | "
                f"Entry ${self.entry_price:,.2f} | Current ${self.current_price:,.2f} | "
                f"Unrealized: ${pnl:,.2f} ({pnl_pct:+.1f}%){extra}")

    def to_dict(self):
        """For serialization / dataframe use (includes SL/TP when set)."""
        d = {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "size_usd": self.size_usd,
            "leverage": self.leverage,
            "initial_margin": round(self.initial_margin, 2),
            "unrealized_pnl": self.unrealized_pnl(),
            "unrealized_pnl_pct": self.unrealized_pnl_pct(),
            "est_liquidation_price": self.estimated_liquidation_price(),
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }
        # Clean None values for UI
        return {k: v for k, v in d.items() if v is not None}


# Quick manual test (run this file directly)
if __name__ == "__main__":
    pos = Position("NVDA", "long", 120, 2000, leverage=10, stop_loss=112, take_profit=135)
    print("Initial:", pos)
    print("Check trigger at 110 (should SL):", pos.check_trigger(110))
    pos.mark_to_market(125)
    print("At 125:", pos)
    print("Check at 125 (should TP):", pos.check_trigger(125))
    print("Est. liq:", pos.estimated_liquidation_price())