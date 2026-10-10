# AGENTS.md: drona.ai

## Purpose
An AI coach that finds each engineer's real gaps in AI skills, coaches them until they've actually mastered the
material, and lets the team lead steer. The human holds the wheel.

## Principles
1. **Rules decide, the model speaks.** Decisions (mastery, plan order, next question) are pure Python functions
   with tests. The LLM explains, asks questions and gives feedback; it never makes those decisions.
2. **The human holds the wheel.** Agents *propose* changes (old → new + reason); a human approves, edits or
   rejects. Nothing takes effect without approval.
3. **Every loop has an exit.** Every agent loop has budgets: max steps, tokens and seconds. On a budget hit, stop
   cleanly and report why.
4. **Grounded or silent.** The tutor answers only from the content pack and cites it. If the content doesn't
   cover a question, say so; never guess.

## Commands
```
uv sync                          # install exact versions from uv.lock
uv run pytest                    # run tests
uv run python -m drona.cli ...   # run the CLI (e.g. `ping`)
uv add <pkg> / uv add --dev <pkg>
```

## Layout
- `drona/`: the package. `core/` (agent loop, tools, budgets), `domain/` (pure rules), `agents/`, `llm/`,
  `state/`, `content/`, `guard/`, `trace/`, `persona/`, `cli.py`
- `packs/<subject>/`: content as code (concepts, notes, questions)
- `tests/`: pytest; one test file per domain module
- `.specify/`: Spec Kit (specs → plan → tasks)
- `docs/`: public design records (coming soon): `adr/` (architecture decisions), `agent-cards/` (one per agent)

## Conventions
- Code uses **role names** (orchestrator, assessor, analyst, planner, tutor). Mahabharata character names live
  only in `drona/persona/`.
- Domain rules (`drona/domain/`) are pure functions: no LLM calls, no I/O, with unit tests. Write tests first.
- All LLM calls go through `drona/llm/client.py`; nothing else imports a provider SDK.
- LLM outputs that code depends on are parsed into Pydantic models (validate, don't trust).
- Python 3.12, type hints everywhere, small modules, one module per change.

## Don'ts
- No agent frameworks (LangChain, LangGraph, CrewAI…) in the v0 core. The loop is hand-written on purpose.
- No secrets in code, logs or commits; config comes from the environment (`.env`, see `.env.example`).
- No copying external course or book content into packs; write original notes and cite sources.
- No new dependencies without saying why.
