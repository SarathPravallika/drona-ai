"""Loads a subject pack from YAML files and rejects broken content (spec 001, User Story 2)."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from drona.content.models import Concept, Pack
from drona.domain.graph import find_cycle


class PackError(ValueError):
    """A pack file is missing or its content is invalid. The message names the problem."""


# Reads one YAML file safely (safe_load never builds arbitrary Python objects)
# Input: Path to a .yaml file
# Output: The parsed data (dict, list or None); raises PackError if missing or not valid YAML
def _read_yaml(path: Path) -> Any:
    if not path.exists():
        raise PackError(f"Missing file: {path.name} (in {path.parent})")
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise PackError(f"{path.name} is not valid YAML: {exc}") from exc


# Turns the raw concepts.yaml list into validated Concept objects (field rules)
# Input: Parsed concepts.yaml content
# Output: List of Concepts; raises PackError naming the concept and field on the first bad one
def _parse_concepts(raw: Any) -> list[Concept]:
    if not raw:
        raise PackError("concepts.yaml is empty: a pack needs at least one concept")
    if not isinstance(raw, list):
        raise PackError("concepts.yaml must be a list of concepts")
    concepts = []
    for position, item in enumerate(raw, start=1):
        name = item.get("id", f"#{position}") if isinstance(item, dict) else f"#{position}"
        try:
            concepts.append(Concept.model_validate(item))
        except ValidationError as exc:
            problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
            raise PackError(f"Concept {name!r} is invalid: {problems}") from exc
    return concepts


# Checks rules that need the whole pack: unique ids, prerequisites exist, no loops
# Input: Validated concepts
# Output: Nothing; raises PackError naming the offending concept(s)
def _check_graph(concepts: list[Concept]) -> None:
    ids: set[str] = set()
    for c in concepts:
        if c.id in ids:
            raise PackError(f"Duplicate concept id: {c.id!r}")
        ids.add(c.id)
    for c in concepts:
        for prereq in c.prerequisites:
            if prereq not in ids:
                raise PackError(f"Concept {c.id!r} needs {prereq!r}, which isn't in the pack")
    loop = find_cycle({c.id: c.prerequisites for c in concepts})
    if loop:
        raise PackError("Prerequisite loop: " + " → ".join([*loop, loop[0]]))


# Loads and validates a subject pack folder (pack.yaml + concepts.yaml)
# Input: Path to the pack folder, e.g. packs/agentic-ai
# Output: A validated Pack; raises PackError for any missing file or broken content
def load_pack(pack_dir: Path) -> Pack:
    meta = _read_yaml(pack_dir / "pack.yaml")
    concepts = _parse_concepts(_read_yaml(pack_dir / "concepts.yaml"))
    _check_graph(concepts)
    try:
        return Pack.model_validate({**(meta or {}), "concepts": concepts})
    except ValidationError as exc:
        raise PackError(f"pack.yaml is invalid: {exc}") from exc
