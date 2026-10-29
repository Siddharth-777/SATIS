class FestivalDiscount:
    def __init__(self, percentage=0, min_order_amount=0, active=False):
        if percentage < 0 or percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        if min_order_amount < 0:
            raise ValueError("Minimum order amount cannot be negative")
        self.percentage = percentage
        self.min_order_amount = min_order_amount
        self.active = active

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def apply_discount(self, total):
        if not self.active:
            return total
        if total < self.min_order_amount:
            return total
        discount_amount = total * (self.percentage / 100)
        return round(total - discount_amount, 2)

    def get_discount_amount(self, total):
        if not self.active:
            return 0
        if total < self.min_order_amount:
            return 0
        return round(total * (self.percentage / 100), 2)
