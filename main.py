"""
GitHub Action entrypoint.

Reads PR context from the GitHub Actions environment, fetches the diff,
runs the LangGraph review agent, and posts a comment — then exits.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent.review import LangGraphAgent
from github.client import fetch_pr_diff
from system.logs import logger


async def main() -> None:
    # --- Gather GitHub Actions context ---
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    # PR number: prefer explicit input override, then event file
    pr_number: int | None = None
    raw_input = os.environ.get("INPUT_PR_NUMBER", "").strip()
    if raw_input.isdigit():
        pr_number = int(raw_input)

    if pr_number is None:
        event_path = os.environ.get("GITHUB_EVENT_PATH", "")
        if event_path and os.path.exists(event_path):
            with open(event_path) as f:
                event = json.load(f)
            pr_number = event.get("pull_request", {}).get("number")

    if not repo:
        logger.error("missing_env_var", var="GITHUB_REPOSITORY")
        sys.exit(1)
    if not pr_number:
        logger.error("missing_pr_number", hint="trigger on pull_request or pass pr-number input")
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.error("missing_env_var", var="GITHUB_TOKEN")
        sys.exit(1)

    logger.info("review_starting", repo=repo, pr_number=pr_number)

    # --- Fetch diff ---
    try:
        raw_diff = await fetch_pr_diff(repo, int(pr_number), token)
    except Exception as e:
        logger.error("diff_fetch_failed", error=str(e))
        sys.exit(1)

    if not raw_diff.strip():
        logger.info("empty_diff", repo=repo, pr_number=pr_number)
        sys.exit(0)

    # --- Run review agent ---
    agent = LangGraphAgent(repo=repo, pr_number=int(pr_number))
    try:
        await agent.run(raw_diff)
    except Exception as e:
        logger.error("agent_error", error=str(e))
        sys.exit(1)

    logger.info("review_complete", repo=repo, pr_number=pr_number)


if __name__ == "__main__":
    asyncio.run(main())
