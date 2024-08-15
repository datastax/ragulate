from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from ragulate.datasets import BaseDataset


class Step(BaseModel):
    """Step of a recipe."""

    name: str
    script: str
    method: str


class Recipe(BaseModel):
    """Recipe object."""

    name: str
    ingest: Step | None
    query: Step
    cleanup: Step | None
    ingredients: dict[str, Any]


class Config(BaseModel):
    """Config object."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    recipes: dict[str, Recipe] = {}
    datasets: dict[str, BaseDataset] = {}
