"""
Order history module for the Online Shopping System.
Handles retrieval of past user orders, line items, and payment receipts.
Enforces customer data isolation: users can only access their own orders.
"""

import sqlite3
from typing import Any, Dict, List, Optional

import database


def get_orders(user_id: Any, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all orders placed by the specified user_id.
    Strictly isolated: only orders belonging to user_id are returned.
    Each order includes totals, items, and payment details.
    """
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return []

    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()

        # Query orders strictly for this user_id
        cursor.execute(
            """
            SELECT 
                o.order_id,
                o.user_id,
                o.subtotal,
                o.discount,
                o.tax,
                o.delivery_charge,
                o.total,
                o.order_date,
                p.method AS payment_method,
                p.status AS payment_status
            FROM Orders o
            LEFT JOIN Payments p ON o.order_id = p.order_id
            WHERE o.user_id = ?
            ORDER BY o.order_id DESC;
            """,
            (uid,),
        )
        order_rows = cursor.fetchall()

        orders_list: List[Dict[str, Any]] = []

        for ord_row in order_rows:
            ord_id = ord_row["order_id"]

            # Fetch line items for this specific order
            cursor.execute(
                """
                SELECT 
                    oi.item_id,
                    oi.product_id,
                    oi.quantity,
                    oi.price,
                    pr.name AS product_name,
                    pr.category AS product_category
                FROM Order_Items oi
                LEFT JOIN Products pr ON oi.product_id = pr.product_id
                WHERE oi.order_id = ?
                ORDER BY oi.item_id ASC;
                """,
                (ord_id,),
            )
            item_rows = cursor.fetchall()

            items = [
                {
                    "item_id": ir["item_id"],
                    "product_id": ir["product_id"],
                    "name": ir["product_name"] or "Unknown Product",
                    "category": ir["product_category"] or "General",
                    "quantity": ir["quantity"],
                    "price": round(float(ir["price"]), 2),
                    "line_total": round(float(ir["price"]) * ir["quantity"], 2),
                }
                for ir in item_rows
            ]

            orders_list.append(
                {
                    "order_id": ord_id,
                    "user_id": ord_row["user_id"],
                    "subtotal": round(float(ord_row["subtotal"]), 2),
                    "discount": round(float(ord_row["discount"]), 2),
                    "tax": round(float(ord_row["tax"]), 2),
                    "delivery_charge": round(float(ord_row["delivery_charge"]), 2),
                    "total": round(float(ord_row["total"]), 2),
                    "order_date": ord_row["order_date"],
                    "payment_method": ord_row["payment_method"] or "N/A",
                    "payment_status": ord_row["payment_status"] or "UNKNOWN",
                    "items": items,
                }
            )

        return orders_list

    except sqlite3.Error:
        return []
    finally:
        conn.close()
