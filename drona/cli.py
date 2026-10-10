"""drona command line. Run with: uv run python -m drona.cli <command>"""

import argparse
import time

from pydantic import BaseModel, Field
from rich.console import Console

from drona.llm.client import MODELS, LLMError, complete

console = Console()


class PingResult(BaseModel):
    concept: str = Field(description="Name of the concept, e.g. 'agent loop'")
    one_line: str = Field(description="One-sentence explanation")
    confidence: float = Field(ge=0, le=1, description="How sure the model is, 0 to 1")


# Checks the whole path end to end: CLI → client → Gemini → validated JSON
# Input: Parsed command-line args (uses args.tier)
# Output: Prints the result as JSON and returns exit code 0 (ok) or 1 (failed)
def ping(args: argparse.Namespace) -> int:
    messages = [
        {"role": "system", "content": "You are a precise AI tutor. Be concise."},
        {"role": "user", "content": "Explain the concept 'agent loop'."},
    ]
    start = time.perf_counter()
    try:
        result = complete(messages, schema=PingResult, tier=args.tier)
    except LLMError as exc:
        console.print(f"[red]ping failed:[/red] {exc}")
        return 1
    console.print_json(result.model_dump_json())
    console.print(f"[dim]{MODELS[args.tier]} · {time.perf_counter() - start:.1f}s[/dim]")
    return 0


# Builds the CLI and runs the chosen subcommand
# Input: Nothing (reads the command line)
# Output: Exit code from the subcommand
def main() -> int:
    parser = argparse.ArgumentParser(prog="drona", description="drona.ai: an AI coach for engineers")
    commands = parser.add_subparsers(dest="command", required=True)

    ping_cmd = commands.add_parser("ping", help="check the LLM path end to end")
    ping_cmd.add_argument("--tier", choices=list(MODELS), default="fast")
    ping_cmd.set_defaults(func=ping)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
