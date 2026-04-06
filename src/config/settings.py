import os

class Settings:
    def __init__(self):
        # Application Settings
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "Code Review Bot")
        self.VERSION = os.getenv("VERSION", "1.0.0")
        self.DESCRIPTION = os.getenv("DESCRIPTION", "A bot that reviews code and provides feedback")


settings = Settings()