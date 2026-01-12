import json
import shutil
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import typer
from requests import HTTPError
from rich import print

from ragstrap.cli_capture.policy import should_auto_capture_cli
from ragstrap.cli_capture.rust import capture_help, cargo_build
from ragstrap.cli_detect.rust import is_rust_cli
from ragstrap.examples.harvest import harvest_examples
from ragstrap.fetch.github import fetch_repo_recursive
from ragstrap.fetch.github_archive import download_repo_archive
from ragstrap.index.generate import generate_index
from ragstrap.util.github import parse_github_repo

app = typer.Typer(
    help="ragstrap — bootstrap authoritative references for external tools",
    add_completion=False,
)


def _load_meta(reference_dir: Path, name: str) -> dict:
    meta_path = reference_dir / "meta.json"
    if not meta_path.exists():
        raise typer.Abort(f"Reference '{name}' is missing meta.json")
    try:
        return json.loads(meta_path.read_text())
    except json.JSONDecodeError as exc:
        raise typer.Abort(f"Invalid meta.json for '{name}': {exc}") from exc


def _read_meta_optional(reference_dir: Path) -> dict | None:
    meta_path = reference_dir / "meta.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        return None


def _format_optional_list(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        items = [str(item) for item in value if item]
        return ", ".join(items) if items else None
    return str(value)


def _reset_dir(path: Path):
    _remove_path(path)
    path.mkdir(parents=True, exist_ok=True)


def _remove_path(path: Path):
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


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

    examples_dir = base / "examples"
    harvest_examples(raw, examples_dir)
    print("[green]Examples harvested[/green]")

    print("[green]Done[/green]")


@app.command()
def update(
    name: str,
    capture_cli: bool | None = typer.Option(
        None,
        "--capture-cli/--no-capture-cli",
        help="Capture CLI --help output (auto by default when safe)",
    ),
):
    """
    Update an existing reference.
    """
    base = Path("references") / name
    if not base.exists():
        raise typer.Abort(f"Reference '{name}' not found")
    if not base.is_dir():
        raise typer.Abort(f"Reference '{name}' is not a directory")

    meta = _load_meta(base, name)
    source = meta.get("source")
    owner = meta.get("owner")
    repo = meta.get("repo")

    if source and (not owner or not repo):
        try:
            owner, repo = parse_github_repo(source)
        except ValueError as exc:
            raise typer.Abort(str(exc)) from exc

    if not owner or not repo:
        raise typer.Abort(f"Reference '{name}' is missing owner/repo metadata")

    raw = base / "raw"
    _reset_dir(raw)

    print(f"[bold]Updating {owner}/{repo}[/bold]")
    print("[bold]Downloading repository archive[/bold]")
    download_repo_archive(owner, repo, raw)

    meta["owner"] = owner
    meta["repo"] = repo
    if source:
        meta["source"] = source
    meta["fetched_at"] = datetime.utcnow().isoformat() + "Z"
    meta["ragstrap_version"] = version("ragstrap")

    (base / "meta.json").write_text(json.dumps(meta, indent=2))

    generate_index(base)
    print("[green]Index generated[/green]")

    do_capture = capture_cli is True or (
        capture_cli is None and should_auto_capture_cli(raw)
    )

    cli_dir = base / "cli"
    if do_capture:
        print("[bold]Capturing CLI help output[/bold]")
        binary = cargo_build(raw)
        capture_help(binary, cli_dir)
        print("[green]CLI help captured[/green]")
    else:
        _remove_path(cli_dir)
        print("[dim]Skipping CLI help capture[/dim]")

    examples_dir = base / "examples"
    harvest_examples(raw, examples_dir)
    print("[green]Examples harvested[/green]")

    print("[green]Done[/green]")


@app.command()
def list(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON",
    ),
):
    """
    List available references.
    """
    base = Path("references")
    if not base.exists():
        if json_output:
            print("[]")
        else:
            print("[dim]No references found[/dim]")
        return
    if not base.is_dir():
        raise typer.Abort("'references' exists but is not a directory")

    refs = sorted(
        (p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.name.lower(),
    )

    if not refs:
        if json_output:
            print("[]")
        else:
            print("[dim]No references found[/dim]")
        return

    if json_output:
        payload = []
        for ref in refs:
            meta = _read_meta_optional(ref)
            payload.append(
                {
                    "name": meta.get("name", ref.name) if meta else ref.name,
                    "directory": ref.name,
                    "path": str(ref),
                    "meta": meta,
                }
            )
        print(json.dumps(payload, indent=2))
        return

    for ref in refs:
        meta = _read_meta_optional(ref)
        display_name = meta.get("name", ref.name) if meta else ref.name
        details: list[str] = []
        if meta:
            source = meta.get("source")
            if source:
                details.append(source)
            language = meta.get("language")
            if language:
                details.append(language)
        if details:
            print(f"- {display_name} — {', '.join(details)}")
        else:
            print(f"- {display_name}")


@app.command()
def info(
    name: str,
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON",
    ),
):
    """
    Show metadata about a reference.
    """
    base = Path("references") / name
    if not base.exists():
        raise typer.Abort(f"Reference '{name}' not found")
    if not base.is_dir():
        raise typer.Abort(f"Reference '{name}' is not a directory")

    meta = _load_meta(base, name)

    if json_output:
        payload = {
            "name": meta.get("name", name),
            "directory": name,
            "path": str(base),
            "meta": meta,
        }
        print(json.dumps(payload, indent=2))
        return

    print(f"[bold]{meta.get('name', name)}[/bold]")
    print(f"Path: {base}")
    source = meta.get("source")
    if source:
        print(f"Source: {source}")

    owner = meta.get("owner")
    repo = meta.get("repo")
    if owner and repo:
        print(f"Repo: {owner}/{repo}")

    fetched_at = meta.get("fetched_at")
    if fetched_at:
        print(f"Fetched at: {fetched_at}")

    ragstrap_version = meta.get("ragstrap_version")
    if ragstrap_version:
        print(f"Ragstrap version: {ragstrap_version}")

    language = meta.get("language")
    if language:
        print(f"Language: {language}")

    secondary_languages = _format_optional_list(meta.get("secondary_languages"))
    if secondary_languages:
        print(f"Secondary languages: {secondary_languages}")


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
