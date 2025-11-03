"""Handle expected results."""

import tomllib
from pathlib import Path

from rich.console import Console

from gahllenges.schemas import type_aliases as t

stdout = Console()


def validate(
    results: list[t.Result], *, example: bool = False, overwrite: bool = False
) -> None:
    """Get the expected results for one challenge."""
    if not results:
        return

    toml_name = f"expected{'_example' if example else ''}.toml"
    puzzle_dir = results[0].puzzle_dir
    expectations_path = puzzle_dir / toml_name

    if not expectations_path.exists() or overwrite:
        write_expectations(expectations_path, results)
        return

    expected = tomllib.loads(expectations_path.read_text(encoding="utf-8"))
    for result in results:
        section = f"{result.name}-{result.input.path.stem}"
        expected_value = expected.get(section, {"value": None})["value"]
        if result.value is not None and result.value != expected_value:
            stdout.print(
                f"[blue]{result.value!r}[/] != [blue]{expected_value!r}[/] for"
                f" {result.name}. Use [yellow]--overwrite[/] or [yellow]-o[/] "
                "to overwrite the expected value.",
                style="red",
                highlight=False,
            )


def write_expectations(expectations_path: Path, results: list[t.Result]) -> None:
    """Update the expected results on disk."""
    output: list[str] = []
    for result in results:
        output.extend(
            [
                f"[{result.name}-{result.input.path.stem}]",
                f"input_path = {toml_dumps(result.input.path.name)}",
                f"value = {toml_dumps(result.value)}",
                f"duration = {toml_dumps(result.duration)}",
                (
                    f"parse_duration = {toml_dumps(result.input.duration)}\n"
                    if result.input.parse_function
                    else ""
                ),
            ]
        )
    expectations_path.write_text("\n".join(output), encoding="utf-8")


def toml_dumps(value: str | int | float | None) -> str:  # noqa: PYI041
    """Write a simple value as a TOML value."""
    # sourcery skip: assign-if-exp, reintroduce-else
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, int):
        return format(value, "_d")
    if isinstance(value, float):
        return str(value)

    return '""'
