# drona.ai devlog

## 2026-10-10 · Session 1: setup + first model call
- **Built:** repo + uv project, a provider-neutral LLM client and `drona.cli ping`, which returns schema-validated JSON.
- **Learned:** uv = pip + venv + pyenv + poetry; Spec Kit makes the spec the contract for AI coding agents.
- **Surprise:** the newest Gemini model took 144s for 14 words (overloaded). Measured 10 models and picked by latency: flash-lite 1.4s vs flash 8s.
