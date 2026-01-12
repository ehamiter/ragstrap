from pathlib import Path


def is_rust_cli(raw: Path) -> bool:
    # Strong signals only
    if (raw / "Cargo.toml").exists() and (raw / "src" / "main.rs").exists():
        return True

    # Also allow explicit [[bin]] crates
    cargo = raw / "Cargo.toml"
    if cargo.exists():
        text = cargo.read_text(errors="ignore")
        if "[[bin]]" in text:
            return True

    return False
