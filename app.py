"""
The Gain Factory — A Supplements Store
Billing & Inventory Dashboard
Owner: Jay Sharma | Mob: 8127321610
Address: Shop No. UGF-16, Kingship by Kahlon, Sec-16, Vrindavan Yojna, Lucknow
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import hashlib
import database as db
import streamlit.components.v1 as components
import urllib.parse


# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _check_credentials(username: str, password: str):
    """Validate login. Reads from DB first, then falls back to secrets / local defaults."""
    user = db.verify_user(username, password)
    if user:
        return True, user["role"], user["username"]
        
    try:
        valid_user = st.secrets["credentials"]["username"]
        valid_hash = st.secrets["credentials"]["password_hash"]
        if username.strip() == valid_user and _hash(password) == valid_hash:
            return True, "admin", valid_user
    except Exception:
        # Fallback for first-time local setup
        if username.strip() == "admin" and password == "gainfactory2024":
            return True, "admin", "admin"
            
    return False, None, None


def build_whatsapp_message(inv, items):
    """Build a plain-text bill summary for WhatsApp sharing."""
    lines = [
        f"🏋️ *THE GAIN FACTORY* 🏋️",
        f"_A Supplements Store_",
        f"📍 Shop No. UGF-16, Vrindavan Yojna, Lucknow",
        f"📞 {STORE_PHONE}",
        f"",
        f"*Invoice:* {inv['invoice_number']}",
        f"*Date:* {inv['created_at']}",
        f"*Customer:* {inv['customer_name']}",
        f"*Payment:* {inv['payment_method']} — {inv['payment_status']}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"{'Item':<22} {'Qty':>3} {'Amt':>9}",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]
    for it in items:
        name = it['product_name'][:20]
        lines.append(f"{name:<22} {it['quantity']:>3} ₹{it['total']:>8,.0f}")
    lines += [
        f"━━━━━━━━━━━━━━━━━━━━",
        f"Subtotal:        ₹{inv['subtotal']:>8,.2f}",
        f"Discount:       -₹{inv['discount']:>8,.2f}",
        f"GST ({inv['tax_rate']}%):      ₹{inv['tax_amount']:>8,.2f}",
        f"*TOTAL:          ₹{inv['total']:>8,.2f}*",
        f"",
        f"💪 Thank you for shopping with us!",
        f"Stay strong, stay consistent. 🔥",
        f"📸 @the_gain_factory_",
    ]
    return "\n".join(lines)

# ─── Page Config ─────────────────────────────────────────────────────────────
# ─── Store Constants ──────────────────────────────────────────────────────────
STORE_NAME      = "The Gain Factory"
STORE_TAGLINE   = "A Supplements Store"
STORE_ADDRESS   = "Shop No. UGF-16, Kingship by Kahlon, Sec-16, Vrindavan Yojna, Lucknow"
STORE_OWNER     = "Jay Sharma"
STORE_PHONE     = "8127321610"
STORE_EMAIL     = "thegainfactory@gmail.com"
STORE_INSTAGRAM  = "the_gain_factory_"
STORE_GST        = "27AABCT3518Q1ZV"  # Update with your actual GSTIN
STORE_BRANDS     = ["Dymatize", "Optimum Nutrition", "Anmufar Sports", "MuscleTech", "MuscleBlaze"]
LOGO_PATH        = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.jpeg")

st.set_page_config(
    page_title="The Gain Factory — Billing",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Login Gate ───────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Encode logo for login page
    import base64 as _b64
    _logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as _lf:
            _logo_b64 = _b64.b64encode(_lf.read()).decode()
    _logo_tag = (
        f"<img src='data:image/jpeg;base64,{_logo_b64}' style='max-height:110px; width:auto;'>"
        if _logo_b64 else "<div style='font-size:4rem;'>💪</div>"
    )

    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, #0a0a00 0%, #1a1a00 50%, #0d0d0d 100%);
    }}
    [data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="stHeader"]  {{ display: none !important; }}
    .login-card {{
        max-width: 420px; margin: 6vh auto 0 auto;
        background: linear-gradient(145deg, #1a1a00, #111);
        border: 2px solid #f7c200;
        border-radius: 20px;
        padding: 2.5rem 2.5rem 2rem 2.5rem;
        box-shadow: 0 16px 64px rgba(247,194,0,0.2);
        text-align: center;
    }}
    .login-title  {{ color:#f7c200; font-size:1.7rem; font-weight:800; margin:0.8rem 0 0.2rem 0; }}
    .login-sub    {{ color:#888; font-size:0.82rem; margin-bottom:1.4rem; }}
    </style>
    <div class='login-card'>
        {_logo_tag}
        <div class='login-title'>THE GAIN FACTORY</div>
        <div class='login-sub'>Billing &amp; Inventory Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # Spacer so form appears inside the card visually
    with st.container():
        # Center the form
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.markdown("<br>", unsafe_allow_html=True)
            login_user = st.text_input("👤 Username", key="login_user", placeholder="Enter username")
            login_pass = st.text_input("🔒 Password", type="password", key="login_pass", placeholder="Enter password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔓 Login", use_container_width=True, type="primary"):
                ok, role, name = _check_credentials(login_user, login_pass)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.role = role
                    st.session_state.username = name
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")
            st.markdown("""
            <div style='text-align:center; font-size:0.72rem; color:#444; margin-top:1rem;'>
                🔐 Authorized access only
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Bebas+Neue&family=Black+Ops+One&display=swap');

/* Logo font — matches The Gain Factory brand */
.logo-font {
    font-family: 'Bebas Neue', 'Black Ops One', Impact, 'Arial Narrow', sans-serif !important;
    letter-spacing: 0.06em;
    font-style: italic;
}
.store-sub-font {
    font-family: 'Black Ops One', 'Bebas Neue', Impact, sans-serif !important;
    letter-spacing: 0.1em;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark sidebar — matches store brand colors: black & yellow */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111111 0%, #1a1a00 60%, #222200 100%);
}
[data-testid="stSidebar"] * { color: #f0f0e0 !important; }

/* Header — yellow/black brand */
.main-header {
    background: linear-gradient(135deg, #1a1a00 0%, #2d2d00 40%, #111 100%);
    border: 2px solid #f7c200;
    padding: 1.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(247, 194, 0, 0.25);
}
.main-header h1 {
    color: #f7c200;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
    text-shadow: 0 2px 12px rgba(247,194,0,0.4);
    letter-spacing: 0.02em;
}
.main-header p {
    color: rgba(255,255,255,0.75);
    margin: 0.25rem 0 0 0;
    font-size: 0.9rem;
}
.main-header .store-meta {
    color: #f7c200;
    font-size: 0.8rem;
    margin-top: 0.4rem;
    opacity: 0.85;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #252540 100%);
    border: 1px solid rgba(255,107,53,0.2);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.metric-card .label {
    color: #888;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.metric-card .value {
    color: #f7c200;
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0.3rem 0;
}
.metric-card .sub {
    color: #aaa;
    font-size: 0.78rem;
}

/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #f7c200;
    border-left: 4px solid #f7c200;
    padding-left: 0.75rem;
    margin: 1.5rem 0 1rem 0;
}

/* Pill badge */
.badge-paid { background:#1a3a2a; color:#4ade80; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-pending { background:#3a2a1a; color:#fb923c; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }

/* Invoice preview box */
.invoice-box {
    background: white;
    color: #111;
    border-radius: 12px;
    padding: 2rem;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}
/* ── Print Styles ─────────────────────────────────────────────── */
@media print {
    /* Hide everything in Streamlit except the invoice */
    body > * { display: none !important; }
    .stApp { display: block !important; }
    [data-testid="stSidebar"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    .stButton, .section-header,
    .main-header, .metric-card,
    [data-testid="stDataFrame"],
    .stSelectbox, .stRadio, .stTextInput,
    .stSlider, .stNumberInput, .stTextArea,
    .stInfo, .stSuccess, .stWarning,
    #print-btn-row { display: none !important; }
    .invoice-box { display: block !important; box-shadow: none !important; }
    .print-only { display: block !important; }
}
.print-only { display: none; }
.no-print { }

""", unsafe_allow_html=True)

# ─── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    # Store logo
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("""
        <div style='text-align:center; padding: 0.5rem 0;'>
            <div style='font-size:3rem;'>💪</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; padding: 0.3rem 0 1.2rem 0;'>
        <div class='logo-font' style='font-size:1.6rem; color:#f7c200;'>THE GAIN FACTORY</div>
        <div class='store-sub-font' style='font-size:0.65rem; color:#aaa; margin-top:2px;'>A SUPPLEMENTS STORE</div>
        <div style='font-size:0.68rem; color:#666; margin-top:6px; line-height:1.7;'>
            📍 Vrindavan Yojna, Lucknow<br>
            📞 8127321610<br>
            📸 @the_gain_factory_
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Admin menu vs Staff menu
    menu_options = ["🏠 Dashboard", "🧾 New Invoice", "📋 Invoice History", "📦 Products", "👥 Customers"]
    if st.session_state.get("role") == "admin":
        menu_options.append("👤 Users")

    page = st.radio(
        "Navigate",
        menu_options,
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(f"<div style='font-size:0.75rem; color:#555; text-align:center;'>📅 {datetime.now().strftime('%d %b %Y, %I:%M %p')}</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    # Header — logo image + store info
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
        st.markdown("""
        <div style='background:linear-gradient(135deg,#1a1a00,#111); border:1px solid #f7c200;
                    border-radius:0 0 14px 14px; padding:0.6rem 1.5rem; margin-top:-6px;
                    margin-bottom:1.2rem;'>
            <span style='color:#f7c200; font-size:0.82rem;'>
                📍 Shop No. UGF-16, Kingship by Kahlon, Sec-16, Vrindavan Yojna, Lucknow
                &nbsp;|&nbsp; 📞 8127321610 &nbsp;|&nbsp; 📸 @the_gain_factory_ &nbsp;|&nbsp; Owner: Jay Sharma
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='main-header'>
            <h1 class='logo-font' style='font-size:2.8rem; letter-spacing:0.06em;'>💪 THE GAIN FACTORY</h1>
            <div class='store-sub-font' style='color:#f7c200; font-size:0.82rem; margin-bottom:4px;'>A SUPPLEMENTS STORE</div>
            <p>Billing &amp; Inventory Dashboard</p>
            <div class='store-meta'>📍 Shop No. UGF-16, Kingship by Kahlon, Sec-16, Vrindavan Yojna, Lucknow &nbsp;|&nbsp; 📞 8127321610 &nbsp;|&nbsp; Owner: Jay Sharma</div>
        </div>
        """, unsafe_allow_html=True)


    stats = db.get_dashboard_stats()

    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='label'>Total Revenue</div>
            <div class='value'>₹{stats['total_revenue']:,.0f}</div>
            <div class='sub'>All time</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='label'>Today's Revenue</div>
            <div class='value'>₹{stats['today_revenue']:,.0f}</div>
            <div class='sub'>Today</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='label'>Total Invoices</div>
            <div class='value'>{stats['total_invoices']}</div>
            <div class='sub'>Billed</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='label'>Customers</div>
            <div class='value'>{stats['total_customers']}</div>
            <div class='sub'>Registered</div>
        </div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='label'>Products</div>
            <div class='value'>{stats['products_in_stock']}</div>
            <div class='sub'>In stock</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<div class='section-header'>📈 Monthly Revenue</div>", unsafe_allow_html=True)
        monthly = stats["monthly_revenue"]
        if monthly:
            df_monthly = pd.DataFrame(monthly)
            df_monthly.columns = ["Month", "Revenue"]
            df_monthly = df_monthly.sort_values("Month")
            fig = px.area(
                df_monthly, x="Month", y="Revenue",
                color_discrete_sequence=["#ff6b35"],
                template="plotly_dark",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis_title="Revenue (₹)",
                xaxis_title="",
                showlegend=False,
                height=280,
            )
            fig.update_traces(fill='tozeroy', line_color='#ff6b35', fillcolor='rgba(255,107,53,0.15)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data yet. Create your first invoice!")

    with col_right:
        st.markdown("<div class='section-header'>🏷️ Sales by Category</div>", unsafe_allow_html=True)
        cat_sales = stats["category_sales"]
        if cat_sales:
            df_cat = pd.DataFrame(cat_sales)
            df_cat.columns = ["Category", "Revenue"]
            fig2 = px.pie(
                df_cat, names="Category", values="Revenue",
                color_discrete_sequence=["#ff6b35","#f7931e","#ffcd3c","#4ade80","#60a5fa","#a78bfa"],
                template="plotly_dark",
                hole=0.4,
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                height=280,
                legend=dict(font=dict(size=11)),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No category data yet.")

    # Recent Invoices
    st.markdown("<div class='section-header'>🧾 Recent Invoices</div>", unsafe_allow_html=True)
    invoices = db.get_all_invoices()
    if invoices:
        df_inv = pd.DataFrame(invoices[:10])
        df_inv = df_inv[["invoice_number", "customer_name", "total", "payment_method", "payment_status", "created_at"]]
        df_inv.columns = ["Invoice #", "Customer", "Total (₹)", "Payment Method", "Status", "Date"]
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
    else:
        st.info("No invoices yet. Go to **New Invoice** to create one!")

    # Brands We Carry
    st.markdown("<div class='section-header'>🏆 Brands We Carry</div>", unsafe_allow_html=True)
    brand_icons = {
        "Dymatize":           "🔵",
        "Optimum Nutrition":  "🔴",
        "Anmufar Sports":     "🟠",
        "MuscleTech":         "🟣",
        "MuscleBlaze":        "🟡",
    }
    brand_cols = st.columns(len(brand_icons))
    for col, (brand, icon) in zip(brand_cols, brand_icons.items()):
        with col:
            st.markdown(f"""
            <div style='background:#1e1e0a; border:1px solid #f7c200; border-radius:12px;
                        padding:0.8rem; text-align:center; box-shadow:0 2px 12px rgba(247,194,0,0.1);'>
                <div style='font-size:2rem;'>{icon}</div>
                <div style='color:#f7c200; font-weight:700; font-size:0.82rem; margin-top:4px;'>{brand}</div>
            </div>
            """, unsafe_allow_html=True)

    # Instagram Banner
    st.markdown("""
    <div style='margin-top:1.5rem; background:linear-gradient(135deg,#1a1a00,#2d2200);
                border:1px solid #f7c200; border-radius:12px; padding:0.9rem 1.5rem;
                display:flex; align-items:center; gap:1rem;'>
        <span style='font-size:1.8rem;'>📸</span>
        <div>
            <div style='color:#f7c200; font-weight:700; font-size:0.9rem;'>Follow us on Instagram</div>
            <div style='color:#aaa; font-size:0.82rem;'>@the_gain_factory_</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: NEW INVOICE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧾 New Invoice":
    st.markdown("""
    <div class='main-header'>
        <h1>🧾 Create New Invoice</h1>
        <p>The Gain Factory — A Supplements Store &nbsp;|&nbsp; Shop No. UGF-16, Vrindavan Yojna, Lucknow</p>
    </div>
    """, unsafe_allow_html=True)

    products = db.get_all_products()
    customers = db.get_all_customers()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-header'>👤 Customer Info</div>", unsafe_allow_html=True)
        cust_option = st.radio("Customer", ["Existing Customer", "Walk-in / New Customer"], horizontal=True)
        customer_id = None
        if cust_option == "Existing Customer" and customers:
            cust_map = {c["name"]: c for c in customers}
            selected_cust = st.selectbox("Select Customer", list(cust_map.keys()))
            customer_name = selected_cust
            customer_id = cust_map[selected_cust]["id"]
            st.caption(f"📞 {cust_map[selected_cust]['phone']} | 📧 {cust_map[selected_cust]['email']}")
        else:
            customer_name = st.text_input("Customer Name", placeholder="e.g. Rohit Verma")

    with col2:
        st.markdown("<div class='section-header'>💳 Payment Details</div>", unsafe_allow_html=True)
        payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Net Banking", "Credit"])
        payment_status = st.selectbox("Payment Status", ["Paid", "Pending", "Partial"])
        discount = st.number_input("Discount (₹)", min_value=0.0, value=0.0, step=10.0)
        tax_rate = st.slider("GST Rate (%)", 0, 28, 18)
        notes = st.text_area("Notes (optional)", height=68)

    st.markdown("<div class='section-header'>🛒 Add Products</div>", unsafe_allow_html=True)

    if "cart" not in st.session_state:
        st.session_state.cart = []

    prod_map = {f"{p['name']} — {p['brand']} (₹{p['price']})": p for p in products}
    col_a, col_b, col_c = st.columns([3, 1, 1])
    with col_a:
        selected_prod = st.selectbox("Select Product", ["— choose —"] + list(prod_map.keys()))
    with col_b:
        qty = st.number_input("Qty", min_value=1, value=1)
    with col_c:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add to Cart", use_container_width=True):
            if selected_prod != "— choose —":
                p = prod_map[selected_prod]
                st.session_state.cart.append({
                    "product_id": p["id"],
                    "product_name": p["name"],
                    "quantity": qty,
                    "unit_price": p["price"],
                })
                st.success(f"Added {p['name']} x{qty}")
                st.rerun()

    if st.session_state.cart:
        st.markdown("**🛒 Cart**")
        cart_rows = []
        for i, item in enumerate(st.session_state.cart):
            cart_rows.append({
                "#": i + 1,
                "Product": item["product_name"],
                "Qty": item["quantity"],
                "Unit Price (₹)": item["unit_price"],
                "Total (₹)": item["quantity"] * item["unit_price"],
            })
        df_cart = pd.DataFrame(cart_rows)
        st.dataframe(df_cart, use_container_width=True, hide_index=True)

        subtotal = sum(i["quantity"] * i["unit_price"] for i in st.session_state.cart)
        tax = round((subtotal - discount) * tax_rate / 100, 2)
        grand_total = round(subtotal - discount + tax, 2)

        st.markdown(f"""
        <div style='background:#1e1e2e; border-radius:12px; padding:1rem 1.5rem; margin-top:0.5rem;
             border:1px solid rgba(255,107,53,0.2); display:flex; gap:2rem; flex-wrap:wrap;'>
            <span style='color:#aaa;'>Subtotal: <b style="color:white">₹{subtotal:,.2f}</b></span>
            <span style='color:#aaa;'>Discount: <b style="color:#f87171">-₹{discount:,.2f}</b></span>
            <span style='color:#aaa;'>GST ({tax_rate}%): <b style="color:white">₹{tax:,.2f}</b></span>
            <span style='color:#aaa; font-size:1.1rem;'>Grand Total: <b style="color:#ff6b35; font-size:1.3rem;">₹{grand_total:,.2f}</b></span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_gen, col_clr = st.columns([2, 1])
        with col_clr:
            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        with col_gen:
            if st.button("✅ Generate Invoice", type="primary", use_container_width=True):
                if not customer_name.strip():
                    st.error("Please enter a customer name.")
                else:
                    inv_id, inv_num = db.create_invoice(
                        customer_name=customer_name,
                        items=st.session_state.cart,
                        discount=discount,
                        tax_rate=tax_rate,
                        payment_method=payment_method,
                        payment_status=payment_status,
                        notes=notes,
                        customer_id=customer_id,
                    )
                    st.session_state.cart = []
                    st.session_state["last_invoice_id"] = inv_id
                    st.success(f"✅ Invoice **{inv_num}** created successfully!")
                    st.balloons()

        # Preview last invoice
        if "last_invoice_id" in st.session_state:
            inv = db.get_invoice_by_id(st.session_state["last_invoice_id"])
            items = db.get_invoice_items(st.session_state["last_invoice_id"])
            if inv:
                st.markdown("<div class='section-header'>🖨️ Invoice Preview</div>", unsafe_allow_html=True)

                # Encode logo as base64 for embedding in HTML
                import base64
                logo_b64 = ""
                if os.path.exists(LOGO_PATH):
                    with open(LOGO_PATH, "rb") as _f:
                        logo_b64 = base64.b64encode(_f.read()).decode()
                logo_html = (
                    f"<img src='data:image/jpeg;base64,{logo_b64}' "
                    f"style='max-height:80px; width:auto; object-fit:contain;'>"
                    if logo_b64 else
                    "<div class='logo-font' style='font-size:2rem; color:#f7c200;'>💪 THE GAIN FACTORY</div>"
                    "<div class='store-sub-font' style='font-size:0.72rem; color:#ccc;'>A SUPPLEMENTS STORE</div>"
                )

                items_html = "".join([
                    f"<tr><td>{i+1}</td><td>{it['product_name']}</td><td>{it['quantity']}</td>"
                    f"<td>₹{it['unit_price']:,.2f}</td><td>₹{it['total']:,.2f}</td></tr>"
                    for i, it in enumerate(items)
                ])
                st.markdown(f"""
                <div class='invoice-box'>
                  <!-- Invoice Header -->
                  <div style='display:flex; justify-content:space-between; align-items:flex-start;
                              background:#111; color:white; border-radius:10px 10px 0 0;
                              padding:1rem 1.5rem; margin:-2rem -2rem 1.2rem -2rem;'>
                    <div>
                      {logo_html}
                      <div style='font-size:0.75rem; color:#aaa; margin-top:4px; line-height:1.6;'>
                        📍 Shop No. UGF-16, Kingship by Kahlon, Sec-16<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;Vrindavan Yojna, Lucknow<br>
                        📞 {STORE_PHONE} &nbsp;|&nbsp; Owner: {STORE_OWNER}
                      </div>
                    </div>
                    <div style='text-align:right;'>
                      <div style='font-size:1.4rem; font-weight:800; color:#f7c200;'>INVOICE</div>
                      <div style='font-size:0.85rem; color:#ccc; margin-top:4px;'>{inv['invoice_number']}</div>
                      <div style='font-size:0.78rem; color:#999;'>{inv['created_at']}</div>
                      <div style='font-size:0.72rem; color:#f7c200; margin-top:6px;'>GSTIN: {STORE_GST}</div>
                    </div>
                  </div>

                  <!-- Bill To -->
                  <div style='background:#f9f9f0; border-radius:8px; padding:0.7rem 1rem;
                              margin-bottom:1rem; border-left:4px solid #f7c200;'>
                    <div style='font-size:0.78rem; color:#888; text-transform:uppercase;
                                letter-spacing:0.06em; font-weight:600;'>Bill To</div>
                    <div style='font-size:1rem; font-weight:700; color:#111;'>{inv['customer_name']}</div>
                    <div style='font-size:0.82rem; color:#555;'>
                      Payment: <b>{inv['payment_method']}</b> &nbsp;|&nbsp;
                      Status: <b style="color:{'#16a34a' if inv['payment_status'] == 'Paid' else '#dc2626'}">{inv['payment_status']}</b>
                    </div>
                  </div>

                  <!-- Items Table -->
                  <table style='width:100%; border-collapse:collapse; font-size:0.87rem;'>
                    <thead>
                      <tr style='background:#111; color:#f7c200;'>
                        <th style='padding:9px 8px; text-align:left; border-radius:4px 0 0 0;'>#</th>
                        <th style='padding:9px 8px; text-align:left;'>Product</th>
                        <th style='padding:9px 8px; text-align:center;'>Qty</th>
                        <th style='padding:9px 8px; text-align:right;'>Unit Price</th>
                        <th style='padding:9px 8px; text-align:right; border-radius:0 4px 0 0;'>Amount</th>
                      </tr>
                    </thead>
                    <tbody>{items_html}</tbody>
                  </table>

                  <!-- Totals -->
                  <hr style='border-color:#ddd; margin:1rem 0;'>
                  <div style='display:flex; justify-content:flex-end;'>
                    <div style='font-size:0.9rem; min-width:240px;'>
                      <div style='display:flex; justify-content:space-between; padding:3px 0; color:#555;'>
                        <span>Subtotal</span><span>₹{inv['subtotal']:,.2f}</span>
                      </div>
                      <div style='display:flex; justify-content:space-between; padding:3px 0; color:#dc2626;'>
                        <span>Discount</span><span>-₹{inv['discount']:,.2f}</span>
                      </div>
                      <div style='display:flex; justify-content:space-between; padding:3px 0; color:#555;'>
                        <span>GST ({inv['tax_rate']}%)</span><span>₹{inv['tax_amount']:,.2f}</span>
                      </div>
                      <div style='display:flex; justify-content:space-between; padding:8px 12px;
                                  background:#111; color:#f7c200; border-radius:8px; margin-top:6px;
                                  font-size:1.1rem; font-weight:800;'>
                        <span>TOTAL</span><span>₹{inv['total']:,.2f}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Footer -->
                  <hr style='border-color:#eee; margin:1.2rem 0 0.8rem 0;'>
                  <div style='text-align:center; font-size:0.75rem; color:#888; line-height:1.8;'>
                    Thank you for shopping at <b>The Gain Factory</b>! 💪 Stay strong, stay consistent.<br>
                    📍 Shop No. UGF-16, Kingship by Kahlon, Sec-16, Vrindavan Yojna, Lucknow &nbsp;|&nbsp; 📞 {STORE_PHONE}<br>
                    GSTIN: <b>{STORE_GST}</b> &nbsp;|&nbsp; 📸 @the_gain_factory_<br>
                    Brands: Dymatize · Optimum Nutrition · Anmufar · MuscleTech · MuscleBlaze
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Action Buttons: Print & WhatsApp ─────────────────────
                wa_msg = build_whatsapp_message(inv, items)
                wa_encoded = urllib.parse.quote(wa_msg)

                # Build a fully standalone invoice HTML for the print popup
                import json
                popup_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset='UTF-8'>
  <title>Invoice {inv['invoice_number']} — The Gain Factory</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', Arial, sans-serif; background: #fff; color: #111;
            padding: 24px; max-width: 780px; margin: 0 auto; }}
    .inv-header {{ display:flex; justify-content:space-between; align-items:flex-start;
                   background:#111; color:#fff; border-radius:10px 10px 0 0;
                   padding:16px 20px; margin-bottom:16px; }}
    .inv-header .right {{ text-align:right; }}
    .inv-header .inv-label {{ font-size:1.5rem; font-weight:800; color:#f7c200; }}
    .inv-header .inv-num {{ font-size:0.9rem; color:#ccc; margin-top:4px; }}
    .inv-header .inv-date {{ font-size:0.8rem; color:#999; }}
    .inv-header .gst {{ font-size:0.75rem; color:#f7c200; margin-top:6px; }}
    .inv-header img {{ max-height:70px; width:auto; }}
    .inv-header .store-addr {{ font-size:0.75rem; color:#aaa; margin-top:6px; line-height:1.7; }}
    .bill-to {{ background:#f9f9f0; border-left:4px solid #f7c200; border-radius:6px;
                padding:10px 14px; margin-bottom:14px; }}
    .bill-to .label {{ font-size:0.72rem; color:#888; text-transform:uppercase;
                       letter-spacing:0.06em; font-weight:600; }}
    .bill-to .name {{ font-size:1rem; font-weight:700; color:#111; margin-top:2px; }}
    .bill-to .meta {{ font-size:0.82rem; color:#555; margin-top:2px; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.87rem; margin-bottom:12px; }}
    thead tr {{ background:#111; color:#f7c200; }}
    thead th {{ padding:9px 8px; text-align:left; }}
    thead th:nth-child(3) {{ text-align:center; }}
    thead th:nth-child(4), thead th:nth-child(5) {{ text-align:right; }}
    tbody td {{ padding:7px 8px; border-bottom:1px solid #eee; }}
    tbody td:nth-child(3) {{ text-align:center; }}
    tbody td:nth-child(4), tbody td:nth-child(5) {{ text-align:right; }}
    tbody tr:nth-child(even) {{ background:#fafafa; }}
    .totals {{ display:flex; justify-content:flex-end; margin-top:8px; }}
    .totals-box {{ min-width:260px; font-size:0.9rem; }}
    .totals-row {{ display:flex; justify-content:space-between; padding:4px 0; color:#555; }}
    .totals-discount {{ color:#dc2626; }}
    .totals-grand {{ background:#111; color:#f7c200; font-weight:800; font-size:1.05rem;
                     border-radius:8px; padding:8px 12px; margin-top:6px;
                     display:flex; justify-content:space-between; }}
    .footer {{ text-align:center; font-size:0.74rem; color:#888; line-height:1.9;
               border-top:1px solid #eee; margin-top:16px; padding-top:10px; }}
    @media print {{
      body {{ padding: 10px; }}
      @page {{ margin: 1cm; size: A4; }}
    }}
  </style>
</head>
<body>
  <div class='inv-header'>
    <div>
      {logo_html}
      <div class='store-addr'>
        📍 Shop No. UGF-16, Kingship by Kahlon, Sec-16<br>
        &nbsp;&nbsp;&nbsp;&nbsp;Vrindavan Yojna, Lucknow<br>
        📞 {STORE_PHONE} &nbsp;|&nbsp; Owner: {STORE_OWNER}
      </div>
    </div>
    <div class='right'>
      <div class='inv-label'>INVOICE</div>
      <div class='inv-num'>{inv['invoice_number']}</div>
      <div class='inv-date'>{inv['created_at']}</div>
      <div class='gst'>GSTIN: {STORE_GST}</div>
    </div>
  </div>
  <div class='bill-to'>
    <div class='label'>Bill To</div>
    <div class='name'>{inv['customer_name']}</div>
    <div class='meta'>Payment: <b>{inv['payment_method']}</b> &nbsp;|&nbsp;
      Status: <b style='color:{"#16a34a" if inv["payment_status"]=="Paid" else "#dc2626"}'>{inv['payment_status']}</b>
    </div>
  </div>
  <table>
    <thead><tr>
      <th>#</th><th>Product</th><th>Qty</th><th>Unit Price</th><th>Amount</th>
    </tr></thead>
    <tbody>{items_html}</tbody>
  </table>
  <div class='totals'>
    <div class='totals-box'>
      <div class='totals-row'><span>Subtotal</span><span>₹{inv['subtotal']:,.2f}</span></div>
      <div class='totals-row totals-discount'><span>Discount</span><span>-₹{inv['discount']:,.2f}</span></div>
      <div class='totals-row'><span>GST ({inv['tax_rate']}%)</span><span>₹{inv['tax_amount']:,.2f}</span></div>
      <div class='totals-grand'><span>TOTAL</span><span>₹{inv['total']:,.2f}</span></div>
    </div>
  </div>
  <div class='footer'>
    Thank you for shopping at <b>The Gain Factory</b>! 💪 Stay strong, stay consistent.<br>
    📍 Shop No. UGF-16, Kingship by Kahlon, Sec-16, Vrindavan Yojna, Lucknow &nbsp;|&nbsp; 📞 {STORE_PHONE}<br>
    GSTIN: <b>{STORE_GST}</b> &nbsp;|&nbsp; 📸 @the_gain_factory_<br>
    Brands: Dymatize · Optimum Nutrition · Anmufar · MuscleTech · MuscleBlaze
  </div>
</body>
</html>"""

                # Escape the HTML for safe embedding inside a JS string
                popup_js_safe = popup_html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

                st.markdown("<br>", unsafe_allow_html=True)
                act_col1, act_col2 = st.columns(2)

                with act_col1:
                    # st.components.v1.html() actually executes JS (st.markdown does not)
                    components.html(f"""
                    <html><body style='margin:0; padding:0; background:transparent;'>
                    <script>
                    function printInvoice() {{
                        var w = window.open('', '_blank', 'width=950,height=750,scrollbars=yes,resizable=yes');
                        if (!w) {{ alert('Popup was blocked. Please allow popups for localhost and try again.'); return; }}
                        w.document.open();
                        w.document.write(`{popup_js_safe}`);
                        w.document.close();
                        w.focus();
                        setTimeout(function() {{ w.print(); }}, 800);
                    }}
                    </script>
                    <button onclick="printInvoice()"
                        style='width:100%; background:#111; color:#f7c200;
                               border:2px solid #f7c200; padding:0.75rem 1rem;
                               border-radius:10px; font-size:1rem; font-weight:700;
                               cursor:pointer; letter-spacing:0.05em;
                               font-family:Inter,Arial,sans-serif; transition:all 0.2s;'
                        onmouseover="this.style.background='#f7c200';this.style.color='#111';"
                        onmouseout="this.style.background='#111';this.style.color='#f7c200';">
                        &#128424;&#65039; &nbsp;Print / Save PDF
                    </button>
                    <div style='font-size:0.72rem; color:#666; margin-top:6px; text-align:center; font-family:Arial,sans-serif;'>
                        Opens clean invoice print dialog
                    </div>
                    </body></html>
                    """, height=90)

                with act_col2:
                    # WhatsApp share — enter phone number then click
                    wa_phone = st.text_input(
                        "📱 Customer WhatsApp No.",
                        placeholder="e.g. 9876543210",
                        key="wa_phone_input",
                        help="Enter 10-digit mobile number (India). Click the button below to send."
                    )
                    phone_clean = "".join(filter(str.isdigit, wa_phone or ""))
                    if len(phone_clean) == 10:
                        full_phone = "91" + phone_clean
                        wa_url = f"https://wa.me/{full_phone}?text={wa_encoded}"
                        st.markdown(f"""
                        <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                            <button style='width:100%; background:#25D366; color:white;
                                           border:none; padding:0.75rem 1rem;
                                           border-radius:10px; font-size:1rem; font-weight:700;
                                           cursor:pointer; font-family:inherit;
                                           transition:all 0.2s;'
                                onmouseover="this.style.background='#128C7E';"
                                onmouseout="this.style.background='#25D366';">
                                💬 &nbsp;Send Bill on WhatsApp
                            </button>
                        </a>
                        <div style='font-size:0.72rem; color:#666; margin-top:4px; text-align:center;'>
                            Opens WhatsApp with bill pre-filled
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <button disabled
                            style='width:100%; background:#1a3a2a; color:#4ade8066;
                                   border:2px solid #25D36644; padding:0.75rem 1rem;
                                   border-radius:10px; font-size:1rem; font-weight:700;
                                   cursor:not-allowed; font-family:inherit;'>
                            💬 &nbsp;Send Bill on WhatsApp
                        </button>
                        <div style='font-size:0.72rem; color:#666; margin-top:4px; text-align:center;'>
                            Enter a 10-digit number to enable
                        </div>
                        """, unsafe_allow_html=True)

    else:
        st.info("Add products to the cart to begin billing.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INVOICE HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Invoice History":
    st.markdown("""
    <div class='main-header'>
        <h1>📋 Invoice History</h1>
        <p>The Gain Factory — View and search all past billing records</p>
    </div>
    """, unsafe_allow_html=True)

    invoices = db.get_all_invoices()
    if not invoices:
        st.info("No invoices found.")
    else:
        search = st.text_input("🔍 Search by Customer or Invoice #", "")
        filtered = [i for i in invoices if
                    search.lower() in i["customer_name"].lower() or
                    search.lower() in i["invoice_number"].lower()] if search else invoices

        df = pd.DataFrame(filtered)
        df_display = df[["invoice_number", "customer_name", "total", "payment_method", "payment_status", "created_at"]]
        df_display.columns = ["Invoice #", "Customer", "Total (₹)", "Payment", "Status", "Date"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # View detail
        st.markdown("<div class='section-header'>🔎 Invoice Detail</div>", unsafe_allow_html=True)
        inv_numbers = [i["invoice_number"] for i in filtered]
        selected_inv = st.selectbox("Select Invoice to View", inv_numbers)
        if selected_inv:
            inv = next(i for i in filtered if i["invoice_number"] == selected_inv)
            items = db.get_invoice_items(inv["id"])
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Customer:** {inv['customer_name']}")
                st.markdown(f"**Date:** {inv['created_at']}")
                st.markdown(f"**Payment:** {inv['payment_method']} — {inv['payment_status']}")
            with col2:
                st.markdown(f"**Subtotal:** ₹{inv['subtotal']:,.2f}")
                st.markdown(f"**Discount:** -₹{inv['discount']:,.2f}")
                st.markdown(f"**GST ({inv['tax_rate']}%):** ₹{inv['tax_amount']:,.2f}")
                st.markdown(f"**Total:** ₹{inv['total']:,.2f}")
            if items:
                df_items = pd.DataFrame(items)[["product_name", "quantity", "unit_price", "total"]]
                df_items.columns = ["Product", "Qty", "Unit Price (₹)", "Total (₹)"]
                st.dataframe(df_items, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📦 Products":
    st.markdown("""
    <div class='main-header'>
        <h1>📦 Product Inventory</h1>
        <p>The Gain Factory — Edit prices &amp; stock inline, or bulk-upload a CSV</p>
    </div>
    """, unsafe_allow_html=True)

    products = db.get_all_products()

    # ── 1. Inline Editable Table ──
    st.markdown("<div class='section-header'>✏️ Edit Buying Price, Selling Price &amp; Stock</div>",
                unsafe_allow_html=True)
    st.caption("Click any price or stock cell to edit. Press Enter to confirm, then click 💾 Save.")

    if products:
        df_edit = pd.DataFrame(products)[["id", "name", "brand", "buying_price", "price", "stock"]].copy()
        df_edit.columns = ["ID", "Product", "Brand", "Buying Price (₹)", "Selling Price (₹)", "Stock"]

        edited = st.data_editor(
            df_edit,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            disabled=["ID", "Product", "Brand"],
            column_config={
                "ID":                  st.column_config.NumberColumn("ID", width="small"),
                "Product":             st.column_config.TextColumn("Product", width="large"),
                "Brand":               st.column_config.TextColumn("Brand"),
                "Buying Price (₹)":  st.column_config.NumberColumn("Buying ₹",  min_value=0, step=10, format="₹%.2f"),
                "Selling Price (₹)": st.column_config.NumberColumn("Selling ₹", min_value=0, step=10, format="₹%.2f"),
                "Stock":               st.column_config.NumberColumn("Stock", min_value=0, step=1),
            },
            key="product_editor",
        )

        if st.button("💾 Save All Changes to Database", type="primary"):
            for _, row in edited.iterrows():
                db.update_product(
                    int(row["ID"]),
                    float(row["Buying Price (₹)"]),
                    float(row["Selling Price (₹)"]),
                    int(row["Stock"]),
                )
            st.success(f"✅ All {len(edited)} product(s) saved to database!")
            st.rerun()

    # ── 2. CSV Bulk Upload ──
    st.markdown("<div class='section-header'>📂 Bulk Update via CSV</div>", unsafe_allow_html=True)
    with st.expander("📋 CSV Format — click to expand"):
        st.markdown("""
**Required column:** `name` (case-insensitive match)

**Optional columns:**

| Column | Description |
|--------|-------------|
| `buying_price` | Your cost price |
| `selling_price` | Customer price |
| `stock` | Stock quantity |

**Example:**
```
name,buying_price,selling_price,stock
Whey Protein Gold Standard,2800,3499,50
```
        """)

    csv_file = st.file_uploader("Upload CSV to update prices / stock", type=["csv"], key="csv_upload")
    if csv_file is not None:
        try:
            df_csv = pd.read_csv(csv_file)
            df_csv.columns = [c.strip().lower().replace(" ", "_") for c in df_csv.columns]
            st.markdown("**Preview:**")
            st.dataframe(df_csv.head(10), use_container_width=True, hide_index=True)
            if st.button("⚡ Apply CSV Updates to Database", type="primary", key="apply_csv"):
                rows = df_csv.to_dict("records")
                updated, skipped = db.bulk_update_products_csv(rows)
                if updated:
                    st.success(f"✅ Updated {updated} product(s)!")
                if skipped:
                    st.warning(f"⚠️ {skipped} row(s) skipped — name not found in DB.")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error reading CSV: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    # ── 3. Inventory Summary ──
    with col_left:
        st.markdown("<div class='section-header'>📋 Current Inventory</div>", unsafe_allow_html=True)
        if products:
            df_p = pd.DataFrame(db.get_all_products())
            df_p = df_p[["name", "brand", "category", "buying_price", "price", "stock", "unit"]]
            df_p.columns = ["Product", "Brand", "Category", "Buying (₹)", "Selling (₹)", "Stock", "Unit"]
            df_p["Margin (₹)"] = df_p["Selling (₹)"] - df_p["Buying (₹)"]
            df_p["Margin %"] = ((df_p["Margin (₹)"] / df_p["Buying (₹)"]) * 100).round(1).astype(str) + "%"
            def highlight_stock(val):
                if val <= 5:
                    return "background-color: rgba(239,68,68,0.2); color: #f87171"
                elif val <= 15:
                    return "background-color: rgba(251,146,60,0.2); color: #fb923c"
                return ""
            # Version-safe Pandas Styler mapping (Pandas 2.0 uses .map, older uses .applymap)
            df_styled = df_p.style
            if hasattr(df_styled, "map"):
                df_styled = df_styled.map(highlight_stock, subset=["Stock"])
            else:
                df_styled = df_styled.applymap(highlight_stock, subset=["Stock"])

            st.dataframe(
                df_styled,
                use_container_width=True, hide_index=True
            )
            st.caption("⚠️ Buying price is internal — never shown on customer invoices.")

    # ── 4. Add / Update Product (smart duplicate check) ──
    with col_right:
        st.markdown("<div class='section-header'>📦 Add / Update Product</div>", unsafe_allow_html=True)

        # Mode toggle
        prod_mode = st.radio(
            "Select action",
            ["✏️ Update Existing Product", "➕ Add New Product"],
            horizontal=True, key="prod_mode"
        )

        if prod_mode == "✏️ Update Existing Product" and products:
            # Build map: deduplicated list sorted by name
            prod_map = {}
            for p in products:
                prod_map[f"{p['name']} ({p['brand']})"] = p
            sel_key = st.selectbox(
                "Select product to update",
                list(prod_map.keys()),
                key="update_sel"
            )
            sel_prod = prod_map[sel_key]
            with st.form("update_product_form"):
                st.caption(f"ID: {sel_prod['id']} | Category: {sel_prod['category']}")
                u1, u2 = st.columns(2)
                with u1:
                    u_buying = st.number_input(
                        "Buying Price (₹)", min_value=0.0, step=10.0,
                        value=float(sel_prod['buying_price']),
                        help="Internal cost — never shown on bills"
                    )
                with u2:
                    u_selling = st.number_input(
                        "Selling Price (₹)", min_value=0.0, step=10.0,
                        value=float(sel_prod['price'])
                    )
                u_stock = st.number_input(
                    "Stock Qty", min_value=0, step=1, value=int(sel_prod['stock'])
                )
                if st.form_submit_button("💾 Update Product", use_container_width=True, type="primary"):
                    db.update_product(sel_prod['id'], u_buying, u_selling, u_stock)
                    st.success(f"✅ '{sel_prod['name']}' updated!")
                    st.rerun()

        elif prod_mode == "➕ Add New Product":
            with st.form("add_product"):
                p_name = st.text_input("Product Name*")
                p_brand = st.text_input("Brand")
                p_category = st.selectbox("Category", [
                    "Protein", "Mass Gainer", "Creatine", "Pre-Workout",
                    "Amino Acids", "Fat Burner", "Vitamins", "Supplements", "Other"
                ])
                c1, c2 = st.columns(2)
                with c1:
                    p_buying = st.number_input("Buying Price (₹)*", min_value=0.0, step=10.0,
                                               help="Your cost price — never shown on bills")
                with c2:
                    p_price = st.number_input("Selling Price (₹)*", min_value=0.0, step=10.0,
                                              help="Price charged to customer")
                p_stock = st.number_input("Initial Stock*", min_value=0, step=1)
                p_unit = st.selectbox("Unit", ["unit", "kg", "g", "bottle", "pack"])
                submitted = st.form_submit_button("➕ Add Product", use_container_width=True, type="primary")
                if submitted:
                    if p_name and p_price > 0:
                        # Check for duplicate name
                        existing_names = [p['name'].lower() for p in products]
                        if p_name.strip().lower() in existing_names:
                            st.warning(f"⚠️ '{p_name}' already exists. Use 'Update Existing Product' to modify it.")
                        else:
                            db.add_product(p_name, p_brand, p_category, p_buying, p_price, p_stock, p_unit)
                            st.success(f"✅ '{p_name}' added successfully!")
                            st.rerun()
                    else:
                        st.error("Product name and selling price are required.")


# PAGE: CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Customers":
    st.markdown("""
    <div class='main-header'>
        <h1>👥 Customer Management</h1>
        <p>The Gain Factory — Lucknow | View and manage your customer base</p>
    </div>
    """, unsafe_allow_html=True)

    customers = db.get_all_customers()
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<div class='section-header'>👥 All Customers</div>", unsafe_allow_html=True)
        if customers:
            df_c = pd.DataFrame(customers)
            df_c = df_c[["name", "phone", "email", "address", "created_at"]]
            df_c.columns = ["Name", "Phone", "Email", "Address", "Joined"]
            st.dataframe(df_c, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("<div class='section-header'>➕ Add Customer</div>", unsafe_allow_html=True)
        with st.form("add_customer"):
            c_name = st.text_input("Full Name*")
            c_phone = st.text_input("Phone Number")
            c_email = st.text_input("Email")
            c_addr = st.text_area("Address", height=80)
            sub_c = st.form_submit_button("➕ Add Customer", use_container_width=True, type="primary")
            if sub_c:
                if c_name.strip():
                    db.add_customer(c_name, c_phone, c_email, c_addr)
                    st.success(f"✅ '{c_name}' added!")
                    st.rerun()
                else:
                    st.error("Customer name is required.")

# PAGE: USERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👤 Users" and st.session_state.get("role") == "admin":
    st.markdown("""
    <div class='main-header'>
        <h1>👤 User Accounts</h1>
        <p>The Gain Factory — Manage login credentials and access roles</p>
    </div>
    """, unsafe_allow_html=True)

    users_list = db.get_all_users()
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<div class='section-header'>👤 Active User Accounts</div>", unsafe_allow_html=True)
        if users_list:
            df_u = pd.DataFrame(users_list)
            df_u = df_u[["username", "role", "created_at"]]
            df_u.columns = ["Username", "Access Role", "Created On"]
            st.dataframe(df_u, use_container_width=True, hide_index=True)
            
            st.markdown("<br><div class='section-header'>🗑️ Delete User Account</div>", unsafe_allow_html=True)
            non_admin_users = {u["username"]: u for u in users_list if u["username"] != st.session_state.get("username")}
            if non_admin_users:
                to_delete = st.selectbox("Select user to delete", list(non_admin_users.keys()))
                if st.button("🗑️ Delete Account", use_container_width=True, type="primary"):
                    success, msg = db.delete_user(non_admin_users[to_delete]["id"])
                    if success:
                        st.success(f"✅ User '{to_delete}' deleted!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            else:
                st.info("No other user accounts to delete.")

    with col_right:
        st.markdown("<div class='section-header'>➕ Add New User Account</div>", unsafe_allow_html=True)
        with st.form("add_user_form"):
            new_username = st.text_input("Username*")
            new_password = st.text_input("Password*", type="password")
            new_role = st.selectbox("Access Role", ["staff", "admin"])
            submit_user = st.form_submit_button("➕ Create User Account", use_container_width=True, type="primary")
            if submit_user:
                if new_username.strip() and new_password.strip():
                    success = db.add_user(new_username.strip(), new_password.strip(), new_role)
                    if success:
                        st.success(f"✅ User account '{new_username}' created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Username already exists.")
                else:
                    st.error("Both username and password are required.")
