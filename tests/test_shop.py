"""
Unit Test Suite for the Online Shopping System.
Covers all 10 core verification cases (T1 - T10) and business pricing rules using a temporary SQLite test database.
Run with: python -m unittest
"""

import os
import tempfile
import unittest

import admin
import database
import order
import order_history
import payment
import product
import shopping
import user


class TestOnlineShoppingSystem(unittest.TestCase):
    """Comprehensive test cases for the Online Shopping System course project."""

    def setUp(self):
        """Set up an isolated temporary database for each test case."""
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db_file.name
        self.temp_db_file.close()

        # Initialize schema, sample products, and default admin
        database.init_db(self.db_path)

    def tearDown(self):
        """Clean up and remove temporary database file after test completes."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    # -------------------------------------------------------------------------
    # T1: Register valid customer
    # -------------------------------------------------------------------------
    def test_T1_register_valid_user(self):
        """T1: Verify registering a new user with valid details succeeds."""
        success, msg, user_id = user.register(
            name="Alice Walker",
            email="alice@example.com",
            password="Password123",
            db_path=self.db_path,
        )
        self.assertTrue(success, f"Expected successful registration, got: {msg}")
        self.assertIsNotNone(user_id)
        self.assertGreater(user_id, 0)

        # Confirm user can login
        login_ok, login_msg, user_dict = user.login(
            email="alice@example.com",
            password="Password123",
            db_path=self.db_path,
        )
        self.assertTrue(login_ok)
        self.assertEqual(user_dict["email"], "alice@example.com")
        self.assertEqual(user_dict["role"], "customer")

    # -------------------------------------------------------------------------
    # T2: Duplicate email rejected
    # -------------------------------------------------------------------------
    def test_T2_duplicate_email_rejected(self):
        """T2: Verify that attempting to register an existing email is rejected."""
        # First registration
        ok1, _, _ = user.register(
            name="Bob Smith",
            email="bob@example.com",
            password="Secret123",
            db_path=self.db_path,
        )
        self.assertTrue(ok1)

        # Duplicate registration with same email
        ok2, msg2, uid2 = user.register(
            name="Bob Imposter",
            email="bob@example.com",
            password="DifferentPass1",
            db_path=self.db_path,
        )
        self.assertFalse(ok2)
        self.assertIn("already registered", msg2.lower())
        self.assertIsNone(uid2)

    # -------------------------------------------------------------------------
    # T3: Wrong password refused
    # -------------------------------------------------------------------------
    def test_T3_wrong_password_refused(self):
        """T3: Verify that authentication fails with an incorrect password."""
        user.register(
            name="Charlie Brown",
            email="charlie@example.com",
            password="CorrectPass1",
            db_path=self.db_path,
        )

        ok, msg, user_dict = user.login(
            email="charlie@example.com",
            password="WrongPassword99",
            db_path=self.db_path,
        )
        self.assertFalse(ok)
        self.assertIn("invalid", msg.lower())
        self.assertIsNone(user_dict)

    # -------------------------------------------------------------------------
    # T4: Search existing vs missing product
    # -------------------------------------------------------------------------
    def test_T4_search_existing_and_missing_products(self):
        """T4: Verify search returns matching products and empty list for non-existent."""
        # Search for an existing keyword (Headphones is seeded)
        results_found = product.search(keyword="Headphones", db_path=self.db_path)
        self.assertGreater(len(results_found), 0)
        self.assertTrue(any("Headphones" in p["name"] for p in results_found))

        # Search for a category
        books = product.search(category="Books", db_path=self.db_path)
        self.assertEqual(len(books), 3)
        for b in books:
            self.assertEqual(b["category"], "Books")

        # Search for a missing keyword
        missing = product.search(keyword="NonExistentSpaceshipXYZ999", db_path=self.db_path)
        self.assertEqual(len(missing), 0)

    # -------------------------------------------------------------------------
    # T5: Quantity above stock rejected
    # -------------------------------------------------------------------------
    def test_T5_quantity_above_stock_rejected(self):
        """T5: Verify cart rejects adding quantities greater than available inventory."""
        prods = product.list_all(db_path=self.db_path)
        test_prod = prods[0]
        pid = test_prod["product_id"]
        stock = test_prod["stock"]

        cart = {}
        # Try to add stock + 5 units
        excess_qty = stock + 5
        ok, msg, _ = shopping.add_to_cart(cart, pid, excess_qty, db_path=self.db_path)
        self.assertFalse(ok)
        self.assertIn("available", msg.lower())

        # Valid addition within stock succeeds
        ok_valid, _, updated_cart = shopping.add_to_cart(cart, pid, 2, db_path=self.db_path)
        self.assertTrue(ok_valid)

        # Trying to add more than remaining stock also fails
        ok_excess2, _, _ = shopping.add_to_cart(updated_cart, pid, stock, db_path=self.db_path)
        self.assertFalse(ok_excess2)

    # -------------------------------------------------------------------------
    # T6: Remove item from cart updates totals
    # -------------------------------------------------------------------------
    def test_T6_remove_item_updates_totals(self):
        """T6: Verify removing an item from cart recalculates subtotal and total."""
        prods = product.list_all(db_path=self.db_path)
        p1 = prods[0]
        p2 = prods[1]

        cart = {}
        _, _, cart = shopping.add_to_cart(cart, p1["product_id"], 1, db_path=self.db_path)
        _, _, cart = shopping.add_to_cart(cart, p2["product_id"], 1, db_path=self.db_path)

        totals_two = shopping.compute_totals(cart, db_path=self.db_path)
        self.assertEqual(totals_two["item_count"], 2)

        # Remove p1
        ok_rem, _, cart = shopping.remove_from_cart(cart, p1["product_id"])
        self.assertTrue(ok_rem)

        totals_one = shopping.compute_totals(cart, db_path=self.db_path)
        self.assertEqual(totals_one["item_count"], 1)
        self.assertEqual(totals_one["subtotal"], p2["price"])
        self.assertLess(totals_one["subtotal"], totals_two["subtotal"])

    # -------------------------------------------------------------------------
    # T7: Successful checkout saves order and reduces stock
    # -------------------------------------------------------------------------
    def test_T7_checkout_success_saves_order_and_reduces_stock(self):
        """T7: Verify checkout creates order, line items, payment, and decrements stock."""
        # Create user
        _, _, uid = user.register(
            name="David Miller",
            email="david@example.com",
            password="PassWord1",
            db_path=self.db_path,
        )

        prods = product.list_all(db_path=self.db_path)
        target = prods[0]
        pid = target["product_id"]
        initial_stock = target["stock"]
        buy_qty = 3

        cart = {}
        _, _, cart = shopping.add_to_cart(cart, pid, buy_qty, db_path=self.db_path)

        # Perform checkout
        ok, msg, order_summary = order.checkout(
            user_id=uid,
            cart=cart,
            method="UPI",
            simulate_fail=False,
            db_path=self.db_path,
        )
        self.assertTrue(ok, f"Checkout failed: {msg}")
        self.assertIsNotNone(order_summary)
        order_id = order_summary["order_id"]

        # Verify stock decreased
        updated_stock = product.check_stock(pid, db_path=self.db_path)
        self.assertEqual(updated_stock, initial_stock - buy_qty)

        # Verify order in history
        history = order_history.get_orders(uid, db_path=self.db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["order_id"], order_id)
        self.assertEqual(history[0]["payment_status"], "SUCCESS")
        self.assertEqual(history[0]["items"][0]["quantity"], buy_qty)

    # -------------------------------------------------------------------------
    # T8: Non-numeric input handled gracefully
    # -------------------------------------------------------------------------
    def test_T8_non_numeric_input_handled(self):
        """T8: Verify invalid, non-numeric inputs return friendly errors without crashing."""
        cart = {}

        # String quantity in add_to_cart
        ok, msg, _ = shopping.add_to_cart(cart, 1, "invalid_qty", db_path=self.db_path)
        self.assertFalse(ok)
        self.assertIn("integer", msg.lower())

        # Negative quantity
        ok_neg, msg_neg, _ = shopping.add_to_cart(cart, 1, -5, db_path=self.db_path)
        self.assertFalse(ok_neg)

        # Invalid product_id in check_stock
        stk = product.check_stock("non_numeric_id", db_path=self.db_path)
        self.assertIsNone(stk)

        # Non-numeric stock in admin update_stock
        ok_adm, msg_adm = admin.update_stock(1, "bad_stock_val", db_path=self.db_path)
        self.assertFalse(ok_adm)

    # -------------------------------------------------------------------------
    # T9: Admin adds product and updates stock
    # -------------------------------------------------------------------------
    def test_T9_admin_add_product_and_update_stock(self):
        """T9: Verify admin can add a product and update stock level."""
        # Add new product
        ok_add, msg_add, new_id = admin.add_product(
            name="Wireless Ergonomic Mouse",
            category="Electronics",
            price=1250.00,
            stock=14,
            db_path=self.db_path,
        )
        self.assertTrue(ok_add, msg_add)
        self.assertIsNotNone(new_id)

        # Check product is listed
        prod = product.get_product(new_id, db_path=self.db_path)
        self.assertIsNotNone(prod)
        self.assertEqual(prod["name"], "Wireless Ergonomic Mouse")
        self.assertEqual(prod["stock"], 14)
        self.assertEqual(prod["price"], 1250.00)

        # Update stock
        ok_upd, msg_upd = admin.update_stock(new_id, 35, db_path=self.db_path)
        self.assertTrue(ok_upd, msg_upd)

        # Verify new stock reflected
        self.assertEqual(product.check_stock(new_id, db_path=self.db_path), 35)

    # -------------------------------------------------------------------------
    # T10: Order history isolation (users only see their own orders)
    # -------------------------------------------------------------------------
    def test_T10_order_history_user_isolation(self):
        """T10: Verify customer A cannot see orders belonging to customer B."""
        # User A
        _, _, uid_a = user.register(
            name="User A",
            email="usera@example.com",
            password="Password1",
            db_path=self.db_path,
        )
        # User B
        _, _, uid_b = user.register(
            name="User B",
            email="userb@example.com",
            password="Password2",
            db_path=self.db_path,
        )

        # User A places an order
        cart_a = {}
        _, _, cart_a = shopping.add_to_cart(cart_a, 1, 1, db_path=self.db_path)
        order.checkout(uid_a, cart_a, method="Card", db_path=self.db_path)

        # User B places two orders
        cart_b = {}
        _, _, cart_b = shopping.add_to_cart(cart_b, 2, 1, db_path=self.db_path)
        order.checkout(uid_b, cart_b, method="UPI", db_path=self.db_path)
        order.checkout(uid_b, cart_b, method="UPI", db_path=self.db_path)

        orders_a = order_history.get_orders(uid_a, db_path=self.db_path)
        orders_b = order_history.get_orders(uid_b, db_path=self.db_path)

        self.assertEqual(len(orders_a), 1)
        self.assertEqual(orders_a[0]["user_id"], uid_a)

        self.assertEqual(len(orders_b), 2)
        for ord_b in orders_b:
            self.assertEqual(ord_b["user_id"], uid_b)
            self.assertNotEqual(ord_b["user_id"], uid_a)

    # -------------------------------------------------------------------------
    # Business Rules: Price calculations (discount, tax, delivery)
    # -------------------------------------------------------------------------
    def test_pricing_rules_below_discount_and_below_free_delivery(self):
        """Test subtotal < 1000 (no discount) and taxable < 500 (₹50 delivery fee)."""
        # Create a product with price = ₹400
        _, _, pid = admin.add_product(
            name="Test Small Item",
            category="Home",
            price=400.00,
            stock=10,
            db_path=self.db_path,
        )

        cart = {str(pid): 1}
        totals = shopping.compute_totals(cart, db_path=self.db_path)

        self.assertEqual(totals["subtotal"], 400.00)
        self.assertEqual(totals["discount"], 0.00)
        self.assertEqual(totals["taxable_amount"], 400.00)
        # Tax = 18% of 400 = 72.00
        self.assertEqual(totals["tax"], 72.00)
        # Delivery = 50.00 (taxable < 500)
        self.assertEqual(totals["delivery_charge"], 50.00)
        # Total = 400 + 72 + 50 = 522.00
        self.assertEqual(totals["total"], 522.00)

    def test_pricing_rules_with_discount_and_free_delivery(self):
        """Test subtotal >= 1000 (10% discount) and taxable >= 500 (Free delivery)."""
        # Create a product with price = ₹1200
        _, _, pid = admin.add_product(
            name="Test Premium Item",
            category="Electronics",
            price=1200.00,
            stock=10,
            db_path=self.db_path,
        )

        cart = {str(pid): 1}
        totals = shopping.compute_totals(cart, db_path=self.db_path)

        self.assertEqual(totals["subtotal"], 1200.00)
        # Discount = 10% of 1200 = 120.00
        self.assertEqual(totals["discount"], 120.00)
        # Taxable amount = 1200 - 120 = 1080.00
        self.assertEqual(totals["taxable_amount"], 1080.00)
        # Tax = 18% of 1080 = 194.40
        self.assertEqual(totals["tax"], 194.40)
        # Delivery = 0.00 (taxable >= 500)
        self.assertEqual(totals["delivery_charge"], 0.00)
        # Total = 1080 + 194.40 + 0 = 1274.40
        self.assertEqual(totals["total"], 1274.40)

    # -------------------------------------------------------------------------
    # Simulated Payment Failure: Stock and DB remain unchanged
    # -------------------------------------------------------------------------
    def test_failed_payment_leaves_stock_and_orders_unchanged(self):
        """Verify simulated payment failure does not decrement stock or write orders."""
        _, _, uid = user.register(
            name="Eve Hacker",
            email="eve@example.com",
            password="Password123",
            db_path=self.db_path,
        )

        prods = product.list_all(db_path=self.db_path)
        pid = prods[0]["product_id"]
        stock_before = prods[0]["stock"]

        cart = {str(pid): 2}

        # Attempt checkout with simulate_fail=True
        ok, msg, order_summary = order.checkout(
            user_id=uid,
            cart=cart,
            method="UPI",
            simulate_fail=True,
            db_path=self.db_path,
        )

        self.assertFalse(ok)
        self.assertIn("failed", msg.lower())
        self.assertIsNone(order_summary)

        # Stock must remain unchanged
        stock_after = product.check_stock(pid, db_path=self.db_path)
        self.assertEqual(stock_after, stock_before)

        # No order should have been created for Eve
        orders = order_history.get_orders(uid, db_path=self.db_path)
        self.assertEqual(len(orders), 0)


if __name__ == "__main__":
    unittest.main()
