"""
Shopping cart module for the Online Shopping System.
Handles cart manipulation, quantity validation against real stock, and pricing rules.
"""

from typing import Any, Dict, List, Optional, Tuple
import product

# Business rule constants for pricing and discounts
DISCOUNT_THRESHOLD = 1000.0   # Minimum subtotal for 10% discount
DISCOUNT_RATE = 0.10          # 10% discount
TAX_RATE = 0.18               # 18% GST on taxable amount
DELIVERY_CHARGE = 50.0        # Flat delivery fee in INR
FREE_DELIVERY_THRESHOLD = 500.0  # Delivery waived if taxable amount >= 500.0


def add_to_cart(
    cart: Dict[Any, int],
    product_id: Any,
    qty: Any,
    db_path: Optional[str] = None,
) -> Tuple[bool, str, Dict[Any, int]]:
    """
    Add a quantity of product_id to the cart dictionary.
    Rejects non-numeric input, qty <= 0, non-existent products,
    and requests that exceed available stock.
    Returns: (success: bool, message: str, cart: dict)
    """
    # Safe validation of product_id
    try:
        pid = int(product_id)
    except (ValueError, TypeError):
        return False, "Invalid product ID.", cart

    # Safe validation of quantity
    try:
        quantity = int(qty)
    except (ValueError, TypeError):
        return False, "Quantity must be a valid integer.", cart

    if quantity <= 0:
        return False, "Quantity must be greater than zero.", cart

    # Check product existence and current stock
    prod = product.get_product(pid, db_path=db_path)
    if not prod:
        return False, f"Product ID {pid} does not exist.", cart

    stock = prod["stock"]
    if stock <= 0:
        return False, f"Sorry, '{prod['name']}' is out of stock.", cart

    # Check if existing cart quantity + requested quantity exceeds stock
    key_str = str(pid)
    current_qty = cart.get(key_str, cart.get(pid, 0))
    total_requested = current_qty + quantity

    if total_requested > stock:
        return (
            False,
            f"Cannot add {quantity} units. Only {stock} available in stock (already in cart: {current_qty}).",
            cart,
        )

    # Normalize cart keys to strings for JSON session compatibility
    new_cart = dict(cart)
    # Remove integer key if present to avoid dual-entry
    if pid in new_cart:
        del new_cart[pid]
    new_cart[key_str] = total_requested

    return True, f"Added {quantity} unit(s) of '{prod['name']}' to cart.", new_cart


def remove_from_cart(
    cart: Dict[Any, int],
    product_id: Any,
) -> Tuple[bool, str, Dict[Any, int]]:
    """
    Remove a product completely from the cart dictionary.
    Returns: (success: bool, message: str, cart: dict)
    """
    try:
        pid = int(product_id)
    except (ValueError, TypeError):
        return False, "Invalid product ID.", cart

    new_cart = dict(cart)
    str_key = str(pid)

    removed = False
    if str_key in new_cart:
        del new_cart[str_key]
        removed = True
    if pid in new_cart:
        del new_cart[pid]
        removed = True

    if not removed:
        return False, "Item was not found in cart.", new_cart

    return True, "Item removed from cart.", new_cart


def view_cart(
    cart: Dict[Any, int],
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convert the cart dictionary {product_id: quantity} into a rich list of item details:
    product_id, name, category, price, quantity, line_total, and available stock.
    """
    items: List[Dict[str, Any]] = []
    if not cart:
        return items

    for key, qty in cart.items():
        try:
            pid = int(key)
            q = int(qty)
        except (ValueError, TypeError):
            continue

        if q <= 0:
            continue

        prod = product.get_product(pid, db_path=db_path)
        if prod:
            line_total = round(prod["price"] * q, 2)
            items.append(
                {
                    "product_id": pid,
                    "name": prod["name"],
                    "category": prod["category"],
                    "price": prod["price"],
                    "quantity": q,
                    "line_total": line_total,
                    "stock": prod["stock"],
                }
            )

    return items


def compute_totals(
    cart: Dict[Any, int],
    db_path: Optional[str] = None,
) -> Dict[str, float]:
    """
    Compute pricing breakdown according to course business rules:
      subtotal        = sum(price x quantity)
      discount        = 10% of subtotal if subtotal >= 1000, else 0
      taxable_amount  = subtotal - discount
      tax (GST)       = 18% of taxable_amount
      delivery_charge = ₹50, waived (₹0) if taxable_amount >= 500 (and subtotal > 0)
      TOTAL           = (subtotal - discount) + tax + delivery_charge

    All currency values rounded to 2 decimal places.
    """
    items = view_cart(cart, db_path=db_path)

    if not items:
        return {
            "subtotal": 0.00,
            "discount": 0.00,
            "taxable_amount": 0.00,
            "tax": 0.00,
            "delivery_charge": 0.00,
            "total": 0.00,
            "item_count": 0,
        }

    subtotal = round(sum(item["line_total"] for item in items), 2)
    total_items = sum(item["quantity"] for item in items)

    # Discount rule
    if subtotal >= DISCOUNT_THRESHOLD:
        discount = round(subtotal * DISCOUNT_RATE, 2)
    else:
        discount = 0.00

    taxable_amount = round(subtotal - discount, 2)

    # Tax rule (18% GST)
    tax = round(taxable_amount * TAX_RATE, 2)

    # Delivery rule: waived if taxable_amount >= 500
    if taxable_amount >= FREE_DELIVERY_THRESHOLD or subtotal == 0.0:
        delivery_charge = 0.00
    else:
        delivery_charge = DELIVERY_CHARGE

    total = round(taxable_amount + tax + delivery_charge, 2)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "taxable_amount": taxable_amount,
        "tax": tax,
        "delivery_charge": delivery_charge,
        "total": total,
        "item_count": total_items,
    }
