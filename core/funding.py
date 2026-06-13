class FundingCalculator:
    """
    Handles funding rate calculations for perpetual positions.
    This is a simplified version for the paper trading simulator.
    """

    def __init__(self, funding_rate: float = 0.0001):
        """
        funding_rate: The funding rate per period (default = 0.01% per hour)
        """
        self.funding_rate = funding_rate

    def calculate_funding(self, position_size_usd: float, is_long: bool) -> float:
        """
        Calculate the funding payment for a position.
        Positive value = you receive funding
        Negative value = you pay funding
        """
        funding_amount = position_size_usd * self.funding_rate

        if is_long:
            # Longs typically pay funding when rate is positive
            return -funding_amount
        else:
            # Shorts typically receive funding when rate is positive
            return funding_amount

    def apply_funding_to_position(self, position, account):
        """
        Apply funding to a position and update the account.
        """
        is_long = position.direction == "long"
        funding_pnl = self.calculate_funding(position.size_usd, is_long)

        # Update the account with funding PnL
        account.update_realized_pnl(funding_pnl)

        return funding_pnl