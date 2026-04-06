import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent.review import LangGraphAgent

async def main():
    with open("diff.patch", "r") as f:
        raw_diff = f.read()

    agent = LangGraphAgent()
    message = await agent._chat(raw_diff)

    if message:
        print(message.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
