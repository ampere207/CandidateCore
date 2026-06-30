from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions.custom_exceptions import (
    CandidateCoreException,
    ProjectionException,
    ValidationException,
    AdapterException,
    MergeException,
    PipelineException,
    NormalizationException
)
from app.logging.logger import logger

def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom exception middleware handlers on the FastAPI application.
    Enforces unified API error response formatting and mappings.
    """

    @app.exception_handler(CandidateCoreException)
    async def candidate_core_exception_handler(request: Request, exc: CandidateCoreException):
        # 1. Determine HTTP status code based on error type
        if isinstance(exc, (ProjectionException, ValidationException)):
            status_code = 400  # Bad Request
        else:
            status_code = 422  # Unprocessable Entity

        record = {
            "error_type": exc.__class__.__name__,
            "details": exc.details,
            "path": request.url.path,
            "status_code": status_code
        }
        
        logger.warning(
            f"Pipeline operation warning: {exc.message} (Status Code: {status_code})", 
            extra={"extra_context": record}
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(
            f"Unhandled exception panic on route {request.url.path}", 
            exc_info=exc
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "InternalServerError",
                "message": "A critical system error occurred. Please contact backend engineering."
            }
        )
