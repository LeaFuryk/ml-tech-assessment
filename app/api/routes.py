from fastapi import APIRouter, HTTPException, Request, Depends
from app.domain.models import TranscriptRequest, TranscriptAnalysis

router = APIRouter(prefix="/api/v1", tags=["Transcripts"])

def get_transcript_service(request: Request):
    service = getattr(request.app.state, "transcript_service", None)
    if service is None:
        raise HTTPException(status_code=500, detail="Transcript service not initialized")
    return service

@router.post(
    "/transcripts/analyze",
    response_model=TranscriptAnalysis,
    status_code=201,
    summary="Analyze a single transcript",
)
def analyze_transcript(body: TranscriptRequest, service=Depends(get_transcript_service)):
    return service.analyze(body.transcript)