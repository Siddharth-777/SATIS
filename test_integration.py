import concurrent.futures
import pytest
from restaurant import Restaurant
from cart import Cart
from discount import FestivalDiscount
from payment import PaymentProcessor
from notification import NotificationService
from delivery import DeliveryTracker
from order import OrderManager


def test_it01_cart_items_flow_into_order_total():
    cart = Cart()
    cart.add_item("Burger", 250, 2)
    cart.add_item("Fries", 100, 1)
    expected_total = 250 * 2 + 100 * 1

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    order_id = manager.place_order(cart, "Burger Palace")
    order = manager.get_order(order_id)

    assert order["total"] == expected_total
    assert "Burger" in order["items"]
    assert "Fries" in order["items"]
    assert order["items"]["Burger"]["quantity"] == 2


def test_it02_festival_discount_applied_to_order():
    cart = Cart()
    cart.add_item("Pizza", 500, 2)

    discount = FestivalDiscount(percentage=20, min_order_amount=500, active=True)

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    order_id = manager.place_order(cart, "Pizza Place", discount=discount)
    order = manager.get_order(order_id)

    assert order["total"] == 800.0


def test_it03_failed_payment_prevents_order():
    cart = Cart()
    cart.add_item("Sushi", 300, 1)

    payment = PaymentProcessor()
    payment.simulate_failure = True
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    with pytest.raises(ValueError, match="Payment failed"):
        manager.place_order(cart, "Sushi Bar")

    assert len(manager.orders) == 0
    assert len(notification.get_notifications()) == 0
    assert len(delivery.deliveries) == 0


def test_it04_confirmed_order_triggers_notification():
    cart = Cart()
    cart.add_item("Pasta", 400, 1)

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    order_id = manager.place_order(cart, "Italian Bistro")

    notifications = notification.get_notifications_for_order(order_id)
    assert len(notifications) == 1
    assert notifications[0]["restaurant_name"] == "Italian Bistro"
    assert "Pasta" in notifications[0]["items"]


def test_it05_confirmed_order_creates_delivery_tracking():
    cart = Cart()
    cart.add_item("Biryani", 350, 1)

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    order_id = manager.place_order(cart, "Spice Garden")

    status = delivery.get_status(order_id)
    assert status == "PLACED"


def test_it06_cancel_order_refunds_payment():
    cart = Cart()
    cart.add_item("Noodles", 200, 1)

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    order_id = manager.place_order(cart, "Wok Express")
    order = manager.get_order(order_id)
    payment_id = order["payment_id"]

    manager.cancel_order(order_id)

    assert manager.get_order_status(order_id) == "CANCELLED"
    assert payment.get_payment_status(payment_id) == "REFUNDED"
    assert delivery.get_status(order_id) == "CANCELLED"


def test_it07_cancel_out_for_delivery_rejected():
    cart = Cart()
    cart.add_item("Dosa", 150, 2)

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    order_id = manager.place_order(cart, "South Indian Cafe")

    delivery.update_status(order_id, "PREPARING")
    delivery.update_status(order_id, "OUT_FOR_DELIVERY")

    with pytest.raises(ValueError, match="Cannot cancel order"):
        manager.cancel_order(order_id)

    assert manager.get_order_status(order_id) == "CONFIRMED"


def test_it08_empty_cart_cannot_place_order():
    cart = Cart()

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    with pytest.raises(ValueError, match="Cannot place order with empty cart"):
        manager.place_order(cart, "Any Restaurant")

    assert len(manager.orders) == 0


def test_it09_unavailable_item_rejected_in_order_flow():
    restaurant = Restaurant("Fusion Kitchen", {
        "Burger": {"price": 250, "available": True},
        "Lobster": {"price": 1500, "available": False},
    })

    cart = Cart()
    for item_name in restaurant.get_menu():
        if restaurant.is_item_available(item_name):
            cart.add_item(item_name, restaurant.get_item_price(item_name), 1)

    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    order_id = manager.place_order(cart, restaurant.name)
    order = manager.get_order(order_id)

    assert "Lobster" not in order["items"]
    assert "Burger" in order["items"]
    assert order["total"] == 250


def test_it10_peak_load_concurrent_orders():
    payment = PaymentProcessor()
    notification = NotificationService()
    delivery = DeliveryTracker()
    manager = OrderManager(payment, notification, delivery)

    num_orders = 500

    def place_single_order(i):
        cart = Cart()
        cart.add_item(f"Item-{i}", 100, 1)
        return manager.place_order(cart, "Peak Restaurant")

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(place_single_order, i) for i in range(num_orders)]
        order_ids = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(order_ids) == num_orders
    assert len(set(order_ids)) == num_orders
    assert len(notification.get_notifications()) == num_orders
    assert len(delivery.deliveries) == num_orders
