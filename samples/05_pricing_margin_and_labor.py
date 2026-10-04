"""Cost to customer price, with the commercial rules made explicit.

From a contractor quoting platform. Three rules that a spreadsheet tends to hide
are modelled directly: a minimum charge for a job, an operator's manual override
that beats the calculation, and a target margin that is validated rather than
trusted.

Runnable with no dependencies:

    python3 05_pricing_margin_and_labor.py
"""

from __future__ import annotations


def calculate_material_cost(quantity: float, unit_cost: float, waste_factor: float) -> float:
    return round(quantity * unit_cost * (1 + waste_factor), 2)


def _labor_result(
    calculated_cost: float,
    minimum_charge: float = 0,
    manual_override_cost: float | None = None,
) -> dict:
    """Apply the override and minimum rules, and say which one applied."""
    manual_override_applied = manual_override_cost is not None
    minimum_charge_applied = not manual_override_applied and calculated_cost < minimum_charge

    if manual_override_applied:
        final_cost = manual_override_cost
    elif minimum_charge_applied:
        final_cost = minimum_charge
    else:
        final_cost = calculated_cost

    return {
        "calculated_cost": round(calculated_cost, 2),
        "final_cost": round(final_cost, 2),
        "minimum_charge_applied": minimum_charge_applied,
        "manual_override_applied": manual_override_applied,
    }


def calculate_labor_cost(
    quantity: float,
    labor_unit_cost: float,
    complexity_multiplier: float,
    minimum_charge: float = 0,
    manual_override_cost: float | None = None,
) -> dict:
    calculated_cost = quantity * labor_unit_cost * complexity_multiplier
    return _labor_result(calculated_cost, minimum_charge, manual_override_cost)


def calculate_customer_price(total_cost: float, target_margin: float) -> float:
    if target_margin < 0 or target_margin >= 1:
        raise ValueError("target_margin must be greater than or equal to 0 and less than 1")
    return round(total_cost / (1 - target_margin), 2)


def calculate_quote_totals(
    material_lines: list[dict],
    labor_lines: list[dict],
    permit_cost: float,
    overhead_cost: float,
    target_margin: float,
    tax_rate: float,
) -> dict:
    material_cost = round(sum(line["line_cost"] for line in material_lines), 2)
    labor_cost = round(sum(line["final_cost"] for line in labor_lines), 2)

    subtotal_cost = material_cost + labor_cost + permit_cost + overhead_cost
    tax_amount = round(subtotal_cost * tax_rate, 2)
    total_cost = round(subtotal_cost + tax_amount, 2)

    return {
        "material_cost": material_cost,
        "labor_cost": labor_cost,
        "tax_amount": tax_amount,
        "total_cost": total_cost,
        "customer_price": calculate_customer_price(total_cost, target_margin),
    }


if __name__ == "__main__":
    siding = calculate_material_cost(quantity=49.28, unit_cost=112.50, waste_factor=0.10)
    install = calculate_labor_cost(
        quantity=49.28,
        labor_unit_cost=95.00,
        complexity_multiplier=1.25,
        minimum_charge=700,
    )
    totals = calculate_quote_totals(
        material_lines=[{"line_cost": siding}],
        labor_lines=[install],
        permit_cost=0.0,
        overhead_cost=250.0,
        target_margin=0.28,
        tax_rate=0.0,
    )

    print(f"material cost            {siding}")
    print(f"labor calculated cost    {install['calculated_cost']}")
    print(f"labor final cost         {install['final_cost']}")
    print(f"minimum charge applied   {install['minimum_charge_applied']}")
    print(f"total cost               {totals['total_cost']}")
    print(f"customer price at 28%    {totals['customer_price']}")
