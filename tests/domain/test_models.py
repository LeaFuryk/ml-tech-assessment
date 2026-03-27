import pytest
import pydantic

from app.domain.models import TranscriptRequest, BatchTranscriptRequest, MAX_BATCH_SIZE


class TestTranscriptRequest:
    def test_valid_transcript(self):
        request = TranscriptRequest(transcript="Some transcript text")
        assert request.transcript == "Some transcript text"

    def test_empty_string_raises(self):
        with pytest.raises(pydantic.ValidationError):
            TranscriptRequest(transcript="")

    def test_whitespace_only_raises(self):
        with pytest.raises(pydantic.ValidationError):
            TranscriptRequest(transcript="   ")


class TestBatchTranscriptRequest:
    def test_valid_list(self):
        request = BatchTranscriptRequest(transcripts=["Text 1", "Text 2"])
        assert len(request.transcripts) == 2

    def test_empty_list_raises(self):
        with pytest.raises(pydantic.ValidationError):
            BatchTranscriptRequest(transcripts=[])

    def test_exceeds_max_batch_size_raises(self):
        transcripts = [f"Transcript {i}" for i in range(MAX_BATCH_SIZE + 1)]
        with pytest.raises(pydantic.ValidationError, match="Maximum"):
            BatchTranscriptRequest(transcripts=transcripts)

    def test_empty_transcript_in_list_raises(self):
        with pytest.raises(
            pydantic.ValidationError, match="Each transcript must not be empty"
        ):
            BatchTranscriptRequest(transcripts=["Valid text", ""])

    def test_exactly_at_max_batch_size(self):
        transcripts = [f"Transcript {i}" for i in range(MAX_BATCH_SIZE)]
        request = BatchTranscriptRequest(transcripts=transcripts)
        assert len(request.transcripts) == MAX_BATCH_SIZE

    def test_single_transcript_in_list(self):
        request = BatchTranscriptRequest(transcripts=["Only one"])
        assert len(request.transcripts) == 1
