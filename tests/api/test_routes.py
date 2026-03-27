import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptAnalysis, MAX_BATCH_SIZE


class FakeTranscriptService:
    def __init__(self):
        self._storage: dict[str, TranscriptAnalysis] = {}
        self._should_fail = False
        self._call_count = 0

    def set_failure(self, should_fail: bool):
        self._should_fail = should_fail

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        if self._should_fail:
            raise TranscriptAnalysisError("LLM analysis failed")
        self._call_count += 1
        analysis = TranscriptAnalysis(
            id=f"generated-id-{self._call_count}",
            summary="Test summary",
            action_items=["Action 1", "Action 2"],
        )
        self._storage[analysis.id] = analysis
        return analysis

    def get_analysis(self, analysis_id: str) -> TranscriptAnalysis | None:
        return self._storage.get(analysis_id)

    async def analyze_batch(self, transcripts: list[str]) -> list[TranscriptAnalysis]:
        return [self.analyze(t) for t in transcripts]


@pytest.fixture
def fake_service():
    return FakeTranscriptService()


@pytest.fixture
def client(fake_service):
    app = FastAPI()
    app.include_router(router)
    app.state.transcript_service = fake_service
    return TestClient(app)


def test_analyze_returns_201_with_valid_transcript(client):
    response = client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": "Some transcript text"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "generated-id-1"
    assert data["summary"] == "Test summary"
    assert data["action_items"] == ["Action 1", "Action 2"]


def test_analyze_returns_422_for_empty_transcript(client):
    response = client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": ""},
    )
    assert response.status_code == 422


def test_analyze_returns_422_for_whitespace_transcript(client):
    response = client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": "   "},
    )
    assert response.status_code == 422


def test_analyze_returns_422_for_missing_transcript_field(client):
    response = client.post(
        "/api/v1/transcripts/analyze",
        json={},
    )
    assert response.status_code == 422


def test_analyze_returns_502_when_llm_fails(client, fake_service):
    fake_service.set_failure(True)

    response = client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": "Some transcript text"},
    )

    assert response.status_code == 502
    assert "LLM analysis failed" in response.json()["detail"]


def test_get_analysis_returns_200_for_existing_id(client):
    client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": "Some transcript text"},
    )

    analysis_id = client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": "Some transcript text"},
    ).json()["id"]

    response = client.get(f"/api/v1/transcripts/{analysis_id}")

    assert response.status_code == 200
    assert response.json()["id"] == analysis_id


def test_get_analysis_returns_404_for_unknown_id(client):
    response = client.get("/api/v1/transcripts/nonexistent")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"


def test_analyze_response_contains_all_expected_fields(client):
    response = client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": "Some transcript text"},
    )

    data = response.json()
    assert set(data.keys()) == {"id", "summary", "action_items"}


def test_returns_500_when_service_not_initialized():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post(
        "/api/v1/transcripts/analyze",
        json={"transcript": "Some transcript text"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Transcript service not initialized"


def test_batch_returns_201_with_list_of_analyses(client):
    response = client.post(
        "/api/v1/transcripts/analyze/batch",
        json={"transcripts": ["Text 1", "Text 2", "Text 3"]},
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3


def test_batch_results_have_expected_fields(client):
    response = client.post(
        "/api/v1/transcripts/analyze/batch",
        json={"transcripts": ["Text 1"]},
    )

    data = response.json()
    assert set(data[0].keys()) == {"id", "summary", "action_items"}


def test_batch_returns_422_for_empty_list(client):
    response = client.post(
        "/api/v1/transcripts/analyze/batch",
        json={"transcripts": []},
    )
    assert response.status_code == 422


def test_batch_returns_422_for_empty_transcript_in_list(client):
    response = client.post(
        "/api/v1/transcripts/analyze/batch",
        json={"transcripts": ["Valid text", ""]},
    )
    assert response.status_code == 422


def test_batch_returns_422_when_exceeding_max_size(client):
    transcripts = [f"Text {i}" for i in range(MAX_BATCH_SIZE + 1)]
    response = client.post(
        "/api/v1/transcripts/analyze/batch",
        json={"transcripts": transcripts},
    )
    assert response.status_code == 422


def test_batch_returns_502_when_llm_fails(client, fake_service):
    fake_service.set_failure(True)

    response = client.post(
        "/api/v1/transcripts/analyze/batch",
        json={"transcripts": ["Text 1"]},
    )

    assert response.status_code == 502
    assert "LLM analysis failed" in response.json()["detail"]


def test_batch_single_transcript(client):
    response = client.post(
        "/api/v1/transcripts/analyze/batch",
        json={"transcripts": ["Only one"]},
    )

    assert response.status_code == 201
    assert len(response.json()) == 1
