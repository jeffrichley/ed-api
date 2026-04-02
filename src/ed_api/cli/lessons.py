"""Lessons CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.client import EdClient

app = typer.Typer(help="Lesson commands.")
console = Console()
err_console = Console(stderr=True)


@app.command(name="list")
def list_lessons(
    course_id: int = typer.Argument(help="Course ID"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List lessons in a course, grouped by module."""
    client = EdClient()
    lessons, modules = client.lessons.list(course_id)

    if json_output:
        typer.echo(json.dumps({
            "lessons": [
                {"id": l.id, "title": l.title, "module_id": l.module_id,
                 "lesson_number": l.lesson_number, "is_hidden": l.is_hidden,
                 "slide_count": len(l.slides), "created_at": str(l.created_at)}
                for l in lessons
            ],
            "modules": [
                {"id": m.id, "name": m.name}
                for m in modules
            ],
        }))
    else:
        from rich.table import Table

        modules_by_id = {m.id: m for m in modules}
        # Group lessons by module
        grouped: dict[int | None, list] = {}
        for l in lessons:
            grouped.setdefault(l.module_id, []).append(l)

        table = Table(title=f"Lessons in course {course_id}")
        table.add_column("#", justify="right")
        table.add_column("Title")
        table.add_column("Slides", justify="right")
        table.add_column("Hidden", justify="center")

        for mod_id, mod_lessons in grouped.items():
            if mod_id and mod_id in modules_by_id:
                table.add_row("", f"[bold]{modules_by_id[mod_id].name}[/bold]", "", "")
            for l in mod_lessons:
                hidden = "[yellow]yes[/yellow]" if l.is_hidden else ""
                table.add_row(str(l.lesson_number), f"  {l.title}", str(len(l.slides)), hidden)

        console.print(table)


@app.command()
def get(
    lesson_id: int = typer.Argument(help="Lesson ID"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Get a lesson with its slides."""
    client = EdClient()
    lesson = client.lessons.get(lesson_id)

    if json_output:
        typer.echo(json.dumps({
            "id": lesson.id, "title": lesson.title,
            "lesson_number": lesson.lesson_number,
            "slides": [
                {"id": s.id, "type": s.type, "title": s.title, "index": s.index,
                 "video_url": s.video_url, "file_url": s.file_url, "url": s.url}
                for s in lesson.slides
            ],
        }))
    else:
        console.print(f"[bold]{lesson.title}[/bold]")
        console.print(f"[dim]Lesson #{lesson.lesson_number} | {len(lesson.slides)} slides[/dim]\n")
        for s in lesson.slides:
            type_color = {"video": "red", "document": "blue", "quiz": "green",
                          "code": "yellow", "pdf": "magenta"}.get(s.type, "white")
            extra = ""
            if s.video_url:
                extra = f" [dim]{s.video_url}[/dim]"
            elif s.file_url:
                extra = f" [dim]{s.file_url}[/dim]"
            elif s.url:
                extra = f" [dim]{s.url}[/dim]"
            hidden = " [yellow](hidden)[/yellow]" if s.is_hidden else ""
            console.print(f"  {s.index}. [{type_color}][{s.type}][/{type_color}] {s.title}{hidden}{extra}")


@app.command()
def videos(
    course_id: int = typer.Argument(help="Course ID"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List all video slides in a course."""
    client = EdClient()
    results = client.lessons.video_slides(course_id)

    if json_output:
        typer.echo(json.dumps([
            {"lesson_id": lesson.id, "lesson_title": lesson.title,
             "slide_id": slide.id, "slide_title": slide.title,
             "video_url": slide.video_url}
            for lesson, slide in results
        ]))
    else:
        from rich.table import Table

        table = Table(title=f"Video slides in course {course_id}")
        table.add_column("Lesson")
        table.add_column("Slide")
        table.add_column("Video URL")
        for lesson, slide in results:
            table.add_row(lesson.title, slide.title, slide.video_url or "")
        console.print(table)
