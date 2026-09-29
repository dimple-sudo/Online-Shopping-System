"""
Command Line Interface (CLI) Entry Point for the Online Shopping System.
Demonstrates the layered architecture by consuming the exact same business logic modules.
Run with: python main.py
"""

import sys
from typing import Any, Dict

import admin
import database
import order
import order_history
import product
import shopping
import user


def print_header(title: str) -> None:
    """Print a clean section header."""
    print("\n" + "=" * 60)
    print(f"  {title.upper()}")
    print("=" * 60)


def print_products_table(prods: list) -> None:
    """Display product list in formatted ASCII columns."""
    if not prods:
        print("  No products found.")
        return
    print(f"{'ID':<5} {'Name':<38} {'Category':<15} {'Price (₹)':<12} {'Stock':<6}")
    print("-" * 78)
    for p in prods:
        print(f"{p['product_id']:<5} {p['name'][:36]:<38} {p['category'][:13]:<15} ₹{p['price']:<10.2f} {p['stock']:<6}")


def print_bill_summary(totals: Dict[str, float]) -> None:
    """Print formatted bill breakdown according to course rules."""
    print("-" * 45)
    print(f"  Items in Cart  : {int(totals.get('item_count', 0))}")
    print(f"  Subtotal       : ₹{totals.get('subtotal', 0.0):.2f}")
    if totals.get("discount", 0.0) > 0:
        print(f"  Discount (10%) : -₹{totals.get('discount', 0.0):.2f}")
    else:
        print(f"  Discount       : ₹0.00 (min ₹1000 for 10% off)")
    print(f"  Taxable Amount : ₹{totals.get('taxable_amount', 0.0):.2f}")
    print(f"  GST Tax (18%)  : ₹{totals.get('tax', 0.0):.2f}")
    if totals.get("delivery_charge", 0.0) == 0.0:
        print(f"  Delivery Fee   : ₹0.00 (Free delivery over ₹500)")
    else:
        print(f"  Delivery Fee   : ₹{totals.get('delivery_charge', 0.0):.2f}")
    print("-" * 45)
    print(f"  TOTAL PAYABLE  : ₹{totals.get('total', 0.0):.2f}")
    print("-" * 45)


def customer_menu(current_user: Dict[str, Any]) -> None:
    """Submenu for authenticated customer interactions."""
    cart: Dict[str, int] = {}

    while True:
        cart_totals = shopping.compute_totals(cart)
        item_count = cart_totals["item_count"]
        print_header(f"Customer Menu - Welcome, {current_user['name']} (Cart: {item_count} items)")
        print("1. Browse All Products")
        print("2. Search Products by Keyword or Category")
        print("3. Check Stock for a Product")
        print("4. Add Product to Cart")
        print("5. View Cart & Bill Breakdown")
        print("6. Remove Product from Cart")
        print("7. Checkout & Pay")
        print("8. View Order History")
        print("9. Logout")

        choice = input("\nEnter choice (1-9): ").strip()

        if choice == "1":
            print_header("All Products")
            prods = product.list_all()
            print_products_table(prods)

        elif choice == "2":
            print_header("Search Products")
            kw = input("Enter keyword (or press Enter to skip): ").strip()
            cat = input("Enter category (Electronics/Books/Clothing/Home or Enter to skip): ").strip()
            prods = product.search(keyword=kw, category=cat)
            print_products_table(prods)

        elif choice == "3":
            print_header("Check Stock")
            pid = input("Enter Product ID: ").strip()
            stk = product.check_stock(pid)
            if stk is None:
                print(f"  [Error] Product ID '{pid}' does not exist.")
            else:
                prod = product.get_product(pid)
                print(f"  Product: {prod['name']}")
                print(f"  Current Stock: {stk} units")

        elif choice == "4":
            print_header("Add to Cart")
            pid = input("Enter Product ID: ").strip()
            qty = input("Enter Quantity: ").strip()
            ok, msg, updated_cart = shopping.add_to_cart(cart, pid, qty)
            if ok:
                cart = updated_cart
                print(f"  [Success] {msg}")
            else:
                print(f"  [Error] {msg}")

        elif choice == "5":
            print_header("Your Shopping Cart")
            items = shopping.view_cart(cart)
            if not items:
                print("  Your cart is currently empty.")
            else:
                print(f"{'ID':<5} {'Name':<36} {'Price':<10} {'Qty':<6} {'Line Total':<12}")
                print("-" * 72)
                for itm in items:
                    print(f"{itm['product_id']:<5} {itm['name'][:34]:<36} ₹{itm['price']:<9.2f} {itm['quantity']:<6} ₹{itm['line_total']:<10.2f}")
                print_bill_summary(cart_totals)

        elif choice == "6":
            print_header("Remove from Cart")
            if not cart:
                print("  Your cart is already empty.")
                continue
            pid = input("Enter Product ID to remove: ").strip()
            ok, msg, updated_cart = shopping.remove_from_cart(cart, pid)
            if ok:
                cart = updated_cart
                print(f"  [Success] {msg}")
            else:
                print(f"  [Error] {msg}")

        elif choice == "7":
            print_header("Checkout & Payment")
            items = shopping.view_cart(cart)
            if not items:
                print("  Cannot checkout: Your cart is empty.")
                continue

            totals = shopping.compute_totals(cart)
            print_bill_summary(totals)

            print("Select Payment Method:")
            print("1. UPI")
            print("2. Card")
            print("3. Cash on Delivery")
            m_choice = input("Enter choice (1-3): ").strip()
            method_map = {"1": "UPI", "2": "Card", "3": "Cash on Delivery"}
            selected_method = method_map.get(m_choice, "UPI")

            sim_fail_in = input("Simulate payment failure? (y/N): ").strip().lower()
            simulate_fail = sim_fail_in == "y"

            ok, msg, order_summary = order.checkout(
                user_id=current_user["user_id"],
                cart=cart,
                method=selected_method,
                simulate_fail=simulate_fail,
            )

            if ok and order_summary:
                print(f"\n  [SUCCESS] Order #{order_summary['order_id']} placed successfully!")
                print(f"  Payment Method: {order_summary['payment_method']}")
                print(f"  Amount Paid: ₹{order_summary['totals']['total']:.2f}")
                cart = {}
            else:
                print(f"\n  [FAILED] {msg}")

        elif choice == "8":
            print_header(f"Order History for {current_user['name']}")
            orders = order_history.get_orders(current_user["user_id"])
            if not orders:
                print("  You have not placed any orders yet.")
            else:
                for ord_entry in orders:
                    print(f"\nOrder #{ord_entry['order_id']} | Date: {ord_entry['order_date']}")
                    print(f"Payment: {ord_entry['payment_method']} ({ord_entry['payment_status']})")
                    print("Items:")
                    for itm in ord_entry["items"]:
                        print(f"  - {itm['name']} (x{itm['quantity']}) @ ₹{itm['price']:.2f} = ₹{itm['line_total']:.2f}")
                    print(f"Subtotal: ₹{ord_entry['subtotal']:.2f} | Discount: ₹{ord_entry['discount']:.2f} | Tax: ₹{ord_entry['tax']:.2f} | Delivery: ₹{ord_entry['delivery_charge']:.2f}")
                    print(f"Total Paid: ₹{ord_entry['total']:.2f}")
                    print("-" * 50)

        elif choice == "9":
            print("\nLogging out...")
            break
        else:
            print("  Invalid selection. Please choose 1-9.")


def admin_menu(current_user: Dict[str, Any]) -> None:
    """Submenu for administrator tasks."""
    while True:
        print_header(f"Admin Dashboard - Logged in as: {current_user['name']}")
        print("1. View All Products & Current Stock")
        print("2. Add New Product")
        print("3. Update Product Stock")
        print("4. Logout")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            print_header("Inventory List")
            prods = admin.list_products()
            print_products_table(prods)

        elif choice == "2":
            print_header("Add New Product")
            name = input("Enter Product Name: ").strip()
            cat = input("Enter Category (Electronics/Books/Clothing/Home): ").strip()
            price_str = input("Enter Price (₹): ").strip()
            stock_str = input("Enter Initial Stock Quantity: ").strip()

            ok, msg, new_id = admin.add_product(name, cat, price_str, stock_str)
            if ok:
                print(f"  [Success] {msg}")
            else:
                print(f"  [Error] {msg}")

        elif choice == "3":
            print_header("Update Product Stock")
            pid = input("Enter Product ID: ").strip()
            stk = input("Enter New Stock Quantity: ").strip()

            ok, msg = admin.update_stock(pid, stk)
            if ok:
                print(f"  [Success] {msg}")
            else:
                print(f"  [Error] {msg}")

        elif choice == "4":
            print("\nLogging out from Admin console...")
            break
        else:
            print("  Invalid selection. Please choose 1-4.")


def main() -> None:
    """Main CLI execution loop."""
    database.init_db()
    print_header("Online Shopping System - Course Project CLI")
    print("Layered Architecture: Business logic split into 9 independent modules.")

    while True:
        print("\nMain Menu:")
        print("1. Customer Login")
        print("2. Customer Register")
        print("3. Admin Login")
        print("4. Exit Application")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            print_header("Customer Login")
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            ok, msg, user_dict = user.login(email, password)
            if ok and user_dict:
                print(f"  [Success] {msg}")
                customer_menu(user_dict)
            else:
                print(f"  [Error] {msg}")

        elif choice == "2":
            print_header("Customer Registration")
            name = input("Full Name: ").strip()
            email = input("Email Address: ").strip()
            password = input("Password (min 6 chars, 1 letter, 1 digit): ").strip()

            ok, msg, uid = user.register(name, email, password, role="customer")
            if ok:
                print(f"  [Success] {msg} You can now log in.")
            else:
                print(f"  [Error] {msg}")

        elif choice == "3":
            print_header("Administrator Login")
            print("Default credentials: admin@shop.com / Admin@123")
            email = input("Admin Email: ").strip()
            password = input("Admin Password: ").strip()
            ok, msg, admin_dict = user.admin_login(email, password)
            if ok and admin_dict:
                print(f"  [Success] {msg}")
                admin_menu(admin_dict)
            else:
                print(f"  [Error] {msg}")

        elif choice == "4":
            print("\nExiting. Thank you for using Online Shopping System!")
            sys.exit(0)

        else:
            print("  Invalid selection. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
