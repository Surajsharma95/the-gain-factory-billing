# 💪 The Gain Factory — Billing System

A complete billing and inventory management system built with **Python + Streamlit + SQLite** for The Gain Factory supplement store.

---

## 📁 Project Structure

```
the-gain-factory-billing/
├── app.py            # Streamlit dashboard (main app)
├── database.py       # SQLite backend (all DB logic)
├── requirements.txt  # Python dependencies
├── gain_factory.db   # Auto-created SQLite database
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## ✨ Features

| Page | Features |
|------|----------|
| 🏠 **Dashboard** | Revenue KPIs, monthly chart, category pie, recent invoices |
| 🧾 **New Invoice** | Cart system, GST calculation, discount, invoice preview |
| 📋 **Invoice History** | Search, filter, view details |
| 📦 **Products** | Add supplements, update stock, low-stock highlight |
| 👥 **Customers** | Add & view customer database |

---

## 🗃️ Database Tables

- `customers` — Customer records
- `products` — Supplement catalog with stock
- `invoices` — Invoice headers with totals
- `invoice_items` — Line items per invoice

---

## 🧾 Invoice Features

- Auto-generated invoice numbers (`TGF-YYYYMMDD-XXXX`)
- GST calculation (configurable 0–28%)
- Discount support
- Payment method: Cash / UPI / Card / Net Banking / Credit
- Payment status: Paid / Pending / Partial
- In-app invoice preview (printable)
