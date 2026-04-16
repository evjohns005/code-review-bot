import asyncio
import httpx

from functools import cached_property
from langgraph.graph import END, StateGraph
from langgraph.graph.state import Command, CompiledStateGraph

from data.schemas.graph import ReviewState
from system.logs import logger

from agent.prompts import load_system_prompt
from config.settings import settings
from utils.diff_parser import format_for_prompt, parse_diff
from services.llm_provider import llm_service


class LangGraphAgent:
    def __init__(self):
        self._graph: CompiledStateGraph | None = None
    

    async def _parse_diff_node(self, state: ReviewState) -> Command:
        chunks = parse_diff(state.raw_diff)
        if not chunks:
            logger.info("no_python_files_found")
            return Command(update={"chunks": []}, goto=END)
        logger.info("diff_parsed", file_count=len(chunks))
        return Command(update={"chunks": chunks}, goto="review")

    async def _review_node(self, state: ReviewState) -> Command:
        reviews = []
        for chunk in state.chunks:
            formatted_chunk = format_for_prompt(chunk)
            review = await llm_service.call(formatted_chunk)
            reviews.append(review)

        if not reviews:
            logger.info("no_reviews_generated")
            return Command(update={"reviews": [], "has_issues": False}, goto=END)

        logger.info("chunks_reviewed", count=len(reviews))
        return Command(update={"reviews": reviews, "has_issues": True}, goto="post_comment")

    async def _post_comment_node(self, state: ReviewState) -> Command:
        TOKEN = settings.GITHUB_TOKEN
        REPO = state.repo
        ISSUE_NUMBER = state.pr_number
        URL = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"

        if not state.has_issues:
            body = "✅ No issues found."
        else:
            messages = []
            for chunk, review in zip(state.chunks, state.reviews):
                file_name = chunk["file"]
                messages.append(f"### `{file_name}`\n{review}")
            body = "\n\n".join(messages)

        headers = {
            "Authorization": f"token {TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"body": body}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(URL, headers=headers, json=data)

            if response.status_code == 201:
                logger.info("Successfully posted comment to Github")
            else:
                logger.error("failed_to_post_comment", status_code=response.status_code, body=response.text)
        except Exception as e:
            logger.error("github_api_error", error=str(e))

        return Command(goto=END)

    async def create_graph(self) -> CompiledStateGraph:
        if self._graph is None:
            graph_builder = StateGraph(ReviewState)
            graph_builder.add_node("parse_diff", self._parse_diff_node)
            graph_builder.add_node("review", self._review_node)
            graph_builder.add_node("post_comment", self._post_comment_node)
            graph_builder.set_entry_point("parse_diff")
            self.graph = graph_builder.compile()
        return self._graph

    async def run(self, raw_diff: str) -> None:
        if self._graph is None:
            await self.create_graph()
        await self._graph.ainvoke({"raw_diff": raw_diff})


agent = LangGraphAgent()