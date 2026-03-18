from fastapi import Request, status
from fastapi.responses import JSONResponse
from app import exceptions


def register_exception_handlers(app):

    # GENERAL HANDLER
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

    # CUSTOMIZED HANDLERS
    @app.exception_handler(exceptions.IsNotCurrentParticipantError)
    async def not_participant_error_handler(request: Request, exc: exceptions.IsNotCurrentParticipantError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "User is not a participant"}
        )

    @app.exception_handler(exceptions.TokenExpiredError)
    async def token_expired_error_handler(request: Request, exc: exceptions.TokenExpiredError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Token expired. You need to login again"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(exceptions.InvalidTokenError)
    async def invalid_token_error_handler(request: Request, exc: exceptions.InvalidTokenError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid token. You need to login again"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(exceptions.InvalidCredentialsError)
    async def invalid_credentials_error_handler(request: Request, exc: exceptions.InvalidCredentialsError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    @app.exception_handler(exceptions.OnlyOwnerCanModifyError)
    async def only_owner_access_error_handler(request: Request, exc: exceptions.OnlyOwnerCanModifyError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Only project owner can perform this action"}
        )

    @app.exception_handler(exceptions.AccessForbiddenError)
    async def access_forbidden_error_handler(request: Request, exc: exceptions.AccessForbiddenError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "You have no access"}
        )

    @app.exception_handler(exceptions.ProjectNotFoundError)
    async def project_not_found_handler(request: Request, exc: exceptions.ProjectNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Project not found"}
        )

    @app.exception_handler(exceptions.AccessLinkInvalidError)
    async def project_access_link_invalid_error_handler(request: Request, exc: exceptions.AccessLinkInvalidError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Access link invalid"}
        )

    @app.exception_handler(exceptions.ProfileNotFoundError)
    async def profile_not_found_handler(request: Request, exc: exceptions.ProfileNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Profile not found"}
        )

    @app.exception_handler(exceptions.UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: exceptions.UserNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "User not found"}
        )

    @app.exception_handler(exceptions.UsernameAlreadyExistsError)
    async def unique_username_error_handler(request: Request, exc: exceptions.UsernameAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Username already exists"}
        )

    @app.exception_handler(exceptions.UserIsAlreadyParticipatedInProjectError)
    async def already_participant_handler(request: Request, exc: exceptions.UserIsAlreadyParticipatedInProjectError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User has already been added to the project"}
        )

    @app.exception_handler(exceptions.DuplicateParticipantError)
    async def duplicate_participant_error_handler(request: Request, exc: exceptions.DuplicateParticipantError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "This participant already added to the project"}
        )


    @app.exception_handler(exceptions.DatabaseError)
    async def database_error_handler_for_user(request: Request, exc: exceptions.DatabaseError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

