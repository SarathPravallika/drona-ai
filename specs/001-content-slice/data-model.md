# Data Model: Content Slice and Root-Cause Finder

## Pack (`packs/agentic-ai/pack.yaml` → `drona.content.models.Pack`)
| Field | Type | Rules |
|---|---|---|
| `slug` | str | required, e.g. `agentic-ai` |
| `name` | str | required, e.g. "Agentic AI for Engineers" |
| `version` | str | required, e.g. `0.1.0` |
| `status` | `draft` \| `approved` \| `retired` | required |
| `owner` | str | required |
| `concepts` | list[Concept] | from `concepts.yaml`; must be non-empty; ids unique |

## Concept (`packs/agentic-ai/concepts.yaml` → `drona.content.models.Concept`)
| Field | Type | Rules |
|---|---|---|
| `id` | str | required, lowercase slug (`a-z`, `0-9`, `-`), unique in the pack |
| `title` | str | required, non-empty |
| `summary` | str | required, non-empty, one or two sentences |
| `level` | int | required, 1–4 (L1 Foundations … L4) |
| `est_minutes` | int | required, > 0 |
| `prerequisites` | list[str] | default `[]`; every id must exist in the pack; no loops |

### v0 concepts (FR-001, FR-003)
| id | title | level | prerequisites |
|---|---|---|---|
| `llm-basics` | LLM basics | 1 | — |
| `prompting-structured-output` | Prompting & structured output | 1 | `llm-basics` |
| `tool-calling` | Tool calling | 1 | `prompting-structured-output` |
| `agent-loop` | The agent loop | 1 | `tool-calling` |
| `workflows-vs-agents` | Workflows vs agents | 1 | `agent-loop` |

## Prerequisite map (domain input)
`Mapping[str, Sequence[str]]`: concept id → direct prerequisite ids, in pack order.
Built from a loaded `Pack` by `pack.prereq_map()`.

## Mastery scores (domain input)
`Mapping[str, float]`: concept id → score in [0, 1]. A missing id means **unassessed**.

## RootCauseResult (domain output, `drona.domain.graph`)
| Field | Type | Meaning |
|---|---|---|
| `root_gaps` | list[str] | weak concepts with nothing weak beneath them; deepest first, ties in pack order |
| `needs_assessment` | list[str] | unassessed concepts in the target's walk (incl. the target); deepest first, ties in pack order |

## Validation → error mapping
| Problem | Raised by | Error |
|---|---|---|
| missing field / bad level / minutes ≤ 0 / bad id | Pydantic → loader | `PackError` naming concept + field |
| empty pack | loader | `PackError` |
| duplicate id | loader | `PackError` naming the id |
| unknown prerequisite | loader | `PackError` naming concept + missing id |
| loop | loader (via `find_cycle`) | `PackError` listing the loop |
| unknown target | finder | `ValueError` naming the id |
| score outside 0–1 | finder | `ValueError` naming the concept + score |
