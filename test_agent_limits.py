"""Check the tool allowlist and four-turn limit against the real agent loop."""

import unittest
from unittest.mock import Mock, call

from agent import QUESTION, ask_repo


class AgentLimitsTest(unittest.TestCase):
    def test_unknown_tool_returns_error_to_model(self):
        list_files = Mock(return_value=["README.md", "orders.py"])
        read_file = Mock()
        model_calls = []
        explanation = "write_file is not available. This agent can only list and read files."

        def prepared_unknown_tool(history, tool_names):
            self.assertEqual(tool_names, ("list_files", "read_file"))
            model_calls.append(history.copy())
            if len(model_calls) == 1:
                return {"tool": "write_file", "arguments": {"path": "orders.py"}}
            self.assertEqual(
                history[-1],
                {
                    "role": "tool",
                    "name": "write_file",
                    "content": {"error": "unknown_tool"},
                },
            )
            return {"answer": explanation}

        trace, answer = ask_repo(
            QUESTION,
            prepared_unknown_tool,
            {"list_files": list_files, "read_file": read_file},
        )

        list_files.assert_not_called()
        read_file.assert_not_called()
        self.assertEqual(len(model_calls), 2)
        self.assertEqual(
            trace,
            [
                {
                    "tool": "write_file",
                    "arguments": {"path": "orders.py"},
                    "result": {"error": "unknown_tool"},
                }
            ],
        )
        self.assertEqual(answer, explanation)

    def test_repeated_allowed_tool_stops_after_four_turns(self):
        list_files = Mock(return_value=["README.md", "orders.py"])
        read_file = Mock()
        model_calls = []

        def prepared_repeated_tool(history, tool_names):
            self.assertEqual(tool_names, ("list_files", "read_file"))
            model_calls.append(history.copy())
            return {"tool": "list_files", "arguments": {}}

        with self.assertRaisesRegex(
            RuntimeError, r"^Model did not answer within 4 turns\.$"
        ):
            ask_repo(
                QUESTION,
                prepared_repeated_tool,
                {"list_files": list_files, "read_file": read_file},
            )

        self.assertEqual(len(model_calls), 4)
        self.assertEqual(list_files.call_args_list, [call()] * 4)
        read_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
