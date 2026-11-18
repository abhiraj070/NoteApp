from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserFields(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")

    @field_validator("name", "username", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class Register(UserFields):
    password: str = Field(min_length=8, max_length=128)


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    @field_validator("name", "username", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("name", "username", "password")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class UserOut(UserFields):
    model_config = ConfigDict(from_attributes=True)
    id: int


class NoteInput(BaseModel):
    content: str = Field(min_length=1, max_length=100000)

    @field_validator("content")
    @classmethod
    def require_content(cls, value):
        if not value.strip():
            raise ValueError("Content cannot be blank")
        return value


class NoteOut(NoteInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
