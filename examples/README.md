# Example Requests

## Single Transcript Analysis

| File | Endpoint | Expected | Description |
|------|----------|----------|-------------|
| `single_request.json` | POST `/api/v1/transcripts/analyze` | 201 | Valid transcript |
| `single_request_empty.json` | POST `/api/v1/transcripts/analyze` | 422 | Empty transcript |
| `single_request_whitespace.json` | POST `/api/v1/transcripts/analyze` | 422 | Whitespace-only transcript |
| `single_request_missing_field.json` | POST `/api/v1/transcripts/analyze` | 422 | Missing transcript field |

## Batch Transcript Analysis

| File | Endpoint | Expected | Description |
|------|----------|----------|-------------|
| `batch_request.json` | POST `/api/v1/transcripts/analyze/batch` | 201 | Valid batch of 2 transcripts |
| `batch_request_empty_list.json` | POST `/api/v1/transcripts/analyze/batch` | 422 | Empty transcripts list |
| `batch_request_with_empty_transcript.json` | POST `/api/v1/transcripts/analyze/batch` | 422 | One valid, one empty transcript |
| `batch_request_exceeds_limit.json` | POST `/api/v1/transcripts/analyze/batch` | 422 | 11 transcripts (exceeds limit of 10) |
