"""Type aliases and data structures for working with coding challenges."""

from pathlib import Path
from typing import Any

from gahllenges.schemas import StrictModel


class Input(StrictModel):
    """Puzzle input."""

    value: Any
    path: Path
    parse_function: str | None = None
    duration: float = 0.0


class Result(StrictModel):
    """Result after solving a puzzle."""

    name: str
    value: int | str | None
    puzzle_dir: Path
    input: Input
    duration: float
