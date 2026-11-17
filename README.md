# A tiny Cursor-style coding MVP

ACM University of Birmingham Dubai · Tejesh Vaish · 17 November 2026 GST

Two product actions about `example_repo/orders.py`:

1. Ask: **What does checkout() in orders.py do?**
2. Propose: **Rename cart to items in checkout() in orders.py.**

The flow is **ask → list + read → answer or propose a diff → human review**.
Design inspiration: [Cursor Agent](https://cursor.com/help/ai-features/agent)
and [reviewing changes](https://docs.cursor.com/en/agent/review).
Cursor can edit files and run commands. The ask and preview commands stop at an
answer or proposed patch. The approval exercise adds human-approved application
in memory and two behavior checks.
The model still has only the two read-only tools.

The model choices and final answers are **prepared locally** for this example.
Python runs the real `list_files()` and `read_file(path)` functions on files in
`example_repo/`, beside `agent.py`. No API requests, SDKs or external dependencies.

The [sample folder](example_repo/) contains the checkout source, a quick check, and a small skill adapted from [TStack](https://github.com/tridev-tej/tstack).

## Optional OpenAI setup

The workshop runs offline. For a separate live model experiment, create your
own key at [OpenAI API Keys](https://platform.openai.com/api-keys).

macOS/Linux:

```sh
export OPENAI_API_KEY="your-own-key"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-own-key"
```

## How an agent uses tools

Open `example_repo/orders.py`. Explain what `checkout()` does, then try the
prepared missing-file case:

```sh
python3 agent.py
python3 agent.py --missing
```

Normal output:

```text
list_files()
['README.md', 'orders.py']
read_file("orders.py")
def checkout(cart):
    return sum(item["price"] for item in cart)
checkout() adds the prices of all cart items and returns the total.
```

With `--missing`:

```text
list_files()
['README.md', 'app.py']
orders.py could not be found.
```

The missing-file run supplies a simulated list and makes zero `read_file` calls.
The normal run lists actual regular files in `example_repo/`, sorted by name,
and reads from that folder regardless of the terminal's current directory.

## Review a proposed edit

Preview a patch, then try the same request with the source file missing:

```sh
python3 agent.py --preview
python3 agent.py --missing --preview
```

With `--preview`, the same `list_files()` then `read_file("orders.py")` calls
run. The final answer is a patch derived from the actual read result using
Python's standard-library `difflib`:

```diff
--- a/orders.py
+++ b/orders.py
@@ -1,2 +1,2 @@
-def checkout(cart):
-    return sum(item["price"] for item in cart)
+def checkout(items):
+    return sum(item["price"] for item in items)
```

Review the two changed lines: the parameter and the loop source. The CLI ends
without changing the file. The preview CLI has no apply mode, shell tool or
general-purpose renamer.

With `--missing --preview`, the result is the same truthful missing-file answer
shown above, with no read and no patch.

## Code in a few lines

`ask_repo(question, model, tools)` passes history and available tool names to the
injected model. The model returns a named tool call or an answer.
Python dispatches the call and sends its result back in history, in order.
An answer stops the loop. Four model turns is the limit; unexpected errors stop execution.
`demo(missing=False, preview=False)` supplies exactly two read-only tools and
returns the trace and answer or patch.
The prepared model checks what `list_files()` actually returned before choosing
whether to read `orders.py`. Both actions use the same `ask_repo` loop. The fixed
preview changes only the sample's parameter and loop source in a proposed copy.

## Approve and test a patch

Approve the diff, apply it in memory, and test its behavior.

Unzip the student kit from your instructor, or download it from the
[GitHub release](https://github.com/tridev-tej/uobd-agent-workshop/releases/latest)
and open a terminal in the extracted folder.
You can also clone the repository:

```sh
git clone https://github.com/tridev-tej/uobd-agent-workshop.git
cd uobd-agent-workshop
```

Python 3.9 or newer and the repository files are enough. Once downloaded, everything runs
offline. First try the instructor version:

```sh
python3 approve_patch.py
python3 approve_patch.py --stale
```

Both show the previewed diff first. Type `y` to approve. A fresh approval
applies the two-line rename to the in-memory `orders.py`, then checks an empty
cart totals `0` and a two-item cart totals `30`. Any other response declines,
keeps current source and skips checks. `--stale` adds a newline after preview;
approving refuses the edit and asks for a fresh diff. No retry. No disk files
change, and the model gains no write or shell tool.

Edits to `example_repo/orders.py` appear in the preview, but checks accept only
the fixed built-in checkout proposal. Editable file contents cannot authorize
code execution.

The repository clone includes the completed `patch_exercise.py`. Run the checker:

```sh
python3 check_patch.py
```

The checker should pass in the repository clone. The downloadable student kit
contains the starter exercise, which initially raises `NotImplementedError`.
In the student kit, open `patch_exercise.py` in your editor and replace the raise
under its single TODO with your own
`apply_edit(current, before, proposed, approved)` implementation. Its docstring
gives the whole contract: decline returns current; stale approval raises the
specified error; fresh approval returns proposed. Approval and checks are
already wired outside this function. Then run:

```sh
python3 check_patch.py
python3 patch_exercise.py
python3 patch_exercise.py --stale
```

The checker should report **10 tests, OK**. Try `y` on both student runs, then
try declining. Success and decline exit `0`; stale approval exits `1`.
`python3 check_patch.py --reference` runs the same cases on the instructor
solution. The unfinished exercise is excluded from `unittest discover`.

For homework, check whether the approved rename preserves existing callers
that use `cart=`. Follow the steps in [HOMEWORK.md](HOMEWORK.md).

## Five-minute pair exercise in Colab

1. Open `workshop.ipynb` using Colab's **Upload notebook** option and connect.
2. Upload **`uobd-workshop-student-kit.zip`** into the runtime folder using the
   **Files** pane. Add a temporary code cell before the original cells and run
   this one-line setup:

   ```python
   from zipfile import ZipFile; ZipFile("uobd-workshop-student-kit.zip").extractall(members=["agent.py", "example_repo/README.md", "example_repo/orders.py"])
   ```

3. Open `example_repo/orders.py` in the Files pane. Read the question with your
   partner. Predict the normal tool calls and where the loop should stop if
   `orders.py` is missing.
4. Run both prepared code cells unchanged. Inspect the calls, results and answers.
5. Optionally run the preview cell. Review the two changed lines together.

The setup extracts `agent.py` and the two `example_repo/` files from the ZIP.
Notebook outputs are saved empty. For terminal use, follow
[Approve and test a patch](#approve-and-test-a-patch) above.

Credit: this example uses the model → tool → result loop used at Lumian.

## Follow-up: build, break, fix

Keep the same question and two tools. What if `list_files()` includes `orders.py`,
but `read_file("orders.py")` raises `FileNotFoundError`?

The repo and [student ZIP](https://github.com/tridev-tej/uobd-agent-workshop/releases/latest)
include a `before-fix/` subdirectory containing
the unfixed agent and the same test. From the ZIP root, run these in order:

```sh
python3 before-fix/test_agent.py
python3 test_agent.py
```

The first run shows a `FileNotFoundError: orders.py` traceback and fails.
The second repeats the identical test against the fix and passes.
Run `python3 test_agent.py` from a repo checkout to test the fix.

The small `try/except` catches `FileNotFoundError` only for `read_file` and records
`{'error': 'file_not_found'}` through the usual tool-result history. The prepared
model uses that result to answer: `orders.py could not be read because it is missing.`
Other failures still raise. Report what actually happened when a tool ran.

## Two more reliability exercises

Run the prepared checks from the repo or workshop ZIP root:

```sh
python3 test_agent_limits.py -v
```

1. The model requests unregistered `write_file` with `{"path": "orders.py"}`.
   No function runs. Python records `{"error": "unknown_tool"}` in the usual
   history and trace, then the prepared model explains the restriction.
2. The model keeps requesting allowed `list_files`. After exactly four model
   calls and four tool calls, the existing limit raises
   `RuntimeError("Model did not answer within 4 turns.")`.

Ask students: **What happens if the model requests an unapproved write? What
happens if it does not stop?**

Both tests should pass: the second test expects the limit error. Both product
actions use the same offline prepared model and two read-only tools.

Check the preview CLI and missing-source behavior, then run all checks:

```sh
python3 test_agent_preview.py -v
python3 test_agent_example_repo.py -v
python3 -B -m unittest discover -v
```
