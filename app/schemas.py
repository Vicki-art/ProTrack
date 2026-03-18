from pydantic import BaseModel, model_validator, field_validator, Field, EmailStr
from datetime import datetime
import re


class UserCreate(BaseModel):
    username: str = Field(alias="login", min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    repeat_password: str = Field(exclude=True)

    @field_validator("password")
    def validate_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain a number")
        return value

    @model_validator(mode="after")
    def check_password_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Passwords do not match")
        return self


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        orm_mode = True


class ProfileIn(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=254)


class ProfileOut(BaseModel):
    first_name: str | None
    last_name: str | None
    email: EmailStr | None


class LoginCredentials(BaseModel):
    login: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str | None = None

class ProjectTokenData(BaseModel):
    owner_id: str | None = None
    project_id: str | None = None

class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(max_length=5000)


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    owner: ProfileOut

class ParticipantActionResquest(BaseModel):
    user_id: int
