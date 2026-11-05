from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, HttpUrl, TypeAdapter

from app.project_schemas import Name

_http_url = TypeAdapter(HttpUrl)


def _validate_website(value: str) -> str:
    text = str(_http_url.validate_python(value))
    if len(text) > 500:
        raise ValueError("Website must be at most 500 characters")
    return text


Website = Annotated[str, AfterValidator(_validate_website)]


class VendorWrite(BaseModel):
    """Used for create and full update. company_id is rejected: it only comes from the token."""

    model_config = ConfigDict(extra="forbid")

    name: Name
    website: Website | None = None


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website: str | None
    created_at: datetime
    updated_at: datetime
