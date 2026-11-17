"""Decide whether the reviewed source can be applied."""


def apply_edit(current, before, proposed, approved):
    """Select source without writing files or running checks.

    current is the file content now; before is the snapshot used for the diff;
    proposed is the reviewed replacement; approved is the human's decision.
    If declined, return current even when it differs from before.
    If approved but current != before, raise
    ValueError("File changed since preview. Review a fresh diff.").
    Otherwise, return proposed. Check decline before checking freshness.
    """
    if not approved:
        return current
    if current != before:
        raise ValueError("File changed since preview. Review a fresh diff.")
    return proposed


if __name__ == "__main__":
    from approve_patch import main

    raise SystemExit(main(apply_edit))
