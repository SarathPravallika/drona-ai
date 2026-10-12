"""Tests for drona.content.pack_loader: loading and validating a subject pack (spec 001, User Story 2)."""

from pathlib import Path

import pytest
import yaml

from drona.content.pack_loader import PackError, load_pack

REAL_PACK = Path(__file__).parent.parent / "packs" / "agentic-ai"
PACK_META = {"slug": "test", "name": "Test pack", "version": "0.1.0", "status": "draft", "owner": "tests"}


# Builds one valid concept, with any field overridden
# Input: Concept id, plus fields to override (e.g. level=5)
# Output: A concept dict ready to write to concepts.yaml
def concept(concept_id: str, **overrides) -> dict:
    return {
        "id": concept_id,
        "title": concept_id.title(),
        "summary": f"About {concept_id}.",
        "level": 1,
        "est_minutes": 30,
        "prerequisites": [],
    } | overrides


# Writes a pack (pack.yaml + concepts.yaml) into a temporary folder
# Input: Temp folder, list of concepts, and whether to write pack.yaml
# Output: The pack folder path
def write_pack(folder: Path, concepts: list[dict] | None, with_meta: bool = True) -> Path:
    if with_meta:
        (folder / "pack.yaml").write_text(yaml.safe_dump(PACK_META))
    (folder / "concepts.yaml").write_text(yaml.safe_dump(concepts) if concepts is not None else "")
    return folder


# ── The real pack ───────────────────────────────────────────────────────────


# The real pack loads with its 5 concepts in order and the FR-003 chain
# Input: packs/agentic-ai
# Output: Asserts name, concept order and prerequisite map
def test_real_pack_loads():
    pack = load_pack(REAL_PACK)
    assert pack.name == "Agentic AI for Engineers"
    assert [c.id for c in pack.concepts] == [
        "llm-basics",
        "prompting-structured-output",
        "tool-calling",
        "agent-loop",
        "workflows-vs-agents",
    ]
    assert pack.prereq_map() == {
        "llm-basics": [],
        "prompting-structured-output": ["llm-basics"],
        "tool-calling": ["prompting-structured-output"],
        "agent-loop": ["tool-calling"],
        "workflows-vs-agents": ["agent-loop"],
    }


# ── Broken packs: each must fail with a message naming the problem ──────────


# A prerequisite that doesn't exist is rejected, naming both concepts
# Input: tool-calling needs "json-basics", which isn't in the pack
# Output: Asserts PackError mentioning tool-calling and json-basics
def test_unknown_prerequisite(tmp_path):
    folder = write_pack(tmp_path, [concept("tool-calling", prerequisites=["json-basics"])])
    with pytest.raises(PackError, match=r"tool-calling.*json-basics|json-basics.*tool-calling"):
        load_pack(folder)


# A loop is rejected, listing its members
# Input: a needs b, b needs a
# Output: Asserts PackError mentioning both a and b
def test_loop(tmp_path):
    folder = write_pack(tmp_path, [concept("a", prerequisites=["b"]), concept("b", prerequisites=["a"])])
    with pytest.raises(PackError) as error:
        load_pack(folder)
    assert "a" in str(error.value) and "b" in str(error.value)


# The same id twice is rejected, naming it
# Input: two concepts called agent-loop
# Output: Asserts PackError mentioning agent-loop
def test_duplicate_id(tmp_path):
    folder = write_pack(tmp_path, [concept("agent-loop"), concept("agent-loop")])
    with pytest.raises(PackError, match="agent-loop"):
        load_pack(folder)


# Bad or missing fields are rejected, naming the concept and the field
# Input: one concept with a missing title, level 5, 0 minutes, or a bad id
# Output: Asserts PackError mentioning the concept id and the field
@pytest.mark.parametrize(
    ("bad_concept", "concept_id", "field"),
    [
        ({k: v for k, v in concept("agent-loop").items() if k != "title"}, "agent-loop", "title"),
        (concept("agent-loop", level=5), "agent-loop", "level"),
        (concept("agent-loop", est_minutes=0), "agent-loop", "est_minutes"),
        (concept("Bad_ID"), "Bad_ID", "id"),
    ],
)
def test_bad_field(tmp_path, bad_concept, concept_id, field):
    folder = write_pack(tmp_path, [bad_concept])
    with pytest.raises(PackError) as error:
        load_pack(folder)
    assert concept_id in str(error.value) and field in str(error.value)


# A pack with no concepts is rejected
# Input: an empty concepts.yaml
# Output: Asserts PackError mentioning "empty"
def test_empty_pack(tmp_path):
    folder = write_pack(tmp_path, None)
    with pytest.raises(PackError, match="empty"):
        load_pack(folder)


# A missing pack.yaml is rejected, naming the file
# Input: a folder with only concepts.yaml
# Output: Asserts PackError mentioning pack.yaml
def test_missing_pack_yaml(tmp_path):
    folder = write_pack(tmp_path, [concept("a")], with_meta=False)
    with pytest.raises(PackError, match="pack.yaml"):
        load_pack(folder)
