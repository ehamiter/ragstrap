import requests
import tarfile
import io
import os
import sys
from pathlib import Path


def download_repo_archive(owner: str, repo: str, dest: Path):
    url = f"https://api.github.com/repos/{owner}/{repo}/tarball"

    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers, stream=True)
    
    if resp.status_code == 403:
        # Check if it's a rate limit error
        rate_limit_header = resp.headers.get("X-RateLimit-Remaining")
        if rate_limit_header == "0" or "rate limit" in resp.text.lower():
            print("GitHub API rate limit exceeded.", file=sys.stderr)
            print("Set GITHUB_TOKEN to avoid this.", file=sys.stderr)
            sys.exit(1)
    
    resp.raise_for_status()

    tar = tarfile.open(fileobj=io.BytesIO(resp.content))
    members = tar.getmembers()

    # GitHub tarballs have a single top-level folder
    root_prefix = members[0].name.split("/")[0]

    for member in members:
        if not member.isfile():
            continue

        relative = member.name.replace(root_prefix + "/", "", 1)
        if not relative:
            continue

        out = dest / relative
        out.parent.mkdir(parents=True, exist_ok=True)

        f = tar.extractfile(member)
        if f:
            out.write_bytes(f.read())
