from pydantic import AliasChoices, BaseModel, Field, field_validator


class WWWTraineeCreateRequest(BaseModel):
    enrollment_no: str = Field(..., min_length=1, max_length=100)
    participant_name: str = Field(..., min_length=1, max_length=255)

    # WWW currently does not send gender.
    # Keep it optional; if absent, LMS stores NULL/blank.
    gender: str | None = Field(default=None, max_length=50)

    # WWW sends DOB, not age.
    # LMS service calculates age automatically.
    age: int | None = Field(default=None, ge=1, le=120)

    date_of_birth: str | None = Field(
        default=None,
        max_length=20,
        validation_alias=AliasChoices(
            "date_of_birth",
            "dob",
        ),
    )

    mobile_no: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=1000)

    state_code: str | None = Field(default=None, max_length=50)
    district_code: str | None = Field(default=None, max_length=50)

    # WWW sends centre_id.
    # It is matched ONLY against centre_masters.mis_center_id.
    centre_code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices(
            "centre_id",
            "centre_code",
        ),
    )

    # WWW batch_id may be numeric or string.
    batch_id: str | None = Field(
        default=None,
        max_length=100,
    )

    # Optional because current WWW payload does not send it.
    batch_name: str | None = Field(
        default=None,
        max_length=255,
    )

    username: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
    )

    pin: str | None = Field(
        default=None,
        max_length=10,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    # Accept both images and WWW photo_url.
    images: str | None = Field(
        default=None,
        max_length=2000,
        validation_alias=AliasChoices(
            "images",
            "photo_url",
        ),
    )

    @field_validator("centre_code", mode="before")
    @classmethod
    def _coerce_centre_code(cls, value):
        if value is None:
            return value

        return str(value).strip()

    @field_validator("batch_id", mode="before")
    @classmethod
    def _coerce_batch_id(cls, value):
        if value is None:
            return None

        value = str(value).strip()
        return value or None

    @field_validator("batch_name", mode="before")
    @classmethod
    def _coerce_batch_name(cls, value):
        if value is None:
            return None

        value = str(value).strip()
        return value or None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def _coerce_dob(cls, value):
        if value is None:
            return None

        value = str(value).strip()
        return value or None

    @field_validator("gender", mode="before")
    @classmethod
    def _coerce_gender(cls, value):
        if value is None:
            return None

        value = str(value).strip()
        return value or None
