"""Typer CLI entry point for ed-api."""

import logging
import typer
from rich.console import Console
from rich.logging import RichHandler

from ed_api.cli.auth import app as auth_app
from ed_api.cli.courses import app as courses_app
from ed_api.cli.threads import app as threads_app
from ed_api.cli.comments import app as comments_app
from ed_api.cli.files import app as files_app
from ed_api.cli.lessons import app as lessons_app
from ed_api.cli.content import app as content_app

app = typer.Typer(name="ed-api", help="EdStem API client.", rich_markup_mode="rich")
app.add_typer(auth_app, name="auth")
app.add_typer(courses_app, name="courses")
app.add_typer(threads_app, name="threads")
app.add_typer(comments_app, name="comments")
app.add_typer(files_app, name="files")
app.add_typer(lessons_app, name="lessons")
app.add_typer(content_app, name="content")


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    level = logging.DEBUG if verbose else (logging.WARNING if quiet else logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=False,
                show_path=verbose,
                markup=True,
            )
        ],
    )


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress info output"),
) -> None:
    """EdStem API client."""
    setup_logging(verbose=verbose, quiet=quiet)
