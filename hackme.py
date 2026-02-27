import streamlit as st
import sqlite3
from geopy.distance import geodesic
import difflib
import calendar
from datetime import datetime

st.set_page_config(page_title="LowKey Deals", layout="wide", page_icon="✨")

# ======================================================
# DATABASE SETUP
# ======================================================

conn = sqlite3.connect("lowkey_deals.db", check_same_thread=False)
cursor = conn.cursor()

def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sellers (
        username TEXT PRIMARY KEY,
        store_name TEXT,
        address TEXT,
        lat REAL,
        lon REAL,
        open_from INTEGER,
        open_to INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price REAL,
        sale_price REAL,
        store_username TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        username TEXT,
        rating INTEGER,
        comment TEXT
    )
    """)
    conn.commit()

create_tables()

# ======================================================
# AUTH
# ======================================================

def login_page():
    st.title("🔐 Login")

    role = st.radio("Login As", ["User", "Seller"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?",
                       (username, password, role))
        user = cursor.fetchone()
        if user:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.divider()
    st.subheader("Sign Up")

    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    new_role = st.radio("Role", ["User", "Seller"], key="signup_role")

    if st.button("Create Account"):
        try:
            cursor.execute("INSERT INTO users VALUES (?, ?, ?)",
                           (new_user, new_pass, new_role))
            conn.commit()
            st.success("Account created! Please login.")
        except:
            st.error("Username already exists")

# ======================================================
# SELLER DASHBOARD
# ======================================================

def seller_dashboard():
    st.title("📦 Manage Inventory")

    cursor.execute("SELECT * FROM sellers WHERE username=?", (st.session_state.username,))
    seller = cursor.fetchone()

    if not seller:
        st.subheader("Setup Store")
        store_name = st.text_input("Store Name")
        address = st.text_input("Address")
        lat = st.number_input("Latitude", value=9.93)
        lon = st.number_input("Longitude", value=76.27)
        open_from = st.number_input("Open From (0-23)", 0, 23, 9)
        open_to = st.number_input("Close At (0-23)", 0, 23, 21)

        if st.button("Save Store"):
            cursor.execute("""
            INSERT INTO sellers VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (st.session_state.username, store_name, address, lat, lon, open_from, open_to))
            conn.commit()
            st.success("Store Created!")
            st.rerun()
        return

    st.subheader("Add Product")

    name = st.text_input("Product Name")
    desc = st.text_area("Description")
    price = st.number_input("Price", min_value=0.0)
    sale_price = st.number_input("Sale Price", min_value=0.0)

    if st.button("Add Product"):
        cursor.execute("""
        INSERT INTO products (name, description, price, sale_price, store_username)
        VALUES (?, ?, ?, ?, ?)
        """, (name, desc, price, sale_price, st.session_state.username))
        conn.commit()
        st.success("Product Added!")

# ======================================================
# USER HOME
# ======================================================

def user_home():
    st.title("✨ LowKey Deals")

    st.session_state.user_location = (9.9312, 76.2673)

    search = st.text_input("Search Product")

    if search:
        cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + search + '%',))
    else:
        cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    if not products:
        st.info("No products available")
        return

    for product in products:
        product_id, name, desc, price, sale_price, store_username = product

        cursor.execute("SELECT * FROM sellers WHERE username=?", (store_username,))
        seller = cursor.fetchone()

        store_name = seller[1]
        address = seller[2]
        store_loc = (seller[3], seller[4])

        dist = geodesic(st.session_state.user_location, store_loc).km
        final_price = sale_price if sale_price and sale_price < price else price

        st.markdown("---")
        st.subheader(name)
        st.write(f"🏪 {store_name}")
        st.write(f"📍 {address}")
        st.write(f"💰 ₹{final_price}")
        st.write(f"🚗 {dist:.1f} km away")

        rating = st.slider("Rate this product", 1, 5, key=f"rate_{product_id}")
        comment = st.text_input("Comment", key=f"comment_{product_id}")

        if st.button("Submit Review", key=f"review_{product_id}"):
            cursor.execute("""
            INSERT INTO reviews (product_id, username, rating, comment)
            VALUES (?, ?, ?, ?)
            """, (product_id, st.session_state.username, rating, comment))
            conn.commit()
            st.success("Review submitted!")

# ======================================================
# MAIN FLOW
# ======================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_page()
else:
    with st.sidebar:
        st.write(f"Welcome {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    if st.session_state.role == "Seller":
        seller_dashboard()
    else:
        user_home()
