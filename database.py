"""
Database module for the Online Shopping System.
Handles SQLite connection setup, schema creation, and initial seeding.
"""

import sqlite3
import os
from typing import Optional

DEFAULT_DB_PATH = "shop.db"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.
    Enforces foreign key constraints and sets row factory for dictionary-like access.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: Optional[sqlite3.Connection] = None, db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Create the necessary tables (Users, Products, Orders, Order_Items, Payments)
    if they do not already exist.
    """
    should_close = False
    if conn is None:
        conn = get_connection(db_path)
        should_close = True

    try:
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'admin'))
            );
            """
        )

        # Products table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK (price > 0),
                stock INTEGER NOT NULL CHECK (stock >= 0)
            );
            """
        )

        # Orders table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL,
                tax REAL NOT NULL,
                delivery_charge REAL NOT NULL,
                total REAL NOT NULL,
                order_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            );
            """
        )

        # Order_Items table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Order_Items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES Orders(order_id),
                FOREIGN KEY (product_id) REFERENCES Products(product_id)
            );
            """
        )

        # Payments table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                method TEXT NOT NULL,
                status TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES Orders(order_id)
            );
            """
        )

        conn.commit()
    except sqlite3.Error as err:
        conn.rollback()
        raise err
    finally:
        if should_close:
            conn.close()


def seed_products(conn: Optional[sqlite3.Connection] = None, db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Seed 12 sample products across 4 categories (Electronics, Books, Clothing, Home)
    if the Products table is currently empty.
    """
    should_close = False
    if conn is None:
        conn = get_connection(db_path)
        should_close = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM Products;")
        count = cursor.fetchone()["count"]

        if count == 0:
            sample_products = [
                # Electronics
                ("Wireless Noise-Cancelling Headphones", "Electronics", 2499.00, 15),
                ("Mechanical Backlit USB Keyboard", "Electronics", 1899.00, 20),
                ("Portable Bluetooth Speaker 10W", "Electronics", 1299.00, 25),
                # Books
                ("Clean Code: Software Craftsmanship", "Books", 699.00, 30),
                ("The Pragmatic Programmer (2nd Edition)", "Books", 799.00, 25),
                ("Python Crash Course by Eric Matthes", "Books", 599.00, 40),
                # Clothing
                ("Men's Regular Fit Cotton Casual Shirt", "Clothing", 899.00, 35),
                ("Women's Embroidered Cotton Kurti", "Clothing", 999.00, 28),
                ("Unisex Classic Slim Denim Jeans", "Clothing", 1499.00, 22),
                # Home
                ("Stainless Steel Insulated Flask (1000ml)", "Home", 449.00, 50),
                ("Non-Stick Induction Ceramic Fry Pan", "Home", 1199.00, 18),
                ("Ergonomic Memory Foam Sleeping Pillow", "Home", 849.00, 16),
            ]
            cursor.executemany(
                """
                INSERT INTO Products (name, category, price, stock)
                VALUES (?, ?, ?, ?);
                """,
                sample_products,
            )
            conn.commit()
    except sqlite3.Error as err:
        conn.rollback()
        raise err
    finally:
        if should_close:
            conn.close()


def seed_admin(conn: Optional[sqlite3.Connection] = None, db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Seed default admin user if not already present.
    Email: admin@shop.com
    Password: Admin@123 (hashed with salt)
    Role: admin
    """
    # Import locally to avoid circular dependency
    from user import hash_password

    should_close = False
    if conn is None:
        conn = get_connection(db_path)
        should_close = True

    try:
        cursor = conn.cursor()
        admin_email = "admin@shop.com"
        cursor.execute("SELECT user_id FROM Users WHERE email = ?;", (admin_email,))
        existing = cursor.fetchone()

        if not existing:
            hashed_pw = hash_password("Admin@123")
            cursor.execute(
                """
                INSERT INTO Users (name, email, password, role)
                VALUES (?, ?, ?, 'admin');
                """,
                ("Shop Administrator", admin_email, hashed_pw),
            )
            conn.commit()
    except sqlite3.Error as err:
        conn.rollback()
        raise err
    finally:
        if should_close:
            conn.close()


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Initialize the database completely: create tables, seed products, and seed admin.
    """
    conn = get_connection(db_path)
    try:
        create_tables(conn)
        seed_products(conn)
        seed_admin(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
