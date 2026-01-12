import re
from pathlib import Path

FENCE_RE = re.compile(
    r"```(?:bash|sh|shell)?\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

SHELL_LINE_RE = re.compile(r"^\s*(\$|>|\.\/|\w)", re.MULTILINE)


def extract_shell_blocks(md_path: Path) -> list[str]:
    """
    Return fenced code blocks that look like shell / CLI usage.
    """
    text = md_path.read_text(errors="ignore")
    blocks: list[str] = []

    for match in FENCE_RE.finditer(text):
        block = match.group(1).strip()

        if SHELL_LINE_RE.search(block):
            blocks.append(block)

    return blocks
