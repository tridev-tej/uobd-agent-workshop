"""Review, approve, apply in memory, then check checkout behavior."""

import argparse

from agent import checkout_proposal, demo


def apply_edit(current, before, proposed, approved):
    """Keep declined source, refuse stale approval, or select the proposal."""
    if not approved:
        return current
    if current != before:
        raise ValueError("File changed since preview. Review a fresh diff.")
    return proposed


def verify_checkout(source):
    """Execute only the fixed built-in candidate and check two real carts."""
    trusted = 'def checkout(items):\n    return sum(item["price"] for item in items)'
    if source != trusted:
        raise ValueError("Only the built-in checkout proposal can run.")
    namespace = {"__builtins__": {"sum": sum}}
    exec(source, namespace)
    checkout = namespace["checkout"]
    cases = (
        ("empty cart", [], 0),
        ("two-item cart", [{"price": 10}, {"price": 20}], 30),
    )
    for label, cart, expected in cases:
        actual = checkout(cart)
        if actual != expected:
            raise AssertionError(f"{label}: expected {expected}, got {actual}.")
        print(f"PASS {label}: {actual}")


def main(apply_edit):
    """Keep approval, in-memory application and checks outside the model."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stale", action="store_true",
                        help="simulate an external change after the preview")
    args = parser.parse_args()
    trace, diff = demo(preview=True)
    before = trace[-1]["result"]
    proposed = checkout_proposal(before)
    files = {"orders.py": before}
    print(diff)
    if args.stale:
        files["orders.py"] += "\n"
    approved = input("Apply this change? Type y to approve: ").strip().lower() == "y"
    try:
        selected = apply_edit(files["orders.py"], before, proposed, approved)
    except NotImplementedError as error:
        print(f"{error} Then run python3 check_patch.py.")
        return 1
    except ValueError as error:
        print(f"Refused: {error} Current source kept. Checks skipped.")
        return 1
    if not approved:
        print("Declined. Current source kept. Checks skipped.")
        return 0
    files["orders.py"] = selected
    try:
        verify_checkout(files["orders.py"])
    except (ValueError, AssertionError) as error:
        print(f"Checks refused or failed: {error}")
        return 1
    print("Applied to in-memory orders.py. Checks passed (2/2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(apply_edit))
