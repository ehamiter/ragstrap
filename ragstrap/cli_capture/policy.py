from pathlib import Path

from ragstrap.cli_detect.rust import is_rust_cli


def should_auto_capture_cli(raw: Path) -> bool:
    # Only Rust for now
    if not is_rust_cli(raw):
        return False

    # Require Cargo.toml and src/main.rs
    if not (raw / "Cargo.toml").exists():
        return False

    if not (raw / "src" / "main.rs").exists():
        return False

    return True
