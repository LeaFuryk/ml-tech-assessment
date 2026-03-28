import uuid

import pytest
import pydantic

from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptAnalysis, TranscriptAnalysisDTO
from app.ports.llm import LLM
from app.ports.transcript_analysis_repository import TranscriptAnalysisRepository
from app.services.transcript import TranscriptService


class FakeLLM(LLM):
    def __init__(self, response=None, error=None, fail_on_call=None):
        self._response = response
        self._error = error
        self._fail_on_call = fail_on_call
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
        if self._fail_on_call is not None and self.call_count >= self._fail_on_call:
            raise RuntimeError("API failed mid-batch")
        return self._response


class FakeRepository(TranscriptAnalysisRepository):
    def __init__(self):
        self._storage: dict[uuid.UUID, TranscriptAnalysis] = {}
        self.save_count = 0

    def save(self, analysis: TranscriptAnalysis) -> None:
        self._storage[analysis.id] = analysis
        self.save_count += 1

    def get_by_id(self, analysis_id: uuid.UUID) -> TranscriptAnalysis | None:
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
    assert service.get_analysis(uuid.uuid4()) is None


def test_analyze_does_not_persist_when_llm_returns_none(repository):
    llm = FakeLLM(response=None)
    service = TranscriptService(llm, repository)

    with pytest.raises(TranscriptAnalysisError):
        service.analyze("Some transcript")

    assert repository.save_count == 0


@pytest.mark.asyncio
async def test_analyze_batch_returns_correct_number_of_results(service):
    results = await service.analyze_batch(["Text 1", "Text 2", "Text 3"])
    assert len(results) == 3


@pytest.mark.asyncio
async def test_analyze_batch_generates_unique_ids(service):
    results = await service.analyze_batch(["Text 1", "Text 2", "Text 3"])
    ids = [r.id for r in results]
    assert len(set(ids)) == 3


@pytest.mark.asyncio
async def test_analyze_batch_persists_all_results(service, repository):
    results = await service.analyze_batch(["Text 1", "Text 2"])
    assert repository.save_count == 2
    for result in results:
        assert repository.get_by_id(result.id) is not None


@pytest.mark.asyncio
async def test_analyze_batch_single_transcript(service):
    results = await service.analyze_batch(["Only one"])
    assert len(results) == 1


@pytest.mark.asyncio
async def test_analyze_batch_propagates_llm_failure(repository):
    llm = FakeLLM(error=RuntimeError("API down"))
    service = TranscriptService(llm, repository)

    with pytest.raises(TranscriptAnalysisError):
        await service.analyze_batch(["Text 1", "Text 2"])


@pytest.mark.asyncio
async def test_analyze_batch_calls_llm_once_per_transcript(service, llm):
    await service.analyze_batch(["Text 1", "Text 2", "Text 3"])
    assert llm.call_count == 3


@pytest.mark.asyncio
async def test_analyze_batch_does_not_persist_when_mid_batch_fails(repository):
    llm = FakeLLM(response=_default_dto(), fail_on_call=2)
    service = TranscriptService(llm, repository)

    with pytest.raises(TranscriptAnalysisError):
        await service.analyze_batch(["Text 1", "Text 2", "Text 3"])

    assert repository.save_count == 0
