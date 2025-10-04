# SHOP-EASY



# Features

# Modern UI:

shop/templates/index.html

uses Bootstrap 5 with a sleek “glass” design.

Product API: GET /api/products/ serves a hardcoded catalog from  shop/views.py

Checkout API: POST /api/checkout/ accepts a cart payload and returns a success message.

Client cart + orders: Cart and order history persisted in localStorage.

Tests: Basic API tests in shop/tests.py


# Tech Stack:

Backend: Django 5.2.4

Database: SQLite (dev)

Frontend: Bootstrap 5 (CDN), vanilla JS

Python: 3.10+ recommended

# Project Structure:

ShopEasy/
├─ manage.py
├─ db.sqlite3
├─ ShopEasy/
│  ├─ settings.py
│  └─ urls.py
└─ shop/
   ├─ views.py
   ├─ urls.py
   ├─ tests.py
   └─ templates/
      └─ index.html

Getting Started:-

1) Setup bash

# Windows PowerShell

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install --upgrade pip

pip install "Django==5.2.4"

2) Run database migrations bash

python manage.py migrate

3) Start the server bash

python manage.py runserver

App: http://127.0.0.1:8000/

Products API: http://127.0.0.1:8000/api/products/

Checkout API: http://127.0.0.1:8000/api/checkout/

# API

GET /api/products/

Returns a list of products:

json
[
  { "id": 1, "name": "Wireless Mouse", "price": 19.99, "imageUrl": "...", "category": "Accessories" },
  ...
]

POST /api/checkout/

Body:

json
{ "cart": [ { "productId": 1, "quantity": 2 }, ... ] }

Response:

json
{ "message": "Order received! Thank you for your purchase." }

# Running Tests bash

python manage.py test

Configuration Notes

DEBUG=True and ALLOWED_HOSTS=[] in ShopEasy/settings.py are for local development.

 # Before deploying:

Set DEBUG=False

Set ALLOWED_HOSTS appropriately

Rotate SECRET_KEY and load from an environment variable

Configure static files and a production database if needed

# Requirements:

Create a requirements.txt (optional but recommended):

Django==5.2.4

Install via: bash

pip install -r requirements.txt

# Screenshots:

UI shows a product grid with category filters, search, cart modal, order history modal.