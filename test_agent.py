"""Repeat the listed-but-unreadable file case against the real agent loop."""

import unittest

from agent import QUESTION, ask_repo, prepared_model


class ToolFailureTest(unittest.TestCase):
    def test_file_missing_when_read(self):
        calls = []

        def list_files():
            calls.append(("list_files", {}))
            return ["README.md", "orders.py"]

        def read_file(path):
            calls.append(("read_file", {"path": path}))
            raise FileNotFoundError("orders.py")

        trace, answer = ask_repo(
            QUESTION, prepared_model, {"list_files": list_files, "read_file": read_file}
        )

        self.assertEqual(
            calls, [("list_files", {}), ("read_file", {"path": "orders.py"})]
        )
        self.assertEqual(
            trace,
            [
                {
                    "tool": "list_files",
                    "arguments": {},
                    "result": ["README.md", "orders.py"],
                },
                {
                    "tool": "read_file",
                    "arguments": {"path": "orders.py"},
                    "result": {"error": "file_not_found"},
                },
            ],
        )
        self.assertEqual(answer, "orders.py could not be read because it is missing.")


if __name__ == "__main__":
    unittest.main()
