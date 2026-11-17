# Checkout example

Open `orders.py`. The checkout function adds the prices in a cart.

From this folder, run the example check with Python 3:

```sh
python3 -c 'from orders import checkout; assert checkout(cart=[{"price": 7}, {"price": 3}]) == 10'
```

The [example skill](.cursor/skills/review-checkout/SKILL.md) describes how to
review a checkout patch. Open this folder as a Cursor workspace to try it.
See [TStack](https://github.com/tridev-tej/tstack) for the full setup.
