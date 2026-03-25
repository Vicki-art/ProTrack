from fastapi import status


class AppException(Exception):
    def __init__(self, detail: str, status_code: int, public_detail: str | None = None):
        self.detail = detail
        self.public_detail = public_detail or detail
        self.status_code = status_code


class InvalidCredentialsError(AppException):
    def __init__(self, detail="Could not validate credentials"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)
        self.headers = {"WWW-Authenticate": "Bearer"}


class NotFoundError(AppException):
    def __init__(self, detail="Not Found"):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class ForbiddenActionError(AppException):
    def __init__(self, detail="Forbidden"):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)


class DataConflictError(AppException):
    def __init__(self, detail="Conflict error"):
        super().__init__(detail, status.HTTP_409_CONFLICT)


class DatabaseError(AppException):
    def __init__(self, detail="Internal server error"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            public_detail="Internal server error"
        )
