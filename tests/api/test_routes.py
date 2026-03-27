import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptAnalysis


class FakeTranscriptService:
    def __init__(self):
        self._storage: dict[str, TranscriptAnalysis] = {}
        self._should_fail = False

    def set_failure(self, should_fail: bool):
        self._should_fail = should_fail

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        if self._should_fail:
            raise TranscriptAnalysisError("LLM analysis failed")
        analysis = TranscriptAnalysis(
            id="generated-id",
            summary="Test summary",
            action_items=["Action 1", "Action 2"],
        )
        self._storage[analysis.id] = analysis
        return analysis

    def get_analysis(self, analysis_id: str) -> TranscriptAnalysis | None:
        return self._storage.get(analysis_id)


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
    assert data["id"] == "generated-id"
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

    response = client.get("/api/v1/transcripts/generated-id")

    assert response.status_code == 200
    assert response.json()["id"] == "generated-id"


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
