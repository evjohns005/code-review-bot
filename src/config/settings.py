import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Application Settings
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "Code Review Bot")
        self.VERSION = os.getenv("VERSION", "1.0.0")
        self.DESCRIPTION = os.getenv("DESCRIPTION", "A bot that reviews code and provides feedback")

        # LangGraph Configurations
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "claude-sonnet-4-5")
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
        self.MAX_LLM_CALL_RETRIES = int(os.getenv("MAX_LLM_CALL_RETRIES", "3"))


settings = Settings()