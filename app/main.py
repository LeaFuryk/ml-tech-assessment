from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.configurations import EnvConfigs


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = EnvConfigs()
    # TODO: Add init logic
    yield


app = FastAPI(
    title="Transcript Analyzer API",
    description="Analyzes coaching transcripts and returns summaries with action items.",
    version="1.0.0",
    lifespan=lifespan,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)