import asyncio
import logging
import uuid

from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptAnalysis, TranscriptAnalysisDTO
from app.ports import LLM, TranscriptAnalysisRepository
from app.prompts import RAW_USER_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MAX_CONCURRENT_ANALYSES = 3


class TranscriptService:
    def __init__(self, llm: LLM, repository: TranscriptAnalysisRepository) -> None:
        self.llm = llm
        self.repository = repository

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        logger.info("Starting transcript analysis")
        prompt = RAW_USER_PROMPT.format(transcript=transcript)
        try:
            response = self.llm.run_completion(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                dto=TranscriptAnalysisDTO,
            )
        except Exception as e:
            logger.exception("LLM analysis failed", exc_info=True)
            raise TranscriptAnalysisError("LLM analysis failed") from e

        if response is None:
            logger.exception("LLM returned an empty response")
            raise TranscriptAnalysisError("LLM returned an empty response")

        analysis = TranscriptAnalysis(
            id=str(uuid.uuid4()),
            summary=response.summary,
            action_items=response.action_items,
        )

        self.repository.save(analysis)
        logger.info("Transcript analysis completed with id=%s", analysis.id)
        return analysis

    def get_analysis(self, analysis_id: str) -> TranscriptAnalysis | None:
        logger.info("Fetching transcript analysis id=%s", analysis_id)
        return self.repository.get_by_id(analysis_id)

    async def analyze_batch(self, transcripts: list[str]) -> list[TranscriptAnalysis]:
        logger.info(
            "Starting batch transcript analysis for %d transcripts", len(transcripts)
        )
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)

        async def run_one(transcript: str) -> TranscriptAnalysis:
            async with semaphore:
                return await asyncio.to_thread(self.analyze, transcript)

        tasks = [run_one(t) for t in transcripts]
        analyses = list(await asyncio.gather(*tasks))
        logger.info(
            "Batch transcript analysis completed with %d analyses", len(analyses)
        )
        return analyses
