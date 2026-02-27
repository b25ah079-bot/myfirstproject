import streamlit as st
import pandas as pd
import difflib
from geopy.distance import geodesic
from datetime import datetime
import streamlit.components.v1 as components
import calendar

# ────────────────────────────────────────────────
# CONFIGURATION & SHARED CATALOG
# ────────────────────────────────────────────────
st.set_page_config(page_title="LowKey Deals", layout="wide", page_icon="✨")

@st.cache_resource
def get_shared_catalog():
    return {}

GLOBAL_CATALOG = get_shared_catalog()

def apply_theme():
    st.markdown("""
        <style>
        html, body, [data-testid="stHeader"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span, .stRadio p {
            color: #000000 !important;
            font-weight: 500;
        }
        .stApp { background-color: #FFFFFF; }
        .deal-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 15px;
            border-top: 4px solid #8B4513;
            margin-bottom: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            transition: all 0.25s ease;
        }
        .deal-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.12);
        }
        .price-tag {
            color: #8B4513;
            font-size: 1.5rem;
            font-weight: 700;
        }
        .badge {
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            background: #FFE4B5;
            color: #8B4513;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%,100% { transform: scale(1); }
            50%     { transform: scale(1.04); }
        }
        input, textarea {
            color: #000 !important;
            background: #fff !important;
            border: 2px solid #8B4513 !important;
            border-radius: 8px !important;
        }
        div.stButton > button {
            background: #8B4513 !important;
            color: white !important;
            border-radius: 999px !important;
            font-weight: 600;
            padding: 0.6rem 1.4rem !important;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background: #A0522D !important;
            transform: scale(1.04);
        }
        </style>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# INITIAL DATA SETUP
# ────────────────────────────────────────────────
def init_data():
    if "users" not in st.session_state:
        st.session_state.users = {"user1": "pass1"}

    if "sellers" not in st.session_state:
        st.session_state.sellers = {
            "seller1": {
                "password": "pass1",
                "store_name": "Appliance World",
                "loc": (9.95, 76.29),
                "open_hours": (9, 21),
                "open_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
                "address": "123 Kochi St, Kerala"
            },
            "seller2": {
                "password": "pass2",
                "store_name": "Home Mart",
                "loc": (9.93, 76.27),
                "open_hours": (10, 22),
                "open_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
                "address": "456 Ernakulam Rd, Kerala"
            }
        }

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_location" not in st.session_state:
        st.session_state.user_location = (9.9312, 76.2673)

    if "role" not in st.session_state:
        st.session_state.role = None

# ────────────────────────────────────────────────
# SELLER — MANAGE INVENTORY
# ────────────────────────────────────────────────
def admin_page():
    st.title("📦 Manage Inventory")

    if 'store_info' not in st.session_state or not st.session_state.store_info:
        st.error("Store information missing. Please log out and log in again.")
        return

    store = st.session_state.store_info
    st.markdown(f"**Store:** {store['store_name']}  •  {store['address']}")

    with st.expander("Bulk upload via CSV"):
        st.caption("Columns: name, desc, price, sale_price (optional)")
        uploaded = st.file_uploader("Choose CSV file", type="csv")

        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                count = 0
                for _, row in df.iterrows():
                    name = str(row.get("name", "")).strip()
                    if not name: continue

                    price = float(row.get("price", 0))
                    sale_price_val = float(row.get("sale_price", 0))
                    is_sale = sale_price_val > 0 and sale_price_val < price

                    offer = {
                        "seller_username": st.session_state.username,
                        "store": store["store_name"],
                        "address": store["address"],
                        "loc": store["loc"],
                        "price": price,
                        "sale_price": sale_price_val if is_sale else None,
                        "is_sale": is_sale,
                        "desc": str(row.get("desc", "")).strip(),
                        "reviews": [],
                        "open_hours": store["open_hours"],
                        "open_days": store["open_days"]
                    }

                    if name not in GLOBAL_CATALOG:
                        GLOBAL_CATALOG[name] = []

                    replaced = False
                    for i, ex in enumerate(GLOBAL_CATALOG[name]):
                        if ex.get("seller_username") == st.session_state.username:
                            GLOBAL_CATALOG[name][i] = offer
                            replaced = True
                            break
                    if not replaced:
                        GLOBAL_CATALOG[name].append(offer)
                    count += 1

                if count > 0:
                    st.success(f"Processed {count} items")
                    st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    st.subheader("Add / Update Single Item")
    with st.form("single_item"):
        c1, c2 = st.columns([3,2])
        name = c1.text_input("Product Name")
        price = c2.number_input("Regular Price (₹)", min_value=0.0, step=100.0)
        sale_price = c2.number_input("Sale Price (optional)", min_value=0.0, step=100.0)
        desc = st.text_area("Description")

        if st.form_submit_button("Save"):
            if not name.strip():
                st.error("Product name is required")
                return

            is_sale = sale_price > 0 and sale_price < price
            offer = {
                "seller_username": st.session_state.username,
                "store": store["store_name"],
                "address": store["address"],
                "loc": store["loc"],
                "price": price,
                "sale_price": sale_price if is_sale else None,
                "is_sale": is_sale,
                "desc": desc.strip(),
                "reviews": [],
                "open_hours": store["open_hours"],
                "open_days": store["open_days"]
            }

            if name not in GLOBAL_CATALOG:
                GLOBAL_CATALOG[name] = []

            updated = False
            for i, ex in enumerate(GLOBAL_CATALOG[name]):
                if ex.get("seller_username") == st.session_state.username:
                    GLOBAL_CATALOG[name][i] = offer
                    updated = True
                    break
            if not updated:
                GLOBAL_CATALOG[name].append(offer)

            st.success("Product saved/updated")
            st.rerun()

# ────────────────────────────────────────────────
# USER HOME PAGE
# ────────────────────────────────────────────────
def home_page():
    st.subheader("🗺️ Your Location")
    st.write("Share your location for accurate distance calculation")

    if st.session_state.get("role") == "User":
        components.html("""
            <button onclick="getLocation()" style="background:#8B4513;color:white;padding:10px 20px;border:none;border-radius:20px;cursor:pointer;">
                Get My Location
            </button>
            <script>
            function getLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(showPosition, showError);
                } else {
                    alert("Geolocation is not supported.");
                }
            }
            function showPosition(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const url = new URL(window.parent.location);
                url.searchParams.set('lat', lat);
                url.searchParams.set('lon', lon);
                window.parent.location = url;
            }
            function showError(error) {
                alert("Error: " + error.message);
            }
            </script>
        """, height=70)

    query_params = st.query_params
    if 'lat' in query_params and 'lon' in query_params:
        try:
            lat = float(query_params['lat'][0])
            lon = float(query_params['lon'][0])
            st.session_state.user_location = (lat, lon)
            st.success(f"Location updated: {lat:.5f}, {lon:.5f}")
        except:
            st.warning("Could not read location from URL.")

    with st.expander("Or set location manually"):
        lat = st.number_input("Latitude", value=st.session_state.user_location[0], step=0.0001)
        lon = st.number_input("Longitude", value=st.session_state.user_location[1], step=0.0001)
        if st.button("Save manual location"):
            st.session_state.user_location = (lat, lon)
            st.success("Location saved!")

    st.divider()

    col_title, col_loc = st.columns([4, 1])
    with col_title:
        st.title("✨ LowKey Deals")
        st.markdown("### Highkey savings on local appliances")
    with col_loc:
        st.caption("📍 Your location")
        st.code(f"{st.session_state.user_location[0]:.4f}, {st.session_state.user_location[1]:.4f}")

    # ── Sales section ──
    st.subheader("🔥 Hot Sales Right Now")
    sales = [(item, o) for item, offers in GLOBAL_CATALOG.items() for o in offers if o.get("is_sale")]
    if sales:
        cols = st.columns(3)
        for i, (name, o) in enumerate(sales):
            dist = geodesic(st.session_state.user_location, o["loc"]).km
            with cols[i % 3]:
                st.markdown(f"""
                <div class="deal-card">
                    <span class="badge">SALE 🔥</span>
                    <h4>{name}</h4>
                    <p>{o['desc'][:60]}{'...' if len(o['desc']) > 60 else ''}</p>
                    <del>₹{o['price']:,}</del> <span class="price-tag">₹{o['sale_price']:,}</span>
                    <div style="font-size:0.85rem;color:#666;margin-top:8px;">≈ {dist:.1f} km</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View", key=f"sale_{i}"):
                    st.session_state.selected_item = name
                    st.rerun()
    else:
        st.info("No active sales at the moment.")

    # ── Search & catalog ──
    search = st.text_input("🔍 Search appliances...", "")
    items = list(GLOBAL_CATALOG.keys())
    if search:
        items = difflib.get_close_matches(search, items, n=5, cutoff=0.5)

    if 'selected_item' in st.session_state:
        name = st.session_state.selected_item
        offers = GLOBAL_CATALOG.get(name, [])
        if offers:
            st.header(name)
            for o in offers:
                dist = geodesic(st.session_state.user_location, o["loc"]).km
                price = o["sale_price"] if o.get("is_sale") else o["price"]
                st.markdown(f"""
                <div class="deal-card">
                    <h4>{o['store']}</h4>
                    <p>{o['desc']}</p>
                    <p class="price-tag">₹{price:,}</p>
                    <div>≈ {dist:.1f} km</div>
                </div>
                """, unsafe_allow_html=True)
            if st.button("← Back"):
                if 'selected_item' in st.session_state:
                    del st.session_state.selected_item
                st.rerun()
        else:
            st.info("No offers found.")
    else:
        st.subheader("Available Appliances")
        cols = st.columns(3)
        for i, name in enumerate(items):
            offers = GLOBAL_CATALOG[name]
            if not offers: continue
            min_price = min(o["sale_price"] if o.get("is_sale") else o["price"] for o in offers)
            min_dist = min(geodesic(st.session_state.user_location, o["loc"]).km for o in offers)
            with cols[i % 3]:
                st.markdown(f"""
                <div class="deal-card">
                    <h4>{name}</h4>
                    <p class="price-tag">From ₹{min_price:,}</p>
                    <div style="color:#666;">Closest ≈ {min_dist:.1f} km</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View offers", key=f"view_{i}_{name}"):
                    st.session_state.selected_item = name
                    st.rerun()

# ────────────────────────────────────────────────
# AUTHENTICATION PAGE
# ────────────────────────────────────────────────
def auth_page():
    st.title("Welcome to LowKey Deals")
    st.markdown("**Lowkey the best prices near you** 💸", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        role = st.radio("I am a", ["User", "Seller"])
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
                    st.error("Invalid credentials")
            else:
                if username in st.session_state.sellers and st.session_state.sellers[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.role = "Seller"
                    st.session_state.username = username
                    st.session_state.store_info = st.session_state.sellers[username]
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        role = st.radio("Sign up as", ["User", "Seller"])
        username = st.text_input("Choose username")
        password = st.text_input("Choose password", type="password")

        store_data = {}
        if role == "Seller":
            store_data["store_name"] = st.text_input("Store Name")
            store_data["address"] = st.text_input("Store Address")
            store_data["loc"] = (
                st.number_input("Latitude", value=9.93),
                st.number_input("Longitude", value=76.27)
            )
            store_data["open_hours"] = (
                st.number_input("Opens at (hour)", 0, 23, 9),
                st.number_input("Closes at (hour)", 0, 23, 21)
            )
            store_data["open_days"] = st.multiselect(
                "Open days",
                list(calendar.day_name),
                default=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
            )

        if st.button("Sign Up"):
            if role == "User":
                if username in st.session_state.users:
                    st.error("Username taken")
                else:
                    st.session_state.users[username] = password
                    st.success("Account created. Please log in.")
            else:
                if username in st.session_state.sellers:
                    st.error("Username taken")
                elif not store_data.get("store_name"):
                    st.error("Store name required")
                else:
                    st.session_state.sellers[username] = {
                        "password": password,
                        **store_data
                    }
                    st.success("Seller account created. Please log in.")

# ────────────────────────────────────────────────
# MAIN APPLICATION FLOW
# ────────────────────────────────────────────────
apply_theme()
init_data()

if not st.session_state.get("authenticated", False):
    auth_page()
else:
    with st.sidebar:
        st.markdown(f"**Welcome, {st.session_state.username}** 👋")
        st.caption(f"Role: {st.session_state.role}")

        if st.session_state.role == "Seller":
            nav = st.radio("Dashboard", ["Home", "Manage Inventory"])
        else:
            nav = st.radio("Dashboard", ["Home"])

        st.divider()
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if nav == "Manage Inventory" and st.session_state.role == "Seller":
        admin_page()
    else:
        home_page()
