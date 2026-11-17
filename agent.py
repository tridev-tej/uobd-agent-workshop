"""A tiny coding agent with prepared local model turns."""

import argparse
import difflib
import json
from pathlib import Path


QUESTION = "What does checkout() in orders.py do?"
PREVIEW_QUESTION = "Rename cart to items in checkout() in orders.py."
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
        if name not in tools:
            result = {"error": "unknown_tool"}
        else:
            try:
                result = tools[name](**arguments)
            except FileNotFoundError:
                if name != "read_file":
                    raise
                result = {"error": "file_not_found"}
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
    if latest["name"] == "read_file" and latest["content"] == {"error": "file_not_found"}:
        return {"answer": "orders.py could not be read because it is missing."}
    if history[0]["content"] == PREVIEW_QUESTION:
        return {"answer": checkout_patch(latest["content"])}
    return {"answer": "checkout() adds the prices of all cart items and returns the total."}


def checkout_proposal(source):
    """Return the two fixed replacements for the known checkout sample."""
    proposed = source.replace("def checkout(cart):", "def checkout(items):", 1)
    return proposed.replace("for item in cart)", "for item in items)", 1)


def checkout_patch(source):
    """Show the proposal as a diff against the source actually read."""
    proposed = checkout_proposal(source)
    return "\n".join(difflib.unified_diff(
        source.splitlines(), proposed.splitlines(),
        fromfile="a/orders.py", tofile="b/orders.py", lineterm="",
    ))


def demo(missing=False, preview=False):
    """Read the example folder, or supply the prepared missing-file list."""
    folder = Path(__file__).resolve().with_name("example_repo")

    def list_files():
        if missing:
            return ["README.md", "app.py"]
        return sorted(file.name for file in folder.iterdir() if file.is_file())

    def read_file(path):
        if path not in list_files():
            raise FileNotFoundError(path)
        return (folder / path).read_text().removesuffix("\n")

    tools = {"list_files": list_files, "read_file": read_file}
    question = PREVIEW_QUESTION if preview else QUESTION
    return ask_repo(question, prepared_model, tools)


def cli():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    trace, answer = demo(missing=args.missing, preview=args.preview)
    for event in trace:
        values = [json.dumps(value) for value in event["arguments"].values()]
        print(f'{event["tool"]}({", ".join(values)})')
        print(event["result"])
    print(answer)


if __name__ == "__main__":
    cli()
