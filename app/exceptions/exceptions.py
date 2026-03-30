from http import HTTPStatus


class AppException(Exception):
    """
    Parent exception class for application exceptions

    params:
        detail (str): error description for inner use
        public_detail (str): error description to show to client
        status_code (int): HTTP status code
    """
    def __init__(
            self,
            detail: str,
            status_code: int,
            public_detail: str | None = None
    ):
        self.detail = detail
        self.public_detail = public_detail or detail
        self.status_code = status_code


class InvalidCredentialsError(AppException):
    def __init__(self, detail="Could not validate credentials"):
        super().__init__(detail, HTTPStatus.UNAUTHORIZED)
        self.headers = {"WWW-Authenticate": "Bearer"}


class NotFoundError(AppException):
    def __init__(self, detail="Not Found"):
        super().__init__(detail, HTTPStatus.NOT_FOUND)


class ForbiddenActionError(AppException):
    def __init__(self, detail="Forbidden"):
        super().__init__(detail, HTTPStatus.FORBIDDEN)


class ValidationError(AppException):
    def __init__(self, detail="Validation failed"):
        super().__init__(detail, HTTPStatus.UNPROCESSABLE_ENTITY)


class DataConflictError(AppException):
    def __init__(self, detail="Conflict error"):
        super().__init__(detail, HTTPStatus.CONFLICT)


class DatabaseError(AppException):
    def __init__(self, detail="Internal server error"):
        super().__init__(
            detail=detail,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            public_detail="Internal server error"
        )
