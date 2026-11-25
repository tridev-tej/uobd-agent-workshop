# Build a tiny agent loop

Python 3.9 or newer. No packages to install.

Open `agent.py` and fill its single TODO in `run()`. The question, history,
four-turn loop and stopping limit are supplied. Follow the five steps in its
docstring. Keep `example_repo/orders.py` unchanged.

Two helpers are provided in `helpers.py`:

- `ask_model(history)` returns `(output, answer, call)`. `output` contains every
  response item. Exactly one of `answer` or `call` is present; the other is `None`.
- `run_tool(call)` prints and executes the selected file tool, then returns a
  result item with its original call ID, ready for history.

First run these from this folder:

```sh
python3 agent.py
python3 check.py
```

Both initially fail with **Fill in the agent loop in agent.py.** This is expected.
After completing the TODO, `python3 check.py` should pass. The checker uses local
helper doubles, so it needs no key or network. It checks tool results and complete
history, stopping at an answer, and the four-turn limit.

To run your completed loop with OpenAI, create your own
[API key](https://platform.openai.com/api-keys). You need network access and an
API account with access to `gpt-4.1-mini`. In macOS Terminal using zsh:

```sh
read -rs 'OPENAI_API_KEY?OpenAI API key: '
printf '\n'
export OPENAI_API_KEY
python3 agent.py
unset OPENAI_API_KEY
```

The prompt hides the key; do not put it in source files. The helper reads it only
from `OPENAI_API_KEY`. Live requests send the question, sample filenames and read
source to OpenAI using `store=false`. The model selects real `list_files` and
`read_file` calls. Their names, arguments and actual results appear immediately.
Tools can only list/read the sample source; they cannot edit files or run commands.
API errors stop the run without retries or a prepared answer.
