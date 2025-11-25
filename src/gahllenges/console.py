"""Use Rich for working with the console."""

from collections.abc import Iterable
from itertools import zip_longest
from pathlib import Path

from rich.console import Console

stdout = Console()
stderr = Console(stderr=True)


def render_markdown_table(data: dict[str, list[str]]) -> str:
    """Render data as a Markdown table."""

    def render_row(values: Iterable[str]) -> str:
        """Render one row as markdown."""
        return "| " + " | ".join(values) + " |"

    rows = [render_row(data), render_row("---" for _ in data)]
    rows.extend(render_row(row) for row in zip_longest(*data.values(), fillvalue=""))
    return "\n".join(rows)


def relative_to_cwd(path: Path, *, cwd: Path | None = None, prefix: str = "") -> str:
    """Present a path relative to the current directory.

    In Python 3.12 and later, we can use PurePath.relative_to(path, walk_up=True).
    """
    cwd = Path.cwd() if cwd is None else cwd
    try:
        return f"{prefix}{path.relative_to(cwd)}"
    except ValueError:
        return relative_to_cwd(path, cwd=cwd.parent, prefix=f"../{prefix}")
