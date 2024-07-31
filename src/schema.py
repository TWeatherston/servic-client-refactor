from datetime import datetime
import json

from pydantic import BaseModel, Field, field_validator


class FileType(BaseModel):
    feed_identifier: str
    feed_version: int
    json_schema: str
    active: bool
    storage_backend: str
    flow_name: str


class PaginatedResponse(BaseModel):
    items: list
    page: int
    pages: int
    per_page: int


class PageOfClaims(PaginatedResponse):
    claims: list = Field(..., alias="items")


class Organisation(BaseModel):
    id: int
    host_name: str
    verbose_name: str


class PageOfOrganisations(PaginatedResponse):
    items: list[Organisation]


class SignedURL(BaseModel):
    fields: dict
    file_path: str
    signed_url: str


class FileRecord(BaseModel):
    feed_identifier: str
    feed_version: int
    file_location: str
    catalogued_time: datetime
    posted_by: str
    organisation: str
    file_meta: dict

    @field_validator("file_meta", mode="before")
    def validate_file_meta(cls, v):
        if isinstance(v, str):
            return json.loads(v.replace("'", '"'))
        return v
