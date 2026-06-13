class Position:
    """
    Represents a single open position (Long or Short) in the paper trading simulator.
    This class tracks entry details and calculates unrealized PnL.
    """

    def __init__(self, symbol: str, direction: str, entry_price: float, size_usd: float):
        """
        Initialize a new position.
        
        Args:
            symbol: The asset being traded (e.g. 'NVDA', 'TSLA')
            direction: Either 'long' or 'short'
            entry_price: Price at which the position was opened
            size_usd: Position size in USD value
        """
        self.symbol = symbol.upper()
        self.direction = direction.lower()  # 'long' or 'short'
        self.entry_price = entry_price
        self.size_usd = size_usd
        self.current_price = entry_price  # Will be updated later

    def update_price(self, new_price: float):
        """Update the current market price of the asset."""
        self.current_price = new_price

    def unrealized_pnl(self) -> float:
        """
        Calculate unrealized profit or loss based on current price.
        """
        if self.direction == "long":
            pnl = (self.current_price - self.entry_price) / self.entry_price * self.size_usd
        else:  # short
            pnl = (self.entry_price - self.current_price) / self.entry_price * self.size_usd
        
        return round(pnl, 2)

    def __str__(self):
        return (f"{self.direction.upper()} {self.symbol} | "
                f"Entry: ${self.entry_price:,.2f} | "
                f"Current: ${self.current_price:,.2f} | "
                f"Unrealized PnL: ${self.unrealized_pnl():,.2f}")


# Quick test (we can remove this later)
if __name__ == "__main__":
    # Example: Long $2000 of NVDA at $120
    pos = Position(symbol="NVDA", direction="long", entry_price=120, size_usd=2000)
    print(pos)
    
    # Simulate price moving up to $125
    pos.update_price(125)
    print(pos)