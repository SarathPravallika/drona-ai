# Contract: Python API

Internal library interface used by later agents (analyst, tutor) and the CLI.

## `drona.content.pack_loader`

```python
class PackError(ValueError): ...

def load_pack(pack_dir: Path) -> Pack
```
- Reads `pack_dir/pack.yaml` and `pack_dir/concepts.yaml` with `yaml.safe_load`.
- Returns a validated `Pack`; raises `PackError` for any problem in the data-model error table.

## `drona.content.models`

```python
class Concept(BaseModel): id, title, summary, level, est_minutes, prerequisites
class Pack(BaseModel):    slug, name, version, status, owner, concepts
    def prereq_map(self) -> dict[str, list[str]]   # id → prerequisite ids, pack order
```

## `drona.domain.graph` (pure: no I/O, no LLM)

```python
DEFAULT_THRESHOLD = 0.7

@dataclass(frozen=True)
class RootCauseResult:
    root_gaps: list[str]
    needs_assessment: list[str]

def find_cycle(prereqs: Mapping[str, Sequence[str]]) -> list[str] | None

def find_root_gaps(
    prereqs: Mapping[str, Sequence[str]],
    scores: Mapping[str, float],
    target: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> RootCauseResult
```
- `find_cycle`: the ids forming one loop, or `None` if there are no loops.
- `find_root_gaps`: behaviour per spec FR-006 to FR-014; raises `ValueError` for an unknown target or a
  score outside [0, 1]. Assumes `prereqs` has no loops and no unknown ids (guaranteed by `load_pack`).
