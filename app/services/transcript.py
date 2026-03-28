import asyncio
import logging
import uuid

from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptAnalysis, TranscriptAnalysisDTO
from app.ports import LLM, TranscriptAnalysisRepository
from app.prompts import RAW_USER_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class TranscriptService:
    """Orchestrates transcript analysis using an LLM and persists results."""

    def __init__(
        self,
        llm: LLM,
        repository: TranscriptAnalysisRepository,
        max_concurrent: int = 3,
    ) -> None:
        self._llm = llm
        self._repository = repository
        self._max_concurrent = max_concurrent

    def _run_analysis(self, transcript: str) -> TranscriptAnalysis:
        """Run LLM analysis and return the result without persisting."""
        prompt = RAW_USER_PROMPT.format(transcript=transcript)
        try:
            response = self._llm.run_completion(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                dto=TranscriptAnalysisDTO,
            )
        except Exception as e:
            logger.exception("LLM analysis failed")
            raise TranscriptAnalysisError("LLM analysis failed") from e

        if response is None:
            logger.error("LLM returned an empty response")
            raise TranscriptAnalysisError("LLM returned an empty response")

        return TranscriptAnalysis(
            id=uuid.uuid4(),
            summary=response.summary,
            action_items=response.action_items,
        )

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        """Analyze a single transcript and store the result."""
        logger.info("Starting transcript analysis")
        analysis = self._run_analysis(transcript)
        self._repository.save(analysis)
        logger.info("Transcript analysis completed with id=%s", analysis.id)
        return analysis

    def get_analysis(self, analysis_id: uuid.UUID) -> TranscriptAnalysis | None:
        """Retrieve a stored transcript analysis by its ID."""
        logger.info("Fetching transcript analysis id=%s", analysis_id)
        return self._repository.get_by_id(analysis_id)

    async def analyze_batch(self, transcripts: list[str]) -> list[TranscriptAnalysis]:
        """Analyze multiple transcripts concurrently. Persists only if all succeed."""
        logger.info(
            "Starting batch transcript analysis for %d transcripts", len(transcripts)
        )
        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def run_one(transcript: str) -> TranscriptAnalysis:
            async with semaphore:
                return await asyncio.to_thread(self._run_analysis, transcript)

        tasks = [run_one(t) for t in transcripts]
        analyses = list(await asyncio.gather(*tasks))

        for analysis in analyses:
            self._repository.save(analysis)

        logger.info(
            "Batch transcript analysis completed with %d analyses", len(analyses)
        )
        return analyses
