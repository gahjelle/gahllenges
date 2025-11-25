"""Command line interface for the code runner."""

import doctest
import traceback as tb
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Annotated

import configaroo
import pyperclip
from cyclopts import App, Parameter
from textual_image.renderable import Image

from gahllenges import challenge, expectations, readme, template
from gahllenges.console import relative_to_cwd, stderr, stdout
from gahllenges.schemas.challenge import ChallengeModel

if TYPE_CHECKING:
    from gahllenges.schemas import type_aliases as t


def as_title(path: Path) -> str:
    """Convert a numeric path to a title."""
    _number, _, title = path.stem.partition("_")
    return title.replace("_", " ").replace("-", " ").title()


def get_config(root_dir: Path, config_path: Path) -> ChallengeModel:
    """Read the configuration of the challenge."""
    return (
        (configaroo.Configuration.from_file(config_path) | {"root_dir": root_dir})
        .parse_dynamic()
        .convert_model(ChallengeModel)
    )


def configure_app(root_dir: Path, config_path: Path) -> App:  # noqa: C901
    """Register CLI commands for the given coding challenge."""
    app = App()
    config = get_config(root_dir, config_path)

    @app.default
    def run(  # pyright: ignore[reportUnusedFunction]  # noqa: PLR0913
        event: int,
        puzzle: int,
        *,
        example: Annotated[bool, Parameter(name=["--example", "-e"])] = False,
        overwrite: Annotated[bool, Parameter(name=["--overwrite", "-o"])] = False,
        show_viz: Annotated[bool, Parameter(name=["--viz", "-v"])] = False,
        traceback: Annotated[bool, Parameter(name=["--traceback", "-t"])] = False,
    ) -> None:
        """Run the solution to one puzzle and copy the result to the clipboard."""
        input_pattern = config.patterns.example if example else config.patterns.input

        # Run challenge and show results
        results: list[t.Result] = []
        try:
            for result in challenge.run(
                event, puzzle, config=config, input_pattern=input_pattern
            ):
                results.append(result)
                if result.value is None:
                    continue
                stdout.print(
                    f"[green]{event:>4} {puzzle:>2} {result.name}[/]"
                    f" [gray50]{result.code.stem}[/]"
                    f" [grey50]{result.input.path.stem:<15}[/]"
                    f" [blue]{result.value:>20}[/]"
                    f" [grey50]{1000 * result.duration:8.2f}ms[/]"
                    + (
                        f" [grey50](+ {1000 * result.input.duration:.2f}ms)[/]"
                        if result.input.parse_function
                        else ""
                    ),
                    highlight=False,
                )

                # Add result to the clipboard
                pyperclip.copy(str(result.value))
        except Exception as err:  # noqa: BLE001
            if traceback:
                tb.print_exception(err)
            else:
                stderr.print(f"[red]{type(err).__name__}:[/] {err}")

        # Check results vs expected values
        expectations.validate(results, example=example, overwrite=overwrite)

        # Show visualization of the puzzle
        if show_viz:
            visualize(event, puzzle)

    @app.command
    def run_all(  # pyright: ignore[reportUnusedFunction]
        event: int | None = None,
        *,
        example: Annotated[bool, Parameter(name=["--example", "-e"])] = False,
        overwrite: Annotated[bool, Parameter(name=["--overwrite", "-o"])] = False,
        show_viz: Annotated[bool, Parameter(name=["--viz", "-v"])] = False,
    ) -> None:
        """Run the solution to all puzzles in an event."""
        if event is None:
            for single_event, path in challenge.list_events(config).items():
                stdout.rule(f"{single_event} {as_title(path)}".strip())
                run_all(
                    single_event,
                    example=example,
                    overwrite=overwrite,
                    show_viz=show_viz,
                )
            return

        for puzzle, path in challenge.list_puzzles(config, event).items():
            stdout.print(
                f"[blue]{event:>4} {puzzle:>2} {as_title(path)}[/]",
                highlight=False,
            )
            run(event, puzzle, example=example, overwrite=overwrite, show_viz=show_viz)

    @app.command
    def visualize(
        event: int,
        puzzle: int,
        *,
        example: Annotated[bool, Parameter(name=["--example", "-e"])] = False,
        overwrite: Annotated[bool, Parameter(name=["--overwrite", "-o"])] = False,
    ) -> None:
        """Run visualization for one puzzle."""
        input_pattern = config.patterns.example if example else config.patterns.input

        # Run the visualization and show it
        for path in challenge.draw_viz(
            event,
            puzzle,
            config=config,
            input_pattern=input_pattern,
            overwrite=overwrite,
        ):
            if path is None:
                continue
            stdout.rule(str(path))
            stdout.print(Image(path, width="80%", height="80%"), justify="center")

    @app.command
    def test(  # pyright: ignore[reportUnusedFunction]
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

            path = relative_to_cwd(Path(str(module.__file__)))
            result = doctest.testmod(module, verbose=verbose, report=False)
            score = f"{result.attempted - result.failed}/{result.attempted}"
            color = "red" if result.failed else "blue"
            stdout.print(f"[bold {color}]{path} ({score})[/]")

    @app.command
    def gen(  # pyright: ignore[reportUnusedFunction]
        event: int,
        puzzle: int,
        name: str = "",
        *,
        overwrite: Annotated[bool, Parameter(name=["--overwrite", "-o"])] = False,
    ) -> None:
        """Generate a solution template."""
        path = template.generate(
            config, event=event, puzzle=puzzle, name=name, overwrite=overwrite
        )
        stdout.print(f"Code for {name} generated at [blue]{relative_to_cwd(path)}[/]")

    @app.command
    def update_readme() -> None:  # pyright: ignore[reportUnusedFunction]
        """Update README files."""
        readme.update(config)

    @app.command
    def show_config(section: str | None = None) -> None:  # pyright: ignore[reportUnusedFunction]
        """Show the configuration of the challenge."""
        configaroo.print_configuration(config, section=section)

    return app
