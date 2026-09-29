# Online Shopping System

Python Essentials course project (VITyarthi)

Name: Dimple Sharma

## About

A shopping application that runs in the terminal, written in Python with an SQLite database. A small optional web version (Flask) is also included.

Customer can: register, log in, view and search products, add items to the cart, checkout with a simulated payment (UPI, Card or Cash on Delivery), and view their own order history.

Admin can: log in, view products, add a new product and update stock.

## Requirements

- Python 3.10 or newer
- pip

## Setup and run

1. Download or clone the repository and open a terminal inside the project folder.

2. Create and activate a virtual environment.

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

The database (`shop.db`) and the sample products are created automatically on the first run. No other configuration is needed.

## Login details

- Admin: `admin@shop.com` / `Admin@123`
- Customer: choose "Customer Register" in the menu first. The password needs at least 6 characters with one letter and one digit.

## Web version (optional)

```
python3 app.py
```
Open http://127.0.0.1:5001 in a browser. If the port is busy, change the port number at the bottom of `app.py`.

## Run the tests

```
python3 -m unittest
```
The last line should say OK.

## Price calculation

- discount: 10% of the subtotal if the subtotal is Rs 1000 or more
- tax: 18% GST on (subtotal - discount)
- delivery: Rs 50, free if (subtotal - discount) is Rs 500 or more
- total = (subtotal - discount) + tax + delivery

## Files

- `main.py` - terminal menus (start here)
- `app.py` - Flask web version
- `database.py` - database and tables
- `user.py` - register and login
- `product.py` - products, search, stock
- `shopping.py` - cart and price calculation
- `payment.py` - simulated payment
- `order.py` - checkout and stock update
- `order_history.py` - past orders
- `admin.py` - admin functions
- `tests/test_shop.py` - unit tests