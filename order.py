"""
Order module for the Online Shopping System.
Handles end-to-end checkout, stock re-verification, atomic order creation, and stock updates.
"""

from datetime import datetime
import sqlite3
from typing import Any, Dict, Optional, Tuple

import database
import payment
import product
import shopping


def checkout(
    user_id: Any,
    cart: Dict[Any, int],
    method: str = "UPI",
    simulate_fail: bool = False,
    db_path: Optional[str] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Execute end-to-end checkout with atomic transactional guarantees:
    1. Verify user and non-empty cart.
    2. Re-verify live stock for every item in cart.
    3. Calculate total amount according to course pricing rules.
    4. Process payment (supports failure simulation).
    5. If payment fails: write NOTHING to the database, leave stock intact.
    6. If payment succeeds: in ONE database transaction:
       - Insert record into Orders
       - Insert all line items into Order_Items
       - Decrement purchased stock from Products
       - Record transaction in Payments
       - Commit transaction; roll back entirely on any error.
    7. Return (success: bool, message: str, order_details: dict | None)
    """
    # 1. Basic user validation
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return False, "Invalid user identifier.", None

    if not cart:
        return False, "Your shopping cart is empty.", None

    # Retrieve cart items with current product snapshot
    items = shopping.view_cart(cart, db_path=db_path)
    if not items:
        return False, "No valid items in your cart to checkout.", None

    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()

        # Verify user exists
        cursor.execute("SELECT user_id, name, email FROM Users WHERE user_id = ?;", (uid,))
        user_row = cursor.fetchone()
        if not user_row:
            return False, "User account not found.", None

        # 2. Re-verify live database stock for each item
        for itm in items:
            cursor.execute(
                "SELECT stock, name FROM Products WHERE product_id = ?;",
                (itm["product_id"],),
            )
            prod_row = cursor.fetchone()
            if not prod_row:
                return False, f"Product '{itm['name']}' is no longer available.", None

            current_stock = prod_row["stock"]
            if itm["quantity"] > current_stock:
                return (
                    False,
                    f"Insufficient stock for '{itm['name']}'. Requested: {itm['quantity']}, Available: {current_stock}.",
                    None,
                )

        # 3. Compute final bill totals
        totals = shopping.compute_totals(cart, db_path=db_path)
        final_amount = totals["total"]

        # 4. Process payment
        pay_status, pay_msg = payment.process_payment(
            amount=final_amount,
            method=method,
            simulate_fail=simulate_fail,
        )

        # 5. If payment failed, return error immediately without database changes
        if pay_status != "SUCCESS":
            return False, f"Checkout failed: {pay_msg}", None

        # 6. Atomic Database Transaction: Orders + Order_Items + Stock Decrement + Payments
        order_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO Orders (user_id, subtotal, discount, tax, delivery_charge, total, order_date)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                uid,
                totals["subtotal"],
                totals["discount"],
                totals["tax"],
                totals["delivery_charge"],
                totals["total"],
                order_date_str,
            ),
        )
        order_id = cursor.lastrowid

        # Insert items and decrement stock
        for itm in items:
            cursor.execute(
                """
                INSERT INTO Order_Items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?);
                """,
                (order_id, itm["product_id"], itm["quantity"], itm["price"]),
            )

            # Reduce product stock
            cursor.execute(
                """
                UPDATE Products
                SET stock = stock - ?
                WHERE product_id = ?;
                """,
                (itm["quantity"], itm["product_id"]),
            )

        # Record payment entry
        payment.record_payment(
            conn=conn,
            order_id=order_id,
            method=method,
            status="SUCCESS",
            amount=final_amount,
        )

        # Commit everything atomically
        conn.commit()

        order_summary = {
            "order_id": order_id,
            "order_date": order_date_str,
            "user_id": uid,
            "user_name": user_row["name"],
            "payment_method": method,
            "payment_status": "SUCCESS",
            "items": items,
            "totals": totals,
        }

        return True, f"Order #{order_id} placed successfully!", order_summary

    except sqlite3.Error as err:
        conn.rollback()
        return False, f"Checkout transaction failed: {str(err)}", None
    finally:
        conn.close()
