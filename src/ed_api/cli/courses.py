"""Courses CLI commands."""

import json
import typer
from rich.console import Console
from rich.table import Table
from ed_api.client import EdClient

app = typer.Typer(help="Course commands.")
console = Console()


@app.command(name="list")
def list_courses(
    json_output: bool = typer.Option(False, "--json"),
):
    """List enrolled courses."""
    client = EdClient()
    courses = client.courses.list()
    if json_output:
        print(json.dumps([
            {"id": c.course.id, "code": c.course.code, "name": c.course.name,
             "year": c.course.year, "session": c.course.session, "role": c.role}
            for c in courses
        ]))
    else:
        table = Table(title="Courses")
        table.add_column("ID")
        table.add_column("Code")
        table.add_column("Name")
        table.add_column("Role")
        for c in courses:
            table.add_row(str(c.course.id), c.course.code, c.course.name, c.role)
        console.print(table)


@app.command()
def users(
    course_id: int = typer.Argument(help="Course ID"),
    role: str = typer.Option(None, "--role", help="Filter by role"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List users in a course."""
    client = EdClient()
    users_list = client.courses.users(course_id, role=role)
    if json_output:
        print(json.dumps([
            {"id": u.id, "name": u.name, "email": u.email, "role": u.course_role}
            for u in users_list
        ]))
    else:
        table = Table(title=f"Users in course {course_id}")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Role")
        for u in users_list:
            table.add_row(str(u.id), u.name, u.course_role)
        console.print(table)
