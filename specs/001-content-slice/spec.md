# Feature Specification: Content Slice and Root-Cause Finder

**Feature Branch**: `001-content-slice` (solo workflow: committed directly on `main`)

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "Content slice for drona.ai. A subject pack "Agentic AI for Engineers" with its first 5 concepts (LLM basics; Prompting & structured output; Tool calling; The agent loop; Workflows vs agents), each with a title, summary, level and estimated minutes, plus which concepts are prerequisites of which. The pack must be loaded and checked for problems (a prerequisite that doesn't exist, circular prerequisites). Root-cause finder: given a target concept the learner is struggling with and the learner's mastery score per concept (0-1), identify the deepest weak prerequisite, i.e. the earliest concept in the prerequisite chain below the mastery threshold, so the tutor teaches the real gap first instead of re-teaching the target. Why: re-teaching a concept whose foundations are missing wastes the learner's time."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the real gap behind a struggling concept (Priority: P1)

A learner keeps failing questions on a concept (the *target*). Before the tutor teaches anything, drona
looks at the target's prerequisites and the learner's mastery of each, and identifies the **root gap**:
the earliest weak concept underneath the target. The tutor then starts there instead of re-teaching
the target.

**Why this priority**: this is drona's core promise ("find each engineer's real gaps"). Re-teaching a
concept whose foundations are missing wastes the learner's time and erodes trust.

**Independent Test**: can be fully tested with a small set of concepts, their prerequisite links and
a set of mastery scores, by checking that the identified root gap matches the expected concept.

**Acceptance Scenarios** (threshold 0.7; chain: LLM basics → Structured output → Tool calling → Agent loop):

1. **Given** mastery LLM basics 0.9, Structured output 0.3, Tool calling 0.4, Agent loop 0.2, **When** the
   target is Agent loop, **Then** the root gap is **Structured output**.
2. **Given** all prerequisites of Agent loop are at or above 0.7 and Agent loop is 0.2, **When** the
   target is Agent loop, **Then** the root gap is **Agent loop itself** (its foundations are fine).
3. **Given** mastery LLM basics 0.5 and everything above it also below 0.7, **When** the target is Agent
   loop, **Then** the root gap is **LLM basics** (the very first concept).
4. **Given** the target concept is itself at or above 0.7, **When** the finder is asked about it,
   **Then** it reports **no gap** for that target.
5. **Given** a concept with two prerequisite branches that both contain a weak concept, **When** the
   finder runs, **Then** it reports **every** root gap, deepest first, in a stable, repeatable order.
6. **Given** a score of exactly 0.7, **When** the finder evaluates that concept, **Then** it counts as
   **mastered** (the threshold is inclusive).
7. **Given** Structured output 0.3, Tool calling **0.9**, Agent loop 0.2, **When** the target is Agent loop,
   **Then** the root gap is **Structured output**: the walk continues past the mastered Tool calling.
8. **Given** Tool calling has **no score** (never assessed), Structured output 0.3, Agent loop 0.2, **When**
   the target is Agent loop, **Then** the root gap is **Structured output** and Tool calling is reported
   as **needs assessment**.

---

### User Story 2 - Load the subject pack and catch content mistakes (Priority: P2)

A content author defines the "Agentic AI for Engineers" pack: each concept has a title, summary,
level and estimated minutes, plus the concepts it depends on. When the pack is loaded, drona checks it
and rejects it with a clear message if it is broken, so a mistake in the content can never silently
produce wrong root gaps.

**Why this priority**: the root-cause finder is only as good as the prerequisite map it walks. Broken
content (a missing concept, a loop) must be caught before any learner sees it.

**Independent Test**: can be tested by loading the real 5-concept pack (succeeds) and several
deliberately broken packs (each fails with a message naming the problem).

**Acceptance Scenarios**:

1. **Given** the pack with the 5 v0 concepts and their prerequisites, **When** it is loaded, **Then** all
   5 concepts are available with title, summary, level and estimated minutes, and their prerequisites.
2. **Given** a concept that lists a prerequisite which doesn't exist in the pack, **When** the pack is
   loaded, **Then** loading fails and the message names both the concept and the missing prerequisite.
3. **Given** concepts whose prerequisites form a loop (e.g. A needs B, B needs A), **When** the pack is
   loaded, **Then** loading fails and the message lists the concepts in the loop.
4. **Given** two concepts with the same identifier, **When** the pack is loaded, **Then** loading fails
   and the message names the duplicate.
5. **Given** a concept missing a required field, or a level outside 1–4, or non-positive estimated
   minutes, **When** the pack is loaded, **Then** loading fails and the message names the concept and field.

---

### Edge Cases

- Target concept not in the pack → the finder reports an error naming the unknown concept.
- Target with no prerequisites (e.g. LLM basics) and weak → the root gap is the target itself.
- A concept has no mastery score yet (never assessed) → it is neither weak nor mastered; it is listed
  as **needs assessment** so the diagnostic can test it, and the walk continues past it.
- A mastered concept sits between two weak ones (weak → **strong** → weak target) → the walk continues
  past it; the deeper weak concept is the root gap.
- Every concept under the target is unassessed and the target is weak → root gap is the target itself,
  and the unassessed concepts are listed as needs assessment.
- Two root gaps at the same depth → both reported, in a stable order (pack order).
- A concept reachable through two different paths (diamond shape) → reported once, not twice.
- Mastery score outside 0–1 → rejected with an error.
- An empty pack → loading fails with a clear message.

## Requirements *(mandatory)*

### Functional Requirements

**Subject pack**

- **FR-001**: The pack MUST identify itself (name, version, status) and contain the 5 v0 concepts: LLM
  basics; Prompting & structured output; Tool calling; The agent loop; Workflows vs agents.
- **FR-002**: Each concept MUST have a unique identifier, title, summary, level (1–4) and estimated
  minutes (positive whole number), and a list of prerequisite concept identifiers (possibly empty).
- **FR-003**: The v0 prerequisite chain MUST be: LLM basics → Prompting & structured output → Tool
  calling → The agent loop → Workflows vs agents (each needs the one before it).
- **FR-004**: Loading MUST fail, with a message naming the offending concept(s), when: a prerequisite
  doesn't exist; prerequisites form a loop; identifiers are duplicated; a required field is missing or
  out of range; or the pack is empty.
- **FR-005**: A successfully loaded pack MUST answer "what are the direct prerequisites of concept X?"
  for any concept in it.

**Root-cause finder**

- **FR-006**: Given a target concept, a set of mastery scores (0–1 per concept) and a mastery threshold,
  the finder MUST return the root gap(s) for that target.
- **FR-007**: A concept is *weak* if its score is below the threshold and *mastered* if it is at or above
  it. The default threshold is 0.7, and callers MAY supply a different one.
- **FR-008**: The finder MUST consider the target and **all** concepts beneath it (prerequisites,
  their prerequisites, and so on), walking past mastered and unassessed concepts. A root gap is a weak
  concept among these that has **no weak concept anywhere beneath it**. If the target is weak and
  nothing beneath it is weak, the root gap is the target itself.
- **FR-009**: When there are several root gaps, the finder MUST return all of them, deepest (furthest
  from the target) first, ties in pack order, each concept at most once.
- **FR-010**: If the target is mastered, the finder MUST return no root gaps and nothing to assess.
- **FR-011**: The finder MUST reject an unknown target concept or a score outside 0–1 with a clear error.
- **FR-012**: A concept with no score MUST count as neither weak nor mastered. Alongside the root gaps,
  the finder MUST return every unassessed concept beneath the target (and the target itself if it has
  no score) as **needs assessment**, deepest first, ties in pack order.
- **FR-013**: The walk MUST continue past mastered concepts: a weak concept deeper in the map is still
  a root gap even if a mastered concept sits between it and the target.
- **FR-014**: The finder MUST give the same answer every time for the same inputs (deterministic) and
  MUST NOT depend on any AI model.

### Key Entities

- **Subject pack**: a versioned collection of concepts for one subject (name, version, status,
  owner). v0 holds 5 concepts.
- **Concept**: one teachable topic (identifier, title, summary, level 1–4, estimated minutes) and the
  concepts it directly depends on.
- **Prerequisite link**: "concept A needs concept B first". Together the links form a map with no loops.
- **Mastery score**: how well a learner knows a concept, 0–1 (supplied by the caller in this feature;
  calculating it is a separate feature).
- **Root gap**: a weak concept with no weak concept anywhere beneath it, where teaching should start.
- **Needs assessment**: concepts beneath the target with no score yet, which the diagnostic should test
  before trusting the root gap.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance scenarios in User Stories 1 and 2 pass in automated checks.
- **SC-002**: Every broken-pack case in the Edge Cases and FR-004 is rejected, and each message lets a
  content author locate the problem without reading code (it names the concept and the issue).
- **SC-003**: For a pack of up to 200 concepts, the root gap is identified in under 1 second.
- **SC-004**: Running the finder twice on the same inputs always gives identical results.
- **SC-005**: Zero AI-model calls are needed to load a pack or find a root gap.

## Assumptions

- Mastery scores are given by the caller; computing and updating them (and decay) is a separate feature
  (Session 3).
- The default threshold of 0.7 is a starting value, adjustable later from evidence; it sits below the
  0.8 average used for "verified mastery".
- Only the 5 v0 concepts are in scope; the remaining 15 concepts, teaching notes, questions and sources
  are separate work.
- The pack is authored by hand and reviewed like code; no editing interface is needed.
- One pack (Agentic AI for Engineers) is loaded at a time.
