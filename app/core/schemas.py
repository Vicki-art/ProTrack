import re
from datetime import datetime
import pydantic as py

from app.storage.file_helpers import format_file_size


class UserCreate(py.BaseModel):
    username: str = py.Field(alias="login", min_length=2, max_length=50)
    password: str = py.Field(min_length=8, max_length=128)
    repeat_password: str = py.Field(exclude=True)

    @py.field_validator("password")
    def validate_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain a number")
        return value

    @py.model_validator(mode="after")
    def check_password_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Passwords do not match")
        return self


class UserOut(py.BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        orm_mode = True


class ProfileIn(py.BaseModel):
    first_name: str | None = py.Field(default=None, min_length=1, max_length=100)
    last_name: str | None = py.Field(default=None, min_length=1, max_length=100)
    email: py.EmailStr | None = py.Field(default=None, max_length=254)


class ProfileOut(py.BaseModel):
    first_name: str | None
    last_name: str | None
    email: py.EmailStr | None


class LoginCredentials(py.BaseModel):
    login: str
    password: str


class Token(py.BaseModel):
    access_token: str
    token_type: str


class TokenData(py.BaseModel):
    id: str | None = None


class ProjectTokenData(py.BaseModel):
    owner_id: str | None = None
    project_id: str | None = None


class ProjectIn(py.BaseModel):
    name: str = py.Field(min_length=2, max_length=255)
    description: str = py.Field(max_length=5000)


class ProjectOut(py.BaseModel):
    id: int
    name: str
    description: str
    owner: ProfileOut


class FilesOut(py.BaseModel):
    id: int
    original_filename: str
    file_key: str
    size: int
    content_type: str

    class Config:
        orm_mode = True

    @py.field_serializer("size")
    def serialize_size(self, value):
        return format_file_size(value)



class UploadDocsResponse(py.BaseModel):
    uploaded_documents: list[FilesOut]



class MessageResponse(py.BaseModel):
    message: str

