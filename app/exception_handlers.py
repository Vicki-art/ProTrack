from fastapi import Request, status
from fastapi.responses import JSONResponse
from app import exceptions
import logging

logger = logging.getLogger(__name__)


def register_exception_handlers(app):

    # GENERAL HANDLER
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):

        logger.exception(f"Unhandled exception: {str(exc)}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

    @app.exception_handler(exceptions.AppException)
    async def application_error_handler(request: Request, exc: exceptions.AppException):

        if isinstance(exc, exceptions.DatabaseError):
            logger.error(f"Database error: {exc.detail}", exc_info=True)
        else:
            logger.warning(f"Application error: {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.public_detail},
            headers=getattr(exc, "headers", None)
        )
