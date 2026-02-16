# Repository Guidelines

## Project Structure & Module Organization
- `ragstrap/` holds the CLI implementation and supporting modules (fetchers, index generation, CLI detection/capture, utilities).
- `ragstrap/examples/` contains example scripts for harvesting references.
- `dist/` stores built artifacts (if present).
- `~/.ragstrap/references/` is the shared reference store created by `ragstrap fetch`. Override with `RAGSTRAP_HOME`.
- Top-level docs and metadata live in `README.md`, `LICENSE`, and `pyproject.toml`.

## Build, Test, and Development Commands
- `uv tool install ragstrap`: installs the published CLI from the default index (PyPI unless configured otherwise).
- `uv tool install -e .`: installs the local repo in editable mode for development.
- `ragstrap fetch https://github.com/OWNER/REPO`: builds a local reference snapshot in `~/.ragstrap/references/<name>/`.
- `ragstrap list` / `ragstrap info <name>` / `ragstrap update <name>`: manage existing references.

## Coding Style & Naming Conventions
- Python 3.9+ with type hints; 4-space indentation and PEP 8 naming (snake_case functions, PascalCase types).
- Module names are lowercase (e.g., `ragstrap/fetch/github_archive.py`).
- Prefer small, single-purpose functions and Typer commands in `ragstrap/cli.py`.
- No enforced formatter configured; keep changes consistent with existing style.

## Testing Guidelines
- No automated test suite is currently present. If you add tests, place them in a new `tests/` directory and use `pytest` naming (`test_*.py`).
- When touching critical logic (fetching, indexing, CLI capture), include a brief manual verification note in the PR (example: `ragstrap fetch https://github.com/psf/requests`).

## Commit & Pull Request Guidelines
- Agents must not run git operations beyond viewing diffs. No commits, pulls, pushes, rebases, or branch changes; the user handles all VCS actions.

## Security & Configuration Tips
- GitHub API rate limits apply; set `RAGSTRAP_GITHUB_TOKEN` for higher limits.
- Rust CLI capture builds with `cargo build --release` when a Rust CLI is detected, so a Rust toolchain must be installed.
