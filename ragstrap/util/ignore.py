DEFAULT_IGNORES = {
    ".git",
    "target",
    "node_modules",
    ".github",
}


def should_ignore(path: str) -> bool:
    parts = path.split("/")
    return any(p in DEFAULT_IGNORES for p in parts)
