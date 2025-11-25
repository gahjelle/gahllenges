"""Information about one coding challenge."""

from pathlib import Path

from pydantic import Field, HttpUrl

from gahllenges.schemas import StrictModel
from gahllenges.schemas import type_aliases as t


class Challenge(StrictModel):
    """Information about the challenge."""

    name: str = Field(description="Name of the challenge")
    url: HttpUrl = Field(description="Url to the main page of the challenge")
    icon: str = Field(description="Icon representing one solution in the challenge")


class Patterns(StrictModel):
    """File patterns used in the challenge."""

    solve: str = Field(description="Pattern identifying solve (code) files")
    viz: str | None = Field(None, description="Pattern identifying visualization files")
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


class ReadmeTemplate(StrictModel):
    """Templates for generating README files."""

    challenge: Path = Field(description="Path to template for the main challenge file")
    language: Path = Field(description="Path to template for the language overview")
    event: Path | None = Field(
        None, description="Path to template for the event overview"
    )
    puzzle: Path | None = Field(
        None, description="Path to template for individual puzzles"
    )


class Template(StrictModel):
    """Template for generating code."""

    file_name: str = Field(description="Name of code file")
    docstring: str = Field(description="Docstring on top of file")
    readme: ReadmeTemplate


class Language(StrictModel):
    """Information about each programming language used for the challenge."""

    icon: str
    language_dir: Path


class ChallengeModel(StrictModel):
    """Describe one challenge."""

    root_dir: Path = Field(description="The root path to the challenge directory")
    challenge: Challenge
    patterns: Patterns
    code: Code
    template: Template
    languages: dict[t.LanguageName, Language]
