import threading


class PaymentResult:
    def __init__(self, success, payment_id, message):
        self.success = success
        self.payment_id = payment_id
        self.message = message


class PaymentProcessor:
    def __init__(self):
        self._lock = threading.Lock()
        self._next_payment_id = 1
        self.payments = {}
        self.simulate_failure = False

    def process_payment(self, amount):
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        if self.simulate_failure:
            return PaymentResult(False, None, "Payment declined")
        with self._lock:
            payment_id = f"PAY-{self._next_payment_id:04d}"
            self._next_payment_id += 1
            self.payments[payment_id] = {"amount": amount, "status": "COMPLETED"}
        return PaymentResult(True, payment_id, "Payment successful")

    def refund(self, payment_id):
        with self._lock:
            if payment_id not in self.payments:
                raise ValueError(f"Payment '{payment_id}' not found")
            if self.payments[payment_id]["status"] == "REFUNDED":
                raise ValueError(f"Payment '{payment_id}' already refunded")
            self.payments[payment_id]["status"] = "REFUNDED"
        return PaymentResult(True, payment_id, "Refund successful")

    def get_payment_status(self, payment_id):
        with self._lock:
            if payment_id not in self.payments:
                raise ValueError(f"Payment '{payment_id}' not found")
            return self.payments[payment_id]["status"]
