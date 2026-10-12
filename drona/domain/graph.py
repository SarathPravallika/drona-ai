"""Prerequisite-graph rules: root-cause finder. Pure functions: no I/O, no LLM."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

DEFAULT_THRESHOLD = 0.7

PrereqMap = Mapping[str, Sequence[str]]  # concept id -> ids of its direct prerequisites, in pack order


@dataclass(frozen=True)
class RootCauseResult:
    root_gaps: list[str]  # weak concepts with nothing weak beneath them, deepest first
    needs_assessment: list[str]  # unscored concepts in the walk, deepest first


# Finds every concept beneath a concept (its prerequisites, their prerequisites, and so on)
# Input: Prerequisite map and a concept id
# Output: Set of concept ids beneath it (not including the concept itself)
def _beneath(prereqs: PrereqMap, concept: str) -> set[str]:
    found: set[str] = set()
    to_visit = list(prereqs[concept])
    while to_visit:
        current = to_visit.pop()
        if current not in found:
            found.add(current)
            to_visit.extend(prereqs[current])
    return found


# Works out how deep each concept sits below the target, using the longest path
# Input: Prerequisite map, target id, and the concepts beneath the target
# Output: {concept id: depth}, with the target at depth 0
def _depths(prereqs: PrereqMap, target: str, beneath: set[str]) -> dict[str, int]:
    in_scope = beneath | {target}
    depth = {target: 0}

    # Depth of one concept = 1 + the deepest concept (in scope) that lists it as a prerequisite
    def depth_of(concept: str) -> int:
        if concept not in depth:
            parents = [c for c in in_scope if concept in prereqs[c]]
            depth[concept] = 1 + max(depth_of(p) for p in parents)
        return depth[concept]

    for concept in beneath:
        depth_of(concept)
    return depth


# Says whether a concept is weak: scored, and below the threshold (unscored is never weak)
# Input: Scores, a concept id, the threshold
# Output: True if weak, False if mastered or unscored
def _is_weak(scores: Mapping[str, float], concept: str, threshold: float) -> bool:
    return concept in scores and scores[concept] < threshold


# Finds where teaching should start for a struggling concept (spec 001, FR-006 to FR-014)
# Input: Prerequisite map, mastery scores (0–1, missing = unscored), target concept, threshold
# Output: RootCauseResult with root gaps and needs-assessment, each deepest first, ties in map order
def find_root_gaps(
    prereqs: PrereqMap,
    scores: Mapping[str, float],
    target: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> RootCauseResult:
    if target not in prereqs:
        raise ValueError(f"Unknown target concept: {target!r}")

    beneath = _beneath(prereqs, target)
    in_scope = beneath | {target}
    for concept in in_scope:
        score = scores.get(concept)
        if score is not None and not 0 <= score <= 1:
            raise ValueError(f"Score for {concept!r} must be between 0 and 1, got {score}")

    if target in scores and not _is_weak(scores, target, threshold):
        return RootCauseResult(root_gaps=[], needs_assessment=[])  # target mastered: nothing to do

    depth = _depths(prereqs, target, beneath)
    map_order = {concept: i for i, concept in enumerate(prereqs)}

    def deepest_first(ids: list[str]) -> list[str]:
        return sorted(ids, key=lambda c: (-depth[c], map_order[c]))

    root_gaps = [
        c
        for c in in_scope
        if _is_weak(scores, c, threshold)
        and not any(_is_weak(scores, b, threshold) for b in _beneath(prereqs, c))
    ]
    unscored = [c for c in in_scope if c not in scores]
    return RootCauseResult(root_gaps=deepest_first(root_gaps), needs_assessment=deepest_first(unscored))
