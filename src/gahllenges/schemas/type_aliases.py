"""Type aliases and data structures for working with coding challenges."""

from pathlib import Path

from gahllenges.schemas import StrictModel


class Input[ValueT](StrictModel):
    value: ValueT
    path: Path
    parse_function: str | None = None
    duration: float = 0.0


class Result(StrictModel):
    name: str
    value: int | str | None
    puzzle_dir: Path
    input: Input
    duration: float
