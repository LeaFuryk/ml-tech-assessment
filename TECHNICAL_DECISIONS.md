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

## Prompt Injection Defense

The transcript is raw user input injected into the LLM prompt. To mitigate prompt injection, two layers of defense are applied:

1. **System prompt instruction**: the system message explicitly tells the model to treat the transcript as raw data and not follow instructions within it. OpenAI gives system messages higher priority than user messages, making this the primary guard.
2. **Delimiter tags**: the transcript is wrapped in `<transcript>` tags to reinforce the boundary between instructions and user content.

Neither is bulletproof on its own, but together they significantly reduce the attack surface. The structured output schema (Pydantic DTO) adds a third layer by constraining the response shape regardless of what the model is tricked into generating.

## Excluded DTO Field: Confidence

A `confidence` score is a natural candidate for an LLM-powered DTO but was intentionally left out because it would be a pure passthrough — extracted from the LLM and returned to the caller without any logic acting on it.

To justify its inclusion, it would need to drive behavior: trigger a retry with a rephrased prompt when below a threshold, flag low-confidence results for human review, or filter them from batch responses. The score would also need validation (`Field(ge=0.0, le=1.0)`) since LLM self-reported confidence is not calibrated and the model can return arbitrary values.

Without this kind of downstream logic, adding a field to every layer (prompt, DTO, domain model, API response, tests) is plumbing overhead with no user-facing value.

## Testing Strategy

All tests mock the `LLM` port using a `FakeLLM` implementation, keeping the suite fast, deterministic, and free of external dependencies. The provided `test_openai.py` serves as an integration test against the real API. In a production setting, integration tests like this would be separated with a pytest marker (e.g., `@pytest.mark.integration`) to avoid running them in CI by default, since they are slow, cost money, and can flake on rate limits.
