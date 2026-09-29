"""
Product module for the Online Shopping System.
Handles product retrieval, search, categorization, and stock level verification.
"""

import sqlite3
from typing import Any, Dict, List, Optional

import database


def get_product(product_id: Any, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single product by its ID.
    Returns a dictionary or None if not found or if product_id is invalid.
    """
    try:
        pid = int(product_id)
    except (ValueError, TypeError):
        return None

    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT product_id, name, category, price, stock
            FROM Products
            WHERE product_id = ?;
            """,
            (pid,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "product_id": row["product_id"],
                "name": row["name"],
                "category": row["category"],
                "price": round(float(row["price"]), 2),
                "stock": int(row["stock"]),
            }
        return None
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def list_all(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all products available in the catalogue.
    Returns a list of dictionaries ordered by category and name.
    """
    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT product_id, name, category, price, stock
            FROM Products
            ORDER BY category ASC, product_id ASC;
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "product_id": r["product_id"],
                "name": r["name"],
                "category": r["category"],
                "price": round(float(r["price"]), 2),
                "stock": int(r["stock"]),
            }
            for r in rows
        ]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def search(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search products with case-insensitive LIKE on name and/or category.
    Returns matching products as a list of dicts.
    """
    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT product_id, name, category, price, stock FROM Products WHERE 1=1"
        params: List[Any] = []

        if keyword and str(keyword).strip():
            kw = f"%{str(keyword).strip()}%"
            query += " AND (name LIKE ? OR category LIKE ?)"
            params.extend([kw, kw])

        if category and str(category).strip() and str(category).strip().lower() != "all":
            query += " AND category = ?"
            params.append(str(category).strip())

        query += " ORDER BY category ASC, product_id ASC;"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                "product_id": r["product_id"],
                "name": r["name"],
                "category": r["category"],
                "price": round(float(r["price"]), 2),
                "stock": int(r["stock"]),
            }
            for r in rows
        ]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def check_stock(product_id: Any, db_path: Optional[str] = None) -> Optional[int]:
    """
    Check available stock units for a specific product ID.
    Returns integer stock count or None if product does not exist.
    """
    prod = get_product(product_id, db_path=db_path)
    if prod is not None:
        return prod["stock"]
    return None
