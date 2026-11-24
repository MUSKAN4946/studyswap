"""Request and response models for the StudySwap API."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class BookingRequest(BaseModel):
    """Body of POST /bookings."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"example": {"sessionId": "S1", "alias": "owl42"}},
    )

    sessionId: str = Field(min_length=1, max_length=20)
    # Fictional alias only: letters, digits, underscore, hyphen (3 to 30 chars)
    alias: str = Field(pattern=r"^[A-Za-z0-9_-]{3,30}$")


class BookingOut(BaseModel):
    """A single booking as returned by the API."""

    id: int
    sessionId: str
    alias: str
    status: str


class SessionOut(BaseModel):
    """A study session with live seat counts."""

    id: str
    title: str
    start: str
    capacity: int
    booked: int
    seatsLeft: int


class SessionDetail(SessionOut):
    """A session plus the list of confirmed bookings."""

    bookings: List[BookingOut]


class ErrorOut(BaseModel):
    """Shape of every error response."""

    error: str
    message: str