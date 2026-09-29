"""
User module for the Online Shopping System.
Handles registration, authentication, input validation, and password hashing.
"""

import hashlib
import hmac
import os
import re
import sqlite3
from typing import Any, Dict, Optional, Tuple

import database

# Regular expression for email validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    Hash a password using salted SHA-256.
    Returns string in format: <salt_hex>$<hash_hex>
    """
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"


def verify_password(stored_hash: str, password: str) -> bool:
    """
    Verify a plaintext password against a stored salted hash (<salt_hex>$<hash_hex>).
    """
    if not stored_hash or "$" not in stored_hash:
        return False
    try:
        salt, expected_hash = stored_hash.split("$", 1)
        actual_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def validate_name(name: Any) -> Tuple[bool, str]:
    """
    Validate user full name: must be a non-empty string, min 2 chars.
    """
    if not isinstance(name, str):
        return False, "Name must be a valid string."
    cleaned = name.strip()
    if len(cleaned) < 2:
        return False, "Name must be at least 2 characters long."
    if len(cleaned) > 80:
        return False, "Name cannot exceed 80 characters."
    return True, ""


def validate_email(email: Any) -> Tuple[bool, str]:
    """
    Validate email format using regular expressions.
    """
    if not isinstance(email, str):
        return False, "Email must be a valid string."
    cleaned = email.strip()
    if not cleaned:
        return False, "Email cannot be empty."
    if not EMAIL_REGEX.match(cleaned):
        return False, "Invalid email address format."
    return True, ""


def validate_password(password: Any) -> Tuple[bool, str]:
    """
    Validate password: min 6 chars, at least 1 letter, and at least 1 digit.
    """
    if not isinstance(password, str):
        return False, "Password must be a valid string."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return False, "Password must contain at least one letter and one number."
    return True, ""


def register(
    name: str,
    email: str,
    password: str,
    role: str = "customer",
    db_path: Optional[str] = None,
) -> Tuple[bool, str, Optional[int]]:
    """
    Register a new user in the database.
    Rejects duplicate emails and invalid inputs.
    Returns: (success: bool, message: str, user_id: int | None)
    """
    # Validate name
    ok_name, msg_name = validate_name(name)
    if not ok_name:
        return False, msg_name, None

    # Validate email
    ok_email, msg_email = validate_email(email)
    if not ok_email:
        return False, msg_email, None

    # Validate password
    ok_pwd, msg_pwd = validate_password(password)
    if not ok_pwd:
        return False, msg_pwd, None

    if role not in ("customer", "admin"):
        return False, "Invalid role specified.", None

    clean_name = name.strip()
    clean_email = email.strip().lower()
    hashed_pwd = hash_password(password)

    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()
        # Check if email is already taken
        cursor.execute("SELECT user_id FROM Users WHERE email = ?;", (clean_email,))
        if cursor.fetchone():
            return False, "Email is already registered. Please login.", None

        cursor.execute(
            """
            INSERT INTO Users (name, email, password, role)
            VALUES (?, ?, ?, ?);
            """,
            (clean_name, clean_email, hashed_pwd, role),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return True, "Registration successful!", user_id
    except sqlite3.Error as err:
        conn.rollback()
        return False, f"Database error during registration: {str(err)}", None
    finally:
        conn.close()


def login(
    email: str,
    password: str,
    db_path: Optional[str] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticate a user by email and password.
    Returns: (success: bool, message: str, user_dict: dict | None)
    """
    if not email or not password:
        return False, "Email and password are required.", None

    clean_email = email.strip().lower()
    conn = database.get_connection(db_path) if db_path else database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, email, password, role FROM Users WHERE email = ?;",
            (clean_email,),
        )
        row = cursor.fetchone()
        if not row:
            return False, "Invalid email or password.", None

        if not verify_password(row["password"], password):
            return False, "Invalid email or password.", None

        user_dict = {
            "user_id": row["user_id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"],
        }
        return True, "Login successful.", user_dict
    except sqlite3.Error as err:
        return False, f"Database error during login: {str(err)}", None
    finally:
        conn.close()


def admin_login(
    email: str,
    password: str,
    db_path: Optional[str] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticate an administrator. Verifies credentials and checks role == 'admin'.
    Returns: (success: bool, message: str, user_dict: dict | None)
    """
    success, msg, user_dict = login(email, password, db_path=db_path)
    if not success or not user_dict:
        return False, msg, None

    if user_dict.get("role") != "admin":
        return False, "Access denied. Administrator privileges required.", None

    return True, "Admin authentication successful.", user_dict
