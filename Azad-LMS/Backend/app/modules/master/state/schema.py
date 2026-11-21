from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

# ==========================================================
# Create State Request
# ==========================================================


class StateCreateRequest(BaseModel):

    state_lgd_code: str | int = Field(...)
    state_code: Optional[str] = None

    state_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    status: Literal["0", "1"]

    @field_validator("state_name")
    @classmethod
    def validate_state_name(cls, value: str) -> str:

        value = " ".join(value.split())

        if not value:
            raise ValueError("State name is required")

        return value


# ==========================================================
# Update State Request
# ==========================================================


class StateUpdateRequest(BaseModel):

    state_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
    )

    status: Optional[Literal["0", "1"]] = None

    @field_validator("state_name")
    @classmethod
    def validate_state_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        value = " ".join(value.split())

        if not value:
            raise ValueError("State name cannot be empty")

        return value


# ==========================================================
# State Response
# ==========================================================


class StateResponse(BaseModel):

    id: Optional[int] = None
    state_id: Optional[int] = None
    state_code: Optional[str] = None
    state_lgd_code: str | int
    state_name: str
    status: str

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> str:
        if value is None:
            return "0"
        s = str(value).strip().lower()
        if s in ("1", "active", "true"):
            return "1"
        return "0"

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# State List Response
# ==========================================================


class StateListResponse(BaseModel):

    data: list[StateResponse]

    total: int

    page: int

    per_page: int

    total_pages: int


# ==========================================================
# Delete State Response
# ==========================================================


class DeleteStateResponse(BaseModel):

    message: str
