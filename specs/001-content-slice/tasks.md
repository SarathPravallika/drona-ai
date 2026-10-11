---

description: "Task list for 001: content slice and root-cause finder"
---

# Tasks: Content Slice and Root-Cause Finder

**Input**: Design documents from `specs/001-content-slice/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/python-api.md

**Tests**: REQUIRED. Constitution Principle V: tests for `drona/domain/` are written and fail before the
implementation. Loader tests follow the same order.

**Organization**: grouped by user story; each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on unfinished tasks)
- **[Story]**: US1 = root-cause finder (P1), US2 = pack loading and validation (P2)
- **✍️ hand-written**: implemented by hand, with no code generation (core domain logic)

---

## Phase 1: Setup

**Purpose**: package skeleton for the new modules

- [ ] T001 Create empty package files `drona/content/__init__.py` and `drona/domain/__init__.py`

---

## Phase 2: Foundational

**Purpose**: none needed. US1 works on a plain prerequisite map (research D4), so it doesn't depend on the
pack files or loader; US2 builds those.

---

## Phase 3: User Story 1 - Find the real gap behind a struggling concept (Priority: P1) 🎯 MVP

**Goal**: given a prerequisite map, mastery scores and a target, return root gaps + needs-assessment.

**Independent Test**: `uv run pytest tests/test_graph.py -k root` passes, using hand-built maps only (no YAML).

### Tests for User Story 1 (write first, must FAIL)

- [ ] T002 [US1] Write `find_root_gaps` tests in `tests/test_graph.py` against the contract in
  `contracts/python-api.md`, using the 5-concept chain `llm-basics → prompting-structured-output →
  tool-calling → agent-loop → workflows-vs-agents` built as a dict. One test per spec US1 scenario:
  (1) 0.9/0.3/0.4/0.2 → `['prompting-structured-output']`; (2) prerequisites ≥ 0.7, target 0.2 → `['agent-loop']`;
  (3) all below 0.7 → `['llm-basics']`; (4) target ≥ 0.7 → empty `root_gaps` and empty `needs_assessment`;
  (5) branching map with two weak branches → both root gaps, deepest first, ties in map order;
  (6) score exactly 0.7 counts as mastered; (7) 0.3 → **0.9** → 0.2 → `['prompting-structured-output']`
  (walks past mastered); (8) `tool-calling` unscored → root gap `prompting-structured-output`,
  `needs_assessment == ['tool-calling']`. Edge cases: target with no prerequisites and weak → itself;
  diamond map → the shared concept appears once; depth = longest path (research D6); every concept
  beneath a weak target unscored → root gap is the target, the rest in `needs_assessment`; unknown target →
  `ValueError` naming it; score 1.5 or -0.1 → `ValueError`; custom `threshold=0.5` respected;
  same inputs twice → identical results.
- [ ] T003 [US1] Run `uv run pytest tests/test_graph.py` and confirm the tests FAIL (red: `graph.py` doesn't exist yet)

### Implementation for User Story 1

- [ ] T004 [US1] ✍️ hand-written: in `drona/domain/graph.py` implement `DEFAULT_THRESHOLD = 0.7`,
  `@dataclass(frozen=True) RootCauseResult(root_gaps: list[str], needs_assessment: list[str])` and
  `find_root_gaps(prereqs, scores, target, threshold=DEFAULT_THRESHOLD)` per research D6–D9:
  no I/O, no LLM, stdlib only
- [ ] T005 [US1] Run `uv run pytest tests/test_graph.py` until green; refactor with tests staying green

**Checkpoint**: the MVP root-cause finder works on any valid map.

---

## Phase 4: User Story 2 - Load the subject pack and catch content mistakes (Priority: P2)

**Goal**: the real pack loads into validated models; broken packs fail with messages naming the problem.

**Independent Test**: `uv run pytest tests/test_pack_loader.py tests/test_graph.py -k "cycle or pack"` passes.

### Content

- [ ] T006 [P] [US2] Create `packs/agentic-ai/pack.yaml`: `slug: agentic-ai`, `name: Agentic AI for Engineers`,
  `version: 0.1.0`, `status: draft`, `owner` (data-model.md "Pack")
- [ ] T007 [P] [US2] Create `packs/agentic-ai/concepts.yaml` with the 5 v0 concepts from data-model.md
  ("v0 concepts" table): each has `id` ("lowercase slug (a-z, 0-9, -), unique in the pack"), `title`
  ("non-empty"), `summary` ("non-empty, one or two sentences", original wording), `level` ("1–4"),
  `est_minutes` ("> 0"), `prerequisites` (the chain in FR-003)

### Tests for User Story 2 (write first, must FAIL)

- [ ] T008 [US2] Add `find_cycle` tests to `tests/test_graph.py`: empty map → `None`; the v0 chain → `None`;
  self-loop `a → a`; two-node loop; three-node loop; a loop not involving the first concept; the returned
  list contains exactly the loop's members
- [ ] T009 [P] [US2] Write `tests/test_pack_loader.py` (packs written into `tmp_path`): the real pack at
  `packs/agentic-ai` loads with 5 concepts in order and `prereq_map()` matches FR-003; then one test per
  broken case, each asserting `PackError` and that the message names the concept/field: unknown
  prerequisite, loop (message lists its members), duplicate id, missing `title`, `level: 5`,
  `est_minutes: 0`, id `Bad_ID`, empty `concepts.yaml`, missing `pack.yaml`
- [ ] T010 [US2] Run `uv run pytest` and confirm the new tests FAIL (red)

### Implementation for User Story 2

- [ ] T011 [US2] ✍️ hand-written: implement `find_cycle(prereqs) -> list[str] | None` in
  `drona/domain/graph.py` using three-colour DFS (research D5)
- [ ] T012 [P] [US2] Implement Pydantic `Concept` and `Pack` (+ `prereq_map()`) in `drona/content/models.py`
  with the constraints quoted in data-model.md: id "lowercase slug (a-z, 0-9, -)", level "1–4",
  est_minutes "> 0", status "draft | approved | retired", prerequisites default `[]`
- [ ] T013 [US2] Implement `PackError(ValueError)` and `load_pack(pack_dir: Path) -> Pack` in
  `drona/content/pack_loader.py`: `yaml.safe_load` only (research D2); wrap Pydantic errors as `PackError`
  naming the concept and field; check empty pack, duplicate ids, unknown prerequisites, then
  `find_cycle` (research D3)
- [ ] T014 [US2] Run `uv run pytest` until green

**Checkpoint**: real pack + root-cause finder work together (quickstart.md step 3).

---

## Phase 5: Polish

- [ ] T015 Run quickstart.md steps 1–4 and confirm the expected outputs
- [ ] T016 Self-review the full diff (function comments present: one line + Input + Output), run
  `uv run pytest`, commit and push

---

## Dependencies & Execution Order

- **Setup (T001)** → everything.
- **US1 (T002–T005)** depends only on Setup. MVP.
- **US2 (T006–T014)** depends on Setup; `find_cycle` (T011) shares `graph.py` with US1, so do US2 after US1
  to avoid editing the same file twice at once. The loader (T013) needs T011 and T012.
- Within each story: tests → confirm red → implementation → green (Principle V).

## Parallel Opportunities

- T006 ∥ T007 (two YAML files).
- T009 ∥ T008 (different test files); T012 ∥ T011 (different modules).

## Implementation Strategy

1. **MVP**: Setup → US1 → stop and check: the core rule works on hand-built maps.
2. **Increment**: US2 → the real pack is loaded and validated, and the finder runs on it.
3. Polish → quickstart → commit.
