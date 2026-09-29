# Online Shopping System

Python Essentials course project (VITyarthi)

- Name: Mim Parveen
- Registration No: 26BAI10084
- GitHub: https://github.com/mim26bai10084-rgb/Online-Shopping-System

## About the project

This is a shopping application that runs in the terminal. It is written in Python and stores everything in an SQLite database. There is also a small web version made with Flask, but it is optional.

There are two kinds of users.

Customer:

- register and log in
- see all products and search by name or category
- check the stock of a product
- add products to the cart and remove them
- see the bill (subtotal, discount, GST, delivery charge)
- pay with UPI, Card or Cash on Delivery (the payment is only simulated)
- see their own past orders

Admin:

- log in as admin
- see all products
- add a new product
- change the stock of a product

## What you need

- Python 3.10 or newer
- pip (comes with Python)
- Git (only if you want to clone the repo)

## How to set up and run

1. Download the project.

```
git clone https://github.com/mim26bai10084-rgb/Online-Shopping-System.git
cd Online-Shopping-System
```

2. Create a virtual environment.

Mac / Linux:

```
python3 -m venv venv
source venv/bin/activate
```

Windows:

```
python -m venv venv
venv\Scripts\activate
```

3. Install the requirements.

```
pip install -r requirements.txt
```

4. Run the program.

```
python3 main.py
```

On Windows use `python main.py`.

The database file `shop.db` is created by itself the first time you run the program. It also adds 12 sample products and the admin account. You do not need to set up anything else, and there is no other configuration.

## How to use it

The main menu has four options:

```
1. Customer Login
2. Customer Register
3. Admin Login
4. Exit Application
```

For a customer, first choose 2 and register. The password must have at least 6 characters, with at least one letter and one digit. Then choose 1 and log in. After that you can browse products, add them to the cart, view the cart and check out. After payment the order is saved and the stock goes down.

For the admin, choose 3 and use this login:

- Email: admin@shop.com
- Password: Admin@123

## Web version (optional)

The same code can also be used from a browser.

```
python3 app.py
```

Then open http://127.0.0.1:5001 in your browser. Press Ctrl + C in the terminal to stop it.

If the port is already busy, change the port number at the bottom of `app.py`. (On Mac, port 5000 is used by AirPlay, which is why this project uses 5001.)

## Running the tests

```
python3 -m unittest
```

If everything is fine, the last line says OK. The tests use a temporary database, so `shop.db` is not changed.

## Price calculation

- subtotal = sum of price x quantity
- discount = 10% of subtotal if the subtotal is Rs 1000 or more, otherwise 0
- tax = 18% GST on (subtotal - discount)
- delivery charge = Rs 50, but free if (subtotal - discount) is Rs 500 or more
- total = (subtotal - discount) + tax + delivery charge

Example: subtotal 1200, discount 120, taxable amount 1080, GST 194.40, delivery 0, so the total is 1274.40.

These values are constants at the top of `shopping.py`, so they are easy to change.

## Files in the project

| File                | What it does                             |
| ------------------- | ---------------------------------------- |
| main.py             | starts the program, shows the menus      |
| app.py              | the Flask web version                    |
| database.py         | creates the database and tables          |
| user.py             | register, login, password checks         |
| product.py          | show products, search, check stock       |
| shopping.py         | cart and price calculation               |
| payment.py          | simulated payment                        |
| order.py            | checkout, saves the order, reduces stock |
| order_history.py    | shows past orders of a user              |
| admin.py            | admin functions for products and stock   |
| templates/, static/ | HTML, CSS and JS for the web version     |
| tests/test_shop.py  | unit tests                               |
| statement.md        | problem statement                        |

## Database tables

- Users: user_id, name, email, password (stored as a hash), role
- Products: product_id, name, category, price, stock
- Orders: order_id, user_id, subtotal, discount, tax, delivery_charge, total, order_date
- Order_Items: item_id, order_id, product_id, quantity, price
- Payments: payment_id, order_id, method, status, amount

One user can have many orders. One order has many items and one payment. One product can appear in many order items.

## Some notes

- Stock is reduced only after the payment succeeds. If the payment fails, nothing is saved.
- Passwords are not saved as plain text.
- All SQL queries use parameters (?) to avoid SQL injection.
- To start again with a fresh database, delete `shop.db` and run the program again.

## Things that can be added later

- a real payment gateway
- product ratings and reviews
- order status like shipped and delivered
- PDF bills for the orders
