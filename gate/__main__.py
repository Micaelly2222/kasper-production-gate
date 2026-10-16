"""Run with python -m gate. Writes reviewable files only."""
import argparse
import json
from pathlib import Path

from .engine import DEFAULT_NOW, evaluate_batch, timestamp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/option_b_gate"))
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    parser.add_argument("--now", default=DEFAULT_NOW.isoformat(), help="ISO timestamp; usage must belong to this month")
    args = parser.parse_args()
    try:
        report = evaluate_batch(json.loads((args.data / "briefs.json").read_text(encoding="utf-8")), json.loads((args.data / "clients.json").read_text(encoding="utf-8")), timestamp(args.now))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Input error: {exc}\nNo new report was written.\n")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = report["summary"]
    lines = ["# Production gate report", "", f"Checked at {report['checked_at']}. Policy {report['policy_version']}.", "", f"**{summary['passed']} passed; {summary['blocked']} blocked; {summary['total']} checked.**", "", "Audience: Squad Leads and Creative Leads. Draft messages below are not sent automatically.", "", "| Brief | Client | Decision | Reasons |", "|---|---|---|---|"]
    for r in report["results"]:
        lines.append(f"| {r['id']} | {r['client']} | {r['status']} | {', '.join(dict.fromkeys(i['code'] for i in r['issues'])) or 'Ready'} |")
    for r in report["results"]:
        if r["issues"]:
            lines += ["", f"## {r['id']} — {r['client']}", "", f"Internal owner: {r['owner']}", ""]
            lines += [f"- {i['evidence']}" for i in r["issues"]]
            lines += ["", "Client clarification draft:", "", r["clarification_message"]]
    (args.out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{summary['passed']} PASS / {summary['blocked']} BLOCKED. Reports: {args.out.resolve()}")


if __name__ == "__main__":
    main()
