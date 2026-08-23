"""
chat_cli.py
-----------
Interactive CLI for testing the graph with your own real queries.

Usage:
    python3 chat_cli.py                 # uses the REAL chat agent (needs GEMINI_API_KEY)
    python3 chat_cli.py --stub          # uses the offline stub chat agent (no API key needed)
    python3 chat_cli.py --trace         # also print the node-by-node trace after each answer
    python3 chat_cli.py --thread mysession   # pick a conversation thread id (default: "cli")

All queries in one run share the same thread_id by default, so multi-turn
follow-ups ("what about their stats last round") work like a real
conversation. Type 'reset' to start a fresh thread, 'trace' to toggle trace
printing, or 'exit' / 'quit' / Ctrl-D to leave.
"""

from __future__ import annotations

import argparse
import sys

from graph import build_graph, run_query


def _stub_chat_agent(query: str, thread_id: str = "default") -> str:
    """Offline stand-in for ai_chat_afl.invoke_afl_agent -- use --stub if you
    don't have GEMINI_API_KEY / the real CSVs set up yet."""
    q = query.lower()
    off_topic_markers = ["weather", "recipe", "python code", "capital of", "joke"]
    if any(m in q for m in off_topic_markers):
        return "I can only help with AFL topics. I can compare AFL clubs, players, or recent match statistics if you like."
    return f"(stub Day3 chat-agent answer for: {query!r} -- run without --stub for the real agent)"


def main():
    parser = argparse.ArgumentParser(description="Interactive CLI for the AFL LangGraph app")
    parser.add_argument("--stub", action="store_true", help="use the offline stub chat agent instead of the real Gemini-backed one")
    parser.add_argument("--trace", action="store_true", help="print the full node-by-node trace after each answer")
    parser.add_argument("--thread", default="cli", help="conversation thread id (default: 'cli')")
    args = parser.parse_args()

    show_trace = args.trace
    thread_id = args.thread

    if args.stub:
        import nodes
        nodes.set_chat_agent_override(_stub_chat_agent)
        print("(using the offline stub chat agent -- factual/retrieval/off-topic answers are canned, not real)")
    else:
        import os
        if not os.getenv("GEMINI_API_KEY"):
            print("WARNING: GEMINI_API_KEY is not set. Prediction queries will still work "
                  "(they don't need it), but factual/retrieval/off-topic queries will fail "
                  "when they hit the real chat agent. Run with --stub to avoid that, or "
                  "export GEMINI_API_KEY=... first.\n")

    print("Building graph...")
    app = build_graph()
    print(f"Ready. thread_id='{thread_id}'. Type 'exit' to quit, 'reset' for a new thread, 'trace' to toggle trace.\n")

    while True:
        try:
            query = input("> ").strip()
        except EOFError:
            print()
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            break
        if query.lower() == "reset":
            import uuid
            thread_id = f"cli-{uuid.uuid4().hex[:8]}"
            print(f"(new thread_id='{thread_id}')")
            continue
        if query.lower() == "trace":
            show_trace = not show_trace
            print(f"(trace printing {'ON' if show_trace else 'OFF'})")
            continue

        try:
            out = run_query(app, query, thread_id=thread_id)
        except Exception as exc:
            print(f"[error] {type(exc).__name__}: {exc}\n")
            continue

        print(f"\n[intent: {out.get('intent')}  confidence: {out.get('router_confidence')}]")
        print(out.get("final_response") or "(no response produced)")

        if show_trace:
            print("\n--- trace ---")
            for line in out.get("trace", []):
                print(f"  {line}")
        print()


if __name__ == "__main__":
    main()
