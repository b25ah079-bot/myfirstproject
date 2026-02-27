import streamlit as st
import pandas as pd
import difflib
from geopy.distance import geodesic
from datetime import datetime
import streamlit.components.v1 as components
import calendar

st.set_page_config(page_title="LowKey Deals", layout="wide", page_icon="✨")

# ----------------------------
# GLOBAL INITIALIZATION
# ----------------------------

def init_data():
    if "catalog" not in st.session_state:
        st.session_state.catalog = {}

    if "catalog_version" not in st.session_state:
        st.session_state.catalog_version = 0

    if "users" not in st.session_state:
        st.session_state.users = {"user1": "pass1"}

    if "sellers" not in st.session_state:
        st.session_state.sellers = {}

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_location" not in st.session_state:
        st.session_state.user_location = (9.9312, 76.2673)


# ----------------------------
# CATALOG MANAGEMENT
# ----------------------------

def refresh_catalog():
    """Forces UI update across pages"""
    st.session_state.catalog_version += 1
    st.rerun()


def add_or_update_offer(product_name, offer):
    """Shared function used by seller to update catalog"""
    catalog = st.session_state.catalog

    if product_name not in catalog:
        catalog[product_name] = []

    updated = False
    for i, existing in enumerate(catalog[product_name]):
        if existing["store"] == offer["store"]:
            catalog[product_name][i] = offer
            updated = True
            break

    if not updated:
        catalog[product_name].append(offer)

    refresh_catalog()


# ----------------------------
# SELLER PAGE
# ----------------------------

def seller_page():
    st.title("📦 Manage Inventory")

    with st.form("add_product"):
        name = st.text_input("Product Name")
        desc = st.text_area("Description")
        price = st.number_input("Price", min_value=0.0)
        sale_price = st.number_input("Sale Price (optional)", min_value=0.0)

        submit = st.form_submit_button("Add / Update Product")

        if submit:
            if not name:
                st.error("Product name required")
                return

            store_info = st.session_state.store_info

            is_sale = sale_price > 0 and sale_price < price

            offer = {
                "store": store_info["store_name"],
                "address": store_info["address"],
                "loc": store_info["loc"],
                "price": price,
                "sale_price": sale_price if is_sale else None,
                "is_sale": is_sale,
                "desc": desc,
                "reviews": [],
                "open_hours": store_info["open_hours"],
                "open_days": store_info["open_days"],
            }

            add_or_update_offer(name, offer)

            st.success("Catalog Updated Successfully! 🎉")


# ----------------------------
# USER HOME PAGE
# ----------------------------

def user_home():
    st.title("✨ LowKey Deals")
    st.write("Find best prices near you 💸")

    catalog = st.session_state.catalog

    if not catalog:
        st.info("No products available yet.")
        return

    search = st.text_input("Search Product")

    items = list(catalog.keys())

    if search:
        items = difflib.get_close_matches(search, items, n=5, cutoff=0.3)

    for item in items:
        st.subheader(item)

        offers = catalog[item]

        prices = [
            o["sale_price"] if o["is_sale"] else o["price"]
            for o in offers
        ]

        min_price = min(prices)

        st.write(f"Starting from ₹{min_price}")

        for o in offers:
            dist = geodesic(st.session_state.user_location, o["loc"]).km
            price = o["sale_price"] if o["is_sale"] else o["price"]

            st.markdown("---")
            st.write(f"🏪 {o['store']}")
            st.write(f"Price: ₹{price}")
            st.write(f"Distance: {dist:.1f} km")
            st.write(f"Address: {o['address']}")

# ----------------------------
# AUTH PAGE
# ----------------------------

def auth_page():
    st.title("Login")

    role = st.radio("Role", ["User", "Seller"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if role == "User":
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.authenticated = True
                st.session_state.role = "User"
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid User Credentials")

        if role == "Seller":
            if username in st.session_state.sellers and st.session_state.sellers[username]["password"] == password:
                st.session_state.authenticated = True
                st.session_state.role = "Seller"
                st.session_state.username = username
                st.session_state.store_info = st.session_state.sellers[username]
                st.rerun()
            else:
                st.error("Invalid Seller Credentials")

    st.divider()
    st.subheader("Quick Seller Signup")

    if st.button("Create Demo Seller"):
        st.session_state.sellers["seller1"] = {
            "password": "pass1",
            "store_name": "Appliance World",
            "loc": (9.95, 76.29),
            "open_hours": (9, 21),
            "open_days": list(calendar.day_name),
            "address": "123 Kochi St"
        }
        st.success("Seller Created → Login with seller1 / pass1")


# ----------------------------
# MAIN FLOW
# ----------------------------

init_data()

if not st.session_state.authenticated:
    auth_page()
else:
    with st.sidebar:
        st.write(f"Welcome {st.session_state.username}")
        if st.session_state.role == "Seller":
            page = st.radio("Menu", ["Home", "Manage Inventory"])
        else:
            page = "Home"

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    if page == "Manage Inventory":
        seller_page()
    else:
        user_home()
