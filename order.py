import threading


class OrderManager:
    def __init__(self, payment_processor, notification_service, delivery_tracker):
        self.payment_processor = payment_processor
        self.notification_service = notification_service
        self.delivery_tracker = delivery_tracker
        self._lock = threading.Lock()
        self._next_order_id = 1
        self.orders = {}

    def place_order(self, cart, restaurant_name, discount=None):
        if cart.is_empty():
            raise ValueError("Cannot place order with empty cart")
        if not restaurant_name:
            raise ValueError("Restaurant name is required")

        items = cart.get_items()
        total = cart.get_total()

        if discount is not None:
            total = discount.apply_discount(total)

        payment_result = self.payment_processor.process_payment(total)
        if not payment_result.success:
            raise ValueError("Payment failed: " + payment_result.message)

        with self._lock:
            order_id = f"ORD-{self._next_order_id:04d}"
            self._next_order_id += 1
            self.orders[order_id] = {
                "restaurant_name": restaurant_name,
                "items": items,
                "total": total,
                "payment_id": payment_result.payment_id,
                "status": "CONFIRMED",
            }

        self.notification_service.notify_restaurant(order_id, restaurant_name, items)
        self.delivery_tracker.create_tracking(order_id)

        return order_id

    def cancel_order(self, order_id):
        if order_id not in self.orders:
            raise ValueError(f"Order '{order_id}' not found")

        order = self.orders[order_id]
        if order["status"] == "CANCELLED":
            raise ValueError(f"Order '{order_id}' is already cancelled")

        delivery_status = self.delivery_tracker.get_status(order_id)
        if delivery_status in ("OUT_FOR_DELIVERY", "DELIVERED"):
            raise ValueError(
                f"Cannot cancel order in '{delivery_status}' status"
            )

        self.delivery_tracker.cancel_delivery(order_id)
        self.payment_processor.refund(order["payment_id"])
        order["status"] = "CANCELLED"

        return True

    def get_order_status(self, order_id):
        if order_id not in self.orders:
            raise ValueError(f"Order '{order_id}' not found")
        return self.orders[order_id]["status"]

    def get_order(self, order_id):
        if order_id not in self.orders:
            raise ValueError(f"Order '{order_id}' not found")
        return dict(self.orders[order_id])
