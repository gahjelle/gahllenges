"""Create README files with statistics and links to solutions."""

from collections.abc import Iterator
from pathlib import Path

from rich.markdown import Markdown

from gahllenges import challenge, expectations
from gahllenges.console import render_markdown_table, stdout
from gahllenges.schemas import type_aliases as t
from gahllenges.schemas.challenge import ChallengeModel


def update(config: ChallengeModel) -> None:
    """Update all README files."""
    results: dict[t.LanguageName, t.ResultSet] = {
        language: read_puzzle_data(config, language) for language in config.languages
    }

    languages = sorted(results)
    events = sorted({event for languages in results.values() for event, _ in languages})
    puzzles = sorted(
        {puzzle for languages in results.values() for _, puzzle in languages}
    )

    update_challenge(
        config, results, languages=languages, events=events, puzzles=puzzles
    )
    for language in languages:
        update_language(config, results, language, events=events, puzzles=puzzles)
        language_events = sorted({event for event, _ in results[language]})
        for language_event in language_events:
            update_event(
                config,
                language,
                language_event,
                {
                    puzzle: result
                    for (event, puzzle), result in results[language].items()
                    if event == language_event
                },
            )


def read_puzzle_data(config: ChallengeModel, language: t.LanguageName) -> t.ResultSet:
    """Update all README files for a language."""
    result: t.ResultSet = {}
    for event in challenge.list_events(config, language):
        for puzzle, puzzle_dir in challenge.list_puzzles(
            config, event, language
        ).items():
            expected_path = puzzle_dir / "expected.toml"
            if not expected_path.exists():
                continue
            stdout.print(
                (
                    f"{language:<8} {event:>4} {puzzle:>2} "
                    f"{puzzle_dir.relative_to(config.root_dir)}"
                ),
                highlight=False,
            )
            result[event, puzzle] = expectations.read_expectations(expected_path)
    return result


def link(  # noqa: PLR0913
    config: ChallengeModel,
    icon: str,
    language: t.LanguageName,
    event: int,
    puzzle: int,
    base_dir: Path,
) -> str:
    """Create a link to the given puzzle."""
    puzzle_dir = challenge.list_puzzles(config, event, language)[puzzle]
    return f"[{icon}]({puzzle_dir.relative_to(base_dir)})"


def update_challenge(
    config: ChallengeModel,
    results: dict[t.LanguageName, t.ResultSet],
    languages: list[t.LanguageName],
    events: list[int],
    puzzles: list[int],
) -> Path:
    """Update the frontpage challenge README with all solutions across all languages."""
    icons = {language: config.languages[language].icon for language in languages}
    base_dir = config.root_dir
    out_path = base_dir / "README.md"
    table_data = {"Day": [str(puzzle) for puzzle in puzzles]}
    for event in events:
        table_data |= {
            str(event): [
                "".join(
                    link(config, icons[language], language, event, puzzle, base_dir)
                    for language in languages
                    if (info := results[language].get((event, puzzle)))
                    and all(part.solved for part in info.values())
                )
                for puzzle in puzzles
            ]
        }
    table = render_markdown_table(table_data)
    stdout.print(Markdown(table))
    language_list = _md_list(
        f"{config.languages[language].icon} {language.title()}: "
        f"{sum(info.solved for puzzle in puzzles.values() for info in puzzle.values())}"
        f" {config.challenge.icon}"
        for language, puzzles in results.items()
    )
    out_path.write_text(
        fill_template(config.template.readme.challenge, table, languages=language_list),
        encoding="utf-8",
    )
    return out_path


def update_language(
    config: ChallengeModel,
    results: dict[t.LanguageName, t.ResultSet],
    language: t.LanguageName,
    events: list[int],
    puzzles: list[int],
) -> Path:
    """Update READMEs for each language."""
    stdout.rule(language)
    base_dir = config.languages[language].language_dir
    out_path = base_dir / "README.md"
    table_data = {"Day": [str(puzzle) for puzzle in puzzles]}
    for event in events:
        table_data |= {
            str(event): [
                link(
                    config,
                    config.challenge.icon * sum(part.solved for part in info.values()),
                    language,
                    event,
                    puzzle,
                    base_dir,
                )
                for puzzle in puzzles
                if (info := results[language].get((event, puzzle)))
            ]
        }
    table = render_markdown_table(table_data)
    stdout.print(Markdown(table))

    count = sum(
        info.solved for puzzle in results[language].values() for info in puzzle.values()
    )
    out_path.write_text(
        fill_template(
            config.template.readme.language,
            table,
            language=language.title(),
            count=f"{count} {config.challenge.icon}",
        ),
        encoding="utf-8",
    )
    return out_path


def update_event(
    config: ChallengeModel,
    language: t.LanguageName,
    event: int,
    results: dict[int, t.Result],
) -> Path:
    """Update the README for one event."""
    stdout.rule(f"{language} - {event}")
    event_path = challenge.locate_event(config, event, language)
    out_path = event_path / "README.md"
    table_data = {
        "Day": [str(puzzle) for puzzle in results],
        "Puzzle": [
            _name_from_path(next(iter(result.values())).puzzle_dir)
            for result in results.values()
        ],
    }
    if config.code.parse_function is not None:
        table_data |= {
            "Parse": [
                _time(max((info.input.duration for info in result.values()), default=0))
                for result in results.values()
            ]
        }
    for column in config.code.solve_functions:
        table_data |= {
            column.title(): [
                _time(info.duration)
                if (info := result.get(column)) and info.solved
                else ""
                for result in results.values()
            ]
        }

    table = render_markdown_table(table_data)
    stdout.print(Markdown(table))

    out_path.write_text(
        fill_template(
            config.template.readme.event,
            table,
            language=language.title(),
            event=str(event),
        ),
        encoding="utf-8",
    )
    return out_path


def update_puzzle(
    config: ChallengeModel, results: dict[t.LanguageName, t.ResultSet]
) -> Path:
    """Update READMEs for each puzzle."""


def fill_template(template_path: Path | None, table: str, **fmt_args: str) -> str:
    """Fill in a template."""
    if template_path is None:
        return table

    template = template_path.read_text(encoding="utf-8")
    return template.format(table=table, **fmt_args)


def _name_from_path(path: Path) -> str:
    """Parse a puzzle name from a path."""
    return path.stem.replace("-", " ").replace("_", " ").split(maxsplit=1)[-1].title()


def _time(duration: float) -> str:
    """Render a duration."""
    time_units = (
        ("m ⚫️", 60),
        ("s 🔴", 1),
        ("ms 🔵", 1e-3),
        ("μs ⚪️", 1e-6),
        ("ns ⚪️", 1e-9),
    )
    for unit, threshold in time_units:
        if duration > threshold:
            return f"{duration / threshold:.2f} {unit}"

    return f"0.00 {time_units[-1]}"


def _md_list(lines: Iterator[str]) -> str:
    """Create a Markdown list."""
    return "\n- ".join(["", *lines]).strip()
