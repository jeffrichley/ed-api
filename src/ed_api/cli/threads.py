"""Threads CLI commands."""

import json
import typer
from rich.console import Console
from rich.table import Table
from ed_api.client import EdClient

app = typer.Typer(help="Thread commands.")
console = Console()


@app.command(name="list")
def list_threads(
    course_id: int = typer.Argument(help="Course ID"),
    limit: int = typer.Option(30, "--limit"),
    sort: str = typer.Option("new", "--sort"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List threads in a course."""
    client = EdClient()
    threads = client.threads.list(course_id, limit=limit, sort=sort)
    if json_output:
        print(json.dumps([
            {"id": t.id, "number": t.number, "title": t.title, "type": t.type,
             "category": t.category, "is_answered": t.is_answered,
             "reply_count": t.reply_count, "created_at": str(t.created_at)}
            for t in threads
        ]))
    else:
        table = Table(title=f"Threads in course {course_id}")
        table.add_column("#")
        table.add_column("Title")
        table.add_column("Category")
        table.add_column("Replies")
        for t in threads:
            table.add_row(str(t.number), t.title, t.category, str(t.reply_count))
        console.print(table)


@app.command()
def get(
    thread_ref: str = typer.Argument(help="Thread ID or course_id:number"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Get a thread with comments."""
    client = EdClient()
    if ":" in thread_ref:
        course_id, number = thread_ref.split(":", 1)
        thread = client.threads.get_by_number(int(course_id), int(number))
    else:
        thread = client.threads.get(int(thread_ref))
    if json_output:
        print(json.dumps({
            "id": thread.id, "number": thread.number, "title": thread.title,
            "content": thread.content, "category": thread.category,
            "is_answered": thread.is_answered,
            "comments": [
                {"id": c.id, "type": c.type, "content": c.content,
                 "is_endorsed": c.is_endorsed, "user_id": c.user_id}
                for c in thread.comments
            ],
        }))
    else:
        console.print(f"[bold]#{thread.number}:[/bold] {thread.title}")
        console.print(f"Category: {thread.category}")
        for c in thread.comments:
            label = "[answer]" if c.type == "answer" else "[comment]"
            endorsed = " (endorsed)" if c.is_endorsed else ""
            console.print(f"\n  {label}{endorsed} by user {c.user_id}")


@app.command()
def search(
    course_id: int = typer.Argument(help="Course ID"),
    query: str = typer.Argument(help="Search query"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Search threads."""
    client = EdClient()
    threads = client.threads.search(course_id, query)
    if json_output:
        print(json.dumps([
            {"id": t.id, "number": t.number, "title": t.title, "category": t.category}
            for t in threads
        ]))
    else:
        for t in threads:
            console.print(f"  #{t.number}: {t.title} [{t.category}]")


@app.command()
def lock(thread_id: int = typer.Argument()):
    """Lock a thread."""
    EdClient().threads.lock(thread_id)
    console.print(f"Thread {thread_id} locked.")


@app.command()
def unlock(thread_id: int = typer.Argument()):
    """Unlock a thread."""
    EdClient().threads.unlock(thread_id)
    console.print(f"Thread {thread_id} unlocked.")


@app.command()
def pin(thread_id: int = typer.Argument()):
    """Pin a thread."""
    EdClient().threads.pin(thread_id)
    console.print(f"Thread {thread_id} pinned.")


@app.command()
def unpin(thread_id: int = typer.Argument()):
    """Unpin a thread."""
    EdClient().threads.unpin(thread_id)
    console.print(f"Thread {thread_id} unpinned.")


@app.command()
def private(thread_id: int = typer.Argument()):
    """Mark a thread as private."""
    EdClient().threads.set_private(thread_id, private=True)
    console.print(f"Thread {thread_id} marked private.")


@app.command()
def public(thread_id: int = typer.Argument()):
    """Mark a thread as public."""
    EdClient().threads.set_private(thread_id, private=False)
    console.print(f"Thread {thread_id} marked public.")


@app.command()
def endorse(thread_id: int = typer.Argument()):
    """Endorse a thread."""
    EdClient().threads.endorse(thread_id)
    console.print(f"Thread {thread_id} endorsed.")


@app.command()
def unendorse(thread_id: int = typer.Argument()):
    """Remove endorsement from a thread."""
    EdClient().threads.unendorse(thread_id)
    console.print(f"Thread {thread_id} unendorsed.")
