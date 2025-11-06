"""Generate puzzle files from a template."""

from pathlib import Path

from gahllenges import challenge
from gahllenges.console import stderr
from gahllenges.schemas.challenge import ChallengeModel


def generate(
    config: ChallengeModel,
    *,
    event: int,
    puzzle: int,
    name: str,
    overwrite: bool = False,
) -> Path:
    """Generate one puzzle file."""
    out_path = challenge.create_puzzle_dir(
        config=config, event=event, puzzle=puzzle, name=name
    ) / config.template.file_name.format(event=event, puzzle=puzzle)
    if out_path.exists() and not overwrite:
        stderr.print(
            f"Code file already exists at [blue]{out_path.relative_to(Path.cwd())}[/]."
            " Use [yellow]--overwrite[/] or [yellow]-o[/] to overwrite existing file.",
            highlight=False,
        )
        raise SystemExit

    docstring = config.template.docstring.format(event=event, puzzle=puzzle, name=name)
    code = [f'"""{docstring}"""']
    if config.code.parse_function:
        code.append(_parse_function(config.code.parse_function))
    code.extend(
        _solve_function(config, solve_function, part)
        for part, solve_function in enumerate(config.code.solve_functions, start=1)
    )
    out_path.write_text("\n\n".join(code), encoding="utf-8")
    return out_path


def _parse_function(name: str) -> str:
    """Template for a parse function."""
    code = [
        f"def {name}(puzzle_input: str) -> list[str]:",
        '    """Parse puzzle input."""',
        '    return [line for line in puzzle_input.split("\\n")]',
    ]
    return "\n".join(code)


def _solve_function(config: ChallengeModel, name: str, part: int) -> str:
    """Template for a solve function."""
    if config.code.parse_function:
        code = [f"def {name}(data: list[str]) -> int:"]
    else:
        code = [f"def {name}(puzzle_input: str) -> int:"]

    if len(config.code.solve_functions) > 1:
        code.append(f'    """Solve part {part}."""')
    else:
        code.append('    """Solve puzzle."""')

    return "\n".join(code)
