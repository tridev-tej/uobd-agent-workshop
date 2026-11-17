def checkout(cart):
    return sum(item["price"] for item in cart)
