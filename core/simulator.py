from core.account import Account
from core.position import Position
from core.funding import FundingCalculator
from datetime import datetime

class Simulator:
    """
    Main coordinator for the paper trading simulator.
    Manages the account, positions, funding, and trade history.
    """

    def __init__(self, starting_balance: float = 10000.0):
        self.account = Account(starting_balance=starting_balance)
        self.positions = {}
        self.trade_history = []
        self.funding_calculator = FundingCalculator(funding_rate=0.001)

    def open_position(self, symbol: str, direction: str, entry_price: float, size_usd: float):
        if symbol in self.positions:
            return f"Position in {symbol} already exists."

        position = Position(symbol, direction, entry_price, size_usd)
        self.positions[symbol] = position
        return f"Opened {direction.upper()} {symbol} position"

    def close_position(self, symbol: str, exit_price: float):
        if symbol not in self.positions:
            return f"No open position in {symbol}"

        position = self.positions[symbol]
        position.update_price(exit_price)
        pnl = position.unrealized_pnl()

        trade_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "direction": position.direction,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "size_usd": position.size_usd,
            "realized_pnl": pnl,
        }
        self.trade_history.append(trade_record)

        self.account.update_realized_pnl(pnl)
        del self.positions[symbol]

        return f"Closed {symbol}. Realized PnL: ${pnl:,.2f}"

    def apply_funding(self):
        if not self.positions:
            return "No open positions to apply funding to."

        total_funding = 0
        for symbol, position in list(self.positions.items()):
            is_long = position.direction == "long"
            funding_pnl = self.funding_calculator.calculate_funding(position.size_usd, is_long)
            self.account.update_realized_pnl(funding_pnl)
            total_funding += funding_pnl

        return f"Applied funding. Total funding PnL: ${total_funding:,.2f}"

    def get_account_summary(self):
        return str(self.account)

    def get_positions(self):
        if not self.positions:
            return "No open positions."
        return "\n".join(str(pos) for pos in self.positions.values())

    def get_trade_history(self):
        if not self.trade_history:
            return "No trades yet."
        return self.trade_history