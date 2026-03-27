from fastapi import APIRouter, HTTPException, Request, Depends
from app.domain.errors import TranscriptAnalysisError
from app.domain.models import TranscriptRequest, TranscriptAnalysis
from app.services.transcript import TranscriptService

router = APIRouter(prefix="/api/v1", tags=["Transcripts"])


def get_transcript_service(request: Request):
    service = getattr(request.app.state, "transcript_service", None)
    if service is None:
        raise HTTPException(
            status_code=500, detail="Transcript service not initialized"
        )
    return service


@router.post(
    "/transcripts/analyze",
    response_model=TranscriptAnalysis,
    status_code=201,
    summary="Analyze a single transcript",
)
def analyze_transcript(
    body: TranscriptRequest,
    service: TranscriptService = Depends(get_transcript_service),
):
    try:
        return service.analyze(body.transcript)
    except TranscriptAnalysisError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get(
    "/transcripts/{analysis_id}",
    response_model=TranscriptAnalysis,
    summary="Get analysis by ID",
)
def get_analysis(
    analysis_id: str, service: TranscriptService = Depends(get_transcript_service)
):
    analysis = service.get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis
