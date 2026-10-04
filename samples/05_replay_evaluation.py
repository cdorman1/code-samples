"""Evaluation by deterministic replay, not by opinion.

From the same trading platform. Execution behaviour is evaluated against a scripted
market and a fake broker, so a change can be re-run and compared rather than argued
about. The harness also pins the negative cases, which is where the value is: a
quote older than policy allows must block, and nothing may reach the broker.

The equivalent of a model evaluation harness for an execution path.
"""

from datetime import datetime, timezone
from typing import Any


class TargetExecutionState:
    TARGET_REACHED = "TARGET_REACHED"
    BLOCKED = "BLOCKED"


class QuoteSnapshot:
    def __init__(self, *, bid: float, ask: float, last: float, timestamp: datetime, minimum_tick: float) -> None:
        self.bid = bid
        self.ask = ask
        self.last = last
        self.timestamp = timestamp
        self.minimum_tick = minimum_tick


class ReplayBroker:
    """Fake broker that records what it was asked to do and nothing else."""

    def __init__(self, *, starting_position: float = 0.0) -> None:
        self.position = starting_position
        self.submitted: list[Any] = []


def test_stale_quote_blocks_submission_and_sends_nothing(executor_factory) -> None:
    broker = ReplayBroker(starting_position=0.0)
    executor = executor_factory(broker=broker)

    # A quote far older than the price policy allows.
    executor.get_quote = lambda target: QuoteSnapshot(
        bid=499.99, ask=500.01, last=500.0, minimum_tick=0.01,
        timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )

    result = executor.execute(target_with(target_quantity=1.0))

    assert result.execution_state == TargetExecutionState.BLOCKED
    assert result.completion_reason == "PRICE_POLICY_REJECTED: STALE_QUOTE"
    assert broker.submitted == []          # nothing reached the broker
    assert broker.position == 0.0


def test_replay_reaches_a_long_flat_short_sequence(executor_factory) -> None:
    """The other half: the happy path, asserted as an exact sequence of orders."""
    broker = ReplayBroker(starting_position=0.0)
    executor = executor_factory(broker=broker)

    for target in (long_target(3.0), flat_target(), short_target(2.0)):
        assert executor.execute(target).execution_state == TargetExecutionState.TARGET_REACHED

    assert [(order.side, order.quantity) for order in broker.submitted] == [
        ("BUY", 3.0),
        ("SELL", 3.0),
        ("SELL", 2.0),
    ]
    assert broker.position == -2.0
