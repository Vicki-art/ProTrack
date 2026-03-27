import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app import exceptions

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(Exception)
    async def general_exception_handler(
            request: Request,
            exc: Exception
    ) -> JSONResponse:

        logger.exception(f"Unhandled exception: {exc}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )


    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
            request: Request,
            exc: RequestValidationError
    ) -> JSONResponse:

        formatted_errors = [
            {
                "field": err["loc"][-1],
                "message": err["msg"]
            }
            for err in exc.errors()
        ]

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": formatted_errors
            }
        )


    @app.exception_handler(exceptions.AppException)
    async def application_error_handler(
            request: Request,
            exc: exceptions.AppException
    ) -> JSONResponse:

        if isinstance(exc, exceptions.DatabaseError):
            logger.error(f"Database error: {exc.detail}", exc_info=True)
        else:
            logger.warning(f"Application error: {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.public_detail},
            headers=getattr(exc, "headers", None)
        )
