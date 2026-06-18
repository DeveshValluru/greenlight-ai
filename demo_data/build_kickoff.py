"""
Build a GreenLight kickoff message from a mix of file types (PDF, TXT,
CSV, JSON, MD) and put it on the clipboard, ready to paste into Band's
Briefing room.

Usage:
    python demo_data/build_kickoff.py --title "Project Title" \
        --script path/to/script.pdf \
        --budget path/to/budget.csv \
        --crew   path/to/crew.json \
        --legal  path/to/contracts.pdf

Any of the file args may be a .pdf, .txt, .md, .csv, .json, or any other
text-extractable format. Skip an arg to omit that section.

Defaults (no args): builds the "The Deep Horizon" sample from demo_data/.

Requires pypdf (already in requirements.txt).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def extract(path: Path) -> str:
    if not path.exists():
        return f"(file not found: {path})"
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return "(pypdf not installed — run `pip install pypdf`)"
        try:
            reader = PdfReader(str(path))
            parts = []
            for page in reader.pages:
                t = page.extract_text() or ""
                if t.strip():
                    parts.append(t)
            return "\n\n".join(parts).strip() or "(empty PDF)"
        except Exception as exc:  # noqa: BLE001
            return f"(PDF parse error: {exc})"
    # all other formats: read as text
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception as exc:  # noqa: BLE001
        return f"(read error: {exc})"


def build_message(
    title: str,
    script: Path | None,
    budget: Path | None,
    crew: Path | None,
    legal: Path | None,
) -> str:
    sections = [
        "@ScriptAnalyst @BudgetAuditor @MarketIntel @LegalEagle @TalentScout "
        "please analyze this film project package:",
        "",
        f"PROJECT: {title}",
    ]
    if script:
        sections += ["", "--- SCRIPT / TREATMENT ---", extract(script)]
    if budget:
        sections += ["", "--- BUDGET ---", extract(budget)]
    if crew:
        sections += ["", "--- CREW LIST ---", extract(crew)]
    if legal:
        sections += ["", "--- LEGAL DOCS ---", extract(legal)]
    return "\n".join(sections)


def to_clipboard(text: str) -> bool:
    try:
        subprocess.run(["clip.exe"], input=text.encode("utf-8"), check=True)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"clipboard failed: {exc}", file=sys.stderr)
        return False


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--title", default="THE DEEP HORIZON")
    demo = Path(__file__).resolve().parent
    p.add_argument("--script", type=Path, default=demo / "sample_script.txt")
    p.add_argument("--budget", type=Path, default=demo / "sample_budget.csv")
    p.add_argument("--crew",   type=Path, default=demo / "sample_crew.json")
    p.add_argument("--legal",  type=Path, default=demo / "sample_contracts.txt")
    p.add_argument("--no-clipboard", action="store_true",
                   help="Print to stdout instead of copying to clipboard.")
    args = p.parse_args()

    msg = build_message(args.title, args.script, args.budget, args.crew, args.legal)

    if args.no_clipboard:
        print(msg)
        return

    if to_clipboard(msg):
        print(f"✅ Mega prompt copied to clipboard ({len(msg):,} chars)")
        print(f"   Title:  {args.title}")
        print(f"   Script: {args.script.name}")
        print(f"   Budget: {args.budget.name}")
        print(f"   Crew:   {args.crew.name}")
        print(f"   Legal:  {args.legal.name}")
        print("\nPaste into the Briefing room. Ctrl+V then Send.")
    else:
        print("Falling back to stdout:")
        print(msg)


if __name__ == "__main__":
    main()
