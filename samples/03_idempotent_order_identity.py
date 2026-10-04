"""Every order has a deterministic identity.

From the same trading platform. The operation identifier is derived from the
economics of the order rather than from a random value or a timestamp, so sending
the same intent twice resolves to the same record instead of a second order.

Retries become idempotent by construction, and every fill can be traced back to
the signal and the risk decision that produced it.
"""

import hashlib
import json
from typing import Any


def content_id(namespace: str, payload: dict) -> str:
    """Stable content-addressed identity: same payload, same id, every time."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    return f"{namespace}:{digest}"


def client_operation_id_for(proposed_order: Any, risk_decision: Any) -> str:
    payload = {
        "account": proposed_order.account_id,
        "strategy_id": proposed_order.strategy_id,
        "signal_id": proposed_order.signal_id,
        "symbol": proposed_order.symbol,
        "side": proposed_order.side.value,
        "quantity": float(risk_decision.approved_quantity),
        "order_type": proposed_order.order_type.value,
        "limit_price": proposed_order.limit_price,
        "security_type": proposed_order.security_type,
        "exchange": proposed_order.exchange,
        "contract_month": proposed_order.last_trade_date_or_contract_month,
    }
    return content_id("pg", payload)
