import pytest
from unittest.mock import MagicMock
from restaurant import Restaurant, RestaurantBrowser
from cart import Cart
from discount import FestivalDiscount
from payment import PaymentProcessor, PaymentResult
from notification import NotificationService
from delivery import DeliveryTracker
from order import OrderManager


def test_ut01_browse_restaurants_returns_names():
    browser = RestaurantBrowser()
    r1 = Restaurant("Pizza Palace", {"Pizza": {"price": 300, "available": True}})
    r2 = Restaurant("Burger Barn", {"Burger": {"price": 200, "available": True}})
    browser.add_restaurant(r1)
    browser.add_restaurant(r2)
    result = browser.browse()
    assert result == ["Pizza Palace", "Burger Barn"]


def test_ut02_get_menu_returns_items():
    menu = {
        "Pasta": {"price": 400, "available": True},
        "Salad": {"price": 150, "available": False},
    }
    restaurant = Restaurant("Italian Bistro", menu)
    result = restaurant.get_menu()
    assert "Pasta" in result
    assert "Salad" in result
    assert result["Pasta"]["price"] == 400


def test_ut03_available_item_returns_true():
    restaurant = Restaurant("Test", {"Burger": {"price": 200, "available": True}})
    assert restaurant.is_item_available("Burger") is True


def test_ut04_unavailable_item_returns_false():
    restaurant = Restaurant("Test", {"Sushi": {"price": 500, "available": False}})
    assert restaurant.is_item_available("Sushi") is False


def test_ut05_nonexistent_item_raises_error():
    restaurant = Restaurant("Test", {"Burger": {"price": 200, "available": True}})
    with pytest.raises(ValueError, match="not found in menu"):
        restaurant.is_item_available("Taco")


def test_ut06_find_nonexistent_restaurant_raises_error():
    browser = RestaurantBrowser()
    browser.add_restaurant(Restaurant("Pizza Palace", {}))
    with pytest.raises(ValueError, match="not found"):
        browser.find_restaurant("Ghost Kitchen")


def test_ut07_add_item_to_cart():
    cart = Cart()
    cart.add_item("Burger", 200, 2)
    items = cart.get_items()
    assert "Burger" in items
    assert items["Burger"]["price"] == 200
    assert items["Burger"]["quantity"] == 2


def test_ut08_add_zero_quantity_raises_error():
    cart = Cart()
    with pytest.raises(ValueError, match="Quantity must be positive"):
        cart.add_item("Burger", 200, 0)


def test_ut09_add_negative_quantity_raises_error():
    cart = Cart()
    with pytest.raises(ValueError, match="Quantity must be positive"):
        cart.add_item("Burger", 200, -1)


def test_ut10_remove_item_from_cart():
    cart = Cart()
    cart.add_item("Burger", 200, 1)
    cart.remove_item("Burger")
    assert cart.is_empty()


def test_ut11_remove_nonexistent_item_raises_error():
    cart = Cart()
    with pytest.raises(ValueError, match="not in cart"):
        cart.remove_item("Taco")


def test_ut12_get_total_multiple_items():
    cart = Cart()
    cart.add_item("Burger", 250, 2)
    cart.add_item("Fries", 100, 3)
    assert cart.get_total() == 250 * 2 + 100 * 3


def test_ut13_cart_initially_empty():
    cart = Cart()
    assert cart.is_empty() is True
    assert cart.get_total() == 0


def test_ut14_clear_cart_empties():
    cart = Cart()
    cart.add_item("Burger", 200, 1)
    cart.clear()
    assert cart.is_empty() is True


def test_ut15_add_negative_price_raises_error():
    cart = Cart()
    with pytest.raises(ValueError, match="Price cannot be negative"):
        cart.add_item("Burger", -50, 1)


def test_ut16_active_discount_applies_correctly():
    discount = FestivalDiscount(percentage=20, min_order_amount=500, active=True)
    result = discount.apply_discount(1000)
    assert result == 800.0


def test_ut17_inactive_discount_returns_original():
    discount = FestivalDiscount(percentage=20, min_order_amount=500, active=False)
    result = discount.apply_discount(1000)
    assert result == 1000


def test_ut18_below_min_amount_no_discount():
    discount = FestivalDiscount(percentage=20, min_order_amount=500, active=True)
    result = discount.apply_discount(400)
    assert result == 400


def test_ut19_exact_min_amount_boundary_applies():
    discount = FestivalDiscount(percentage=10, min_order_amount=500, active=True)
    result = discount.apply_discount(500)
    assert result == 450.0


def test_ut20_invalid_percentage_raises_error():
    with pytest.raises(ValueError, match="Discount percentage must be between"):
        FestivalDiscount(percentage=150)
    with pytest.raises(ValueError, match="Discount percentage must be between"):
        FestivalDiscount(percentage=-10)


def test_ut21_activate_deactivate_discount():
    discount = FestivalDiscount(percentage=10, min_order_amount=0, active=False)
    assert discount.active is False
    discount.activate()
    assert discount.active is True
    assert discount.apply_discount(100) == 90.0
    discount.deactivate()
    assert discount.active is False
    assert discount.apply_discount(100) == 100


def test_ut22_process_payment_success():
    processor = PaymentProcessor()
    result = processor.process_payment(500)
    assert result.success is True
    assert result.payment_id == "PAY-0001"
    assert processor.get_payment_status("PAY-0001") == "COMPLETED"


def test_ut23_zero_amount_raises_error():
    processor = PaymentProcessor()
    with pytest.raises(ValueError, match="Payment amount must be positive"):
        processor.process_payment(0)


def test_ut24_negative_amount_raises_error():
    processor = PaymentProcessor()
    with pytest.raises(ValueError, match="Payment amount must be positive"):
        processor.process_payment(-100)


def test_ut25_refund_payment_success():
    processor = PaymentProcessor()
    processor.process_payment(500)
    result = processor.refund("PAY-0001")
    assert result.success is True
    assert processor.get_payment_status("PAY-0001") == "REFUNDED"


def test_ut26_refund_nonexistent_raises_error():
    processor = PaymentProcessor()
    with pytest.raises(ValueError, match="not found"):
        processor.refund("PAY-9999")


def test_ut27_double_refund_raises_error():
    processor = PaymentProcessor()
    processor.process_payment(500)
    processor.refund("PAY-0001")
    with pytest.raises(ValueError, match="already refunded"):
        processor.refund("PAY-0001")


def test_ut28_simulated_payment_failure():
    processor = PaymentProcessor()
    processor.simulate_failure = True
    result = processor.process_payment(500)
    assert result.success is False
    assert result.payment_id is None


def test_ut29_notify_restaurant_success():
    service = NotificationService()
    result = service.notify_restaurant("ORD-0001", "Pizza Palace", {"Pizza": 2})
    assert result["order_id"] == "ORD-0001"
    assert result["restaurant_name"] == "Pizza Palace"
    assert result["status"] == "SENT"
    assert len(service.get_notifications()) == 1


def test_ut30_empty_order_id_raises_error():
    service = NotificationService()
    with pytest.raises(ValueError, match="Order ID is required"):
        service.notify_restaurant("", "Pizza Palace", {"Pizza": 2})


def test_ut31_empty_restaurant_name_raises_error():
    service = NotificationService()
    with pytest.raises(ValueError, match="Restaurant name is required"):
        service.notify_restaurant("ORD-0001", "", {"Pizza": 2})


def test_ut32_get_notifications_for_order():
    service = NotificationService()
    service.notify_restaurant("ORD-0001", "Pizza Palace", {"Pizza": 2})
    service.notify_restaurant("ORD-0002", "Burger Barn", {"Burger": 1})
    result = service.get_notifications_for_order("ORD-0001")
    assert len(result) == 1
    assert result[0]["order_id"] == "ORD-0001"


def test_ut33_create_tracking_success():
    tracker = DeliveryTracker()
    status = tracker.create_tracking("ORD-0001")
    assert status == "PLACED"
    assert tracker.get_status("ORD-0001") == "PLACED"


def test_ut34_duplicate_tracking_raises_error():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    with pytest.raises(ValueError, match="Tracking already exists"):
        tracker.create_tracking("ORD-0001")


def test_ut35_transition_placed_to_preparing():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    result = tracker.update_status("ORD-0001", "PREPARING")
    assert result == "PREPARING"
    assert tracker.get_status("ORD-0001") == "PREPARING"


def test_ut36_transition_preparing_to_out_for_delivery():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    tracker.update_status("ORD-0001", "PREPARING")
    result = tracker.update_status("ORD-0001", "OUT_FOR_DELIVERY")
    assert result == "OUT_FOR_DELIVERY"


def test_ut37_transition_out_for_delivery_to_delivered():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    tracker.update_status("ORD-0001", "PREPARING")
    tracker.update_status("ORD-0001", "OUT_FOR_DELIVERY")
    result = tracker.update_status("ORD-0001", "DELIVERED")
    assert result == "DELIVERED"


def test_ut38_invalid_transition_raises_error():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    with pytest.raises(ValueError, match="Invalid transition"):
        tracker.update_status("ORD-0001", "DELIVERED")


def test_ut39_update_delivered_order_raises_error():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    tracker.update_status("ORD-0001", "PREPARING")
    tracker.update_status("ORD-0001", "OUT_FOR_DELIVERY")
    tracker.update_status("ORD-0001", "DELIVERED")
    with pytest.raises(ValueError, match="Order already delivered"):
        tracker.update_status("ORD-0001", "PREPARING")


def test_ut40_cancel_delivery_from_placed():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    result = tracker.cancel_delivery("ORD-0001")
    assert result == "CANCELLED"
    assert tracker.get_status("ORD-0001") == "CANCELLED"


def test_ut41_cancel_out_for_delivery_raises_error():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    tracker.update_status("ORD-0001", "PREPARING")
    tracker.update_status("ORD-0001", "OUT_FOR_DELIVERY")
    with pytest.raises(ValueError, match="Cannot cancel delivery"):
        tracker.cancel_delivery("ORD-0001")


def test_ut42_update_cancelled_order_raises_error():
    tracker = DeliveryTracker()
    tracker.create_tracking("ORD-0001")
    tracker.cancel_delivery("ORD-0001")
    with pytest.raises(ValueError, match="Cannot update status of a cancelled order"):
        tracker.update_status("ORD-0001", "PREPARING")


def test_ut43_place_order_success():
    mock_cart = MagicMock()
    mock_cart.is_empty.return_value = False
    mock_cart.get_items.return_value = {"Burger": {"price": 200, "quantity": 1}}
    mock_cart.get_total.return_value = 200

    mock_payment = MagicMock()
    mock_payment.process_payment.return_value = MagicMock(
        success=True, payment_id="PAY-0001", message="OK"
    )
    mock_notification = MagicMock()
    mock_delivery = MagicMock()

    manager = OrderManager(mock_payment, mock_notification, mock_delivery)
    order_id = manager.place_order(mock_cart, "Test Restaurant")

    assert order_id == "ORD-0001"
    assert manager.get_order_status("ORD-0001") == "CONFIRMED"
    mock_payment.process_payment.assert_called_once_with(200)
    mock_notification.notify_restaurant.assert_called_once()
    mock_delivery.create_tracking.assert_called_once_with("ORD-0001")


def test_ut44_place_order_empty_cart_raises_error():
    mock_cart = MagicMock()
    mock_cart.is_empty.return_value = True

    manager = OrderManager(MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ValueError, match="Cannot place order with empty cart"):
        manager.place_order(mock_cart, "Test Restaurant")


def test_ut45_place_order_payment_failure_raises_error():
    mock_cart = MagicMock()
    mock_cart.is_empty.return_value = False
    mock_cart.get_items.return_value = {"Burger": {"price": 200, "quantity": 1}}
    mock_cart.get_total.return_value = 200

    mock_payment = MagicMock()
    mock_payment.process_payment.return_value = MagicMock(
        success=False, payment_id=None, message="Declined"
    )
    mock_notification = MagicMock()
    mock_delivery = MagicMock()

    manager = OrderManager(mock_payment, mock_notification, mock_delivery)

    with pytest.raises(ValueError, match="Payment failed"):
        manager.place_order(mock_cart, "Test Restaurant")

    mock_notification.notify_restaurant.assert_not_called()
    mock_delivery.create_tracking.assert_not_called()


def test_ut46_cancel_order_success():
    mock_payment = MagicMock()
    mock_delivery = MagicMock()
    mock_delivery.get_status.return_value = "PLACED"

    manager = OrderManager(mock_payment, MagicMock(), mock_delivery)
    manager.orders["ORD-0001"] = {
        "restaurant_name": "Test",
        "items": {"Burger": {"price": 200, "quantity": 1}},
        "total": 200,
        "payment_id": "PAY-0001",
        "status": "CONFIRMED",
    }

    result = manager.cancel_order("ORD-0001")

    assert result is True
    assert manager.orders["ORD-0001"]["status"] == "CANCELLED"
    mock_delivery.cancel_delivery.assert_called_once_with("ORD-0001")
    mock_payment.refund.assert_called_once_with("PAY-0001")


def test_ut47_cancel_already_cancelled_raises_error():
    manager = OrderManager(MagicMock(), MagicMock(), MagicMock())
    manager.orders["ORD-0001"] = {
        "restaurant_name": "Test",
        "items": {},
        "total": 200,
        "payment_id": "PAY-0001",
        "status": "CANCELLED",
    }

    with pytest.raises(ValueError, match="already cancelled"):
        manager.cancel_order("ORD-0001")


def test_ut48_get_order_status():
    manager = OrderManager(MagicMock(), MagicMock(), MagicMock())
    manager.orders["ORD-0001"] = {
        "restaurant_name": "Test",
        "items": {},
        "total": 100,
        "payment_id": "PAY-0001",
        "status": "CONFIRMED",
    }
    assert manager.get_order_status("ORD-0001") == "CONFIRMED"


def test_ut49_get_nonexistent_order_raises_error():
    manager = OrderManager(MagicMock(), MagicMock(), MagicMock())
    with pytest.raises(ValueError, match="not found"):
        manager.get_order_status("ORD-9999")


def test_ut50_place_order_empty_restaurant_raises_error():
    mock_cart = MagicMock()
    mock_cart.is_empty.return_value = False

    manager = OrderManager(MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ValueError, match="Restaurant name is required"):
        manager.place_order(mock_cart, "")


















































TEST_PLAN = """
SOFTWARE TEST PLAN
Project Name: Online Food Delivery System (OFDS)
Document ID: STP-001
Version: 1.0
Testing Type: Unit Testing and Integration Testing

1. Objective
The objective of this test plan is to verify that the Online Food Delivery System (OFDS)
works correctly through unit testing and integration testing. Unit tests validate each
module independently in isolation, while integration tests verify that multiple modules
work together to deliver complete business workflows including order placement, payment
processing, discount application, restaurant notification, delivery tracking, and order
cancellation.

2. Functional Requirements
- The system shall allow customers to browse restaurants and view their menus.
- The system shall allow customers to add items to a cart with a positive quantity and
  non-negative price.
- The system shall allow customers to remove items from the cart.
- The system shall calculate the correct total from items in the cart.
- The system shall apply festival discounts only when the discount is active and the order
  meets the minimum order amount.
- The system shall process online payments and reject invalid payment amounts.
- The system shall allow payment refunds for completed payments.
- The system shall prevent order placement when the cart is empty.
- The system shall require a restaurant name when placing an order.
- The system shall notify the restaurant when an order is confirmed.
- The system shall create delivery tracking when an order is confirmed.
- The system shall follow valid delivery status transitions
  (PLACED -> PREPARING -> OUT_FOR_DELIVERY -> DELIVERED).
- The system shall allow order cancellation only when the delivery has not yet reached
  OUT_FOR_DELIVERY or DELIVERED status.
- The system shall refund payment when an order is cancelled.
- The system shall generate unique order IDs for every order, even under concurrent load.

3. Non-Functional Requirements
- Reliability: The system shall handle 500 concurrent orders without data loss, duplicate
  order IDs, or missing notifications and tracking records.
- Correctness: All monetary calculations including totals and discounts shall be
  mathematically accurate with proper rounding to two decimal places.
- Performance: Peak-load order placement of 500 concurrent orders shall complete within
  a few seconds.
- Error Handling: The system shall raise clear and specific error messages (ValueError)
  for all invalid operations such as empty carts, invalid quantities, invalid payment
  amounts, and invalid delivery transitions.
- Maintainability: Each module shall be independently testable with clear separation of
  concerns between restaurant browsing, cart management, discounts, payments,
  notifications, delivery tracking, and order management.

4. Features to Be Tested
- Restaurant browsing and menu viewing
- Cart management (add items, remove items, calculate total, clear cart)
- Festival discount calculation, activation, and deactivation
- Payment processing, simulated failure, and refund handling
- Restaurant notification on order confirmation
- Delivery tracking creation, status transitions, and cancellation
- Order placement with validation, cancellation with eligibility checks, and status retrieval
- Thread-safe concurrent order placement under simulated peak load

5. Functions to Be Tested
- Restaurant class: __init__, get_menu, is_item_available, get_item_price
- RestaurantBrowser class: add_restaurant, browse, find_restaurant
- Cart class: __init__, add_item, remove_item, get_total, get_items, clear, is_empty
- FestivalDiscount class: __init__, activate, deactivate, apply_discount, get_discount_amount
- PaymentProcessor class: __init__, process_payment, refund, get_payment_status
- PaymentResult class: __init__ (success, payment_id, message)
- NotificationService class: __init__, notify_restaurant, get_notifications,
  get_notifications_for_order
- DeliveryTracker class: __init__, create_tracking, update_status, get_status, cancel_delivery
- OrderManager class: __init__, place_order, cancel_order, get_order_status, get_order

6. Non-Functional Testing
- Peak-Load Test (IT10): 500 orders are placed concurrently using
  concurrent.futures.ThreadPoolExecutor with 50 worker threads. Each thread creates its
  own Cart, adds one item, and calls place_order on a shared OrderManager. The test then
  asserts that all 500 order IDs are unique, none are lost, and every order has a
  corresponding notification and delivery tracking record. This validates the thread safety
  of OrderManager (threading.Lock around order ID generation), PaymentProcessor,
  NotificationService, and DeliveryTracker under simulated festival dinner-hour load.
- Error Handling Tests: Multiple unit tests (UT05, UT06, UT08, UT09, UT11, UT15, UT20,
  UT23, UT24, UT26, UT27, UT30, UT31, UT34, UT38, UT39, UT41, UT42, UT44, UT45, UT47,
  UT49, UT50) verify that invalid inputs raise appropriate ValueError exceptions with
  descriptive messages using pytest.raises.
- Reliability Tests: Integration tests IT03, IT06, IT07, and IT08 verify that failures or
  invalid states in one step correctly prevent or roll back downstream operations.

7. Test Cases

| Test Case ID | Test Scenario | Test Input/Action | Expected Result |
|---|---|---|---|
| UT01 | Browse restaurants returns names | Add two restaurants to browser, call browse() | Returns list with both restaurant names |
| UT02 | Get menu returns items | Create restaurant with two menu items, call get_menu() | Returns dict with both items and correct prices |
| UT03 | Available item returns True | Call is_item_available for an available item | Returns True |
| UT04 | Unavailable item returns False | Call is_item_available for an unavailable item | Returns False |
| UT05 | Non-existent item raises error | Call is_item_available for item not in menu | Raises ValueError with not found in menu |
| UT06 | Find non-existent restaurant raises error | Call find_restaurant with unknown name | Raises ValueError with not found |
| UT07 | Add item to cart | Add Burger at price 200 quantity 2 | Item in cart with correct price and quantity |
| UT08 | Add zero quantity raises error | Call add_item with quantity 0 | Raises ValueError with Quantity must be positive |
| UT09 | Add negative quantity raises error | Call add_item with quantity -1 | Raises ValueError with Quantity must be positive |
| UT10 | Remove item from cart | Add item then remove it | Cart is empty |
| UT11 | Remove non-existent item raises error | Call remove_item for item not in cart | Raises ValueError with not in cart |
| UT12 | Get total with multiple items | Add Burger(250x2) and Fries(100x3) | Total equals 800 |
| UT13 | Cart initially empty | Create new Cart instance | is_empty returns True and total is 0 |
| UT14 | Clear cart empties it | Add item then call clear() | is_empty returns True |
| UT15 | Add negative price raises error | Call add_item with price -50 | Raises ValueError with Price cannot be negative |
| UT16 | Active discount applies correctly | Apply 20 percent discount on 1000 with min 500 active | Returns 800.0 |
| UT17 | Inactive discount returns original | Apply discount with active=False on 1000 | Returns 1000 unchanged |
| UT18 | Below min amount no discount | Apply 20 percent discount on 400 with min 500 active | Returns 400 unchanged |
| UT19 | Exact min amount boundary applies | Apply 10 percent discount on 500 with min 500 active | Returns 450.0 |
| UT20 | Invalid percentage raises error | Create FestivalDiscount with percentage 150 or -10 | Raises ValueError for both |
| UT21 | Activate and deactivate discount | Toggle active flag and verify behavior each time | Applies when active and does not apply when inactive |
| UT22 | Process payment success | Call process_payment with amount 500 | Returns success True with payment_id PAY-0001 |
| UT23 | Zero amount raises error | Call process_payment with amount 0 | Raises ValueError |
| UT24 | Negative amount raises error | Call process_payment with amount -100 | Raises ValueError |
| UT25 | Refund payment success | Process payment then call refund | Status changes to REFUNDED |
| UT26 | Refund non-existent raises error | Call refund with payment_id PAY-9999 | Raises ValueError with not found |
| UT27 | Double refund raises error | Refund same payment twice | Raises ValueError with already refunded |
| UT28 | Simulated payment failure | Set simulate_failure=True then process payment | Returns success=False and payment_id=None |
| UT29 | Notify restaurant success | Call notify_restaurant with valid data | Notification created with SENT status |
| UT30 | Empty order ID raises error | Call notify_restaurant with empty order_id string | Raises ValueError with Order ID is required |
| UT31 | Empty restaurant name raises error | Call notify_restaurant with empty restaurant_name | Raises ValueError with Restaurant name is required |
| UT32 | Get notifications for specific order | Send two notifications for different orders then filter | Returns only the matching notification |
| UT33 | Create tracking success | Call create_tracking for ORD-0001 | Status is PLACED |
| UT34 | Duplicate tracking raises error | Call create_tracking twice for same order | Raises ValueError with Tracking already exists |
| UT35 | Transition PLACED to PREPARING | Update status from PLACED to PREPARING | Returns PREPARING |
| UT36 | Transition PREPARING to OUT_FOR_DELIVERY | Update status from PREPARING to OUT_FOR_DELIVERY | Returns OUT_FOR_DELIVERY |
| UT37 | Transition OUT_FOR_DELIVERY to DELIVERED | Update status from OUT_FOR_DELIVERY to DELIVERED | Returns DELIVERED |
| UT38 | Invalid transition raises error | Try to skip from PLACED directly to DELIVERED | Raises ValueError with Invalid transition |
| UT39 | Update delivered order raises error | Try to update status after DELIVERED | Raises ValueError with Order already delivered |
| UT40 | Cancel delivery from PLACED | Call cancel_delivery in PLACED status | Status becomes CANCELLED |
| UT41 | Cancel OUT_FOR_DELIVERY raises error | Call cancel_delivery in OUT_FOR_DELIVERY status | Raises ValueError with Cannot cancel delivery |
| UT42 | Update cancelled order raises error | Try to update status of CANCELLED delivery | Raises ValueError with Cannot update status |
| UT43 | Place order success with mocked deps | Place order with mocked cart payment notification delivery | Returns ORD-0001 with CONFIRMED status and all mocks called |
| UT44 | Place order empty cart raises error | Place order with mock cart is_empty=True | Raises ValueError with Cannot place order with empty cart |
| UT45 | Payment failure prevents order | Place order with mock payment returning failure | Raises ValueError and notification and delivery not called |
| UT46 | Cancel order success with mocked deps | Cancel CONFIRMED order with mock delivery in PLACED | Status CANCELLED and refund and cancel_delivery called |
| UT47 | Cancel already cancelled raises error | Cancel order with status already CANCELLED | Raises ValueError with already cancelled |
| UT48 | Get order status | Retrieve status of a CONFIRMED order | Returns CONFIRMED |
| UT49 | Get non-existent order raises error | Call get_order_status with ORD-9999 | Raises ValueError with not found |
| UT50 | Place order empty restaurant raises error | Place order with empty string restaurant name | Raises ValueError with Restaurant name is required |
| IT01 | Cart items flow into order total | Add Burger(250x2) and Fries(100x1) then place order | Order total is 600 with both items present |
| IT02 | Festival discount applied to order | Add Pizza(500x2) with 20 percent discount min 500 | Order total is 800.0 |
| IT03 | Failed payment prevents order | Set simulate_failure=True then place order | ValueError raised and no order notification or tracking created |
| IT04 | Confirmed order triggers notification | Place order for Italian Bistro | Notification exists for order with correct restaurant name |
| IT05 | Confirmed order creates delivery tracking | Place order for Spice Garden | Delivery status is PLACED for the order |
| IT06 | Cancel order refunds payment | Place order then cancel it | Order CANCELLED and payment REFUNDED and delivery CANCELLED |
| IT07 | Cancel out-for-delivery rejected | Place order then advance to OUT_FOR_DELIVERY then cancel | ValueError raised and order remains CONFIRMED |
| IT08 | Empty cart cannot place order | Create empty cart and try to place order | ValueError raised and no orders created |
| IT09 | Unavailable item rejected in order flow | Check availability then add only available items and order | Unavailable item not in order and only available item present |
| IT10 | Peak-load concurrent orders | Place 500 orders using 50 threads simultaneously | All 500 IDs unique and 500 notifications and 500 tracking records |

8. Test Approach
Unit Testing: Each module (restaurant, cart, discount, payment, notification, delivery,
order) is tested independently. For the order module, external dependencies (payment
processor, notification service, delivery tracker, and cart) are replaced with
unittest.mock.MagicMock objects to isolate the order logic. All tests use plain pytest
assertions for expected values and pytest.raises for error verification. This approach
ensures that a failure in one module does not cause false failures in tests of another
module.

Integration Testing: Real module instances are used with no mocking of the interactions
being verified. Tests verify that data flows correctly across module boundaries. For
example, cart items and totals flow into orders, festival discounts are applied through
the order placement flow, failed payments prevent downstream actions like notification
and tracking, and confirmed orders trigger both restaurant notifications and delivery
tracking. The peak-load test uses concurrent.futures.ThreadPoolExecutor to simulate
festival dinner-hour traffic with 500 simultaneous orders.

This two-level approach is well suited for OFDS because it first guarantees each
component is correct on its own, then verifies that the components work together in
real customer scenarios such as browsing, ordering, paying, tracking, and cancelling.

9. Test Environment
- Programming Language: Python 3.12
- Testing Framework: pytest
- Mocking Library: unittest.mock (Python standard library)
- Concurrency Library: concurrent.futures (Python standard library)
- Thread Safety: threading.Lock (Python standard library)
- Operating System: Windows 11 or Linux
- Application Modules: restaurant.py, cart.py, discount.py, payment.py, notification.py,
  delivery.py, order.py

10. Test Deliverables
- Application source files: restaurant.py, cart.py, discount.py, payment.py,
  notification.py, delivery.py, order.py
- Unit test file: test_unit.py (50 unit tests covering all modules)
- Integration test file: test_integration.py (10 integration tests covering cross-module
  workflows and peak-load concurrency)
- Software Test Plan: stored as the TEST_PLAN variable inside test_unit.py

11. Pass/Fail Criteria
- All 60 test cases (50 unit + 10 integration) must pass when running pytest from the
  project root directory.
- All assertions must hold true with no errors or unexpected exceptions.
- The peak-load test (IT10) must complete with all 500 order IDs unique, no orders lost,
  and all notification and tracking records present.
- No test may depend on the execution order of other tests.
- Each test must be independently runnable and repeatable.

12. Risks and Contingencies
- Invalid Input Risk: Users may enter invalid quantities, prices, or item names.
  Mitigation: All modules validate inputs at entry points and raise clear ValueError
  messages. Unit tests UT08, UT09, UT15, UT20, UT23, UT24 verify this behavior.
- Payment Module Failure: The payment gateway may be unavailable or decline transactions.
  Mitigation: The order module checks the payment result before confirming orders. If
  payment fails, no order, notification, or tracking is created. Tested by UT28, UT45,
  and IT03.
- Notification Failure: Restaurant notifications may fail due to missing or invalid data.
  Mitigation: The notification service validates all required fields (order ID, restaurant
  name, items) before creating a notification. Tested by UT30 and UT31.
- Duplicate Order IDs Under Load: Concurrent order placement during festival peak hours
  may cause ID collisions if shared state is not protected. Mitigation: OrderManager uses
  threading.Lock to protect order ID generation, and PaymentProcessor, NotificationService,
  and DeliveryTracker each use their own locks. The peak-load test IT10 verifies uniqueness
  with 500 concurrent orders.
- Incorrect Discount Affecting Totals: Discount miscalculation could overcharge or
  undercharge customers. Mitigation: FestivalDiscount validates percentage bounds (0-100)
  and checks minimum order thresholds before applying. Boundary test UT19 verifies
  exact-minimum behavior, and IT02 verifies end-to-end discount application.
- Delivery Status Corruption: Invalid status transitions could leave orders in inconsistent
  states. Mitigation: DeliveryTracker enforces a strict transition map (PLACED -> PREPARING
  -> OUT_FOR_DELIVERY -> DELIVERED) and rejects any invalid state change. Tested by UT38,
  UT39, and UT42.
"""
