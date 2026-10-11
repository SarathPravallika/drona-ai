# drona.ai Constitution

## Core Principles

### I. Rules Decide, the Model Speaks
Every decision that changes learner state or direction (mastery, root-cause gaps, plan order,
next question) MUST be made by a pure, unit-tested Python function in `drona/domain/`. The LLM
MAY explain, ask questions and give feedback; it MUST NOT make or override those decisions.
LLM self-reported confidence MUST NOT drive any decision.
*Rationale:* code is deterministic and testable; model output is neither.

### II. The Human Holds the Wheel
Agents MUST propose changes (old → new, with a reason) and a human MUST approve, edit or reject
them before they take effect. Plans are versioned; nothing is silently overwritten.
*Rationale:* learners and leads stay in control; every change is explainable and reversible.

### III. Every Loop Has an Exit
Every agent loop MUST enforce budgets for max steps, tokens and seconds. Every LLM call MUST have
a timeout and bounded retries (transient errors only). On a budget hit, the agent MUST stop
cleanly and report why.
*Rationale:* prevents runaway cost, hangs and infinite loops.

### IV. Grounded or Silent
The tutor MUST answer only from the content pack and MUST cite the source it used. If the
content does not cover a question, it MUST say so and MUST NOT guess.
*Rationale:* trust depends on faithfulness; citations make it checkable.

### V. Test-First for Domain Rules
Tests for `drona/domain/` rules MUST be written (and fail) before the implementation, and MUST
cover edge cases (empty input, cycles, ties, boundaries). Domain rules MUST have no I/O and no
LLM calls.
*Rationale:* the rules are the product's core logic; tests are their specification.

## Technical Constraints

- Python 3.12 (pinned in `.python-version`), managed with uv; `uv.lock` is committed.
- All LLM calls MUST go through `drona/llm/client.py`; no other module imports a provider SDK.
- LLM outputs that code depends on MUST be parsed and validated into Pydantic models.
- No agent frameworks (LangChain, LangGraph, CrewAI…) in the v0 core; the agent loop is
  hand-written.
- No secrets in code, logs or commits; configuration comes from the environment.
- Pack content (notes, questions) MUST be original; external material is linked and cited in
  `sources.yaml`, never copied wholesale.
- New dependencies MUST be justified in the plan.

## Quality Gates & Workflow

- Every feature follows spec → plan → tasks → implement (Spec Kit).
- Every plan MUST include a Constitution Check against Principles I–V and the constraints above;
  any violation MUST be justified or the plan revised.
- Solo developer for now: small commits directly on `main`, no PRs. Every commit requires
  `uv run pytest` green and a self-reviewed diff. Revisit (feature branches + PRs) when a second
  contributor joins.
- Content changes (packs) follow the same review flow: content is code.

## Governance

This constitution supersedes other practices where they conflict. Amendments require a written
reason, a version bump and a reviewed commit. Versioning: MAJOR for removing or redefining a
principle, MINOR for a new principle or materially expanded guidance, PATCH for wording fixes.
Every plan and review MUST verify compliance. Runtime development guidance lives in `AGENTS.md`.

**Version**: 1.0.0 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-11
