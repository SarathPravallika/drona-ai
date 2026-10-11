# Implementation Plan: Content Slice and Root-Cause Finder

**Branch**: `001-content-slice` (solo workflow: commits on `main`) | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-content-slice/spec.md`

## Summary

Author the "Agentic AI for Engineers" pack (5 concepts + prerequisites) as YAML files in the repo,
load it into validated Pydantic models (rejecting missing prerequisites, loops, duplicates and bad
fields), and implement the root-cause finder as a pure function over a plain prerequisite map:
it returns the root gaps (weak concepts with nothing weak beneath them) and the concepts that need
assessment. The graph algorithms (cycle detection, root-gap walk) live in `drona/domain/graph.py`
with no I/O and no LLM; the loader in `drona/content/` does file reading and calls them.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: PyYAML (`safe_load` only), Pydantic v2. Both already declared; no new dependencies.

**Storage**: YAML files in `packs/agentic-ai/` (content as code). No database in v0.

**Testing**: pytest; tests write broken packs into `tmp_path`.

**Target Platform**: local CLI (macOS/Linux)

**Project Type**: single Python package (`drona/`) + CLI

**Performance Goals**: root-gap result in < 1 s for packs up to 200 concepts (SC-003)

**Constraints**: deterministic output (SC-004); domain code pure (no I/O, no LLM: Principle I, V)

**Scale/Scope**: 5 concepts now, 20 in the full pack, ≤ 200 assumed max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design: still passing.*

| Rule | How this plan complies | Status |
|---|---|---|
| I. Rules decide, the model speaks | Root gaps and cycle checks are pure functions in `drona/domain/graph.py`; no LLM anywhere in this feature | ✅ |
| II. Human holds the wheel | No agent actions in this feature (pack changes go through review as code) | ✅ n/a |
| III. Every loop has an exit | Graph walks visit each concept at most once (visited set); cycles rejected at load time, so walks always terminate | ✅ |
| IV. Grounded or silent | Not applicable (no tutor output); the pack is the future grounding source | ✅ n/a |
| V. Test-first for domain rules | `tests/test_graph.py` written and failing before `graph.py`; covers empty, cycles, ties, boundary 0.7, diamond, unassessed | ✅ |
| LLM calls only via client.py | No LLM calls | ✅ |
| Pydantic validation | Pack files parsed into Pydantic models | ✅ |
| No agent frameworks | stdlib + PyYAML + Pydantic only | ✅ |
| No secrets | None involved | ✅ |
| Original content | Concept titles and summaries written by hand; no copied text | ✅ |
| New dependencies justified | None added | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-content-slice/
├── plan.md              # This file
├── research.md          # Phase 0: design decisions
├── data-model.md        # Phase 1: entities and validation rules
├── quickstart.md        # Phase 1: how to validate the feature
├── contracts/
│   └── python-api.md    # Phase 1: public functions and errors
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
packs/agentic-ai/
├── pack.yaml                 # slug, name, version, status, owner
└── concepts.yaml             # 5 concepts + prerequisites

drona/
├── content/
│   ├── __init__.py
│   ├── models.py             # Pydantic: Concept, Pack (field validation)
│   └── pack_loader.py        # load_pack(dir) -> Pack; PackError
└── domain/
    ├── __init__.py
    └── graph.py              # find_cycle(), find_root_gaps() -> RootCauseResult (pure, hand-written)

tests/
├── test_graph.py             # root-gap + cycle rules (written first)
└── test_pack_loader.py       # real pack loads; broken packs rejected
```

**Structure Decision**: single package, following the layout in `AGENTS.md`. Content models live in
`drona/content/models.py` (not `state/models.py`, which is for learner state). `domain/graph.py` takes
a plain `Mapping[str, Sequence[str]]` (concept id → prerequisite ids) instead of Pydantic objects, so
domain rules don't depend on the content layer and are trivial to test.

## Complexity Tracking

No constitution violations; nothing to justify.
