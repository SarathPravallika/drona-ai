"""Tests for drona.domain.graph: root-cause finder (spec 001, User Story 1)."""

import pytest

from drona.domain import graph
from drona.domain.graph import DEFAULT_THRESHOLD, RootCauseResult, find_root_gaps

LLM, PROMPT, TOOLS, LOOP, WORKFLOWS = (
    "llm-basics",
    "prompting-structured-output",
    "tool-calling",
    "agent-loop",
    "workflows-vs-agents",
)

# v0 chain: each concept needs the one before it (spec FR-003)
CHAIN = {
    LLM: [],
    PROMPT: [LLM],
    TOOLS: [PROMPT],
    LOOP: [TOOLS],
    WORKFLOWS: [LOOP],
}


# Builds the expected result in one short call
# Input: Root gap ids, and optionally the needs-assessment ids
# Output: A RootCauseResult to compare against
def expected(root_gaps: list[str], needs_assessment: list[str] | None = None) -> RootCauseResult:
    return RootCauseResult(root_gaps=root_gaps, needs_assessment=needs_assessment or [])


# ── Spec User Story 1: acceptance scenarios ─────────────────────────────────


# Scenario 1: the deepest weak concept under the target is the root gap
# Input: Chain scores 0.9 / 0.3 / 0.4 / 0.2, target agent-loop
# Output: Asserts root gap = prompting-structured-output
def test_s1_deepest_weak_prerequisite_is_root_gap():
    scores = {LLM: 0.9, PROMPT: 0.3, TOOLS: 0.4, LOOP: 0.2}
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([PROMPT])


# Scenario 2: weak target with strong foundations is its own root gap
# Input: All prerequisites ≥ 0.7, target 0.2
# Output: Asserts root gap = agent-loop
def test_s2_target_is_root_gap_when_foundations_are_fine():
    scores = {LLM: 0.9, PROMPT: 0.8, TOOLS: 0.75, LOOP: 0.2}
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([LOOP])


# Scenario 3: when everything is weak, the very first concept is the root gap
# Input: All chain scores below 0.7
# Output: Asserts root gap = llm-basics
def test_s3_first_concept_is_root_gap_when_everything_is_weak():
    scores = {LLM: 0.5, PROMPT: 0.3, TOOLS: 0.4, LOOP: 0.2}
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([LLM])


# Scenario 4: a mastered target has nothing to fix or assess
# Input: Target 0.9, with weak and unscored concepts beneath it
# Output: Asserts empty root gaps and empty needs-assessment
def test_s4_mastered_target_has_no_gaps():
    scores = {PROMPT: 0.3, LOOP: 0.9}  # llm-basics and tool-calling unscored
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([])


# Scenario 5: two weak branches give two root gaps, deepest first
# Input: target → a (weak) → a0 (strong); target → b (strong) → b0 (weak)
# Output: Asserts root gaps = [b0 (depth 2), a (depth 1)]
def test_s5_every_root_gap_reported_deepest_first():
    prereqs = {"a0": [], "a": ["a0"], "b0": [], "b": ["b0"], "t": ["a", "b"]}
    scores = {"a0": 0.9, "a": 0.3, "b0": 0.4, "b": 0.9, "t": 0.2}
    assert find_root_gaps(prereqs, scores, "t") == expected(["b0", "a"])


# Scenario 6: a score of exactly the threshold counts as mastered
# Input: tool-calling = 0.7 exactly, target weak
# Output: Asserts root gap = agent-loop (tool-calling is not weak)
def test_s6_threshold_is_inclusive():
    scores = {LLM: 0.9, PROMPT: 0.9, TOOLS: DEFAULT_THRESHOLD, LOOP: 0.2}
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([LOOP])


# Scenario 7: the walk continues past a mastered concept (spec decision Q2 = B)
# Input: prompting 0.3 → tool-calling 0.9 → agent-loop 0.2
# Output: Asserts root gap = prompting-structured-output
def test_s7_walk_continues_past_mastered_concept():
    scores = {LLM: 0.9, PROMPT: 0.3, TOOLS: 0.9, LOOP: 0.2}
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([PROMPT])


# Scenario 8: an unscored concept is "needs assessment", not weak (spec decision Q1 = B)
# Input: tool-calling has no score; prompting 0.3; target 0.2
# Output: Asserts root gap = prompting, needs assessment = [tool-calling]
def test_s8_unscored_concept_needs_assessment():
    scores = {LLM: 0.9, PROMPT: 0.3, LOOP: 0.2}
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([PROMPT], [TOOLS])


# ── Edge cases ──────────────────────────────────────────────────────────────


# A weak concept with no prerequisites is its own root gap
# Input: Target llm-basics at 0.4
# Output: Asserts root gap = llm-basics
def test_weak_target_without_prerequisites_is_itself():
    assert find_root_gaps(CHAIN, {LLM: 0.4}, LLM) == expected([LLM])


# Everything beneath a weak target is unscored: target is the root, the rest need assessment
# Input: Only agent-loop scored (0.2)
# Output: Asserts root gap = agent-loop; needs assessment deepest first
def test_all_beneath_unscored_target_is_root_and_rest_need_assessment():
    result = find_root_gaps(CHAIN, {LOOP: 0.2}, LOOP)
    assert result == expected([LOOP], [LLM, PROMPT, TOOLS])


# An unscored target is listed in needs-assessment; weak concepts beneath are still found
# Input: Target agent-loop has no score; prompting 0.3
# Output: Asserts root gap = prompting, needs assessment = [agent-loop]
def test_unscored_target_needs_assessment():
    scores = {LLM: 0.9, PROMPT: 0.3, TOOLS: 0.9}
    assert find_root_gaps(CHAIN, scores, LOOP) == expected([PROMPT], [LOOP])


# A concept reachable by two paths (diamond) is reported once
# Input: t → left → d and t → right → d; only d weak (besides t)
# Output: Asserts root gaps = [d], exactly once
def test_diamond_shared_concept_reported_once():
    prereqs = {"d": [], "left": ["d"], "right": ["d"], "t": ["left", "right"]}
    scores = {"d": 0.3, "left": 0.9, "right": 0.9, "t": 0.2}
    assert find_root_gaps(prereqs, scores, "t") == expected(["d"])


# Depth is the LONGEST path from the target (research D6)
# Input: d is reachable at depth 1 (t → d) and depth 2 (t → a → d); f at depth 2 (t → e → f)
# Output: Asserts [d, f]: both depth 2, tie broken by map order (shortest path would give [f, d])
def test_depth_uses_longest_path():
    prereqs = {"d": [], "f": [], "a": ["d"], "e": ["f"], "t": ["d", "a", "e"]}
    scores = {"d": 0.3, "f": 0.3, "a": 0.9, "e": 0.9, "t": 0.2}
    assert find_root_gaps(prereqs, scores, "t") == expected(["d", "f"])


# Root gaps at the same depth come out in map (pack) order, not prerequisite-list order
# Input: t needs [x, y], both weak; the map lists y before x
# Output: Asserts [y, x]
def test_ties_broken_by_map_order():
    prereqs = {"y": [], "x": [], "t": ["x", "y"]}
    scores = {"x": 0.3, "y": 0.3, "t": 0.2}
    assert find_root_gaps(prereqs, scores, "t") == expected(["y", "x"])


# A custom threshold changes what counts as weak
# Input: prompting 0.6, tool-calling 0.4, target 0.2, threshold 0.5
# Output: Asserts root gap = tool-calling (prompting is mastered at 0.5)
def test_custom_threshold():
    scores = {LLM: 0.9, PROMPT: 0.6, TOOLS: 0.4, LOOP: 0.2}
    assert find_root_gaps(CHAIN, scores, LOOP, threshold=0.5) == expected([TOOLS])


# Same inputs always give the same answer (spec FR-014, SC-004)
# Input: The scenario-5 branching map, called twice
# Output: Asserts both results are identical
def test_deterministic():
    prereqs = {"a0": [], "a": ["a0"], "b0": [], "b": ["b0"], "t": ["a", "b"]}
    scores = {"a0": 0.9, "a": 0.3, "b0": 0.4, "b": 0.9, "t": 0.2}
    assert find_root_gaps(prereqs, scores, "t") == find_root_gaps(prereqs, scores, "t")


# ── Errors ──────────────────────────────────────────────────────────────────


# An unknown target is rejected with its name in the message
# Input: Target "rag-basics", not in the map
# Output: Asserts ValueError mentioning "rag-basics"
def test_unknown_target_raises():
    with pytest.raises(ValueError, match="rag-basics"):
        find_root_gaps(CHAIN, {}, "rag-basics")


# Scores outside 0–1 are rejected with the concept in the message
# Input: tool-calling scored 1.5, then -0.1
# Output: Asserts ValueError mentioning "tool-calling" both times
@pytest.mark.parametrize("bad_score", [1.5, -0.1])
def test_score_out_of_range_raises(bad_score):
    scores = {LLM: 0.9, PROMPT: 0.9, TOOLS: bad_score, LOOP: 0.2}
    with pytest.raises(ValueError, match=TOOLS):
        find_root_gaps(CHAIN, scores, LOOP)


# ── find_cycle (spec User Story 2: loops must be caught) ────────────────────
# Called as graph.find_cycle so these tests fail on their own while the function doesn't exist yet.


# A map with no concepts has no loop
# Input: Empty map
# Output: Asserts None
def test_cycle_empty_map_has_none():
    assert graph.find_cycle({}) is None


# The real v0 chain has no loop
# Input: The 5-concept chain
# Output: Asserts None
def test_cycle_chain_has_none():
    assert graph.find_cycle(CHAIN) is None


# A concept that needs itself is a loop
# Input: a → a
# Output: Asserts the loop is {a}
def test_cycle_self_loop():
    assert set(graph.find_cycle({"a": ["a"]})) == {"a"}


# Two concepts that need each other form a loop
# Input: a → b → a
# Output: Asserts the loop is {a, b}
def test_cycle_two_nodes():
    assert set(graph.find_cycle({"a": ["b"], "b": ["a"]})) == {"a", "b"}


# Only the loop's members are returned, even when the loop isn't at the start of the map
# Input: x (no loop), d → a, and a → b → c → a
# Output: Asserts the loop is exactly {a, b, c} (not x, not d)
def test_cycle_returns_only_loop_members():
    prereqs = {"x": [], "d": ["a"], "a": ["b"], "b": ["c"], "c": ["a"]}
    assert set(graph.find_cycle(prereqs)) == {"a", "b", "c"}
