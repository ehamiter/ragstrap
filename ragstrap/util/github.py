from urllib.parse import urlparse


def parse_github_repo(url: str) -> tuple[str, str]:
    """
    Parse a GitHub repo URL into (owner, repo).
    """
    parsed = urlparse(url)
    if parsed.netloc != "github.com":
        raise ValueError("Only github.com URLs are supported")

    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL")

    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo
