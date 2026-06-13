class Account:
    """
    Manages the paper trading account (USDC-style collateral for Hyperliquid perps).

    Important distinctions for leveraged perps paper trading:
    - balance: Cash / free collateral after all realized PnL and funding payments.
    - used_margin: Total initial margin currently locked in open positions.
    - realized_pnl: Cumulative closed PnL + funding (already added to balance).
    - Equity (total account value) = balance + sum(unrealized_pnl of open positions)
    - available_margin = equity - used_margin  (what you can use to open new or add to positions)
    """

    def __init__(self, starting_balance: float = 10000.0):
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.used_margin = 0.0
        self.realized_pnl = 0.0

    def get_equity(self, total_unrealized_pnl: float = 0.0) -> float:
        """
        Total account equity = cash balance + current unrealized PnL across all positions.
        This must be called by Simulator with the sum of open positions' unrealized.
        """
        return self.balance + total_unrealized_pnl

    @property
    def equity(self) -> float:
        """
        Fallback equity (assumes zero unrealized).
        Prefer using get_equity(total_unrealized) from Simulator for accuracy.
        """
        return self.balance + self.realized_pnl

    def get_available_margin(self, total_unrealized_pnl: float = 0.0) -> float:
        """Available margin = current equity - margin already committed to positions."""
        equity = self.get_equity(total_unrealized_pnl)
        return max(0.0, equity - self.used_margin)

    def add_used_margin(self, amount: float):
        """Lock margin when opening a new position."""
        self.used_margin += max(0.0, amount)

    def release_used_margin(self, amount: float):
        """Release margin when a position is closed (or reduced)."""
        self.used_margin = max(0.0, self.used_margin - max(0.0, amount))

    def update_realized_pnl(self, pnl: float):
        """
        Add closed PnL or funding payment.
        This directly increases/decreases your cash balance.
        """
        self.realized_pnl += pnl
        self.balance += pnl

    def reset(self, starting_balance: float = None):
        """Reset the account to starting state (useful for new paper trading sessions)."""
        if starting_balance is None:
            starting_balance = self.starting_balance
        self.balance = starting_balance
        self.used_margin = 0.0
        self.realized_pnl = 0.0

    def __str__(self):
        return (f"Balance: ${self.balance:,.2f} | "
                f"Realized PnL: ${self.realized_pnl:,.2f} | "
                f"Used Margin: ${self.used_margin:,.2f}")


# Quick manual test
if __name__ == "__main__":
    account = Account(starting_balance=10000)
    print("Start:", account)
    account.update_realized_pnl(250)
    print("After +250 realized:", account)