"""
Payment module for the Online Shopping System.
Handles simulated payment processing and database recording of payment transactions.
"""

import sqlite3
from typing import Optional, Tuple

VALID_PAYMENT_METHODS = ["UPI", "Card", "Cash on Delivery"]


def process_payment(
    amount: float,
    method: str,
    simulate_fail: bool = False,
) -> Tuple[str, str]:
    """
    Process simulated payment for an order.
    Allowed methods: 'UPI', 'Card', 'Cash on Delivery'.
    If simulate_fail is True, simulates a bank/gateway rejection.
    Returns: (status: 'SUCCESS' | 'FAILED', message: str)
    """
    # Validate method
    clean_method = (method or "").strip()
    if clean_method not in VALID_PAYMENT_METHODS:
        return "FAILED", f"Invalid payment method '{clean_method}'. Choose from: {', '.join(VALID_PAYMENT_METHODS)}."

    # Validate amount
    try:
        amt = float(amount)
        if amt < 0:
            return "FAILED", "Payment amount cannot be negative."
    except (ValueError, TypeError):
        return "FAILED", "Invalid payment amount format."

    if simulate_fail:
        return "FAILED", f"Simulated transaction failure for {clean_method} payment of ₹{amt:.2f}."

    return "SUCCESS", f"Payment of ₹{amt:.2f} completed successfully via {clean_method}."


def record_payment(
    conn: sqlite3.Connection,
    order_id: int,
    method: str,
    status: str,
    amount: float,
) -> int:
    """
    Record payment details into the Payments table using the active database connection.
    Returns the newly inserted payment_id.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Payments (order_id, method, status, amount)
        VALUES (?, ?, ?, ?);
        """,
        (int(order_id), str(method), str(status), round(float(amount), 2)),
    )
    return cursor.lastrowid
