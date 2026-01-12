import subprocess
from pathlib import Path


def cargo_build(raw: Path) -> Path:
    """
    Build the Rust binary and return path to executable.
    """
    subprocess.run(
        ["cargo", "build", "--release"],
        cwd=raw,
        check=True,
    )

    target = raw / "target" / "release"
    bins = [p for p in target.iterdir() if p.is_file() and p.stat().st_mode & 0o111]

    if not bins:
        raise RuntimeError("No executable produced by cargo build")

    return bins[0]

def capture_help(binary: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    def run_help(args: list[str], name: str):
        result = subprocess.run(
            [binary, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,  # help often exits non-zero
        )
        (out_dir / f"{name}.help.txt").write_text(result.stdout)

    # Root help
    run_help(["--help"], "root")

    # Discover subcommands by parsing root help (lightly)
    root_text = (out_dir / "root.help.txt").read_text()

    subcommands = []
    for line in root_text.splitlines():
        if line.startswith("  ") and line.strip() and " " not in line.strip():
            subcommands.append(line.strip())

    for cmd in subcommands:
        run_help([cmd, "--help"], cmd)

