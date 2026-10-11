# Quickstart: validate the content slice

## Prerequisites
- `uv sync` done (Python 3.12, PyYAML, Pydantic, pytest installed).

## 1. Run the tests
```bash
uv run pytest tests/test_graph.py tests/test_pack_loader.py -v
```
Expected: all green. `test_graph.py` covers spec User Story 1 scenarios 1–8 plus edge cases
(empty input, cycles, diamond, ties, boundary 0.7, unknown target, bad score);
`test_pack_loader.py` covers User Story 2 scenarios 1–5.

## 2. Load the real pack
```bash
uv run python -c "from pathlib import Path; from drona.content.pack_loader import load_pack; p = load_pack(Path('packs/agentic-ai')); print(p.name, [c.id for c in p.concepts])"
```
Expected: `Agentic AI for Engineers ['llm-basics', 'prompting-structured-output', 'tool-calling', 'agent-loop', 'workflows-vs-agents']`

## 3. Find a root gap (spec US1, scenario 1)
```bash
uv run python -c "
from pathlib import Path
from drona.content.pack_loader import load_pack
from drona.domain.graph import find_root_gaps
p = load_pack(Path('packs/agentic-ai'))
s = {'llm-basics': 0.9, 'prompting-structured-output': 0.3, 'tool-calling': 0.4, 'agent-loop': 0.2}
print(find_root_gaps(p.prereq_map(), s, 'agent-loop'))"
```
Expected: `RootCauseResult(root_gaps=['prompting-structured-output'], needs_assessment=[])`

## 4. Broken pack is rejected
Add a concept whose prerequisite is `does-not-exist` to a copy of the pack; loading raises
`PackError` naming the concept and `does-not-exist`.
