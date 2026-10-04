"""Nothing is submitted until everything is verified.

From the same trading platform. Before an order can leave the process it passes a
gate that checks the risk decision, the quantity, the price, the order type, broker
health, the account identity, and whether this operation already exists upstream.
Any failure raises, and the order is not sent.

Duplicate prevention is the point: a resubmission after a network timeout is a
normal event in trading, and it must not become a second position.
"""

from typing import Any


class ReconciliationRequired(RuntimeError):
    """Raised when the platform cannot prove the state of the world is known."""


class SubmissionGate:
    def __init__(self, manager: Any) -> None:
        self.broker = manager.broker_client
        self.find_broker_open_order = manager.find_broker_open_order

    def assert_can_submit(
        self,
        *,
        proposed_order: Any,
        risk_decision: Any,
        client_operation_id: str,
        order_ref: str,
    ) -> None:
        if not risk_decision.approved:
            raise ReconciliationRequired("submission gate requires an approved risk decision")
        if float(risk_decision.approved_quantity) != float(proposed_order.quantity):
            raise ReconciliationRequired("approved quantity must equal proposed quantity")
        if proposed_order.quantity <= 0 or proposed_order.estimated_price <= 0:
            raise ReconciliationRequired("positive quantity and estimated price are required")
        if not proposed_order.symbol or not proposed_order.strategy_id or not proposed_order.signal_id:
            raise ReconciliationRequired("symbol, strategy_id and signal_id are required")
        if proposed_order.order_type.value == "LIMIT" and proposed_order.limit_price is None:
            raise ReconciliationRequired("LIMIT order requires limit_price")
        if not self.broker.is_connected():
            raise ReconciliationRequired("broker connection is unhealthy")

        configured_account = str(proposed_order.account_id or "")
        broker_account = str(getattr(self.broker, "account", "") or "")
        if configured_account and broker_account and configured_account != broker_account:
            raise ReconciliationRequired("broker account mismatch")

        # The duplicate checks that matter: has this operation already been seen?
        if self.find_broker_open_order(client_operation_id, order_ref):
            raise ReconciliationRequired("broker already has an open order for this operation")
