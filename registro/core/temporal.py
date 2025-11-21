from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field as PydField
from sqlmodel import SQLModel, Field


def _now_tz() -> datetime:
    """Timezone-aware now (UTC)."""
    return datetime.now(timezone.utc)


class TimeAwareSchema(BaseModel):
    """Pure Pydantic, bitemporal fields for value objects/DTOs."""

    valid_from: datetime = PydField(default_factory=_now_tz)
    valid_to: Optional[datetime] = None
    tx_from: datetime = PydField(default_factory=_now_tz)
    tx_to: Optional[datetime] = None


class TimeAwareMixin(SQLModel):
    """SQLModel mixin providing indexed bitemporal fields for persistence."""

    valid_from: datetime = Field(default_factory=_now_tz, index=True)
    valid_to: Optional[datetime] = Field(default=None, index=True)
    tx_from: datetime = Field(default_factory=_now_tz, index=True)
    tx_to: Optional[datetime] = Field(default=None, index=True)

