from pathlib import Path


def _has_xcode_project(raw: Path) -> bool:
    try:
        for entry in raw.iterdir():
            name = entry.name
            if name.endswith(".xcodeproj") or name.endswith(".xcworkspace"):
                return True
    except FileNotFoundError:
        return False
    return False


def detect_languages(raw: Path) -> tuple[str, list[str]]:
    """
    Detect primary and secondary languages using strong repository signals.
    Returns (primary_language, secondary_languages).
    """
    signals = {
        "python": [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
        ],
        "rust": [
            "Cargo.toml",
        ],
        "javascript": [
            "package.json",
        ],
        "typescript": [
            "tsconfig.json",
        ],
        "go": [
            "go.mod",
        ],
        "swift": [
            "Package.swift",
        ],
    }

    detected: list[str] = []

    for language, files in signals.items():
        for f in files:
            if (raw / f).exists():
                detected.append(language)
                break

    if _has_xcode_project(raw) and "swift" not in detected:
        detected.append("swift")

    if not detected:
        return "unknown", []

    primary = detected[0]
    secondary = detected[1:]

    return primary, secondary
