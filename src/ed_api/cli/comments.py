"""Comments CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.client import EdClient

app = typer.Typer(help="Comment commands.")
console = Console()


@app.command()
def post(
    thread_id: int = typer.Argument(help="Thread ID"),
    body: str = typer.Option(..., "--body", help="Comment body (markdown)"),
    answer: bool = typer.Option(False, "--answer", help="Post as answer"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Post a comment on a thread."""
    client = EdClient()
    comment = client.comments.post(thread_id, body, is_answer=answer)
    if json_output:
        print(json.dumps({"id": comment.id, "type": comment.type, "thread_id": comment.thread_id}))
    else:
        console.print(f"Posted {comment.type} (id: {comment.id}) on thread {thread_id}")


@app.command()
def reply(
    comment_id: int = typer.Argument(help="Comment ID to reply to"),
    body: str = typer.Option(..., "--body", help="Reply body (markdown)"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Reply to a comment."""
    client = EdClient()
    comment = client.comments.reply(comment_id, body)
    if json_output:
        print(json.dumps({"id": comment.id, "type": comment.type}))
    else:
        console.print(f"Replied (id: {comment.id}) to comment {comment_id}")


@app.command()
def endorse(comment_id: int = typer.Argument()):
    """Endorse a comment."""
    EdClient().comments.endorse(comment_id)
    console.print(f"Comment {comment_id} endorsed.")


@app.command()
def unendorse(comment_id: int = typer.Argument()):
    """Remove endorsement from a comment."""
    EdClient().comments.unendorse(comment_id)
    console.print(f"Comment {comment_id} unendorsed.")


@app.command()
def accept(
    comment_id: int = typer.Argument(help="Comment ID to accept as answer"),
):
    """Accept a comment as the answer."""
    EdClient().comments.accept(comment_id)
    console.print(f"Comment {comment_id} accepted as answer.")
