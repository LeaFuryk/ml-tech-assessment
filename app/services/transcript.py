import asyncio
import logging
import time
import uuid

import tiktoken

from app.domain.errors import TranscriptAnalysisError, TranscriptValidationError
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
        model: str,
        max_transcript_tokens: int,
        max_concurrent: int = 3,
    ) -> None:
        self._llm = llm
        self._repository = repository
        self._max_concurrent = max_concurrent
        self._max_transcript_tokens = max_transcript_tokens
        self._encoder = tiktoken.encoding_for_model(model)

    def _count_tokens(self, transcript: str) -> int:
        """Count tokens and reject transcripts that would exceed the model's context window."""
        token_count = len(self._encoder.encode(transcript))
        if token_count > self._max_transcript_tokens:
            raise TranscriptValidationError(
                f"Transcript exceeds token limit ({token_count} tokens, max {self._max_transcript_tokens})"
            )
        return token_count

    def _run_analysis(self, transcript: str) -> TranscriptAnalysis:
        """Run LLM analysis and return the result without persisting."""
        token_count = self._count_tokens(transcript)
        prompt = RAW_USER_PROMPT.format(transcript=transcript)
        start = time.monotonic()
        try:
            response = self._llm.run_completion(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                dto=TranscriptAnalysisDTO,
            )
        except Exception as e:
            logger.exception("LLM analysis failed")
            raise TranscriptAnalysisError("LLM analysis failed") from e

        duration = time.monotonic() - start
        logger.info(
            "LLM call completed in %.2fs, token_count=%d",
            duration,
            token_count,
        )

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
