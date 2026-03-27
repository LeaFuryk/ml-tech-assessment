import pydantic


class TranscriptAnalysisDTO(pydantic.BaseModel):
    """DTO for OpenAI structured output response."""

    summary: str
    action_items: list[str]


class TranscriptAnalysis(pydantic.BaseModel):
    """Domain model stored and returned by the API."""

    id: str
    summary: str
    action_items: list[str]


class TranscriptRequest(pydantic.BaseModel):
    """Request body for single transcript analysis."""

    transcript: str

    @pydantic.field_validator("transcript")
    @classmethod
    def transcript_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transcript must not be empty")
        return v
