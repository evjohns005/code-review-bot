import os
import structlog
from agent.prompts import load_system_prompt
from utils.diff_parser import format_for_prompt, parse_diff
from anthropic import Anthropic

logger = structlog.get_logger()

class LangGraphAgent:
    async def _chat(self, raw_diff: str):
        try:
            client = Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )

            system = load_system_prompt()
            chunks = parse_diff(raw_diff)
            user_message = format_for_prompt(chunks[0])

            message = client.messages.create(
                model="claude-sonnet-4-5",
                system=system,
                messages=[{"role": "user", "content": user_message}]
            )
            return message
        except Exception as e:
            logger.error("Failed calling model", error=str(e))
