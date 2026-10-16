"""Exercise the submitted command, including failures without partial reports."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CommandTests(unittest.TestCase):
    def test_generated_artifacts_match_committed_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-m", "gate", "--out", directory],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in ("results.json", "report.md"):
                actual = (Path(directory) / filename).read_text(encoding="utf-8")
                expected = (ROOT / "outputs" / filename).read_text(encoding="utf-8")
                self.assertEqual(actual, expected)

    def test_invalid_input_does_not_write_a_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            original = ROOT / "data" / "option_b_gate"
            briefs = json.loads((original / "briefs.json").read_text(encoding="utf-8"))
            briefs[0]["platforms"] = "Meta"
            (source / "briefs.json").write_text(json.dumps(briefs), encoding="utf-8")
            (source / "clients.json").write_bytes((original / "clients.json").read_bytes())
            output = source / "output"
            result = subprocess.run(
                [sys.executable, "-m", "gate", "--data", str(source), "--out", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("briefs[0].platforms", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
