"""Type aliases and data structures for working with coding challenges."""

from pathlib import Path
from typing import Any, Literal, TypeAlias

from gahllenges.schemas import StrictModel

LanguageName: TypeAlias = Literal["elixir", "gleam", "julia", "python", "rust"]


class Input(StrictModel):
    """Puzzle input."""

    value: Any
    path: Path
    parse_function: str | None = None
    duration: float = 0.0


class Result(StrictModel):
    """Result after solving a puzzle."""

    interpreter: str
    name: str
    puzzle_dir: Path
    code: Path
    input: Input
    value: int | str | None
    solved: bool
    duration: float


ResultSet: TypeAlias = dict[tuple[int, int], dict[str, Result]]
