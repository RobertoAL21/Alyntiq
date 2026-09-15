from typing import Protocol

from app.execution.types import (
    BrokerAccount,
    BrokerOrder,
    BrokerOrderRequest,
    BrokerOrderStatus,
    BrokerPosition,
)


class BrokerInterface(Protocol):
    """Provider-neutral paper-broker operations; strategies and risk do not call a broker."""

    def submit_order(self, order: BrokerOrderRequest) -> BrokerOrder:
        """Submit a validated order after the execution layer has approved it."""

    def cancel_order(self, order_id: str) -> None:
        """Cancel an open broker order by its provider identifier."""

    def get_positions(self) -> tuple[BrokerPosition, ...]:
        """Return the broker's current open positions."""

    def get_account(self) -> BrokerAccount:
        """Return the broker account balances used for paper-trading monitoring."""

    def get_orders(
        self, status: BrokerOrderStatus = BrokerOrderStatus.ALL, limit: int = 100
    ) -> tuple[BrokerOrder, ...]:
        """Return provider orders matching a bounded status query."""
