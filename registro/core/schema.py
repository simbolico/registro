from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from registro.models.rid import RID


class ResourceSchema(BaseModel):
    """Pure Pydantic DTO base for resources."""

    rid: RID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(frozen=True, populate_by_name=True)

