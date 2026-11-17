# Homework · Keep existing callers working

**Time:** 15–20 minutes. Start after finishing `patch_exercise.py`.

The approval exercise checks call `checkout(...)` by position. A caller in
another file already calls it by name. Does the approved rename still work for
that caller?

1. Run `python3 approve_patch.py` and review the diff. Copy the two added Python lines,
   without the leading `+` signs, into a new file named `homework_orders.py`.
   Keep the indentation in the function body. Make your edits in that file.
2. Put this code in `homework_check.py` in the same directory:

   ```python
   from homework_orders import checkout

   cart = [{"price": 7}, {"price": 3}]
   assert checkout([]) == 0
   assert checkout(cart) == 10
   assert checkout(cart=cart) == 10
   print("All three checkout checks passed.")
   ```

3. Run `python3 homework_check.py`. Record which call fails and why.
4. Edit `homework_orders.py` so the body uses `items` and callers can still use
   `cart=`. Rerun the same three checks and capture the passing output.

Submit the diff for `homework_orders.py`, the failing and passing output, and one
sentence explaining what callers depended on in the original function.
