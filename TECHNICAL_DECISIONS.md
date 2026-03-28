# Technical Decisions

## POST vs GET for Transcript Analysis

The assessment mentions using GET requests for transcript analysis. I chose POST because:

- GET requests should not carry a request body (RFC 7231).
- POST is semantically correct when creating a resource (the analysis).
- Transcripts can be large, exceeding URL length limits if sent as query parameters.

## OpenAI Adapter — Not Modified

The `OpenAIAdapter` was provided as part of the assessment and marked as "do not implement." It was intentionally left unchanged. In a production setting, the adapter would handle OpenAI-specific exceptions (e.g., rate limits, authentication errors) and translate them into domain errors. The current error handling in the service layer acts as a catch-all safety net but is not a substitute for proper adapter-level error handling.

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

Batch requests are bounded by two guardrails with different configuration strategies:

- **MAX_BATCH_SIZE = 10** (`app/domain/models.py`): A hardcoded constant validated at the request model level. This is intentionally not configurable via environment variables because it is part of the API contract — Pydantic exposes it in the Swagger/OpenAPI schema. Changing it at runtime would make the documented API inaccurate.
- **MAX_CONCURRENT_ANALYSES** (`app/configurations.py`): Configurable via the `MAX_CONCURRENT_ANALYSES` environment variable (default: 3). Injected into `TranscriptService` through its constructor. This allows each deployment to tune concurrency based on the OpenAI account's rate limit tier without code changes.

## Batch Error Handling

If any transcript in a batch fails, the entire batch fails with a 502. This all-or-nothing approach is simpler and more predictable than returning partial results, which would require a different response model and per-item error reporting.
