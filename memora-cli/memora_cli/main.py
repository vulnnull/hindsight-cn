"""
Memora CLI - HTTP client for Memora API.
"""

import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.markdown import Markdown
from rich import box
from rich.tree import Tree

app = typer.Typer(
    name="memora",
    help="Modern CLI for Memora - Temporal Semantic Memory System",
    add_completion=False,
)

console = Console()


def get_api_url():
    """Get API URL from environment variable."""
    api_url = os.getenv("MEMORA_API_URL", "http://localhost:8080")
    return api_url.rstrip("/")


def make_api_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    timeout: float = 60.0,
) -> dict:
    """
    Make an API request with proper error handling.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path (e.g., "/api/search")
        json_data: Optional JSON payload for POST requests
        timeout: Request timeout in seconds

    Returns:
        Response data as dict

    Raises:
        typer.Exit on any error
    """
    api_url = get_api_url()
    full_url = f"{api_url}{endpoint}"

    try:
        with httpx.Client(timeout=timeout) as client:
            if method.upper() == "GET":
                response = client.get(full_url)
            elif method.upper() == "POST":
                response = client.post(full_url, json=json_data)
            else:
                console.print(f"[red]Error: Unsupported HTTP method: {method}[/red]")
                raise typer.Exit(1)

            # Check HTTP status
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Check for success field in response (if present)
            if "success" in data and not data["success"]:
                error_msg = data.get("message", "Unknown error")
                console.print(f"[red]API Error: {error_msg}[/red]")
                if "detail" in data:
                    console.print(f"[yellow]Details: {data['detail']}[/yellow]")
                raise typer.Exit(1)

            return data

    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP Error {e.response.status_code}[/red]")
        try:
            error_data = e.response.json()
            if "detail" in error_data:
                console.print(f"[red]Error: {error_data['detail']}[/red]")
            else:
                console.print(f"[red]Error: {error_data}[/red]")
        except Exception:
            console.print(f"[red]Error: {e.response.text}[/red]")
        console.print(f"[yellow]Make sure the API is running at {api_url}[/yellow]")
        raise typer.Exit(1)
    except httpx.ConnectError as e:
        console.print(f"[red]Connection Error: Failed to connect to API at {api_url}[/red]")
        console.print(f"[yellow]Make sure the API server is running[/yellow]")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        console.print(f"[red]Timeout Error: Request took too long[/red]")
        console.print(f"[yellow]Try increasing the timeout or check the API server[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    agent_id: str = typer.Argument(..., help="Agent ID to search for"),
    query: str = typer.Argument(..., help="Search query"),
    fact_type: List[str] = typer.Option(
        ["world", "agent", "opinion"],
        "--type",
        "-t",
        help="Fact types to search (world/agent/opinion)",
    ),
    thinking_budget: int = typer.Option(
        100, "--budget", "-b", help="Thinking budget for search"
    ),
    max_tokens: int = typer.Option(
        4096, "--max-tokens", help="Maximum tokens for search results"
    ),
    trace: bool = typer.Option(False, "--trace", help="Show trace information"),
):
    """
    Search memory using semantic similarity.

    Example:
        memora search alice "What did she say about AI?"
    """
    with console.status(f"[bold blue]Searching memories for {agent_id}...", spinner="dots"):
        data = make_api_request(
            method="POST",
            endpoint="/api/search",
            json_data={
                "query": query,
                "fact_type": list(fact_type),
                "agent_id": agent_id,
                "thinking_budget": thinking_budget,
                "max_tokens": max_tokens,
                "trace": trace,
            },
            timeout=60.0,
        )

    results = data.get("results", [])
    trace_data = data.get("trace")

    # Display results
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    console.print(f"\n[bold green]Found {len(results)} results:[/bold green]\n")

    for i, result in enumerate(results, 1):
        # Create a panel for each result
        score = result.get("score", 0.0)
        text = result.get("text", "")
        fact_type_val = result.get("fact_type", "unknown")
        context = result.get("context", "")
        date = result.get("date", "")

        # Color code based on fact type
        type_colors = {
            "world": "cyan",
            "agent": "magenta",
            "opinion": "yellow"
        }
        color = type_colors.get(fact_type_val, "white")

        # Build info line
        info_parts = [f"[{color}]{fact_type_val.upper()}[/{color}]"]
        if context:
            info_parts.append(f"Context: {context}")
        if date:
            info_parts.append(f"Date: {date}")
        info_parts.append(f"Score: {score:.3f}")

        info_line = " | ".join(info_parts)

        panel = Panel(
            f"{text}\n\n[dim]{info_line}[/dim]",
            title=f"[bold]Result {i}[/bold]",
            border_style=color,
            box=box.ROUNDED,
        )
        console.print(panel)

    # Show trace if requested
    if trace and trace_data:
        console.print("\n[bold blue]Trace Information:[/bold blue]")

        trace_table = Table(show_header=True, box=box.SIMPLE)
        trace_table.add_column("Metric", style="cyan")
        trace_table.add_column("Value", style="green")

        if "search_time_seconds" in trace_data:
            trace_table.add_row("Search Time", f"{trace_data['search_time_seconds']:.3f}s")
        if "total_activated" in trace_data:
            trace_table.add_row("Total Activated", str(trace_data["total_activated"]))
        if "results_returned" in trace_data:
            trace_table.add_row("Results Returned", str(trace_data["results_returned"]))

        console.print(trace_table)


@app.command()
def think(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    query: str = typer.Argument(..., help="Question to think about"),
    thinking_budget: int = typer.Option(
        50, "--budget", "-b", help="Thinking budget"
    ),
):
    """
    Think and generate an answer using agent identity and memories.

    Example:
        memora think alice "What do you think about machine learning?"
    """
    with console.status(f"[bold blue]Thinking...", spinner="dots"):
        result = make_api_request(
            method="POST",
            endpoint="/api/think",
            json_data={
                "query": query,
                "agent_id": agent_id,
                "thinking_budget": thinking_budget,
            },
            timeout=60.0,
        )

    # Display answer
    console.print(Panel(
        Markdown(result["text"]),
        title=f"[bold cyan]Answer for {agent_id}[/bold cyan]",
        border_style="cyan",
        box=box.DOUBLE,
    ))

    # Display what the answer was based on
    based_on = result.get("based_on", {})
    if based_on:
        console.print("\n[bold blue]Based on:[/bold blue]\n")

        for fact_type, facts in based_on.items():
            if facts:
                type_colors = {
                    "world": "cyan",
                    "agent": "magenta",
                    "opinion": "yellow"
                }
                color = type_colors.get(fact_type, "white")

                table = Table(
                    title=f"[{color}]{fact_type.upper()}[/{color}]",
                    show_header=True,
                    box=box.ROUNDED,
                    border_style=color,
                )
                table.add_column("Text", style="white", width=80)
                table.add_column("Score", justify="right", style="green", width=10)

                for fact in facts[:5]:  # Show top 5
                    text = fact.get("text", "")
                    score = fact.get("score", 0.0)
                    table.add_row(text, f"{score:.3f}")

                console.print(table)

    # Display new opinions formed
    new_opinions = result.get("new_opinions", [])
    if new_opinions:
        console.print("\n[bold yellow]New Opinions Formed:[/bold yellow]\n")
        for opinion in new_opinions:
            console.print(Panel(
                f"{opinion['text']}\n\n[dim]Confidence: {opinion['confidence']:.2f}[/dim]",
                border_style="yellow",
                box=box.ROUNDED,
            ))


@app.command()
def put(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    content: str = typer.Argument(..., help="Memory content to store"),
    document_id: Optional[str] = typer.Option(
        None, "--doc-id", "-d", help="Document ID (auto-generated if not provided)"
    ),
    context: Optional[str] = typer.Option(
        None, "--context", "-c", help="Context for the memory"
    ),
    use_async: bool = typer.Option(
        False, "--async", help="Use async batch put (returns immediately, processes in background)"
    ),
):
    """
    Store a memory from text input.

    Example:
        memora put alice "Alice loves machine learning and AI"
        memora put alice "Today we discussed neural networks" --context "team meeting"
        memora put alice "Important note" --async
    """
    # Generate document_id if not provided
    if not document_id:
        document_id = f"cli_put_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Prepare content
    item = {"content": content}
    if context:
        item["context"] = context

    # Choose endpoint based on async flag
    endpoint = "/api/memories/batch_async" if use_async else "/api/memories/batch"
    status_msg = "Queueing memory" if use_async else "Storing memory"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]{status_msg} for {agent_id}...", total=None)

        result = make_api_request(
            method="POST",
            endpoint=endpoint,
            json_data={
                "agent_id": agent_id,
                "items": [item],
                "document_id": document_id,
            },
            timeout=120.0,
        )
        progress.update(task, completed=True)

    # Check if the result indicates success
    if not result.get("success", False):
        console.print(Panel(
            f"[red]✗[/red] Failed to store memory\n"
            f"[dim]Error:[/dim] {result.get('message', 'Unknown error')}",
            title="[bold red]Storage Failed[/bold red]",
            border_style="red",
            box=box.ROUNDED,
        ))
        raise typer.Exit(1)

    # Display result based on async vs sync
    if use_async and result.get("queued", False):
        console.print(Panel(
            f"[green]✓[/green] Memory queued for background processing\n"
            f"[dim]Agent ID:[/dim] {agent_id}\n"
            f"[dim]Document ID:[/dim] {document_id}\n"
            f"[dim]Content length:[/dim] {len(content)} characters\n"
            f"[dim]Items queued:[/dim] {result.get('items_count', 1)}\n"
            f"[yellow]Processing in background...[/yellow]",
            title="[bold green]Memory Queued[/bold green]",
            border_style="green",
            box=box.ROUNDED,
        ))
    else:
        console.print(Panel(
            f"[green]✓[/green] Successfully stored memory\n"
            f"[dim]Agent ID:[/dim] {agent_id}\n"
            f"[dim]Document ID:[/dim] {document_id}\n"
            f"[dim]Content length:[/dim] {len(content)} characters\n"
            f"[dim]Items processed:[/dim] {result.get('items_count', 1)}",
            title="[bold green]Memory Stored[/bold green]",
            border_style="green",
            box=box.ROUNDED,
        ))


@app.command(name="put-files")
def put_files(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    path: str = typer.Argument(..., help="File or directory path"),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="Search directories recursively"
    ),
    use_async: bool = typer.Option(
        False, "--async", help="Use async batch put (returns immediately, processes in background)"
    ),
):
    """
    Store memories from local files (.txt and .md only).
    Each file becomes a separate document with the filename as doc_id.

    Example:
        memora put-files alice ./documents/
        memora put-files alice meeting-notes.txt
        memora put-files alice ./documents/ --async
    """
    path_obj = Path(path)

    if not path_obj.exists():
        console.print(f"[red]Error: Path '{path}' does not exist[/red]")
        raise typer.Exit(1)

    # Collect files to process
    files_to_process = []

    if path_obj.is_file():
        if path_obj.suffix.lower() in ['.txt', '.md']:
            files_to_process.append(path_obj)
        else:
            console.print(f"[yellow]Warning: Skipping '{path}' - only .txt and .md files are supported[/yellow]")
            raise typer.Exit(0)
    else:
        # Directory - find all .txt and .md files
        pattern = "**/*" if recursive else "*"
        for ext in ['.txt', '.md']:
            files_to_process.extend(path_obj.glob(f"{pattern}{ext}"))

        if not files_to_process:
            console.print(f"[yellow]No .txt or .md files found in '{path}'[/yellow]")
            raise typer.Exit(0)

    # Display files to be processed
    console.print(f"\n[bold]Found {len(files_to_process)} files to process:[/bold]\n")

    tree = Tree(f"[bold cyan]{path}[/bold cyan]")
    for file_path in sorted(files_to_process):
        size = file_path.stat().st_size
        size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
        tree.add(f"{file_path.name} [dim]({size_str})[/dim]")
    console.print(tree)
    console.print()

    # Process files
    successful = 0
    failed = 0
    queued = 0

    # Choose endpoint based on async flag
    endpoint = "/api/memories/batch_async" if use_async else "/api/memories/batch"
    status_msg = "Queueing files" if use_async else "Processing files"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        main_task = progress.add_task(
            f"[cyan]{status_msg} for {agent_id}...",
            total=len(files_to_process)
        )

        for file_path in files_to_process:
            try:
                # Read file content
                content = file_path.read_text(encoding='utf-8')

                # Use filename (without extension) as document_id
                doc_id = file_path.stem

                # Prepare content
                item = {
                    "content": content,
                    "context": f"File: {file_path.name}"
                }

                # Store memory via API
                result = make_api_request(
                    method="POST",
                    endpoint=endpoint,
                    json_data={
                        "agent_id": agent_id,
                        "items": [item],
                        "document_id": doc_id,
                    },
                    timeout=120.0,
                )

                # Check if the result indicates success
                if not result.get("success", False):
                    raise Exception(result.get("message", "Unknown error"))

                if use_async and result.get("queued", False):
                    queued += 1
                else:
                    successful += 1
                progress.update(main_task, advance=1)

            except typer.Exit:
                # Re-raise typer.Exit to stop execution
                raise
            except Exception as e:
                console.print(f"[red]Failed to process {file_path.name}: {str(e)}[/red]")
                failed += 1
                progress.update(main_task, advance=1)

    # Summary
    console.print()
    if use_async and queued > 0:
        console.print(Panel(
            f"[green]✓[/green] Successfully queued {queued} file(s) for background processing\n"
            f"[red]✗[/red] Failed: {failed}\n"
            f"[dim]Agent ID:[/dim] {agent_id}\n"
            f"[yellow]Processing in background...[/yellow]",
            title="[bold green]Files Queued[/bold green]",
            border_style="green" if failed == 0 else "yellow",
            box=box.ROUNDED,
        ))
    elif successful > 0:
        console.print(Panel(
            f"[green]✓[/green] Successfully processed {successful} file(s)\n"
            f"[red]✗[/red] Failed: {failed}\n"
            f"[dim]Agent ID:[/dim] {agent_id}",
            title="[bold green]Files Processed[/bold green]",
            border_style="green" if failed == 0 else "yellow",
            box=box.ROUNDED,
        ))
    else:
        console.print("[red]No files were successfully processed[/red]")


@app.command()
def agents():
    """
    List all agents in the memory system.

    Example:
        memora agents
    """
    with console.status("[bold blue]Fetching agents...", spinner="dots"):
        data = make_api_request(
            method="GET",
            endpoint="/api/agents",
            timeout=30.0,
        )

    agent_list = data.get("agents", [])

    if not agent_list:
        console.print("[yellow]No agents found in the system.[/yellow]")
        return

    console.print(f"\n[bold green]Found {len(agent_list)} agent(s):[/bold green]\n")

    table = Table(show_header=True, box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="dim", width=6)
    table.add_column("Agent ID", style="cyan")

    for i, agent in enumerate(agent_list, 1):
        table.add_row(str(i), agent)

    console.print(table)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
