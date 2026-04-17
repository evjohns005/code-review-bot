"""GitHub API client for fetching PR diffs and posting review comments."""

import httpx
from system.logs import logger


async def fetch_pr_diff(repo: str, pr_number: int, token: str) -> str:
    """Fetch the unified diff for a pull request via GitHub API."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        logger.info("diff_fetched", repo=repo, pr_number=pr_number, bytes=len(response.text))
        return response.text
