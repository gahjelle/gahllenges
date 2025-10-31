"""Command line interface for the code runner."""

import doctest
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import configaroo
import pyperclip
from cyclopts import App, Parameter
from rich.console import Console

from gahllenges import challenge, expectations, template
from gahllenges.schemas.challenge import ChallengeModel

if TYPE_CHECKING:
    from gahllenges.schemas import type_aliases as t

stdout = Console()


def get_config(challenge_dir: Path, config_path: Path) -> ChallengeModel:
    """Read the configuration of the I18N challenge."""
    return (
        configaroo.Configuration.from_file(config_path)
        | {"challenge_dir": challenge_dir}
    ).convert_model(ChallengeModel)


def configure_app(challenge_dir: Path, config_path: Path) -> App:
    """Register CLI commands for the given coding challenge."""
    app = App()
    config = get_config(challenge_dir, config_path)

    @app.default
    def run(
        event: int,
        puzzle: int,
        *,
        example: Annotated[bool, Parameter(name=["--example", "-e"])] = False,
        overwrite: Annotated[bool, Parameter(name=["--overwrite", "-o"])] = False,
    ) -> None:
        """Run the solution to one puzzle and copy the result to the clipboard."""
        input_pattern = config.patterns.example if example else config.patterns.input

        # Run challenge and show results
        results: list[t.Result] = []
        for result in challenge.run(
            event, puzzle, config=config, input_pattern=input_pattern
        ):
            results.append(result)
            if result.value is None:
                continue
            stdout.print(
                f"[green]{event:>4} {puzzle:>2} {result.name}[/] "
                f"[grey50]({result.input.path.stem})[/] [blue]{result.value:>25}[/]"
                f" [grey50]({1000 * result.duration:.2f}ms)[/]",
                highlight=False,
            )

            # Add result to the clipboard
            pyperclip.copy(str(result.value))

        # Check results vs expected values
        expectations.validate(results, example=example, overwrite=overwrite)

    @app.command
    def run_all(
        event: int,
        *,
        example: Annotated[bool, Parameter(name=["--example", "-e"])] = False,
        overwrite: Annotated[bool, Parameter(name=["--overwrite", "-o"])] = False,
    ) -> None:
        """Run the solution to all puzzles in an event."""
        for puzzle in challenge.list_puzzles(config, event):
            run(event, puzzle, example=example, overwrite=overwrite)

    @app.command
    def test(
        event: int,
        puzzle: int | None = None,
        *,
        verbose: Annotated[bool, Parameter(name=["--verbose", "-v"])] = False,
    ) -> None:
        """Run doctests for one or all puzzles in an event."""
        if puzzle is None:
            for puzzle_id in challenge.list_puzzles(config, event):
                test(event, puzzle=puzzle_id, verbose=verbose)
        else:
            puzzle_dir = challenge.locate_puzzle(config, event, puzzle)
            module = challenge.import_solver(config, puzzle_dir)

            path = Path(str(module.__file__)).relative_to(config.challenge_dir)
            result = doctest.testmod(module, verbose=verbose, report=False)
            score = f"{result.attempted-result.failed}/{result.attempted}"
            stdout.print(f"[bold blue]{path} ({score})[/]")

    @app.command
    def gen(event: int, puzzle: int, name: str = "") -> None:
        """Generate a solution template."""
        template.generate(config, event=event, puzzle=puzzle, name=name)

    @app.command
    def show_config(section: str | None = None) -> None:
        """Show the configuration of the challenge."""
        configaroo.print_configuration(config, section=section)

    return app
