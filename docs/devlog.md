# drona.ai devlog

## 2026-10-10 · Session 1: setup + first model call
- **Built:** repo + uv project, a provider-neutral LLM client and `drona.cli ping`, which returns schema-validated JSON.
- **Learned:** uv = pip + venv + pyenv + poetry; Spec Kit makes the spec the contract for AI coding agents.
- **Surprise:** the newest Gemini model took 144s for 14 words (overloaded). Measured 10 models and picked by latency: flash-lite 1.4s vs flash 8s.

## 2026-10-12 · Session 2: content slice + root-cause finder
- **Built:** drona now finds the real gap behind a struggling concept: failing "agent loop" → start with "structured output". Topic map as YAML, loader that rejects broken maps, 34 tests.
- **Learned:** dependencies can form loops, so validate the topic map once at the boundary (3-colour DFS) and let the core logic trust it. Spec Kit (constitution → spec → plan → tasks) forced the product decisions before any code.
- **Surprise:** how much thinking edge cases take. "Never tested" ≠ "weak", and a topic reachable by two paths must count once. Both became explicit decisions in the spec, not accidents in the code.

