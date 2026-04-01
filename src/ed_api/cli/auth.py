"""Auth CLI commands."""

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ed_api.client import EdClient

app = typer.Typer(help="Authentication commands.")
console = Console()


@app.command()
def check(
    json_output: bool = typer.Option(False, "--json"),
):
    """Verify API token is valid."""
    try:
        client = EdClient()
        info = client.user.info()
        if json_output:
            print(json.dumps({"status": "ok", "user": info.user.name}))
        else:
            console.print(f"[green]Token valid.[/green] Logged in as {info.user.name}")
    except Exception as e:
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[red]Token invalid:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def whoami(
    json_output: bool = typer.Option(False, "--json"),
):
    """Show current user info."""
    client = EdClient()
    info = client.user.info()
    if json_output:
        print(json.dumps({
            "id": info.user.id,
            "name": info.user.name,
            "email": info.user.email,
            "courses": [
                {"id": c.course.id, "code": c.course.code, "name": c.course.name, "role": c.role}
                for c in info.courses
            ],
        }))
    else:
        console.print(Panel(
            f"[bold]{info.user.name}[/bold]\n{info.user.email}",
            title="EdStem User",
            border_style="blue",
        ))

        table = Table(title="Enrolled Courses", show_lines=False)
        table.add_column("ID", style="dim", justify="right")
        table.add_column("Code", style="bold")
        table.add_column("Name")
        table.add_column("Role")

        courses = sorted(info.courses, key=lambda c: c.course.id, reverse=True)
        for c in courses:
            role_style = "green" if c.role in ("admin", "staff") else "dim"
            table.add_row(
                str(c.course.id),
                c.course.code,
                c.course.name,
                f"[{role_style}]{c.role}[/{role_style}]",
            )

        console.print(table)
