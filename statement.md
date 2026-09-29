# Problem Statement: Online Shopping System

**Course:** Python Essentials (VITyarthi)  
**Student Name:** Mim Parveen  
**Registration Number:** 26BAI10084  

---

## 1. Problem Statement
In retail and digital commerce, businesses require reliable, modular, and secure software to showcase product catalogues, handle shopping carts, compute dynamic taxation and discounts, process payments transactionally, and track customer order history. For academic and enterprise training, monolithic architectures often lead to tightly coupled code that is difficult to maintain, test, and scale. 

There is a critical need for an educational yet robust full-stack **Online Shopping System** built strictly with standard Python libraries and a lightweight web framework (Flask) following a clean, multi-layered architecture.

---

## 2. Objectives
The core objectives of this project are:
1. **Layered Modular Architecture:** Separate data access, core business logic, web routing, and client presentation into distinct, single-purpose Python modules (`database.py`, `user.py`, `product.py`, `shopping.py`, `order.py`, `payment.py`, `order_history.py`, `admin.py`, and `app.py`).
2. **Dual User Role Management:**
   - **Customer:** Secure registration, authentication, product search, cart manipulation, live stock verification, order placement with simulated payment, and private order history tracking.
   - **Administrator:** Secure admin login, real-time inventory monitoring, adding new catalogue items, and updating warehouse stock counts.
3. **Automated & Atomic Business Rules:**
   - Enforce exact currency calculation in INR (₹) with 10% discounts for orders above ₹1,000, 18% GST calculation, and free delivery thresholds (waived over ₹500).
   - Guarantee ACID database transactions during checkout: decrement inventory stock, create order records, log line items, and store payment receipts simultaneously—rolling back completely upon any payment or database failure.
4. **Resilient Data Security & Validation:**
   - Hash all passwords using salted SHA-256 before storing them in SQLite.
   - Prevent SQL injection through strict parameterised queries (`?`).
   - Re-validate all client inputs on the server to prevent negative quantities or purchasing out-of-stock products.
5. **Multi-Interface Usability:**
   - Provide an intuitive, responsive white-themed web interface powered by vanilla HTML/CSS/JavaScript and Flask Jinja templates.
   - Provide an optional, interactive terminal Command Line Interface (`main.py`) running against the exact same Python business modules.

---

## 3. Scope of the System
- **User Authentication:** Salted SHA-256 password hashing, session-based persistence, role-based access control (`customer` vs `admin`).
- **Catalogue & Search:** Full catalogue view, category filtering (Electronics, Books, Clothing, Home), case-insensitive search by keyword.
- **Cart & Pricing Engine:** Session-based cart persistence, live stock quantity checks, automatic computation of discounts, tax, and delivery charges.
- **Checkout & Simulated Gateway:** Choice of payment methods (UPI, Card, Cash on Delivery) with intentional failure simulation for testing edge cases.
- **Order History & Privacy:** Customer order records isolated per account; users cannot view other customers' orders.
- **Admin Inventory Control:** Centralized dashboard for creating products and updating warehouse quantities.
- **Automated Verification:** Comprehensive test suite covering 10 requirement cases (`tests/test_shop.py`).

---

## 4. Limitations & Future Scope
- **Current Limitations:** The payment gateway is simulated locally; sessions use client cookies signed by Flask; single-node SQLite database.
- **Future Scope:** Integration with external production payment gateways (e.g. Razorpay/Stripe), customer review/rating systems, email notification receipts, and migration to PostgreSQL for distributed scaling.
