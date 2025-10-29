"""Information about one coding challenge."""

from pathlib import Path

from pydantic import Field

from gahllenges.schemas import StrictModel


class Patterns(StrictModel):
    """File patterns used in the challenge."""

    code: str = Field(description="Pattern identifying code files")
    input: str = Field(description="Pattern identifying input files")
    example: str = Field(description="Pattern identifying example files")
    suffixes: list[str] = Field(
        [], description="Optional list of suffixes applied to input and example files"
    )


class Code(StrictModel):
    """Code identifiers."""

    parse_function: str | None = Field(
        None, description="Name of functions used to parse data"
    )
    solve_functions: list[str] = Field(
        description="Name of functions used to solve puzzle parts"
    )


class Template(StrictModel):
    """Template for generating code."""

    file_name: str = Field(description="Name of code file")
    docstring: str = Field(description="Docstring on top of file")


class ChallengeModel(StrictModel):
    """Describe one challenge."""

    name: str = Field(description="Name of challenge")
    challenge_dir: Path = Field(description="The path to the challenge directory")
    patterns: Patterns
    code: Code
    template: Template
