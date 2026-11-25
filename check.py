"""Check the student's loop without an API key or network request."""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from unittest.mock import Mock, call, patch

import agent


def check_flow():
    """Check two chosen tools, complete history, and stopping at the answer."""
    chosen = [
        {"type": "function_call", "name": "list_files", "arguments": "{}", "call_id": "list-7"},
        {"type": "function_call", "name": "read_file", "arguments": '{"path":"orders.py"}', "call_id": "read-9"},
    ]
    reasoning = {"type": "reasoning", "id": "reason-3", "summary": []}
    outputs = [[reasoning, chosen[0]], [chosen[1]]]
    values = [["orders.py"], "Source returned by the file tool."]
    results = [{"type": "function_call_output", "call_id": item["call_id"],
                "output": json.dumps(value)} for item, value in zip(chosen, values)]
    replies = [(outputs[0], None, chosen[0]), (outputs[1], None, chosen[1]),
               ([], "Checked answer.", None)]
    received = []

    def ask(history):
        received.append(deepcopy(history))
        return replies[len(received) - 1]

    execute = Mock(side_effect=results)
    printed = StringIO()
    with patch.object(agent, "ask_model", ask), patch.object(agent, "run_tool", execute):
        with redirect_stdout(printed):
            agent.run()
    verify_flow(received, outputs, results, chosen, execute, printed.getvalue())


def verify_flow(received, outputs, results, chosen, execute, printed):
    """Compare full history and exact calls without showing a completed loop."""
    initial = [{"role": "user", "content": "What does checkout() in orders.py do?"}]
    after_list = initial + outputs[0] + [results[0]]
    after_read = after_list + outputs[1] + [results[1]]
    assert received == [initial, after_list, after_read], "Remember complete output and actual tool results."
    assert execute.call_args_list == [call(item) for item in chosen], "Run exactly the selected calls."
    assert printed == "Checked answer.\n", "Print the answer once and stop."


def check_limit():
    """Check that an endlessly tool-calling model stops after four turns."""
    chosen = {"name": "list_files", "arguments": "{}", "call_id": "repeat"}
    ask = Mock(return_value=([chosen], None, chosen))
    execute = Mock(return_value={"type": "function_call_output", "call_id": "repeat", "output": "[]"})
    with patch.object(agent, "ask_model", ask), patch.object(agent, "run_tool", execute):
        try:
            agent.run()
        except RuntimeError as error:
            assert str(error) == "Model did not answer within 4 turns.", "Keep the turn-limit error."
        else:
            raise AssertionError("Raise the turn-limit error after four turns.")
    assert ask.call_count == 4, "Ask the model at most four times."
    assert execute.call_count == 4, "Run one chosen tool per turn."


def main():
    """Report expected unfinished work clearly and return a failing exit code."""
    try:
        assert callable(agent.run), "agent.py needs run()."
        check_flow()
        check_limit()
    except (AssertionError, AttributeError, IndexError, NotImplementedError, RuntimeError) as error:
        print(f"Checks failed: {error}")
        raise SystemExit(1) from None
    print("Checks passed: tool history, final answer, and four-turn limit.")


if __name__ == "__main__":
    main()
