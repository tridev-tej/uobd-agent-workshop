"""A tiny coding agent with prepared local model turns."""

import argparse
import json


QUESTION = "What does checkout() in orders.py do?"
MAX_TURNS = 4


def ask_repo(question, model, tools):
    """Ask the model, run its chosen tool, and return results until it answers."""
    history = [{"role": "user", "content": question}]
    trace = []
    for _ in range(MAX_TURNS):
        action = model(history, tuple(tools))
        history.append({"role": "assistant", **action})
        if "answer" in action:
            return trace, action["answer"]
        name = action["tool"]
        arguments = action["arguments"]
        result = tools[name](**arguments)
        history.append({"role": "tool", "name": name, "content": result})
        trace.append({"tool": name, "arguments": arguments, "result": result})
    raise RuntimeError("Model did not answer within 4 turns.")


def prepared_model(history, tool_names):
    """Choose prepared local turns from the history and available tools."""
    if set(tool_names) != {"list_files", "read_file"}:
        raise ValueError("The prepared model needs list_files and read_file.")
    latest = history[-1]
    if latest["role"] == "user":
        return {"tool": "list_files", "arguments": {}}
    if latest["name"] == "list_files":
        if "orders.py" not in latest["content"]:
            return {"answer": "orders.py could not be found."}
        return {"tool": "read_file", "arguments": {"path": "orders.py"}}
    return {"answer": "checkout() adds the prices of all cart items and returns the total."}


def demo(missing=False):
    """Run the fixed question against the small in-memory repository."""
    files = {
        "README.md": "A tiny shop example.",
        "orders.py": 'def checkout(cart):\n    return sum(item["price"] for item in cart)',
    }
    if missing:
        del files["orders.py"]
        files["app.py"] = ""

    def list_files():
        return list(files)

    def read_file(path):
        return files[path]

    tools = {"list_files": list_files, "read_file": read_file}
    return ask_repo(QUESTION, prepared_model, tools)


def cli():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--missing", action="store_true")
    args = parser.parse_args()
    trace, answer = demo(missing=args.missing)
    for event in trace:
        values = [json.dumps(value) for value in event["arguments"].values()]
        print(f'{event["tool"]}({", ".join(values)})')
        print(event["result"])
    print(answer)


if __name__ == "__main__":
    cli()
