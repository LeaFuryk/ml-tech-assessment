import uuid

import pydantic

MAX_BATCH_SIZE = 10


class TranscriptAnalysisDTO(pydantic.BaseModel):
    """DTO for OpenAI structured output response."""

    summary: str
    action_items: list[str]


class TranscriptAnalysis(pydantic.BaseModel):
    """Domain model stored and returned by the API."""

    id: uuid.UUID
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


class BatchTranscriptRequest(pydantic.BaseModel):
    """Request body for batch transcript analysis."""

    transcripts: list[str]

    @pydantic.field_validator("transcripts")
    @classmethod
    def transcripts_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Transcripts list must not be empty")
        if len(v) > MAX_BATCH_SIZE:
            raise ValueError(f"Maximum {MAX_BATCH_SIZE} transcripts per batch")
        for transcript in v:
            if not transcript.strip():
                raise ValueError("Each transcript must not be empty")
        return v
