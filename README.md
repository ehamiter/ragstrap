# ragstrap

ragstrap is a CLI that builds local reference snapshots from GitHub repositories for
RAG workflows. It downloads the repo archive into a `references/<name>/raw` folder,
records metadata, generates an `index.md`, and can optionally capture `--help` output
for Rust CLIs.

## Install (preferred)

```sh
uv tool install ragstrap
```

## Install from source

```sh
git clone https://github.com/erichamiter/ragstrap.git
cd ragstrap
uv tool install -e .
```

## Usage

```sh
ragstrap fetch https://github.com/OWNER/REPO
```

Common flags:

- `--name/-n`: Name the reference directory (defaults to the repo name).
- `--force/-f`: Overwrite an existing reference directory.
- `--capture-cli/--no-capture-cli`: Capture CLI help output; auto-enabled for Rust
  CLIs when `Cargo.toml` and a `src/main.rs` (or `[[bin]]`) are present.

## Output layout

```text
references/<name>/
  meta.json
  index.md
  raw/...
  cli/ (optional help output)
```

## Notes

- Python >= 3.9 is required.
- GitHub API rate limits apply; set `GITHUB_TOKEN` to increase the limit.
- CLI capture for Rust runs `cargo build --release` and requires a Rust toolchain.
