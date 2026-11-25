"""Provided OpenAI Responses and read-only sample tools; no extra packages."""

from http.client import HTTPException
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


_RESPONSES_URL = "https://api.openai.com/v1/responses"
TOOLS = [
    {"type": "function", "name": "list_files", "description": "List available sample files.",
     "parameters": {"type": "object", "properties": {}, "required": [],
                    "additionalProperties": False}, "strict": True},
    {"type": "function", "name": "read_file", "description": "Read the sample checkout source.",
     "parameters": {"type": "object", "properties": {
         "path": {"type": "string", "enum": ["orders.py"]}},
         "required": ["path"], "additionalProperties": False}, "strict": True},
]


class _NoRedirect(HTTPRedirectHandler):
    """Keep the API credential on the original request."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _post(history):
    """Make one bounded OpenAI request using only the environment key."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key or any(not 33 <= ord(character) <= 126 for character in key):
        raise RuntimeError("Set OPENAI_API_KEY to a nonempty key without whitespace.")
    payload = {"model": "gpt-4.1-mini", "input": history, "tools": TOOLS,
               "instructions": "Inspect the sample with the tools, then answer briefly from its source.",
               "store": False, "parallel_tool_calls": False,
               "tool_choice": "required" if len(history) == 1 else "auto",
               "include": ["reasoning.encrypted_content"]}
    request = Request(_RESPONSES_URL, json.dumps(payload).encode("utf-8"),
                      {"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with build_opener(_NoRedirect()).open(request, timeout=30) as reply:
            raw = reply.read()
    except HTTPError as error:
        code = error.code
        error.close()
        raise RuntimeError(f"OpenAI HTTP error {code}; no retry.") from None
    except (URLError, OSError, HTTPException):
        raise RuntimeError("Could not reach OpenAI; no retry.") from None
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise RuntimeError("OpenAI returned invalid JSON.") from None


def _response_output(response):
    """Require completed output before running any selected function."""
    if not isinstance(response, dict) or response.get("status") != "completed":
        raise RuntimeError("OpenAI response is incomplete or failed; no tool was run.")
    output = response.get("output")
    if response.get("error") is not None or not isinstance(output, list):
        raise RuntimeError("OpenAI returned an invalid response.")
    for item in output:
        if not isinstance(item, dict) or item.get("type") not in ("reasoning", "message", "function_call"):
            raise RuntimeError("OpenAI returned an unsupported output item.")
    return output


def _message_text(item):
    """Read answer text and report refusals explicitly."""
    content = item.get("content")
    if not isinstance(content, list):
        raise RuntimeError("OpenAI returned invalid message content.")
    text = []
    for part in content:
        if not isinstance(part, dict):
            raise RuntimeError("OpenAI returned invalid message content.")
        if part.get("type") == "refusal":
            raise RuntimeError("OpenAI refused the request.")
        if part.get("type") != "output_text" or not isinstance(part.get("text"), str):
            raise RuntimeError("OpenAI returned invalid answer text.")
        text.append(part["text"])
    return "".join(text)


def ask_model(history):
    """Return (complete output, answer, call); exactly one of answer/call is present."""
    output = _response_output(_post(history))
    calls = [item for item in output if item["type"] == "function_call"]
    answer = "".join(_message_text(item) for item in output if item["type"] == "message")
    if len(calls) == 1:
        return output, None, calls[0]
    if calls or not answer.strip():
        raise RuntimeError("OpenAI must return one tool call or a nonempty answer.")
    return output, answer, None


def _tool_details(call):
    """Check the two supported function signatures and retain the original call ID."""
    try:
        name, call_id = call["name"], call["call_id"]
        arguments = json.loads(call["arguments"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("OpenAI returned an invalid function call.") from None
    required = {"path"} if name == "read_file" else set()
    if name not in ("list_files", "read_file"):
        raise RuntimeError("OpenAI selected an unavailable tool.")
    if not isinstance(arguments, dict) or set(arguments) != required:
        raise RuntimeError("OpenAI returned invalid tool arguments.")
    if not isinstance(call_id, str) or not call_id.strip():
        raise RuntimeError("OpenAI returned an invalid call ID.")
    return name, arguments, call_id


def _list_files():
    """List only the allowed regular sample source, excluding escaping symlinks."""
    folder = Path(__file__).resolve().with_name("example_repo").resolve()
    return [file.name for file in folder.iterdir() if file.name == "orders.py"
            and file.is_file() and file.resolve().parent == folder]


def _read_file(path):
    """Read only orders.py resolved inside the sample directory."""
    if path != "orders.py":
        raise ValueError("Only the sample file orders.py can be read.")
    folder = Path(__file__).resolve().with_name("example_repo").resolve()
    source = (folder / path).resolve(strict=True)
    if source.parent != folder or not source.is_file():
        raise ValueError("Sample source must be a regular file inside example_repo.")
    return source.read_text()


def run_tool(call):
    """Print and execute the selected call; return its ready-to-send result item."""
    name, arguments, call_id = _tool_details(call)
    print(f"{name}({json.dumps(arguments)})", flush=True)
    result = {"list_files": _list_files, "read_file": _read_file}[name](**arguments)
    print(result if isinstance(result, str) else json.dumps(result), flush=True)
    return {"type": "function_call_output", "call_id": call_id, "output": json.dumps(result)}
