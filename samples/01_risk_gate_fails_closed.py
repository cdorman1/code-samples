"""Pre-trade risk controls that fail closed.

From a production automated trading platform. A strategy may only trade where an
explicit policy permits it, on the instruments that policy allows, and only while
every downstream gate reports green. A missing policy, a disallowed symbol, or an
unexpected order action raises. There is no default that quietly allows trading.

The design rule is that the absence of a permission is a refusal, not a licence.
"""

from typing import Mapping


class ProposedOrder:
    """Stand-in for the platform's order dataclass."""


class StrategyControlPolicy:
    """Stand-in for the platform's per-strategy policy record."""

    trading_allowed: bool
    order_action: str
    universe: frozenset[str]


PAPER_ORDER_ACTION = "paper_orders_allowed_after_all_gates_green"


def _symbol_in_universe(symbol: str, universe: frozenset[str]) -> bool:
    """Match a symbol against the policy universe, including aliases."""
    return symbol in universe


def require_order_allowed_by_strategy_policy(
    order: ProposedOrder,
    policies: Mapping[str, StrategyControlPolicy],
) -> StrategyControlPolicy:
    """Fail closed unless the policy explicitly permits orders for this symbol."""
    policy = policies.get(order.strategy_id)
    if policy is None:
        raise RuntimeError(f"strategy_policy_missing: strategy={order.strategy_id!r}")
    if not policy.trading_allowed:
        raise RuntimeError(f"strategy_trading_not_allowed: strategy={order.strategy_id!r}")
    if policy.order_action != PAPER_ORDER_ACTION:
        raise RuntimeError(
            f"strategy_order_action_not_allowed: strategy={order.strategy_id!r} "
            f"order_action={policy.order_action!r}"
        )
    if policy.universe and not _symbol_in_universe(order.symbol, policy.universe):
        raise RuntimeError(
            f"strategy_policy_symbol_not_allowed: strategy={order.strategy_id!r} symbol={order.symbol!r}"
        )
    return policy
