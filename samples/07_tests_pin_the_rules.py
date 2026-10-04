"""Tests that pin commercial rules and their boundaries.

From the same quoting platform. These are not coverage-for-its-own-sake tests:
each one pins a rule that either protects margin or protects the customer, and
names the boundary condition explicitly.
"""

import pytest

from src.pricing_engine import (
    RectangularOpening,
    RectangularWall,
    TriangularGable,
    calculate_customer_price,
    calculate_labor_cost,
    calculate_material_cost,
    calculate_vinyl_siding_takeoff,
)


def test_calculate_material_cost_applies_waste_factor():
    assert calculate_material_cost(10, 100, 0.10) == 1100


def test_calculate_labor_cost_applies_complexity_and_minimum():
    result = calculate_labor_cost(5, 100, 1.25, minimum_charge=700)
    assert result["calculated_cost"] == 625
    assert result["final_cost"] == 700
    assert result["minimum_charge_applied"] is True
    assert result["manual_override_applied"] is False


def test_calculate_labor_cost_manual_override_beats_the_minimum():
    result = calculate_labor_cost(10, 100, 1.25, minimum_charge=700, manual_override_cost=800)
    assert result["calculated_cost"] == 1250
    assert result["final_cost"] == 800
    assert result["minimum_charge_applied"] is False
    assert result["manual_override_applied"] is True


def test_calculate_customer_price_rejects_an_impossible_margin():
    with pytest.raises(ValueError):
        calculate_customer_price(1000, 1.0)
    with pytest.raises(ValueError):
        calculate_customer_price(1000, -0.1)


def test_takeoff_deducts_openings_then_applies_waste():
    result = calculate_vinyl_siding_takeoff(
        walls=[RectangularWall(length_ft=40.0, height_ft=9.0)],
        gables=[TriangularGable(base_ft=28.0, height_ft=6.0)],
        openings=[RectangularOpening(width_ft=3.0, height_ft=5.0)],
        waste_percent=0.10,
    )
    assert result.gross_square_feet == 444.0
    assert result.net_square_feet == 429.0
    assert result.waste_square_feet == 42.9
    assert result.total_square_feet == 471.9
    assert result.siding_squares == 5


def test_takeoff_never_returns_a_negative_net_area():
    result = calculate_vinyl_siding_takeoff(
        walls=[RectangularWall(length_ft=2.0, height_ft=2.0)],
        openings=[RectangularOpening(width_ft=10.0, height_ft=10.0)],
    )
    assert result.net_square_feet == 0
    assert result.siding_squares == 0
