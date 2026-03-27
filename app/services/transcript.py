import uuid

from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptAnalysis, TranscriptAnalysisDTO
from app.ports import LLM, TranscriptAnalysisRepository
from app.prompts import RAW_USER_PROMPT, SYSTEM_PROMPT


class TranscriptService:
    def __init__(self, llm: LLM, repository: TranscriptAnalysisRepository) -> None:
        self.llm = llm
        self.repository = repository

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        prompt = RAW_USER_PROMPT.format(transcript=transcript)
        try:
            response = self.llm.run_completion(
                system_prompt=SYSTEM_PROMPT, user_prompt=prompt, dto=TranscriptAnalysisDTO
            )
        except Exception as e:
            raise TranscriptAnalysisError("LLM analysis failed") from e

        if response is None:
            raise TranscriptAnalysisError("LLM returned an empty response")

        analysis = TranscriptAnalysis(
            id=str(uuid.uuid4()),
            summary=response.summary,
            action_items=response.action_items,
        )

        self.repository.save(analysis)
        return analysis

    def get_analysis(self, analysis_id: str) -> TranscriptAnalysis | None:
        return self.repository.get_by_id(analysis_id)
