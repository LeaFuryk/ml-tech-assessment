FROM python:3.12-slim AS builder

RUN pip install poetry==2.3.2

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root --no-interaction --no-ansi

COPY app/ app/

FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /app/.venv .venv
COPY --from=builder /app/app app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
