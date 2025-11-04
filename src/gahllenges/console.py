"""Use Rich for working with the console."""

from rich.console import Console

stdout = Console()
stderr = Console(stderr=True)
