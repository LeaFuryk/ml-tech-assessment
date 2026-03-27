from app.domain.models import TranscriptAnalysis
from app.ports.transcript_analysis_repository import TranscriptAnalysisRepository


class InMemoryTranscriptRepository(TranscriptAnalysisRepository):
    def __init__(self) -> None:
        self._storage: dict[str, TranscriptAnalysis] = {}
    
    def save(self, analysis: TranscriptAnalysis) -> None:
        self._storage[analysis.id] = analysis
    
    def get_by_id(self, analysis_id: str) -> TranscriptAnalysis | None:
        return self._storage.get(analysis_id)