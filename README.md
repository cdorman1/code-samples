# Code samples

Excerpts from production systems I designed, built and operate. They are lightly generalized: vendor
names, hostnames, credentials and environment specifics are removed or replaced with neutral
placeholders, and the surrounding application code is omitted. The systems themselves are private, so
these samples are the parts that stand on their own.

The set is chosen to match the skills the roles I target actually ask for: risk controls, reconciliation,
idempotency, evaluation, observability, model lifecycle, and the reliability work that keeps automated
systems honest.

## What each sample covers

| Skill area | Sample |
| --- | --- |
| Risk controls, fail closed | `samples/01_risk_gate_fails_closed.py` |
| Pre-trade verification, duplicate prevention | `samples/02_order_submission_gate.py` |
| Idempotency, deterministic identity, traceability | `samples/03_idempotent_order_identity.py` |
| Reconciliation, evidence over assumption | `samples/04_reconciliation_never_guesses.py` |
| Evaluation harness, deterministic replay, negative testing | `samples/05_replay_evaluation.py` |
| API integration, typed error handling | `samples/06_vendor_api_client_with_typed_errors.py` |
| Configuration and startup correctness | `samples/07_config_fails_fast.py` |
| Incremental sync, idempotent writes | `samples/08_incremental_activity_sync.py` |
| LLM output constrained to a schema, per field confidence | `samples/09_schema_constrained_llm_extraction.py` |
| Typed domain modelling, quantity and geometry math | `samples/10_typed_takeoff_geometry.py` |
| Pricing, margin, overrides and validation | `samples/11_pricing_margin_and_labor.py` |
| Tests that pin commercial and safety rules | `samples/12_tests_pin_the_rules.py` |
| Service deployment, loopback binding, reverse proxy | `samples/13_deployment_and_routing.md` |

## Where they come from

- **`01` to `05`** come from an automated trading platform I built and operate: risk gates, a durable
  order lifecycle, reconciliation against upstream truth, and a replay harness for evaluating execution.
  Everything sensitive is excluded: no venue or counterparty naming, no balances, no position sizes, no
  risk thresholds, no account identifiers.
- **`06` to `09`** come from services running in production for clients: a communications API service and
  a quoting platform.
- **`10` to `13`** are the modelling, testing and deployment patterns shared across all of it.

## Running them

`10` and `11` are dependency free and run as scripts:

    python3 samples/10_typed_takeoff_geometry.py
    python3 samples/11_pricing_margin_and_labor.py

The rest are excerpts of larger systems, meant to be read: they reference types and helpers defined
elsewhere in their own codebases, and some use small stand-ins so the shape is visible without shipping
private internals.

No credentials, customer records or production configuration appear in this repository.
