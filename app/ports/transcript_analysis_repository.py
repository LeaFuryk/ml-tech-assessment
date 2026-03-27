from abc import ABC, abstractmethod
from app.domain.models import TranscriptAnalysis


class TranscriptAnalysisRepository(ABC):
    @abstractmethod
    def save(self, analysis: TranscriptAnalysis) -> None:
        pass

    @abstractmethod
    def get_by_id(self, analysis_id: str) -> TranscriptAnalysis | None:
        pass
