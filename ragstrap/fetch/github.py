import requests
import sys
from pathlib import Path
from typing import Iterable

GITHUB_API = "https://api.github.com"


def fetch_repo_contents(
    owner: str,
    repo: str,
    path: str = "",
) -> list[dict]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url)

    if resp.status_code == 403:
        # Check if it's a rate limit error
        rate_limit_header = resp.headers.get("X-RateLimit-Remaining")
        if rate_limit_header == "0" or "rate limit" in resp.text.lower():
            print("GitHub API rate limit exceeded.", file=sys.stderr)
            print("Set GITHUB_TOKEN to avoid this.", file=sys.stderr)
            sys.exit(1)

    resp.raise_for_status()
    return resp.json()


def download_file(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url)
    r.raise_for_status()
    dest.write_bytes(r.content)


def fetch_repo_recursive(
    owner: str,
    repo: str,
    remote_path: str,
    local_root: Path,
):
    items = fetch_repo_contents(owner, repo, remote_path)

    if isinstance(items, dict):
        # Single file
        download_file(items["download_url"], local_root / items["path"])
        return

    for item in items:
        if item["type"] == "file":
            download_file(item["download_url"], local_root / item["path"])
        elif item["type"] == "dir":
            fetch_repo_recursive(owner, repo, item["path"], local_root)
