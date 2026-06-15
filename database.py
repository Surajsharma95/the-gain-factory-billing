"""
The Gain Factory - Billing System
Database Backend (SQLite)
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "gain_factory.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Customers table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Products / Supplements table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            buying_price REAL DEFAULT 0,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'unit',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Migrate: add buying_price if it doesn't exist (safe for existing DBs)
    try:
        cur.execute("ALTER TABLE products ADD COLUMN buying_price REAL DEFAULT 0")
    except Exception:
        pass  # Column already exists

    # Invoices table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            customer_name TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax_rate REAL DEFAULT 18.0,
            tax_amount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'Cash',
            payment_status TEXT DEFAULT 'Paid',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Invoice items table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()
    _seed_sample_data()


def _seed_sample_data():
    """Insert sample data if tables are empty."""
    conn = get_connection()
    cur = conn.cursor()

    # Seed products (buying_price, selling_price)
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        products = [
            ("Whey Protein Gold Standard", "Optimum Nutrition", "Protein", 2800.0, 3499.0, 50, "kg"),
            ("Creatine Monohydrate",       "MyProtein",         "Creatine", 550.0, 799.0, 80, "unit"),
            ("Mass Gainer XXL",            "MuscleBlaze",       "Mass Gainer", 1700.0, 2199.0, 30, "kg"),
            ("BCAA Energy",                "Scivation Xtend",   "Amino Acids", 1200.0, 1599.0, 45, "unit"),
            ("Pre-Workout Fury",           "C4 Original",       "Pre-Workout", 1900.0, 2499.0, 25, "unit"),
            ("Multivitamin for Men",       "GNC",               "Vitamins", 650.0, 899.0, 60, "unit"),
            ("Omega-3 Fish Oil",           "HealthVit",         "Supplements", 320.0, 499.0, 100, "unit"),
            ("Casein Protein",             "Optimum Nutrition", "Protein", 3200.0, 3999.0, 20, "kg"),
            ("L-Glutamine",               "MyProtein",         "Amino Acids", 480.0, 699.0, 55, "unit"),
            ("Fat Burner Lipo-6",          "Nutrex",            "Fat Burner", 1300.0, 1799.0, 35, "unit"),
        ]
        cur.executemany(
            "INSERT INTO products (name, brand, category, buying_price, price, stock, unit) VALUES (?,?,?,?,?,?,?)",
            products,
        )

    # Seed customers
    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] == 0:
        customers = [
            ("Rahul Sharma", "9876543210", "rahul@email.com", "123, MG Road, Delhi"),
            ("Priya Singh", "9123456789", "priya@email.com", "45, Linking Road, Mumbai"),
            ("Amit Patel", "9988776655", "amit@email.com", "78, Residency Road, Bangalore"),
        ]
        cur.executemany(
            "INSERT INTO customers (name, phone, email, address) VALUES (?,?,?,?)",
            customers,
        )

    conn.commit()
    conn.close()


# ─── Invoice Helpers ────────────────────────────────────────────────────────

def generate_invoice_number():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM invoices")
    count = cur.fetchone()[0] + 1
    conn.close()
    date_str = datetime.now().strftime("%Y%m%d")
    return f"TGF-{date_str}-{count:04d}"


def create_invoice(customer_name, items, discount=0, tax_rate=18.0,
                   payment_method="Cash", payment_status="Paid", notes="", customer_id=None):
    """
    items: list of dicts with keys: product_id, product_name, quantity, unit_price
    Returns the new invoice id.
    """
    conn = get_connection()
    cur = conn.cursor()

    invoice_number = generate_invoice_number()
    subtotal = sum(i["quantity"] * i["unit_price"] for i in items)
    discounted = subtotal - discount
    tax_amount = round(discounted * tax_rate / 100, 2)
    total = round(discounted + tax_amount, 2)

    cur.execute("""
        INSERT INTO invoices (invoice_number, customer_id, customer_name, subtotal,
            discount, tax_rate, tax_amount, total, payment_method, payment_status, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (invoice_number, customer_id, customer_name, subtotal,
          discount, tax_rate, tax_amount, total, payment_method, payment_status, notes))

    invoice_id = cur.lastrowid

    for item in items:
        cur.execute("""
            INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, unit_price, total)
            VALUES (?,?,?,?,?,?)
        """, (invoice_id, item.get("product_id"), item["product_name"],
              item["quantity"], item["unit_price"],
              item["quantity"] * item["unit_price"]))
        # Deduct stock
        if item.get("product_id"):
            cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                        (item["quantity"], item["product_id"]))

    conn.commit()
    conn.close()
    return invoice_id, invoice_number


# ─── Fetch Helpers ───────────────────────────────────────────────────────────

def get_all_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_all_customers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_all_invoices():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_invoice_items(invoice_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_invoice_by_id(invoice_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total), 0) FROM invoices WHERE payment_status = 'Paid'")
    total_revenue = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM customers")
    total_customers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products WHERE stock > 0")
    products_in_stock = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(total), 0) FROM invoices
        WHERE date(created_at) = date('now','localtime')
    """)
    today_revenue = cur.fetchone()[0]

    cur.execute("""
        SELECT strftime('%Y-%m', created_at) as month, SUM(total) as revenue
        FROM invoices
        WHERE payment_status = 'Paid'
        GROUP BY month ORDER BY month DESC LIMIT 6
    """)
    monthly = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT p.category, SUM(ii.total) as revenue
        FROM invoice_items ii
        JOIN products p ON p.id = ii.product_id
        GROUP BY p.category ORDER BY revenue DESC
    """)
    category_sales = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "total_invoices": total_invoices,
        "total_revenue": total_revenue,
        "total_customers": total_customers,
        "products_in_stock": products_in_stock,
        "today_revenue": today_revenue,
        "monthly_revenue": monthly,
        "category_sales": category_sales,
    }


# ─── CRUD for Products & Customers ──────────────────────────────────────────

def add_product(name, brand, category, buying_price, price, stock, unit="unit"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO products (name, brand, category, buying_price, price, stock, unit)
        VALUES (?,?,?,?,?,?,?)
    """, (name, brand, category, buying_price, price, stock, unit))
    conn.commit()
    conn.close()


def update_product_stock(product_id, new_stock):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
    conn.commit()
    conn.close()


def add_customer(name, phone, email, address):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO customers (name, phone, email, address)
        VALUES (?,?,?,?)
    """, (name, phone, email, address))
    conn.commit()
    conn.close()


# Initialize database on import
init_db()
