"""Files CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.client import EdClient

app = typer.Typer(help="File commands.")
console = Console()


@app.command()
def upload(
    file_path: str = typer.Argument(help="Path to file to upload"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Upload a file to Ed."""
    client = EdClient()
    url = client.files.upload_from_path(file_path)
    if json_output:
        print(json.dumps({"url": url}))
    else:
        console.print(f"Uploaded: {url}")
