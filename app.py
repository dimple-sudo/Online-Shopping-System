"""
Flask Web Application for the Online Shopping System.
Serves HTML pages rendered with Jinja2 templates and exposes RESTful JSON APIs.
"""

from functools import wraps
import os
import sqlite3
from typing import Any, Callable

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import admin
import database
import order
import order_history
import product
import shopping
import user

app = Flask(__name__)
# Secret key for secure session cookies
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "university-python-essentials-secret-key-2026")

# Ensure database and seed data are initialized
database.init_db()


def login_required(f: Callable) -> Callable:
    """Decorator to enforce login on views."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """Decorator to enforce administrator privileges on views."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session or session.get("role") != "admin":
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f: Callable) -> Callable:
    """Decorator to enforce login on JSON API routes."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            return jsonify({"ok": False, "error": "Authentication required. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function


def api_admin_required(f: Callable) -> Callable:
    """Decorator to enforce admin role on JSON API routes."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_id" not in session:
            return jsonify({"ok": False, "error": "Authentication required."}), 401
        if session.get("role") != "admin":
            return jsonify({"ok": False, "error": "Access denied. Administrator privileges required."}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_data() -> dict:
    """Inject current user and cart item count into all Jinja templates."""
    current_cart = session.get("cart", {})
    total_qty = sum(int(q) for q in current_cart.values() if isinstance(q, int) or (isinstance(q, str) and q.isdigit()))
    return {
        "current_user": {
            "user_id": session.get("user_id"),
            "name": session.get("name"),
            "email": session.get("email"),
            "role": session.get("role"),
        } if "user_id" in session else None,
        "cart_count": total_qty,
    }


# ==========================================
# PAGE ROUTES (HTML)
# ==========================================

@app.route("/")
def index():
    """Redirect to /products if logged in, else to /login."""
    if "user_id" in session:
        return redirect(url_for("products_page"))
    return redirect(url_for("login_page"))


@app.route("/login")
def login_page():
    """Login view for customers and administrators."""
    if "user_id" in session:
        return redirect(url_for("products_page"))
    return render_template("login.html")


@app.route("/register")
def register_page():
    """Customer registration view."""
    if "user_id" in session:
        return redirect(url_for("products_page"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Clear user session and redirect to login."""
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/products")
@login_required
def products_page():
    """Browse product catalogue with search and filter capabilities."""
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    all_products = product.search(keyword=keyword, category=category)
    return render_template(
        "products.html",
        products=all_products,
        search_query=keyword,
        selected_category=category,
    )


@app.route("/cart")
@login_required
def cart_page():
    """View shopping cart and calculated bill breakdown."""
    cart_data = session.get("cart", {})
    items = shopping.view_cart(cart_data)
    totals = shopping.compute_totals(cart_data)
    return render_template("cart.html", items=items, totals=totals)


@app.route("/checkout")
@login_required
def checkout_page():
    """Checkout view to review order totals and choose simulated payment method."""
    cart_data = session.get("cart", {})
    items = shopping.view_cart(cart_data)
    totals = shopping.compute_totals(cart_data)
    if not items:
        return redirect(url_for("cart_page"))
    return render_template("checkout.html", items=items, totals=totals)


@app.route("/orders")
@login_required
def orders_page():
    """Order history view showing all past orders placed by the logged-in user."""
    user_id = session.get("user_id")
    past_orders = order_history.get_orders(user_id)
    return render_template("orders.html", orders=past_orders)


@app.route("/admin")
@admin_required
def admin_page():
    """Admin dashboard to view all products, add new products, and update inventory."""
    all_products = admin.list_products()
    return render_template("admin.html", products=all_products)


# ==========================================
# JSON REST APIs
# ==========================================

@app.route("/api/register", methods=["POST"])
def api_register():
    """Register a new customer account."""
    data = request.get_json(silent=True) or request.form.to_dict()
    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")

    success, msg, new_uid = user.register(name=name, email=email, password=password, role="customer")
    if not success:
        return jsonify({"ok": False, "error": msg}), 400

    return jsonify({"ok": True, "data": {"message": msg, "user_id": new_uid}}), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    """Authenticate customer or administrator."""
    data = request.get_json(silent=True) or request.form.to_dict()
    email = data.get("email", "")
    password = data.get("password", "")
    as_admin = data.get("as_admin", False)

    if isinstance(as_admin, str):
        as_admin = as_admin.lower() in ("true", "1", "yes", "on")

    if as_admin:
        success, msg, user_dict = user.admin_login(email=email, password=password)
    else:
        success, msg, user_dict = user.login(email=email, password=password)

    if not success or not user_dict:
        return jsonify({"ok": False, "error": msg}), 401

    # Initialize user session
    session["user_id"] = user_dict["user_id"]
    session["name"] = user_dict["name"]
    session["email"] = user_dict["email"]
    session["role"] = user_dict["role"]
    if "cart" not in session:
        session["cart"] = {}

    return jsonify({"ok": True, "data": {"message": msg, "user": user_dict}}), 200


@app.route("/api/products", methods=["GET"])
def api_products():
    """Search and list products."""
    keyword = request.args.get("q", "")
    category = request.args.get("category", "")
    prods = product.search(keyword=keyword, category=category)
    return jsonify({"ok": True, "data": prods}), 200


@app.route("/api/stock/<int:product_id>", methods=["GET"])
def api_stock(product_id: int):
    """Retrieve stock level for a product."""
    stk = product.check_stock(product_id)
    if stk is None:
        return jsonify({"ok": False, "error": f"Product #{product_id} not found."}), 404
    return jsonify({"ok": True, "data": {"product_id": product_id, "stock": stk}}), 200


@app.route("/api/cart/add", methods=["POST"])
@api_login_required
def api_cart_add():
    """Add item and quantity to current session cart."""
    data = request.get_json(silent=True) or request.form.to_dict()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    cart = session.get("cart", {})
    success, msg, updated_cart = shopping.add_to_cart(cart, product_id, quantity)
    if not success:
        return jsonify({"ok": False, "error": msg}), 400

    session["cart"] = updated_cart
    session.modified = True

    totals = shopping.compute_totals(updated_cart)
    return jsonify({
        "ok": True,
        "data": {
            "message": msg,
            "cart": updated_cart,
            "cart_count": totals["item_count"],
            "totals": totals,
        },
    }), 200


@app.route("/api/cart/remove", methods=["POST"])
@api_login_required
def api_cart_remove():
    """Remove item completely from current session cart."""
    data = request.get_json(silent=True) or request.form.to_dict()
    product_id = data.get("product_id")

    cart = session.get("cart", {})
    success, msg, updated_cart = shopping.remove_from_cart(cart, product_id)
    if not success:
        return jsonify({"ok": False, "error": msg}), 400

    session["cart"] = updated_cart
    session.modified = True

    items = shopping.view_cart(updated_cart)
    totals = shopping.compute_totals(updated_cart)
    return jsonify({
        "ok": True,
        "data": {
            "message": msg,
            "cart": updated_cart,
            "items": items,
            "totals": totals,
            "cart_count": totals["item_count"],
        },
    }), 200


@app.route("/api/cart", methods=["GET"])
@api_login_required
def api_cart():
    """Get all items, counts, and breakdown totals for current session cart."""
    cart = session.get("cart", {})
    items = shopping.view_cart(cart)
    totals = shopping.compute_totals(cart)
    return jsonify({
        "ok": True,
        "data": {
            "items": items,
            "totals": totals,
            "cart_count": totals["item_count"],
        },
    }), 200


@app.route("/api/checkout", methods=["POST"])
@api_login_required
def api_checkout():
    """Execute checkout with payment simulation."""
    data = request.get_json(silent=True) or request.form.to_dict()
    method = data.get("method", "UPI")
    simulate_fail = data.get("simulate_fail", False)
    if isinstance(simulate_fail, str):
        simulate_fail = simulate_fail.lower() in ("true", "1", "yes", "on")

    user_id = session.get("user_id")
    cart = session.get("cart", {})

    success, msg, order_summary = order.checkout(
        user_id=user_id,
        cart=cart,
        method=method,
        simulate_fail=simulate_fail,
    )

    if not success:
        return jsonify({"ok": False, "error": msg}), 400

    # Clear cart upon successful checkout
    session["cart"] = {}
    session.modified = True

    return jsonify({"ok": True, "data": order_summary}), 200


@app.route("/api/orders", methods=["GET"])
@api_login_required
def api_orders():
    """Get past orders for the currently authenticated user."""
    user_id = session.get("user_id")
    past_orders = order_history.get_orders(user_id)
    return jsonify({"ok": True, "data": past_orders}), 200


@app.route("/api/admin/product", methods=["POST"])
@api_admin_required
def api_admin_add_product():
    """Add a new product to catalogue (Admin only)."""
    data = request.get_json(silent=True) or request.form.to_dict()
    name = data.get("name", "")
    category = data.get("category", "")
    price = data.get("price")
    stock = data.get("stock")

    success, msg, prod_id = admin.add_product(
        name=name,
        category=category,
        price=price,
        stock=stock,
    )
    if not success:
        return jsonify({"ok": False, "error": msg}), 400

    return jsonify({"ok": True, "data": {"message": msg, "product_id": prod_id}}), 201


@app.route("/api/admin/stock", methods=["POST"])
@api_admin_required
def api_admin_update_stock():
    """Update stock for an existing product (Admin only)."""
    data = request.get_json(silent=True) or request.form.to_dict()
    product_id = data.get("product_id")
    new_stock = data.get("new_stock")

    success, msg = admin.update_stock(product_id=product_id, new_stock=new_stock)
    if not success:
        return jsonify({"ok": False, "error": msg}), 400

    return jsonify({"ok": True, "data": {"message": msg}}), 200


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5001))
    print(f"Starting Online Shopping System on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
