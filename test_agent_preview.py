"""Exercise the fixed patch preview through the ordinary CLI."""

from pathlib import Path
import subprocess
import sys
import unittest


AGENT = Path(__file__).with_name("agent.py")


class PreviewCliTest(unittest.TestCase):
    def test_missing_source_has_no_read_or_patch(self):
        result = subprocess.run(
            [sys.executable, "-B", str(AGENT), "--missing", "--preview"],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            "list_files()\n['README.md', 'app.py']\norders.py could not be found.\n",
        )

    def test_preview_lists_reads_and_prints_exact_patch(self):
        result = subprocess.run(
            [sys.executable, "-B", str(AGENT), "--preview"],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            "list_files()\n"
            "['README.md', 'orders.py']\n"
            'read_file("orders.py")\n'
            "def checkout(cart):\n"
            '    return sum(item["price"] for item in cart)\n'
            "--- a/orders.py\n"
            "+++ b/orders.py\n"
            "@@ -1,2 +1,2 @@\n"
            "-def checkout(cart):\n"
            '-    return sum(item["price"] for item in cart)\n'
            "+def checkout(items):\n"
            '+    return sum(item["price"] for item in items)\n',
        )


if __name__ == "__main__":
    unittest.main()
