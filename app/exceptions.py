class TokenExpiredError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class ProjectNotFoundError(Exception): #Done
    pass


class UserNotFoundError(Exception): #Done
    pass


class AccessForbiddenError(Exception): #Done
    pass


class OnlyOwnerCanModifyError(Exception): #Done
    pass


class DuplicateParticipantError(Exception): #Done
    pass


class IsNotCurrentParticipantError(Exception):
    pass


class UserIsAlreadyParticipatedInProjectError(Exception):
    pass


class DatabaseError(Exception):
    pass

class ProfileNotFoundError(Exception):
    pass


class AccessLinkInvalidError(Exception):
    pass


