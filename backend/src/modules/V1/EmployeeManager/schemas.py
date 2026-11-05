from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.project_schemas import Name, NormalizedEmail


class EmployeeWrite(BaseModel):
    """Used for create and full update. company_id is rejected: it only comes from the token."""

    model_config = ConfigDict(extra="forbid")

    full_name: Name
    email: NormalizedEmail


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime
