from pydantic import BaseModel, Field

class ReviewState(BaseModel):
    """State definition for the code review pipeline."""

    raw_diff: str = Field(default="", description="Raw unified diff string from GitHub.")
    chunks: list[dict] = Field(default_factory=list, description="Parsed .py file chunks with added lines and context")
    reviews: list[str] = Field(default_factory=list, description="LLM review output per chunk")
    has_issues: bool = Field(default=False, description="Whether any issues were found across all chunks")
    pr_number: int = Field(default=0, description="PR number to comment on")
    repo: str = Field(default="", description="Repository in owner/repo format")