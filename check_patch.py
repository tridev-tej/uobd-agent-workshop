"""Check the approval exercise; use --reference for the solution."""

import argparse
from contextlib import redirect_stdout
import importlib
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


BEFORE = 'def checkout(cart):\n    return sum(item["price"] for item in cart)'
PROPOSED = 'def checkout(items):\n    return sum(item["price"] for item in items)'
STALE = BEFORE + "\n"
STALE_ERROR = "File changed since preview. Review a fresh diff."
DIFF = "\n".join((
    "--- a/orders.py",
    "+++ b/orders.py",
    "@@ -1,2 +1,2 @@",
    "-def checkout(cart):",
    '-    return sum(item["price"] for item in cart)',
    "+def checkout(items):",
    '+    return sum(item["price"] for item in items)',
))
PROMPT = "Apply this change? Type y to approve: "
DECLINED = "Declined. Current source kept. Checks skipped.\n"


class PatchChecks(unittest.TestCase):
    def test_approved_fresh(self):
        self.assertEqual(self.apply_edit(BEFORE, BEFORE, PROPOSED, True), PROPOSED)

    def test_approved_stale(self):
        with self.assertRaises(ValueError) as caught:
            self.apply_edit(STALE, BEFORE, PROPOSED, True)
        self.assertEqual(str(caught.exception), STALE_ERROR)

    def test_declined_fresh(self):
        self.assertEqual(self.apply_edit(BEFORE, BEFORE, PROPOSED, False), BEFORE)

    def test_declined_stale_keeps_current(self):
        self.assertEqual(self.apply_edit(STALE, BEFORE, PROPOSED, False), STALE)

    def assert_cli(self, answer, stale, code, status):
        command = [sys.executable, "-B", str(self.script)]
        if stale:
            command.append("--stale")
        result = subprocess.run(
            command, input=answer + "\n", capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, code, result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, DIFF + "\n" + PROMPT + status)

    def test_cli_fresh_approval(self):
        self.assert_cli("y", False, 0,
                        "PASS empty cart: 0\nPASS two-item cart: 30\n"
                        "Applied to in-memory orders.py. Checks passed (2/2).\n")

    def test_cli_decline(self):
        self.assert_cli("n", False, 0, DECLINED)

    def test_cli_stale_approval(self):
        self.assert_cli("y", True, 1,
                        "Refused: " + STALE_ERROR + " Current source kept. Checks skipped.\n")

    def test_cli_stale_decline(self):
        self.assert_cli("n", True, 0, DECLINED)

    def test_checkout_rejects_untrusted_source_before_execution(self):
        approve_patch = importlib.import_module("approve_patch")
        with patch.object(approve_patch, "exec", create=True) as execute:
            with self.assertRaisesRegex(ValueError, "Only the built-in checkout proposal can run"):
                approve_patch.verify_checkout(PROPOSED + "\nraise RuntimeError('must not run')")
        execute.assert_not_called()

    def test_checkout_checks_exact_totals(self):
        approve_patch = importlib.import_module("approve_patch")
        for wrong_total in (1, 0):
            with self.subTest(wrong_total=wrong_total), redirect_stdout(StringIO()):
                with patch.object(approve_patch, "sum", return_value=wrong_total, create=True):
                    with self.assertRaises(AssertionError):
                        approve_patch.verify_checkout(PROPOSED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", action="store_true")
    args = parser.parse_args()
    module_name = "approve_patch" if args.reference else "patch_exercise"
    PatchChecks.apply_edit = staticmethod(importlib.import_module(module_name).apply_edit)
    PatchChecks.script = Path(__file__).with_name(module_name + ".py")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PatchChecks)
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    if not result.wasSuccessful():
        print("Not finished yet: edit apply_edit() in patch_exercise.py, then rerun this check.")
        return 1
    print("Patch checks passed. Try python3 " + PatchChecks.script.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
