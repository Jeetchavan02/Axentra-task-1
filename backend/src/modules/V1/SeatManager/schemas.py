from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.project_schemas import POSTGRES_INT_MAX


class SeatCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: int = Field(gt=0, le=POSTGRES_INT_MAX)


class SeatRead(BaseModel):
    id: int
    subscription_id: int
    employee_id: int
    employee_name: str
    employee_email: str
    assigned_at: datetime
