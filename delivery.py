import threading


VALID_TRANSITIONS = {
    "PLACED": "PREPARING",
    "PREPARING": "OUT_FOR_DELIVERY",
    "OUT_FOR_DELIVERY": "DELIVERED",
}


class DeliveryTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.deliveries = {}

    def create_tracking(self, order_id):
        with self._lock:
            if order_id in self.deliveries:
                raise ValueError(f"Tracking already exists for order '{order_id}'")
            self.deliveries[order_id] = "PLACED"
        return "PLACED"

    def update_status(self, order_id, new_status):
        with self._lock:
            if order_id not in self.deliveries:
                raise ValueError(f"No tracking found for order '{order_id}'")
            current_status = self.deliveries[order_id]
            if current_status == "CANCELLED":
                raise ValueError("Cannot update status of a cancelled order")
            if current_status == "DELIVERED":
                raise ValueError("Order already delivered")
            expected_next = VALID_TRANSITIONS.get(current_status)
            if new_status != expected_next:
                raise ValueError(
                    f"Invalid transition from '{current_status}' to '{new_status}'"
                )
            self.deliveries[order_id] = new_status
        return new_status

    def get_status(self, order_id):
        with self._lock:
            if order_id not in self.deliveries:
                raise ValueError(f"No tracking found for order '{order_id}'")
            return self.deliveries[order_id]

    def cancel_delivery(self, order_id):
        with self._lock:
            if order_id not in self.deliveries:
                raise ValueError(f"No tracking found for order '{order_id}'")
            current_status = self.deliveries[order_id]
            if current_status in ("OUT_FOR_DELIVERY", "DELIVERED"):
                raise ValueError(
                    f"Cannot cancel delivery in '{current_status}' status"
                )
            self.deliveries[order_id] = "CANCELLED"
        return "CANCELLED"
