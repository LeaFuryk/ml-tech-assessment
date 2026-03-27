import pytest
import pydantic

from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptAnalysis, TranscriptAnalysisDTO
from app.ports.llm import LLM
from app.ports.transcript_analysis_repository import TranscriptAnalysisRepository
from app.services.transcript import TranscriptService


class FakeLLM(LLM):
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error
        self.last_system_prompt = None
        self.last_user_prompt = None
        self.call_count = 0

    def run_completion(
        self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]
    ) -> pydantic.BaseModel:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        self.call_count += 1
        if self._error:
            raise self._error
        return self._response


class FakeRepository(TranscriptAnalysisRepository):
    def __init__(self):
        self._storage: dict[str, TranscriptAnalysis] = {}
        self.save_count = 0

    def save(self, analysis: TranscriptAnalysis) -> None:
        self._storage[analysis.id] = analysis
        self.save_count += 1

    def get_by_id(self, analysis_id: str) -> TranscriptAnalysis | None:
        return self._storage.get(analysis_id)


def _default_dto():
    return TranscriptAnalysisDTO(
        summary="Test summary",
        action_items=["Action 1", "Action 2"],
    )


@pytest.fixture
def repository():
    return FakeRepository()


@pytest.fixture
def llm():
    return FakeLLM(response=_default_dto())


@pytest.fixture
def service(llm, repository):
    return TranscriptService(llm, repository)


def test_analyze_returns_analysis_with_expected_fields(service):
    result = service.analyze("Some transcript")

    assert result.id is not None
    assert result.summary == "Test summary"
    assert result.action_items == ["Action 1", "Action 2"]


def test_analyze_persists_result(service, repository):
    result = service.analyze("Some transcript")

    assert repository.save_count == 1
    assert repository.get_by_id(result.id) is not None


def test_analyze_formats_prompt_with_transcript(service, llm):
    service.analyze("My coaching session")

    assert "My coaching session" in llm.last_user_prompt


def test_analyze_raises_when_llm_throws(repository):
    llm = FakeLLM(error=RuntimeError("API down"))
    service = TranscriptService(llm, repository)

    with pytest.raises(TranscriptAnalysisError, match="LLM analysis failed"):
        service.analyze("Some transcript")


def test_analyze_raises_when_llm_returns_none(repository):
    llm = FakeLLM(response=None)
    service = TranscriptService(llm, repository)

    with pytest.raises(TranscriptAnalysisError, match="LLM returned an empty response"):
        service.analyze("Some transcript")


def test_analyze_does_not_persist_when_llm_fails(repository):
    llm = FakeLLM(error=RuntimeError("API down"))
    service = TranscriptService(llm, repository)

    with pytest.raises(TranscriptAnalysisError):
        service.analyze("Some transcript")

    assert repository.save_count == 0


def test_analyze_generates_unique_ids(service):
    result_1 = service.analyze("Transcript 1")
    result_2 = service.analyze("Transcript 2")

    assert result_1.id != result_2.id


def test_get_analysis_returns_stored_result(service):
    created = service.analyze("Some transcript")

    result = service.get_analysis(created.id)
    assert result is not None
    assert result.id == created.id


def test_get_analysis_returns_none_for_unknown_id(service):
    assert service.get_analysis("nonexistent") is None


def test_analyze_does_not_persist_when_llm_returns_none(repository):
    llm = FakeLLM(response=None)
    service = TranscriptService(llm, repository)

    with pytest.raises(TranscriptAnalysisError):
        service.analyze("Some transcript")

    assert repository.save_count == 0
