from __future__ import annotations

from sqlmodel import SQLModel, Field


class ResourceSQLMixin(SQLModel, table=False):
    """Persistence mixin: adds the `rid` primary key field."""

    rid: str = Field(primary_key=True)

