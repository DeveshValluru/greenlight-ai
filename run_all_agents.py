"""
Launch all 7 GreenLight agent processes.

Each agent runs in its own subprocess so a crash in one doesn't take the others
down. The launcher tails their PIDs and propagates Ctrl+C as a clean shutdown.

Usage:
    python run_all_agents.py
    python run_all_agents.py --only script_analyst budget_auditor
"""
from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path

AGENTS = [
    "script_analyst",
    "budget_auditor",
    "market_intel",
    "legal_eagle",
    "talent_scout",
    "red_team",
    "cro",
]

REPO_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Launch GreenLight AI agents.")
    p.add_argument(
        "--only",
        nargs="+",
        choices=AGENTS,
        help="Only launch these agents (by short name).",
    )
    return p.parse_args()


def launch(agent: str) -> subprocess.Popen:
    script = REPO_ROOT / "agents" / f"{agent}.py"
    print(f"  → starting {agent} ({script.name})")
    return subprocess.Popen(
        [sys.executable, "-m", f"agents.{agent}"],
        cwd=str(REPO_ROOT),
    )


def main() -> int:
    args = parse_args()
    agents = args.only or AGENTS

    print(f"🎬 GreenLight AI — launching {len(agents)} agent(s)")
    processes: list[tuple[str, subprocess.Popen]] = []
    for name in agents:
        try:
            processes.append((name, launch(name)))
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ failed to start {name}: {exc}")

    if not processes:
        print("No agents launched.")
        return 1

    print(f"\n✅ {len(processes)} agent(s) running. Ctrl+C to stop all.\n")

    def shutdown(*_):
        print("\n🛑 stopping all agents...")
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
        deadline = time.time() + 8
        for name, proc in processes:
            remaining = max(0, deadline - time.time())
            try:
                proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  {name} did not exit — killing")
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # Block until any process exits (or Ctrl+C). On any single agent crash,
    # report it but keep the rest alive — the user can restart that one.
    try:
        while True:
            for name, proc in processes:
                code = proc.poll()
                if code is not None:
                    msg = "exited cleanly" if code == 0 else f"crashed (exit {code})"
                    print(f"  ⚠️  {name} {msg}")
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
