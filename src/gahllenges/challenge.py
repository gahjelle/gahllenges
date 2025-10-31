"""Handle one challenge and its puzzles."""

import importlib
from collections.abc import Generator
from pathlib import Path
from types import ModuleType

from codetiming import Timer

from gahllenges.schemas import type_aliases as t
from gahllenges.schemas.challenge import ChallengeModel


def run(
    event: int, puzzle: int, config: ChallengeModel, input_pattern: str
) -> Generator[t.Result]:
    """Run code for one puzzle."""
    # Locate and import code
    puzzle_dir = locate_puzzle(config, event, puzzle)
    module = import_solver(config, puzzle_dir)

    # Run functions
    for func_name, suffix in zip(
        config.code.solve_functions,
        config.patterns.suffixes or [""] * len(config.code.solve_functions),
        strict=True,
    ):
        func = getattr(module, func_name)
        for puzzle_input in get_input(
            config, module, puzzle_dir, input_pattern.format(suffix=suffix)
        ):
            with Timer(logger=None) as timer:
                value = func(puzzle_input.value)
            yield t.Result(
                name=func_name,
                value=value,
                puzzle_dir=puzzle_dir,
                input=puzzle_input,
                duration=timer.last,
            )


def import_solver(config: ChallengeModel, puzzle_dir: Path) -> ModuleType:
    """Import the module solving a particular puzzle."""
    code_path = locate_code(config, puzzle_dir)
    local_code_path = code_path.relative_to(config.challenge_dir)

    # Import puzzle module
    module_name = ".".join(local_code_path.parts).removesuffix(".py")
    return importlib.import_module(module_name)


def get_input(
    config: ChallengeModel, module: ModuleType, puzzle_dir: Path, input_pattern: str
) -> Generator[t.Input]:
    """Read the input from a file."""
    for input_path in sorted(puzzle_dir.glob(input_pattern)):
        puzzle_input = input_path.read_text().rstrip()
        if not config.code.parse_function:
            yield t.Input(value=puzzle_input, path=input_path)
        else:
            parse = getattr(module, config.code.parse_function)
            with Timer(logger=None) as timer:
                value = parse(puzzle_input)
            yield t.Input(
                value=value,
                path=input_path,
                parse_function=config.code.parse_function,
                duration=timer.last,
            )


def _get_numeric_folders(base_dir: Path) -> dict[int, Path]:
    """Find all folders starting with a numeric prefix."""
    return {
        int(folder_id): path
        for path in sorted(base_dir.iterdir())
        if (folder_id := path.name.split("_")[0]).isnumeric()
    }


def list_puzzles(config: ChallengeModel, event: int) -> dict[int, Path]:
    """List all puzzles in the given event."""
    return _get_numeric_folders(locate_event(config, event))


def locate_event(config: ChallengeModel, event: int) -> Path:
    """Locate the folder for a given event."""
    events = _get_numeric_folders(config.challenge_dir)
    try:
        return events[event]
    except KeyError:
        msg = f"no event starting with {event}"
        raise ValueError(msg) from None


def locate_puzzle(config: ChallengeModel, event: int, puzzle: int) -> Path:
    """Locate the folder for a given puzzle."""
    puzzles = list_puzzles(config, event)

    try:
        return puzzles[puzzle]
    except KeyError:
        msg = f"no puzzle number {puzzle} for {event} event"
        raise ValueError(msg) from None


def locate_code(config: ChallengeModel, puzzle_dir: Path, suffix: str = "") -> Path:
    """Locate the code file for a given puzzle."""
    code_pattern = config.patterns.code.format(suffix=suffix)
    for path in puzzle_dir.glob(code_pattern):
        return path

    msg = f"No code file {code_pattern} found in {puzzle_dir}"
    raise ValueError(msg)


def create_puzzle_dir(
    config: ChallengeModel, event: int, puzzle: int, name: str
) -> Path:
    """Create a folder for a puzzle."""
    puzzle_name = f"{puzzle:02d}" + (f"_{_normalize_name(name)}" if name else "")
    puzzle_path = locate_event(config, event) / puzzle_name
    puzzle_path.mkdir(exist_ok=True, parents=True)

    return puzzle_path


def _normalize_name(name: str) -> str:
    """Normalize a name for use in directory names."""
    return name.lower().replace(" ", "-")
