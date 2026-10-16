# Kāsper Production Gate

**Check creative briefs before a designer starts working.**

I implemented **Option B** to catch incomplete requests, unavailable products, invalid claims, unrealistic deadlines and requests above the client’s monthly allowance. Each blocked brief includes a reason and a clarification message.

I chose B because it solves a daily operational problem with clear, testable decisions. Python handles the rules without extra packages or paid model calls.

## Review the three options

| Option | Deliverable |
|---|---|
| **A — Onboarding** | [One-page technical design](designs/option_a.md) |
| **B — Production gate** | Working tool and [report for all 30 briefs](outputs/report.md) |
| **C — Squad health** | [One-page technical design](designs/option_c.md) |

A and C are documents to read. B is the program to run.

## Run B

Requires **Python 3.11+**. Open a terminal in this project folder:

```sh
python -m gate
```

Expected result: **19 PASS / 11 BLOCKED**. Outputs are saved in `outputs/report.md` and `outputs/results.json`.

Run the tests:

```sh
python -m unittest discover -s tests -v
```

Expected result: **22 tests, OK**. The check date is fixed at **2026-10-13 09:00 UTC**, as required by the exercise.

## Open the documents on Windows

```powershell
notepad .\designs\option_a.md
notepad .\outputs\report.md
notepad .\designs\option_c.md
```

On GitHub, use the links above. On Windows, `py -3` can replace `python`; on macOS/Linux, use `python3`.

## How decisions work

Briefs are checked in creation order against the [Definition of Ready](data/option_b_gate/definition_of_ready.md). Only passing briefs consume the remaining allowance. Rush deadlines and overages require the correct Squad Lead’s approval.

For example, BR-15 is blocked because Juliana cannot approve that client’s rush. BR-04 passes because Louise, the Squad Lead, approved it.

See [NOTES.md](NOTES.md) for tool choices, costs, deployment and assumptions. Code is in `gate/`; tests are in `tests/`.
