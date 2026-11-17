"""Check the real example folder through isolated CLI runs."""

from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parent
ORIGINAL = 'def checkout(cart):\n    return sum(item["price"] for item in cart)\n'


class ExampleRepoCliTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.kit = root / "kit"
        self.kit.mkdir()
        self.runtime = root / "runtime"
        self.runtime.mkdir()
        for filename in ("agent.py", "approve_patch.py"):
            shutil.copy2(ROOT / filename, self.kit / filename)
        shutil.copytree(ROOT / "example_repo", self.kit / "example_repo")
        self.orders = self.kit / "example_repo" / "orders.py"

    def run_cli(self, filename, answer=None):
        return subprocess.run(
            [sys.executable, "-B", str(self.kit / filename)],
            cwd=self.runtime, input=answer, capture_output=True, text=True, timeout=5,
        )

    def test_normal_tools_read_changed_fixture_from_module_folder(self):
        self.assertEqual(self.orders.read_bytes(), ORIGINAL.encode())
        source = ORIGINAL + "# fixture marker from disk\n"
        self.orders.write_text(source)
        self.orders.with_name("notes.txt").write_text("Shop notes.\n")
        self.orders.with_name("not_a_file").mkdir()
        result = self.run_cli("agent.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            "list_files()\n['README.md', 'notes.txt', 'orders.py']\n"
            'read_file("orders.py")\n' + source
            + "checkout() adds the prices of all cart items and returns the total.\n",
        )
        self.assertEqual(self.orders.read_bytes(), source.encode())

    def test_approve_patch_refuses_changed_executable_fixture_without_running_or_writing(self):
        payload = 'sum.__self__.open("untrusted-ran.txt", "w").write("ran")'
        source = ORIGINAL + "\n" + payload + "\n"
        self.orders.write_text(source)
        result = self.run_cli("approve_patch.py", "y\n")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertIn(payload, result.stdout)
        self.assertTrue(result.stdout.endswith(
            "Checks refused or failed: Only the built-in checkout proposal can run.\n"
        ), result.stdout)
        self.assertFalse((self.runtime / "untrusted-ran.txt").exists())
        self.assertEqual(self.orders.read_bytes(), source.encode())


if __name__ == "__main__":
    unittest.main()
