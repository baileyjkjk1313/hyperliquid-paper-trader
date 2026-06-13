class Account:
    """
    Manages the paper trading account balance, equity, and margin.
    This is the foundation of the trading simulator.
    """

    def __init__(self, starting_balance: float = 10000.0):
        self.starting_balance = starting_balance
        self.balance = starting_balance          # Cash balance
        self.used_margin = 0.0                   # Margin currently in use
        self.realized_pnl = 0.0                  # Total realized profit/loss

    @property
    def equity(self) -> float:
        """Total account value (balance + unrealized PnL + realized PnL)."""
        # For now, unrealized_pnl is 0 because we haven't built positions yet.
        # We'll update this later when we add the Position class.
        return self.balance + self.realized_pnl

    @property
    def available_margin(self) -> float:
        """How much margin is still available to open new positions."""
        return self.equity - self.used_margin

    def update_realized_pnl(self, pnl: float):
        """Add realized profit or loss to the account."""
        self.realized_pnl += pnl
        self.balance += pnl

    def __str__(self):
        return (f"Account Equity: ${self.equity:,.2f} | "
                f"Balance: ${self.balance:,.2f} | "
                f"Used Margin: ${self.used_margin:,.2f} | "
                f"Available: ${self.available_margin:,.2f}")


# Quick test (we can remove this later)
if __name__ == "__main__":
    account = Account(starting_balance=10000)
    print(account)
    account.update_realized_pnl(250)
    print(account)