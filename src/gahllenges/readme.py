"""Create README files with statistics and links to solutions."""

from gahllenges import challenge, expectations
from gahllenges.console import stdout
from gahllenges.schemas import type_aliases as t
from gahllenges.schemas.challenge import ChallengeModel


def update(config: ChallengeModel) -> None:
    """Update all README files."""
    results: dict[t.LanguageName, t.ResultSet] = {
        language: update_language(config, language) for language in config.languages
    }
    update_front(config, results)


def update_front(
    config: ChallengeModel, results: dict[t.LanguageName, t.ResultSet]
) -> None:
    """Update the front page README with all solutions across all languages."""
    stdout.print(results)


def update_language(config: ChallengeModel, language: t.LanguageName) -> t.ResultSet:
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
