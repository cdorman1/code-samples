"""Reconciliation that refuses to guess.

From the same trading platform. On startup and on demand, every local order that
has not reached a terminal state is matched against what the broker actually
reports. A local order with no counterpart upstream is recorded as UNKNOWN rather
than assumed filled, assumed dead or quietly dropped.

Those unmatched rows are where real money is lost, so they are surfaced loudly and
left for a human rather than resolved by inference.
"""

from typing import Any


class DurableOrderManager:
    """Sketch of the shape the real manager exposes."""

    def nonterminal_orders(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _broker_open_orders(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _mark_unknown(self, operation_id: str, reason: str) -> None:
        raise NotImplementedError

    def process_broker_callback(self, operation_id: str, match: dict[str, Any]) -> None:
        raise NotImplementedError


def _match_operation(
    candidates: list[dict[str, Any]], operation_id: str, order_ref: str | None
) -> dict[str, Any] | None:
    for row in candidates:
        if row.get("client_operation_id") == operation_id:
            return row
        if order_ref and row.get("order_ref") == order_ref:
            return row
    return None


def startup_reconcile(manager: DurableOrderManager) -> list[dict[str, Any]]:
    """Never assume: match every nonterminal order against broker truth."""
    broker_orders = list(manager._broker_open_orders())
    broker_events = list(manager.broker_lifecycle_events())
    results: list[dict[str, Any]] = []

    for row in manager.nonterminal_orders():
        operation_id = str(row["client_operation_id"])
        match = _match_operation(broker_orders, operation_id, row.get("order_ref"))
        if match is None:
            match = _match_operation(broker_events, operation_id, row.get("order_ref"))

        if match is None:
            # Absence of evidence is not evidence: record UNKNOWN and stop.
            manager._mark_unknown(
                operation_id, f"nonterminal order missing from broker visibility; prior_state={row['state']}"
            )
            results.append({"client_operation_id": operation_id, "state": "UNKNOWN", "matched": False})
            continue

        manager.process_broker_callback(operation_id, match)
        results.append({"client_operation_id": operation_id, "state": "reconciled", "matched": True})

    return results
