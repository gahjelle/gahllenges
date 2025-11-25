"""Handle one challenge and its puzzles."""

import functools
import importlib
import re
import sys
from collections.abc import Generator
from pathlib import Path
from types import ModuleType
from typing import Any

import platformdirs
from codetiming import Timer

from gahllenges.schemas import type_aliases as t
from gahllenges.schemas.challenge import ChallengeModel


def run(
    event: int,
    puzzle: int,
    config: ChallengeModel,
    input_pattern: str,
) -> Generator[t.Result]:
    """Run code for one puzzle."""
    # Locate and import code
    puzzle_dir = locate_puzzle(config, event, puzzle, language="python")
    module = import_solver(config, puzzle_dir)

    suffixes = set(config.code.solve_functions)

    # Run functions
    for func_name, suffix in zip(
        config.code.solve_functions,
        config.patterns.suffixes or [""] * len(config.code.solve_functions),
        strict=True,
    ):
        func = getattr(module, func_name)
        for puzzle_input in get_input(
            config,
            module,
            puzzle_dir,
            input_pattern=input_pattern.format(suffix=suffix),
            bad_suffixes=suffixes - {func_name},
        ):
            with Timer(logger=None) as timer:
                value = func(puzzle_input.value)
            yield t.Result(
                interpreter=sys.implementation.cache_tag,
                name=func_name,
                puzzle_dir=puzzle_dir,
                code=Path(str(module.__file__)),
                input=puzzle_input,
                value=value,
                solved=True,  # Assume the puzzle is solved
                duration=timer.last,
            )


def draw_viz(
    event: int,
    puzzle: int,
    *,
    config: ChallengeModel,
    input_pattern: str,
    overwrite: bool,
) -> Generator[Path | None]:
    """Draw visualizations for one puzzle."""
    viz_dir = platformdirs.user_data_path(config.root_dir.name)
    viz_dir.mkdir(parents=True, exist_ok=True)

    # Locate and import code
    puzzle_dir = locate_puzzle(config, event, puzzle, language="python")
    module = import_viz(config, puzzle_dir)
    if module is None:
        return None

    suffixes = set(config.code.solve_functions)

    # Run functions
    for func_name, suffix in zip(
        config.code.solve_functions,
        config.patterns.suffixes or [""] * len(config.code.solve_functions),
        strict=True,
    ):
        viz_path = viz_dir / f"viz-{event}-{puzzle:02d}-{func_name}.png"
        if viz_path.exists() and not overwrite:
            yield viz_path
            continue

        try:
            func = getattr(module, func_name)
        except AttributeError:
            continue
        for puzzle_input in get_input(
            config,
            module,
            puzzle_dir,
            input_pattern=input_pattern.format(suffix=suffix),
            bad_suffixes=suffixes - {func_name},
        ):
            func(puzzle_input.value, viz_path)
            yield viz_path


def import_solver(config: ChallengeModel, puzzle_dir: Path) -> ModuleType:
    """Import the module solving a particular puzzle."""
    code_path = locate_code(config.patterns.solve.format(suffix=""), puzzle_dir)
    local_code_path = code_path.relative_to(config.languages["python"].language_dir)

    # Import puzzle module
    module_name = ".".join(local_code_path.parts).removesuffix(".py")
    return importlib.import_module(module_name)


def import_viz(config: ChallengeModel, puzzle_dir: Path) -> ModuleType | None:
    """Import the module visualizing a particular puzzle."""
    if config.patterns.viz is None:
        return None

    try:
        code_path = locate_code(config.patterns.viz, puzzle_dir)
    except ValueError:
        return None

    # Import visualization module
    local_code_path = code_path.relative_to(config.languages["python"].language_dir)
    module_name = ".".join(local_code_path.parts).removesuffix(".py")
    return importlib.import_module(module_name)


def get_input(
    config: ChallengeModel,
    module: ModuleType,
    puzzle_dir: Path,
    input_pattern: str,
    bad_suffixes: set[str],
) -> Generator[t.Input]:
    """Read the input from a file."""
    for input_path in sorted(puzzle_dir.glob(input_pattern)):
        if any(input_path.stem.endswith(suffix) for suffix in bad_suffixes):
            continue
        puzzle_input = input_path.read_text().rstrip()
        if not config.code.parse_function:
            yield t.Input(value=puzzle_input, path=input_path)
        else:
            value, duration = parse_input(
                puzzle_input, module, config.code.parse_function
            )
            yield t.Input(
                value=value,
                path=input_path,
                parse_function=config.code.parse_function,
                duration=duration,
            )


@functools.cache
def parse_input(
    puzzle_input: str, module: ModuleType, parse_function: str
) -> tuple[Any, float]:
    """Parse the input and cache the result."""
    parse = getattr(module, parse_function)
    with Timer(logger=None) as timer:
        value = parse(puzzle_input)

    return value, timer.last


def _get_numeric_folders(base_dir: Path) -> dict[int, Path]:
    """Find all folders starting with a numeric prefix."""
    return {
        int(folder_id): path
        for path in sorted(base_dir.iterdir())
        if (folder_id := path.name.split("_")[0]).isnumeric()
    }


def list_events(
    config: ChallengeModel, language: t.LanguageName = "python"
) -> dict[int, Path]:
    """List all events in the current challenge."""
    return _get_numeric_folders(config.languages[language].language_dir)


def list_puzzles(
    config: ChallengeModel, event: int, language: t.LanguageName = "python"
) -> dict[int, Path]:
    """List all puzzles in the given event."""
    return _get_numeric_folders(locate_event(config, event, language=language))


def locate_event(
    config: ChallengeModel, event: int, language: t.LanguageName = "python"
) -> Path:
    """Locate the folder for a given event."""
    events = _get_numeric_folders(config.languages[language].language_dir)
    try:
        return events[event]
    except KeyError:
        msg = f"no event starting with {event}"
        raise ValueError(msg) from None


def locate_puzzle(
    config: ChallengeModel, event: int, puzzle: int, language: t.LanguageName = "python"
) -> Path:
    """Locate the folder for a given puzzle."""
    puzzles = list_puzzles(config, event, language=language)

    try:
        return puzzles[puzzle]
    except KeyError:
        msg = f"no puzzle number {puzzle} for {event} event"
        raise ValueError(msg) from None


def locate_code(code_pattern: str, puzzle_dir: Path) -> Path:
    """Locate the code file for a given puzzle."""
    for path in sorted(puzzle_dir.glob(code_pattern)):
        return path

    msg = f"No code file {code_pattern} found in {puzzle_dir}"
    raise ValueError(msg)


def create_puzzle_dir(
    config: ChallengeModel,
    event: int,
    puzzle: int,
    name: str,
    language: t.LanguageName = "python",
) -> Path:
    """Create a folder for a puzzle."""
    puzzle_name = f"{puzzle:02d}" + (f"_{_normalize_name(name)}" if name else "")
    puzzle_path = locate_event(config, event, language=language) / puzzle_name
    puzzle_path.mkdir(exist_ok=True, parents=True)

    return puzzle_path


def _normalize_name(name: str) -> str:
    """Normalize a name for use in directory names."""
    return re.sub(r"[^\w\d_-]", "", name.lower().replace(" ", "-"))
