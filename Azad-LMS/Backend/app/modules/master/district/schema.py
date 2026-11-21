from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DistrictCreateRequest(BaseModel):
    district_lgd_code: str | int = Field(...)
    district_code: str | None = None

    district_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    state_lgd_code: int = Field(
        ...,
        gt=0,
    )

    status: Literal["0", "1"] = "1"

    @field_validator("district_name")
    @classmethod
    def validate_district_name(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("District name is required")

        return value


class DistrictUpdateRequest(BaseModel):
    district_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    state_lgd_code: int = Field(
        ...,
        gt=0,
    )

    status: Literal["0", "1"]

    @field_validator("district_name")
    @classmethod
    def validate_district_name(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("District name is required")

        return value


class DistrictResponse(BaseModel):
    id: int | None = None
    district_id: int | None = None
    district_code: str | None = None
    district_lgd_code: str | None = None
    district_name: str
    state_lgd_code: int
    state_id: int | None = None
    state_name: str | None = None
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


class DistrictListResponse(BaseModel):
    data: list[DistrictResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class DeleteDistrictResponse(BaseModel):
    message: str
