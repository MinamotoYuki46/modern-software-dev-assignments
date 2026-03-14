from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class NoteCreate(BaseModel):
    title: str = Field(...)
    content: str = Field(...)

    @field_validator("title", "content", mode="before")
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("title", "content")
    def not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("must not be empty or whitespace")
        return v


class TagRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class NotePatch(BaseModel):
    title: str | None = None
    content: str | None = None


class ActionItemCreate(BaseModel):
    description: str = Field(...)

    @field_validator("description", mode="before")
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("description")
    def not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("must not be empty or whitespace")
        return v


class ActionItemRead(BaseModel):
    id: int
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    name: str = Field(...)

    @field_validator("name", mode="before")
    def strip_lower(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("name")
    def not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("must not be empty or whitespace")
        return v


class ActionItemPatch(BaseModel):
    description: str | None = None
    completed: bool | None = None


