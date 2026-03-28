import uuid

import pytest

from app.adapters.in_memory_transcript_repository import InMemoryTranscriptRepository
from app.domain.models import TranscriptAnalysis

ID_1 = uuid.uuid4()
ID_2 = uuid.uuid4()


@pytest.fixture
def repository():
    return InMemoryTranscriptRepository()


def _make_analysis(analysis_id: uuid.UUID = ID_1) -> TranscriptAnalysis:
    return TranscriptAnalysis(
        id=analysis_id,
        summary="Test summary",
        action_items=["Action 1", "Action 2"],
    )


def test_save_and_retrieve(repository):
    analysis = _make_analysis()
    repository.save(analysis)

    result = repository.get_by_id(ID_1)
    assert result is not None
    assert result.id == ID_1
    assert result.summary == "Test summary"
    assert result.action_items == ["Action 1", "Action 2"]


def test_get_by_id_returns_none_for_unknown_id(repository):
    assert repository.get_by_id(uuid.uuid4()) is None


def test_save_overwrites_existing_entry(repository):
    original = _make_analysis()
    repository.save(original)

    updated = TranscriptAnalysis(
        id=ID_1,
        summary="Updated summary",
        action_items=["New action"],
    )
    repository.save(updated)

    result = repository.get_by_id(ID_1)
    assert result.summary == "Updated summary"
    assert result.action_items == ["New action"]


def test_multiple_analyses_stored_independently(repository):
    analysis_1 = _make_analysis(ID_1)
    analysis_2 = _make_analysis(ID_2)
    repository.save(analysis_1)
    repository.save(analysis_2)

    assert repository.get_by_id(ID_1) is not None
    assert repository.get_by_id(ID_2) is not None
    assert repository.get_by_id(ID_1).id == ID_1
    assert repository.get_by_id(ID_2).id == ID_2


def test_get_by_id_with_unknown_uuid(repository):
    assert repository.get_by_id(uuid.uuid4()) is None
