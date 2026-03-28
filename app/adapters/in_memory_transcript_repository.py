from app.domain.models import TranscriptAnalysis
from app.ports.transcript_analysis_repository import TranscriptAnalysisRepository


class InMemoryTranscriptRepository(TranscriptAnalysisRepository):
    """Dictionary-backed repository for storing transcript analyses in memory."""

    def __init__(self) -> None:
        self._storage: dict[str, TranscriptAnalysis] = {}

    def save(self, analysis: TranscriptAnalysis) -> None:
        """Persist a transcript analysis, overwriting any existing entry with the same ID."""
        self._storage[analysis.id] = analysis

    def get_by_id(self, analysis_id: str) -> TranscriptAnalysis | None:
        """Retrieve a transcript analysis by ID, or None if not found."""
        return self._storage.get(analysis_id)
