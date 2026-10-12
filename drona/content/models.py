"""Subject pack models: field-level validation for pack.yaml and concepts.yaml (spec 001 data model)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Concept(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a typo like "prerequisite:" fails instead of being ignored

    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")  # lowercase slug: a-z, 0-9, -
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    level: int = Field(ge=1, le=4)
    est_minutes: int = Field(gt=0)
    prerequisites: list[str] = []


class Pack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str
    version: str
    status: Literal["draft", "approved", "retired"]
    owner: str
    concepts: list[Concept]

    # Builds the plain prerequisite map the domain rules work on
    # Input: Nothing (uses this pack's concepts)
    # Output: {concept id: [prerequisite ids]}, in pack order
    def prereq_map(self) -> dict[str, list[str]]:
        return {c.id: list(c.prerequisites) for c in self.concepts}
