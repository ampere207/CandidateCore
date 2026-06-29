from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions.custom_exceptions import CandidateCoreException
from app.logging.logger import logger

def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom exception middleware handlers on the FastAPI application.
    Enforces unified API error response format.
    """

    @app.exception_handler(CandidateCoreException)
    async def candidate_core_exception_handler(request: Request, exc: CandidateCoreException):
        # Log structured error
        record = {
            "error_type": exc.__class__.__name__,
            "details": exc.details,
            "path": request.url.path
        }
        logger.warning(
            f"Pipeline operation warning: {exc.message}", 
            extra={"extra_context": record}
        )
        
        return JSONResponse(
            status_code=422,  # Unprocessable Entity
            content={
                "success": False,
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Capture trace for unhandled system panics
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
