# Technical Decisions

## POST vs GET for Transcript Analysis

The assessment mentions using GET requests for transcript analysis. I chose POST because:

- GET requests should not carry a request body (RFC 7231).
- POST is semantically correct when creating a resource (the analysis).
- Transcripts can be large, exceeding URL length limits if sent as query parameters.

## Hexagonal Architecture

The codebase follows a ports and adapters pattern:

- **Ports** (`app/ports/`) define abstract interfaces (`LLM`, `TranscriptAnalysisRepository`).
- **Adapters** (`app/adapters/`) provide concrete implementations (`OpenAIAdapter`, `InMemoryTranscriptRepository`).
- **Service layer** (`app/services/`) depends only on ports, never on concrete adapters.
- **API layer** (`app/api/`) handles HTTP concerns and delegates to the service.

This separation means swapping the LLM provider or storage backend requires only a new adapter, with zero changes to the service or API layers.

## Separate DTO and Domain Model

`TranscriptAnalysisDTO` represents the shape returned by the LLM (summary + action_items). `TranscriptAnalysis` is the domain model that adds an `id` for persistence and API responses.

Keeping them separate prevents coupling the domain layer to the LLM response shape. If the LLM output changes, only the DTO and the mapping in the service need to change.

## Async Strategy for Batch Processing

The `LLM` port defines only a synchronous `run_completion` method. To achieve concurrent batch processing without modifying the provided port interface, I used `asyncio.to_thread` to run each sync call in a thread pool worker, with `asyncio.gather` to execute them in parallel.

This respects the port contract while fulfilling the requirement of handling multiple analyses simultaneously without blocking the main API thread.

## Concurrency Limits

Batch requests are bounded by two guardrails:

- **MAX_BATCH_SIZE = 10** (`app/domain/models.py`): Validates at the request model level. Prevents excessively large payloads that could overwhelm the API or cause timeouts.
- **MAX_CONCURRENT_ANALYSES = 3** (`app/services/transcript.py`): A semaphore in the service limits how many LLM calls run at the same time, reducing the risk of hitting OpenAI's API rate limits.

These are defined as module-level constants with conservative defaults. In a production environment, they would be loaded from environment variables via `EnvConfigs` (e.g., `MAX_BATCH_SIZE`, `MAX_CONCURRENT_ANALYSES` in `.env`), allowing each deployment to tune them based on the OpenAI account's rate limit tier and infrastructure capacity without code changes.

## Batch Error Handling

If any transcript in a batch fails, the entire batch fails with a 502. This all-or-nothing approach is simpler and more predictable than returning partial results, which would require a different response model and per-item error reporting.
