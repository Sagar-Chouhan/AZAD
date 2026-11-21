from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class BatchBase(BaseModel):
    batch_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9\s,.\-/_()&]+$",
    )

    centre_id: int = Field(
        ...,
        gt=0,
    )

    fy_year: str = Field(
        ...,
        pattern=r"^(\d{4}-\d{2}|[A-Za-z0-9_-]+)$",
    )

    status: int = Field(
        ...,
        ge=0,
        le=1,
    )

    @field_validator("fy_year")
    @classmethod
    def validate_fy_year(cls, value: str):
        val = value.strip()
        if not val:
            raise ValueError("Financial year is required")

        if "-" in val:
            parts = val.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start = int(parts[0])
                end = int(parts[1])
                if end != ((start + 1) % 100):
                    raise ValueError("Financial year must be like 2026-27")

        return val


class BatchCreateRequest(BatchBase):
    pass


class BatchUpdateRequest(BatchBase):
    pass


class BatchStatusUpdateRequest(BaseModel):
    status: int = Field(
        ...,
        ge=0,
        le=1,
    )


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    batch_id: int
    batch_name: str
    centre_id: int
    fy_year: str
    created_by: int
    status: int
    created_at: datetime
    updated_at: datetime


class BatchDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    batch_id: int

    batch_name: str

    state_id: Optional[int] = None
    district_id: Optional[str] = None
    block_id: Optional[int] = None

    centre_id: int
    centre_name: str

    fy_year: str

    created_by: Optional[int] = None
    created_by_name: Optional[str] = None

    status: int

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BatchParticipantResponse(BaseModel):

    participant_id: int
    participant_name: str
    email: Optional[str]
    mobile_no: Optional[str]
    enrollment_no: str


class BatchListResponse(BaseModel):
    # NOTE: this model_config was missing before - without it, Pydantic
    # can't correctly read attributes off the SQLAlchemy Row objects
    # returned by BatchRepository.get_batches, which was silently
    # dropping fields like created_by from the response.
    model_config = ConfigDict(from_attributes=True)

    batch_id: int
    batch_name: str
    # Optional now that centre_name can come back as None from the
    # outerjoin fix in repository.py (a batch whose centre couldn't be
    # resolved still needs to appear in the list).
    centre_name: Optional[str] = None
    # Location ids of the batch's centre — used to pre-select the cascade
    # on the Add Trainee form when adding a participant to this batch.
    centre_id: Optional[int] = None
    state_id: Optional[int] = None
    district_id: Optional[str] = None
    block_id: Optional[int] = None
    fy_year: str
    created_by: Optional[str] = None
    status: int
    participant_count: int
