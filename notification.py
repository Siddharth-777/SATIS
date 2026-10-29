import threading


class NotificationService:
    def __init__(self):
        self._lock = threading.Lock()
        self.notifications = []

    def notify_restaurant(self, order_id, restaurant_name, items):
        if not order_id:
            raise ValueError("Order ID is required")
        if not restaurant_name:
            raise ValueError("Restaurant name is required")
        if not items:
            raise ValueError("Items list is required")
        notification = {
            "order_id": order_id,
            "restaurant_name": restaurant_name,
            "items": items,
            "status": "SENT",
        }
        with self._lock:
            self.notifications.append(notification)
        return notification

    def get_notifications(self):
        with self._lock:
            return list(self.notifications)

    def get_notifications_for_order(self, order_id):
        with self._lock:
            return [n for n in self.notifications if n["order_id"] == order_id]
