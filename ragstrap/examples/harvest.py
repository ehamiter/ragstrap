from pathlib import Path

from ragstrap.examples.extract import extract_shell_blocks


def harvest_examples(raw: Path, out_dir: Path):
    # overwrite existing examples (authoritative snapshot)
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()

    out_dir.mkdir(parents=True, exist_ok=True)

    for md in raw.rglob("*.md"):
        blocks = extract_shell_blocks(md)
        if not blocks:
            continue

        rel = md.relative_to(raw)
        out_name = "_".join(rel.with_suffix("").parts) + ".md"
        out_path = out_dir / out_name

        lines: list[str] = []
        lines.append(f"# Examples from `{rel}`\n")

        for i, block in enumerate(blocks, 1):
            lines.append(f"## Example {i}\n")
            lines.append("```sh")
            lines.append(block)
            lines.append("```\n")

        out_path.write_text("\n".join(lines))
