from pydantic import BaseModel, model_validator, field_validator, Field
from datetime import datetime
import re

class UserCreate(BaseModel):
    username: str = Field(alias="login")
    password: str
    repeat_password: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
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