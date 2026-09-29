"""
Admin module for the Online Shopping System.
Handles administrative operations including listing inventory, adding new products,
and updating stock quantities with comprehensive validation.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

import database
import product


def list_products(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all products in the database with their current stock levels and prices.
    Delegates to product.list_all for consistent sorting and structure.
    """
    return product.list_all(db_path=db_path)


def add_product(
    name: Any,
    category: Any,
    price: Any,
    stock: Any,
    db_path: Optional[str] = None,
) -> Tuple[bool, str, Optional[int]]:
    """
    Add a new product to the inventory with strict type and boundary validations:
    - Name: non-empty string, min 2 chars
    - Category: non-empty string
    - Price: numeric float strictly greater than 0
    - Stock: non-negative integer (>= 0)
    Returns: (success: bool, message: str, product_id: int | None)
    """
    # Name validation
    if not isinstance(name, str) or len(name.strip()) < 2:
        return False, "Product name must be at least 2 characters long.", None
    clean_name = name.strip()

    # Category validation
    if not isinstance(category, str) or len(category.strip()) < 2:
        return False, "Category must be at least 2 characters long.", None
    clean_category = category.strip()

    # Price validation
    try:
        float_price = round(float(price), 2)
        if float_price <= 0:
            return False, "Price must be strictly greater than 0.", None
    except (ValueError, TypeError):
        return False, "Price must be a valid numeric value.", None

    # Stock validation
    try:
        int_stock = int(stock)
        if int_stock < 0:
            return False, "Stock quantity cannot be negative.", None
    except (ValueError, TypeError):
        return False, "Stock must be a valid non-negative integer.", None

    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Products (name, category, price, stock)
            VALUES (?, ?, ?, ?);
            """,
            (clean_name, clean_category, float_price, int_stock),
        )
        conn.commit()
        new_id = cursor.lastrowid
        return True, f"Product '{clean_name}' added successfully with ID #{new_id}.", new_id
    except sqlite3.Error as err:
        conn.rollback()
        return False, f"Database error adding product: {str(err)}", None
    finally:
        conn.close()


def update_stock(
    product_id: Any,
    new_stock: Any,
    db_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Update the inventory stock level for an existing product.
    Validates that:
    - product_id exists
    - new_stock is an integer >= 0
    Returns: (success: bool, message: str)
    """
    # Product ID validation
    try:
        pid = int(product_id)
    except (ValueError, TypeError):
        return False, "Product ID must be an integer."

    # Stock validation
    try:
        stock_val = int(new_stock)
        if stock_val < 0:
            return False, "Stock quantity cannot be negative."
    except (ValueError, TypeError):
        return False, "Stock value must be a valid integer."

    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, name, stock FROM Products WHERE product_id = ?;", (pid,))
        prod = cursor.fetchone()
        if not prod:
            return False, f"Product ID #{pid} does not exist."

        old_stock = prod["stock"]
        cursor.execute(
            """
            UPDATE Products
            SET stock = ?
            WHERE product_id = ?;
            """,
            (stock_val, pid),
        )
        conn.commit()
        return True, f"Stock for '{prod['name']}' updated from {old_stock} to {stock_val}."
    except sqlite3.Error as err:
        conn.rollback()
        return False, f"Database error updating stock: {str(err)}"
    finally:
        conn.close()
