import typer
from rich import print
from pathlib import Path
from datetime import datetime
from requests import HTTPError
import json
from importlib.metadata import version

from ragstrap.util.github import parse_github_repo
from ragstrap.fetch.github import fetch_repo_recursive
from ragstrap.index.generate import generate_index
from ragstrap.cli_detect.rust import is_rust_cli
from ragstrap.cli_capture.rust import cargo_build, capture_help
from ragstrap.cli_capture.policy import should_auto_capture_cli
from ragstrap.fetch.github_archive import download_repo_archive

app = typer.Typer(
    help="ragstrap — bootstrap authoritative references for external tools",
    add_completion=False,
)


def _version_callback(value: bool):
    if value:
        print(version("ragstrap"))
        raise typer.Exit()


@app.command()
def fetch(
    source: str,
    name: str | None = typer.Option(None, "--name", "-n"),
    force: bool = typer.Option(False, "--force", "-f"),
    capture_cli: bool | None = typer.Option(
        None,
        "--capture-cli/--no-capture-cli",
        help="Capture CLI --help output (auto by default when safe)",
    ),
):
    """
    Fetch and build a local reference for a library.
    """

    owner, repo = parse_github_repo(source)
    ref_name = name or repo

    base = Path("references") / ref_name
    raw = base / "raw"

    if base.exists() and not force:
        raise typer.Abort(f"Reference '{ref_name}' already exists (use --force)")

    raw.mkdir(parents=True, exist_ok=True)

    print(f"[bold]Fetching {owner}/{repo}[/bold]")

    print("[bold]Downloading repository archive[/bold]")
    download_repo_archive(owner, repo, raw)

    meta = {
        "name": ref_name,
        "source": source,
        "owner": owner,
        "repo": repo,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "ragstrap_version": version("ragstrap"),
    }

    (base / "meta.json").write_text(json.dumps(meta, indent=2))

    generate_index(base)
    print("[green]Index generated[/green]")

    do_capture = capture_cli is True or (
        capture_cli is None and should_auto_capture_cli(raw)
    )

    if do_capture:
        print("[bold]Capturing CLI help output[/bold]")
        binary = cargo_build(raw)
        capture_help(binary, base / "cli")
        print("[green]CLI help captured[/green]")
    else:
        print("[dim]Skipping CLI help capture[/dim]")

    print("[green]Done[/green]")


@app.command()
def update(name: str):
    """
    Update an existing reference.
    """
    print(f"[bold]ragstrap update[/bold] {name}")


@app.command()
def list():
    """
    List available references.
    """
    print("[bold]ragstrap list[/bold]")


@app.command()
def info(name: str):
    """
    Show metadata about a reference.
    """
    print(f"[bold]ragstrap info[/bold] {name}")


@app.callback()
def callback(
    version_flag: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    pass


def main():
    app()
