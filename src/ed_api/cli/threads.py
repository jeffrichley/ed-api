"""Threads CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.client import EdClient
from ed_api.content import ed_xml_to_markdown

app = typer.Typer(help="Thread commands.")
console = Console()
err_console = Console(stderr=True)


@app.command(name="list")
def list_threads(
    course_id: int = typer.Argument(help="Course ID"),
    limit: int = typer.Option(30, "--limit"),
    sort: str = typer.Option("new", "--sort"),
    no_pinned: bool = typer.Option(False, "--no-pinned", help="Exclude pinned threads"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List threads in a course."""
    client = EdClient()
    fetch_limit = limit * 3 if no_pinned else limit  # over-fetch to compensate for filtering
    threads = client.threads.list(course_id, limit=fetch_limit, sort=sort)
    if no_pinned:
        threads = [t for t in threads if not t.is_pinned]
    threads = threads[:limit]
    if json_output:
        typer.echo(json.dumps([
            {"id": t.id, "number": t.number, "title": t.title, "type": t.type,
             "category": t.category, "is_answered": t.is_answered, "is_pinned": t.is_pinned,
             "reply_count": t.reply_count, "created_at": str(t.created_at)}
            for t in threads
        ]))
    else:
        from rich.table import Table

        has_pinned = any(t.is_pinned for t in threads)
        table = Table(title=f"Threads in course {course_id}")
        table.add_column("#", justify="right")
        table.add_column("Title")
        table.add_column("Category")
        table.add_column("Replies", justify="right")
        if has_pinned:
            table.add_column("Pinned", justify="center")
        for t in threads:
            row = [str(t.number), t.title, t.category, str(t.reply_count)]
            if has_pinned:
                row.append("[yellow]📌[/yellow]" if t.is_pinned else "")
            table.add_row(*row)
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
        typer.echo(json.dumps({
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
        from rich.markdown import Markdown
        from rich.panel import Panel

        # Thread header
        try:
            body_md = ed_xml_to_markdown(thread.content)
        except Exception:
            body_md = thread.content

        author_name = thread.author.name if thread.author else "Unknown"
        console.print(Panel(
            f"[bold]{thread.title}[/bold]\n"
            f"[dim]#{thread.number} | {thread.category} | by {author_name}[/dim]\n"
            f"[dim]Answered: {'yes' if thread.is_answered else 'no'} | "
            f"Endorsed: {'yes' if thread.is_endorsed else 'no'} | "
            f"Private: {'yes' if thread.is_private else 'no'}[/dim]",
            border_style="blue",
        ))
        console.print(Markdown(body_md))

        # Comments
        if not thread.comments:
            console.print("\n[dim]No comments yet.[/dim]")
        for c in thread.comments:
            author = thread.users.get(c.user_id)
            name = author.name if author else f"User {c.user_id}"
            role = f" ({author.role})" if author else ""
            endorsed = " [green]endorsed[/green]" if c.is_endorsed else ""
            type_label = "[bold cyan]Answer[/bold cyan]" if c.type == "answer" else "[bold]Comment[/bold]"

            try:
                comment_md = ed_xml_to_markdown(c.content)
            except Exception:
                comment_md = c.content

            console.print(f"\n{'─' * 60}")
            console.print(f"{type_label} by {name}{role}{endorsed}")
            console.print(Markdown(comment_md))


@app.command()
def create(
    course_id: int = typer.Argument(help="Course ID"),
    title: str = typer.Option(..., "--title", help="Thread title"),
    body: str = typer.Option(..., "--body", help="Thread body (markdown)"),
    category: str = typer.Option("General", "--category", help="Category"),
    type: str = typer.Option("question", "--type", help="Thread type: question, post, announcement"),
    private: bool = typer.Option(False, "--private", help="Create as private thread"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Create a new thread."""
    client = EdClient()
    thread = client.threads.create(
        course_id, title=title, body=body, type=type,
        category=category, is_private=private,
    )
    if json_output:
        typer.echo(json.dumps({
            "id": thread.id, "number": thread.number, "title": thread.title,
        }))
    else:
        console.print(f"[green]Created thread #{thread.number}:[/green] {thread.title} (id: {thread.id})")


@app.command()
def edit(
    thread_id: int = typer.Argument(help="Thread ID"),
    title: str = typer.Option(None, "--title", help="New title"),
    body: str = typer.Option(None, "--body", help="New body (markdown)"),
    category: str = typer.Option(None, "--category", help="New category"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Edit an existing thread."""
    client = EdClient()
    thread = client.threads.edit(thread_id, title=title, body=body, category=category)
    if json_output:
        typer.echo(json.dumps({
            "id": thread.id, "number": thread.number, "title": thread.title,
        }))
    else:
        console.print(f"[green]Updated thread #{thread.number}:[/green] {thread.title}")


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
        typer.echo(json.dumps([
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


@app.command()
def delete(thread_id: int = typer.Argument()):
    """Delete a thread."""
    EdClient().threads.delete(thread_id)
    console.print(f"Thread {thread_id} deleted.")
