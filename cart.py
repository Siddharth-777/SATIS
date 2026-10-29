class Cart:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name, price, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price < 0:
            raise ValueError("Price cannot be negative")
        if item_name in self.items:
            self.items[item_name]["quantity"] += quantity
        else:
            self.items[item_name] = {"price": price, "quantity": quantity}

    def remove_item(self, item_name):
        if item_name not in self.items:
            raise ValueError(f"Item '{item_name}' not in cart")
        del self.items[item_name]

    def get_total(self):
        total = 0
        for item in self.items.values():
            total += item["price"] * item["quantity"]
        return total

    def get_items(self):
        return dict(self.items)

    def clear(self):
        self.items = {}

    def is_empty(self):
        return len(self.items) == 0
