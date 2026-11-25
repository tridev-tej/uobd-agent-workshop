"""Fill in a tiny agent loop using the supplied OpenAI and file helpers."""

from helpers import ask_model, run_tool


def run():
    """TODO: Fill the loop body with these five steps.

    Ask the model.
    Remember its complete output.
    Print the answer and stop.
    Execute the chosen tool.
    Remember the tool result.
    """
    question = "What does checkout() in orders.py do?"
    history = [{"role": "user", "content": question}]
    for _ in range(4):
        raise NotImplementedError("Fill in the agent loop in agent.py.")
    raise RuntimeError("Model did not answer within 4 turns.")


if __name__ == "__main__":
    run()
