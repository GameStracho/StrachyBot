from enum import Enum
from typing import NamedTuple


class NoAPIResponseError(Exception):
    def __init__(self) -> None:
        super().__init__("No API response received.")


class Position(NamedTuple):
    x: int
    y: int


class Vector(NamedTuple):
    x: int
    y: int


class EDirection(Vector, Enum):
    # Primary directions
    NORTH = Vector(-1, 0)
    SOUTH = Vector(1, 0)
    EAST = Vector(0, 1)
    WEST = Vector(0, -1)

    # Diagonal directions
    NORTH_EAST = Vector(-1, 1)
    NORTH_WEST = Vector(-1, -1)
    SOUTH_EAST = Vector(1, 1)
    SOUTH_WEST = Vector(1, -1)

    @classmethod
    def get_axes(cls) -> list[Vector]:
        """
        Returns pairs of opposing directions to check complete lines passing through a cell.
        (e.g., Horizontal axis = WEST + EAST)
        """
        return [
            (cls.EAST.value),  # Horizontal line (-)
            (cls.SOUTH.value),  # Vertical line (|)
            (cls.SOUTH_EAST.value),  # Main diagonal (\)
            (cls.SOUTH_WEST.value),  # Anti-diagonal (/)
        ]
