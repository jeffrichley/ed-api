"""Content conversion CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown

app = typer.Typer(help="Content conversion commands.")
console = Console()


@app.command(name="to-xml")
def to_xml(
    markdown: str = typer.Argument(help="Markdown text to convert"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Convert markdown to Ed XML."""
    xml = markdown_to_ed_xml(markdown)
    if json_output:
        print(json.dumps({"xml": xml}))
    else:
        console.print(xml)


@app.command(name="to-markdown")
def to_markdown(
    xml: str = typer.Argument(help="Ed XML to convert"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Convert Ed XML to markdown."""
    md = ed_xml_to_markdown(xml)
    if json_output:
        print(json.dumps({"markdown": md}))
    else:
        console.print(md)
