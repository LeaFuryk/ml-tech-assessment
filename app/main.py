from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.adapters.in_memory_transcript_repository import InMemoryTranscriptRepository
from app.adapters.openai import OpenAIAdapter
from app.configurations import EnvConfigs
from app.services.transcript import TranscriptService
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = EnvConfigs()
    llm = OpenAIAdapter(config.OPENAI_API_KEY, config.OPENAI_MODEL)
    repository = InMemoryTranscriptRepository()
    transcript_service = TranscriptService(llm, repository)
    app.state.transcript_service = transcript_service
    yield


app = FastAPI(
    title="Transcript Analyzer API",
    description="Analyzes coaching transcripts and returns summaries with action items.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True)
