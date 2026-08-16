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


class User:
    _id: int
    _name: str
    _display_name: str
    _display_avatar: str
    _mention: str
    _is_bot: bool
    _emoji: str

    def __init__(
        self,
        id: int,
        name: str,
        display_name: str,
        display_avatar: str,
        mention: str,
        is_bot: bool,
        emoji: str = "",
    ) -> None:
        self._id = id
        self._name = name
        self._display_name = display_name
        self._display_avatar = display_avatar
        self._mention = mention
        self._is_bot = is_bot
        self._emoji = emoji

    def __str__(self) -> str:
        return f"{self._name} ({self._id})"

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def display_avatar(self) -> str:
        return self._display_avatar

    @property
    def mention(self) -> str:
        return self._mention

    @property
    def is_bot(self) -> bool:
        return self._is_bot

    @property
    def emoji(self) -> str:
        return self._emoji
