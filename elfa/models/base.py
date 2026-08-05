"""Shared base for response models."""

from pydantic import BaseModel, ConfigDict


class ElfaModel(BaseModel):
    """Base model: accepts camelCase aliases, tolerates unknown/new fields."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")
