"""Quantity and geometry math with explicit types.

From a contractor quoting platform, where a quote has to be a calculation rather
than an estimate. Each measurement shape is its own frozen dataclass instead of
an untyped tuple, so a wall and a gable cannot be silently interchanged, and the
result of a takeoff is a named record rather than a bare number.

Runnable with no dependencies:

    python3 04_typed_takeoff_geometry.py
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Sequence


@dataclass(frozen=True)
class RectangularWall:
    length_ft: float
    height_ft: float


@dataclass(frozen=True)
class TriangularGable:
    base_ft: float
    height_ft: float


@dataclass(frozen=True)
class RectangularOpening:
    width_ft: float
    height_ft: float


@dataclass(frozen=True)
class VinylSidingTakeoffResult:
    gross_square_feet: float
    net_square_feet: float
    waste_square_feet: float
    total_square_feet: float
    siding_squares: int


def _rectangular_area(length_ft: float, height_ft: float) -> float:
    return length_ft * height_ft


def _triangular_area(base_ft: float, height_ft: float) -> float:
    return 0.5 * base_ft * height_ft


def calculate_vinyl_siding_takeoff(
    walls: Sequence[RectangularWall] | None = None,
    gables: Sequence[TriangularGable] | None = None,
    openings: Sequence[RectangularOpening] | None = None,
    waste_percent: float = 0.10,
) -> VinylSidingTakeoffResult:
    """
    Calculate vinyl siding takeoff in square feet and 100-sq-ft squares.

    Walls are rectangles, gables are triangles, and openings are rectangular
    deductions. Waste is applied after deductions. One siding square equals
    100 square feet, and squares are rounded up to the next whole square.
    """
    if waste_percent < 0:
        raise ValueError("waste_percent must be greater than or equal to 0")

    walls = walls or []
    gables = gables or []
    openings = openings or []

    gross_square_feet = round(
        sum(_rectangular_area(wall.length_ft, wall.height_ft) for wall in walls)
        + sum(_triangular_area(gable.base_ft, gable.height_ft) for gable in gables),
        2,
    )
    opening_square_feet = round(
        sum(_rectangular_area(opening.width_ft, opening.height_ft) for opening in openings),
        2,
    )
    net_square_feet = round(max(gross_square_feet - opening_square_feet, 0), 2)
    waste_square_feet = round(net_square_feet * waste_percent, 2)
    total_square_feet = round(net_square_feet + waste_square_feet, 2)
    siding_squares = ceil(total_square_feet / 100) if total_square_feet > 0 else 0
    return VinylSidingTakeoffResult(
        gross_square_feet=gross_square_feet,
        net_square_feet=net_square_feet,
        waste_square_feet=waste_square_feet,
        total_square_feet=total_square_feet,
        siding_squares=siding_squares,
    )


if __name__ == "__main__":
    result = calculate_vinyl_siding_takeoff(
        walls=[
            RectangularWall(length_ft=40.0, height_ft=9.0),
            RectangularWall(length_ft=28.0, height_ft=9.0),
        ],
        gables=[TriangularGable(base_ft=28.0, height_ft=6.0)],
        openings=[
            RectangularOpening(width_ft=3.0, height_ft=5.0),
            RectangularOpening(width_ft=8.0, height_ft=7.0),
        ],
        waste_percent=0.10,
    )
    for field, value in result.__dict__.items():
        print(f"{field:22s} {value}")
