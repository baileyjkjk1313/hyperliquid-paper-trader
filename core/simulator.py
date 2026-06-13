from core.account import Account
from core.position import Position
from core.funding import FundingCalculator
from datetime import datetime
import pandas as pd

class Simulator:
    """
    Central paper trading engine for "Jon's Hyperliquid Trading App".

    Responsibilities:
    - Open/close leveraged perps positions with proper margin accounting
    - Track total equity (balance + unrealized) in real time
    - Record equity curve snapshots for performance visualization
    - Apply periodic funding payments (Hyperliquid-style)
    - Provide rich data for the Streamlit UI (positions, history, curves)
    """

    def __init__(self, starting_balance: float = 10000.0):
        self.account = Account(starting_balance=starting_balance)
        self.positions: dict[str, Position] = {}
        self.trade_history: list[dict] = []
        self.equity_history: list[dict] = []          # For the equity curve chart
        self.funding_calculator = FundingCalculator(funding_rate=0.0001)  # ~0.01% per period (realistic-ish)

        # Initial snapshot
        self._snapshot_equity("start")

    # ------------------------------
    # CORE TRADING OPERATIONS
    # ------------------------------

    def open_position(self, symbol: str, direction: str, entry_price: float, size_usd: float,
                      leverage: int = 10, stop_loss: float | None = None, take_profit: float | None = None):
        """
        Open a new leveraged position after validating margin availability.
        SL/TP are optional paper-trading risk orders that will be checked on price updates.
        """
        symbol = symbol.upper()
        if symbol in self.positions:
            return f"Position in {symbol} already exists. Close it first or use a different symbol."

        if size_usd <= 0 or entry_price <= 0 or leverage < 1:
            return "Invalid parameters: size, price, and leverage must be positive."

        required_margin = size_usd / leverage
        current_unrealized = self._calculate_total_unrealized_pnl()
        available = self.account.get_available_margin(current_unrealized)

        if required_margin > available:
            return (f"Insufficient margin. Need ${required_margin:,.2f} but only "
                    f"${available:,.2f} available at current equity.")

        position = Position(symbol, direction, entry_price, size_usd, leverage=leverage,
                            stop_loss=stop_loss, take_profit=take_profit)
        self.positions[symbol] = position
        self.account.add_used_margin(position.initial_margin)

        self._snapshot_equity("open_position")

        sltp_note = ""
        if stop_loss or take_profit:
            sltp_note = " (with SL/TP)"
        return (f"Opened {direction.upper()} {symbol} | ${size_usd:,.0f} notional @ {leverage}x{sltp_note} | "
                f"Margin posted: ${position.initial_margin:,.2f}")

    def close_position(self, symbol: str, exit_price: float):
        """
        Close an entire position, realize PnL, release margin, and record the trade.
        """
        symbol = symbol.upper()
        if symbol not in self.positions:
            return f"No open position in {symbol}."

        position = self.positions[symbol]
        position.mark_to_market(exit_price)
        realized_pnl = position.unrealized_pnl()

        # Record the trade
        trade_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "direction": position.direction,
            "entry_price": round(position.entry_price, 2),
            "exit_price": round(exit_price, 2),
            "size_usd": position.size_usd,
            "leverage": position.leverage,
            "realized_pnl": round(realized_pnl, 2),
            "margin_used": round(position.initial_margin, 2),
        }
        self.trade_history.append(trade_record)

        # Accounting
        self.account.update_realized_pnl(realized_pnl)
        self.account.release_used_margin(position.initial_margin)

        # Cleanup
        del self.positions[symbol]

        self._snapshot_equity("close_position")

        return f"Closed {symbol}. Realized PnL: ${realized_pnl:,.2f}"

    def update_position_price(self, symbol: str, new_price: float):
        """
        Mark a single position to a new market price. Used for live price simulation.
        Does NOT realize PnL (unrealized only).
        """
        symbol = symbol.upper()
        if symbol not in self.positions:
            return f"No open position for {symbol}."

        self.positions[symbol].mark_to_market(new_price)
        self._snapshot_equity("price_update")
        return f"Marked {symbol} to ${new_price:,.2f}"

    def apply_funding(self, periods: int = 1):
        """
        Apply funding payments across all open positions for one or more periods.
        In real Hyperliquid funding happens every hour.
        """
        if not self.positions:
            return "No open positions to apply funding to."

        total_funding = 0.0
        for position in list(self.positions.values()):
            is_long = position.direction == "long"
            # Funding is applied on notional
            funding_pnl = self.funding_calculator.calculate_funding(position.size_usd, is_long)
            funding_pnl *= periods
            self.account.update_realized_pnl(funding_pnl)
            total_funding += funding_pnl

        self._snapshot_equity("funding")

        sign = "+" if total_funding >= 0 else ""
        return f"Applied funding ({periods} period(s)). Net funding PnL: {sign}${total_funding:,.2f}"

    # ------------------------------
    # PRICE SIMULATION + AUTOMATIC SL/TP EXECUTION (paper trading)
    # ------------------------------

    def update_position_price(self, symbol: str, new_price: float, check_triggers: bool = True):
        """
        Mark a single position to a new market price.
        If check_triggers=True, will automatically close if SL or TP is hit.
        """
        symbol = symbol.upper()
        if symbol not in self.positions:
            return f"No open position for {symbol}."

        self.positions[symbol].mark_to_market(new_price)
        self._snapshot_equity("price_update")

        if check_triggers:
            self._check_and_execute_triggers()

        return f"Marked {symbol} to ${new_price:,.2f}"

    def batch_update_prices(self, price_updates: dict[str, float], check_triggers: bool = True):
        """Bulk mark multiple positions (used heavily by the Market Simulator)."""
        for symbol, price in price_updates.items():
            sym = symbol.upper()
            if sym in self.positions:
                self.positions[sym].mark_to_market(price)

        self._snapshot_equity("batch_price_update")

        if check_triggers:
            self._check_and_execute_triggers()

        return f"Updated prices for {len(price_updates)} symbol(s)"

    def _check_and_execute_triggers(self):
        """
        Internal: scan all positions for breached SL/TP and auto-close them.
        Records a note on the trade for history and AI prompts.
        """
        to_close = []
        for sym, pos in list(self.positions.items()):
            trigger = pos.check_trigger()
            if trigger:
                trigger_price = pos.stop_loss if trigger == "sl" else pos.take_profit
                # Close will realize at the trigger price
                self.close_position(sym, trigger_price)
                # Tag the just-recorded trade
                if self.trade_history:
                    self.trade_history[-1]["note"] = f"auto-{trigger.upper()}"
                to_close.append(f"{sym} ({trigger.upper()})")

        if to_close:
            self._snapshot_equity("sl_tp_trigger")

        return to_close

    def simulate_random_tick(self, volatility: float = 0.02, drift: float = 0.0):
        """
        Convenience high-level method: run one random walk tick across all open positions
        using the price simulator utilities (called from UI).
        """
        if not self.positions:
            return "No positions to simulate."

        from utils.price_simulator import batch_random_walk
        from data.mock_data import get_volatility

        current = {s: p.current_price for s, p in self.positions.items()}
        per_vol = {s: get_volatility(s) for s in self.positions}

        updates = batch_random_walk(current, volatility=volatility, drift=drift, per_symbol_vol=per_vol)
        self.batch_update_prices(updates)
        return f"Random tick applied to {len(updates)} positions"

    # ------------------------------
    # EQUITY & PORTFOLIO STATE
    # ------------------------------

    def _calculate_total_unrealized_pnl(self) -> float:
        """Sum of unrealized PnL across all open positions."""
        return sum(pos.unrealized_pnl() for pos in self.positions.values())

    def get_equity(self) -> float:
        """Current total account equity (cash + unrealized PnL)."""
        return self.account.get_equity(self._calculate_total_unrealized_pnl())

    def get_available_margin(self) -> float:
        return self.account.get_available_margin(self._calculate_total_unrealized_pnl())

    def get_used_margin(self) -> float:
        return self.account.used_margin

    def get_total_notional(self) -> float:
        return sum(p.size_usd for p in self.positions.values())

    def _snapshot_equity(self, event: str = "manual"):
        """Record current equity for charting. Call on meaningful events."""
        self.equity_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "equity": round(self.get_equity(), 2),
            "event": event,
            "positions": len(self.positions),
        })

    def get_equity_curve_df(self) -> pd.DataFrame:
        """Return a DataFrame ready for Plotly / charts. Always has at least the starting point."""
        if not self.equity_history:
            return pd.DataFrame([{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "equity": self.account.starting_balance,
                "event": "start"
            }])
        return pd.DataFrame(self.equity_history)

    # ------------------------------
    # DISPLAY / DATA HELPERS (used by UI)
    # ------------------------------

    def get_account_summary(self) -> str:
        unrealized = self._calculate_total_unrealized_pnl()
        equity = self.get_equity()
        return (f"Equity: ${equity:,.2f} | "
                f"Balance: ${self.account.balance:,.2f} | "
                f"Unrealized: ${unrealized:,.2f} | "
                f"Used Margin: ${self.account.used_margin:,.2f}")

    def get_positions(self):
        """Human readable multi-line string (kept for backward compatibility in UI)."""
        if not self.positions:
            return "No open positions."
        lines = []
        total_unreal = self._calculate_total_unrealized_pnl()
        equity = self.get_equity()
        for pos in self.positions.values():
            risk = pos.risk_pct_of_equity(equity)
            lines.append(
                f"{pos} | Risk: {risk}% of equity | Liq ~${pos.estimated_liquidation_price():,.2f}"
            )
        return "\n".join(lines)

    def get_positions_list(self) -> list[dict]:
        """Structured data for nice dataframe display in UI."""
        if not self.positions:
            return []
        total_equity = self.get_equity()
        return [p.to_dict() | {"risk_pct_equity": p.risk_pct_of_equity(total_equity)} for p in self.positions.values()]

    def get_trade_history(self):
        """Return list of trade dicts or friendly message."""
        if not self.trade_history:
            return "No trades yet."
        return self.trade_history

    def get_trade_history_df(self) -> pd.DataFrame:
        if not self.trade_history:
            return pd.DataFrame()
        df = pd.DataFrame(self.trade_history)
        # Add cumulative PnL for nice charts
        df["cumulative_pnl"] = df["realized_pnl"].cumsum()
        return df

    def reset(self, starting_balance: float = 10000.0):
        """Completely reset the simulator (new paper trading session)."""
        self.account.reset(starting_balance)
        self.positions.clear()
        self.trade_history.clear()
        self.equity_history.clear()
        self._snapshot_equity("reset")
        return f"Simulator reset. Starting balance: ${starting_balance:,.2f}"

    # ------------------------------
    # FUNDING CONFIG (for future)
    # ------------------------------

    def set_funding_rate(self, rate: float):
        """Dynamically change the funding rate (e.g. for testing different regimes)."""
        self.funding_calculator.funding_rate = rate
        return f"Funding rate updated to {rate*100:.4f}% per period"
