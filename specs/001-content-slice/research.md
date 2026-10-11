# Research & Design Decisions: Content Slice and Root-Cause Finder

No open clarifications remained after the spec (Q1 and Q2 resolved). These are the design decisions.

## D1. Pack file format: YAML, two files
- **Decision**: `pack.yaml` (metadata) + `concepts.yaml` (a list of concepts with `prerequisites`).
- **Rationale**: human-readable, diff-friendly in reviews (content as code), comments allowed.
  PyYAML is already a dependency.
- **Alternatives**: JSON (no comments, noisier diffs); one file per concept (overkill for 5–20).

## D2. Parse with `yaml.safe_load`, never `yaml.load`
- **Decision**: `safe_load` only.
- **Rationale**: `yaml.load` can build arbitrary Python objects from tagged YAML, which is a code-execution
  risk if a pack file is ever untrusted (future: content owners outside the team).
- **Alternatives**: none acceptable.

## D3. Validation in two layers
- **Decision**: Pydantic validates each concept's fields (required, level 1–4, minutes > 0). The loader then
  validates the pack as a whole: non-empty, unique ids, every prerequisite exists, no cycles.
- **Rationale**: field rules are per-record (Pydantic is good at that); graph rules need the whole set.
  All failures raise one error type, `PackError`, with a message naming the concept(s).
- **Alternatives**: all checks in Pydantic model validators (mixes graph logic into models).

## D4. Graph input is a plain mapping, in pack order
- **Decision**: domain functions take `prereqs: Mapping[str, Sequence[str]]`; dict insertion order = pack
  order, used for tie-breaking.
- **Rationale**: keeps `domain/` independent of Pydantic and YAML; easy to build in tests.
- **Alternatives**: pass `Pack` objects (couples domain to the content layer).

## D5. Cycle detection: depth-first search with three colours
- **Decision**: `find_cycle(prereqs) -> list[str] | None` returns the concepts in one loop (for the error
  message), or `None`. White = unvisited, grey = on the current path, black = done; meeting a grey node
  means a loop.
- **Rationale**: standard, O(V + E), and naturally yields the loop's members.
- **Alternatives**: Kahn's topological sort (detects that a cycle exists, but naming it takes extra work).

## D6. "Depth" = longest prerequisite path from the target
- **Decision**: a concept's depth is the length of the **longest** path from the target down to it.
- **Rationale**: in a diamond (reachable by a short and a long path), the longest path reflects how
  foundational it really is. Deepest-first ordering then lists the most basic gaps first.
- **Alternatives**: shortest path (BFS distance) understates how foundational a concept is.

## D7. Root-gap rule (from spec FR-008, FR-012, FR-013)
- **Decision**: collect the target plus all concepts beneath it (walking past mastered and unassessed
  ones). Weak = score < threshold; mastered = score ≥ threshold; unassessed = no score. A root gap is a
  weak concept with no weak concept anywhere beneath it. Unassessed concepts are returned separately.
  If the target is mastered, return empty results.
- **Rationale**: matches the spec decisions; O(V·(V+E)) worst case, about 40k steps for 200 concepts, far
  under 1 s.
- **Alternatives**: a single-pass memoised walk (faster, but harder to read; not needed at this scale).

## D8. Result type: a frozen dataclass in `domain/`
- **Decision**: `RootCauseResult(root_gaps: list[str], needs_assessment: list[str])`, `frozen=True`.
- **Rationale**: stdlib only (domain stays dependency-free); immutable results are safe to share.
- **Alternatives**: Pydantic model (an unnecessary dependency in domain); a tuple (unclear fields).

## D9. Errors
- **Decision**: `PackError(ValueError)` from the loader; `ValueError` from the finder for an unknown target
  or a score outside 0–1. Scores for concepts outside the walked set are ignored.
- **Rationale**: callers can catch `ValueError` broadly or `PackError` specifically.
