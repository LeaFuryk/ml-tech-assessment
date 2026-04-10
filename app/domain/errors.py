class TranscriptAnalysisError(Exception):
    """Raised when transcript analysis fails due to LLM errors or empty responses."""

    pass


class TranscriptValidationError(Exception):
    """Raised when a transcript fails validation before reaching the LLM."""

    pass
