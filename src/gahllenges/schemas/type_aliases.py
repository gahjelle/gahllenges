"""Type aliases and data structures for working with coding challenges."""

from pathlib import Path
from typing import Any, Literal

from gahllenges.schemas import StrictModel

type LanguageName = Literal["elixir", "gleam", "julia", "python", "rust"]


class Input(StrictModel):
    """Puzzle input."""

    value: Any
    path: Path
    parse_function: str | None = None
    duration: float = 0.0


class Result(StrictModel):
    """Result after solving a puzzle."""

    name: str
    puzzle_dir: Path
    code: Path
    input: Input
    value: int | str | None
    duration: float


type ResultSet = dict[tuple[int, int], dict[str, Result]]
