import uuid
from abc import ABC, abstractmethod

from app.domain.models import TranscriptAnalysis


class TranscriptAnalysisRepository(ABC):
    """Port defining the contract for transcript analysis persistence."""

    @abstractmethod
    def save(self, analysis: TranscriptAnalysis) -> None:
        """Persist a transcript analysis."""
        pass

    @abstractmethod
    def get_by_id(self, analysis_id: uuid.UUID) -> TranscriptAnalysis | None:
        """Retrieve a transcript analysis by ID, or None if not found."""
        pass
