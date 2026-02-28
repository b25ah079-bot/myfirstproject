import streamlit as st
import pandas as pd
import difflib
from geopy.distance import geodesic
from datetime import datetime
import streamlit.components.v1 as components
import calendar

# ────────────────────────────────────────────────
#  CONFIG & STYLING
# ────────────────────────────────────────────────
st.set_page_config(page_title="LowKey Deals", layout="wide", page_icon="✨")

def apply_theme():
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; }
        h1, h2, h3, h4, h5, h6, p, label, span, .stRadio > div > label {
            color: #000000 !important;
        }
        .deal-card {
            background: #FFFFFF;
            padding: 20px;
            border-radius: 12px;
            border-top: 4px solid #8B4513;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: all 0.22s ease;
        }
        .deal-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.11);
        }
        .price-tag {
            color: #8B4513;
            font-size: 1.6rem;
            font-weight: 700;
        }
        .badge {
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-right: 6px;
        }
        .in-stock  { background: #28a745; color: white; }
        .out-of-stock { background: #dc3545; color: white; }
        .sale-badge { background: #e63946; color: white; }
        input, textarea {
            border: 2px solid #8B4513 !important;
            border-radius: 8px !important;
            background: white !important;
        }
        div.stButton > button {
            background: #8B4513 !important;
            color: white !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 0.65rem 1.5rem !important;
            font-weight: 600;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background: #A0522D !important;
            transform: scale(1.03);
        }
    </style>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────
#  STATE INITIALIZATION
# ────────────────────────────────────────────────
@st.cache_resource
def get_global_catalog():
    return {}  # product_name → list of offer dicts

GLOBAL_CATALOG = get_global_catalog()

def init_session_state():
    defaults = {
        "authenticated": False,
        "username": None,
        "role": None,
        "store_info": None,
        "user_location": (9.9312, 76.2673),  # default Kochi approx
        "users": {"user1": "pass1", "testuser": "1234"},
        "sellers": {
            "seller1": {
                "password": "pass1",
                "store_name": "Appliance World",
                "address": "123 Kochi St, Kerala",
                "loc": (9.95, 76.29),
                "open_hours": (9, 21),
                "open_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
            },
            "seller2": {
                "password": "pass2",
                "store_name": "Home Mart",
                "address": "456 Ernakulam Rd, Kerala",
                "loc": (9.93, 76.27),
                "open_hours": (10, 22),
                "open_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            }
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ────────────────────────────────────────────────
#  SHARED COMPONENTS
# ────────────────────────────────────────────────
def show_location_controls(is_user: bool = True):
    if not is_user:
        return

    st.subheader("📍 Your Location")

    components.html("""
    <button id="getLoc" style="background:#8B4513;color:white;padding:10px 22px;border:none;border-radius:999px;font-weight:600;cursor:pointer;">
        📍 Get My Location
    </button>
    <div id="locmsg" style="margin-top:10px; color:#555;"></div>

    <script>
    document.getElementById("getLoc").onclick = () => {
        const msg = document.getElementById("locmsg");
        msg.innerHTML = "Requesting location…";
        if (!navigator.geolocation) {
            msg.innerHTML = "Geolocation not supported.";
            return;
        }
        navigator.geolocation.getCurrentPosition(
            pos => {
                const lat = pos.coords.latitude.toFixed(6);
                const lon = pos.coords.longitude.toFixed(6);
                msg.innerHTML = `Updated: ${lat}, ${lon}`;
                const url = new URL(window.location);
                url.searchParams.set("lat", lat);
                url.searchParams.set("lon", lon);
                window.location = url;
            },
            err => {
                let txt = "Failed to get location.";
                if (err.code === 1) txt = "Location permission denied.";
                if (err.code === 2) txt = "Position unavailable.";
                if (err.code === 3) txt = "Request timeout.";
                msg.innerHTML = txt;
                alert(txt + "\\nPlease allow location access in browser settings.");
            },
            {enableHighAccuracy: true, timeout: 12000, maximumAge: 0}
        );
    };
    </script>
    """, height=120)

    q = st.query_params
    if "lat" in q and "lon" in q:
        try:
            lat, lon = float(q["lat"][0]), float(q["lon"][0])
            st.session_state.user_location = (lat, lon)
            st.success(f"Location updated → {lat:.6f}, {lon:.6f}", icon="✅")
            # Clean query params after use
            st.query_params.clear()
        except:
            st.warning("Invalid location parameters.")

    with st.expander("Set location manually", expanded=False):
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=st.session_state.user_location[0], format="%.6f", step=0.00001)
        lon = c2.number_input("Longitude", value=st.session_state.user_location[1], format="%.6f", step=0.00001)
        if st.button("Save Custom Location", use_container_width=True):
            st.session_state.user_location = (lat, lon)
            st.success("Location saved", icon="📍")
            st.rerun()


def logout_button():
    if st.button("Logout", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ────────────────────────────────────────────────
#  SELLER — MANAGE INVENTORY
# ────────────────────────────────────────────────
def seller_manage_inventory():
    st.title("📦 Manage Inventory")
    store = st.session_state.store_info
    user = st.session_state.username

    st.markdown(f"**Store:** {store['store_name']}  •  {store['address']}")

    # ─── Update Store Location ───
    with st.expander("Update Store Location", expanded=False):
        lat, lon = store.get("loc", (9.93, 76.27))
        with st.form("upd_loc"):
            new_lat = st.number_input("Latitude", value=lat, format="%.6f")
            new_lon = st.number_input("Longitude", value=lon, format="%.6f")
            if st.form_submit_button("Save & Apply to All My Offers"):
                store["loc"] = (new_lat, new_lon)
                st.session_state.store_info = store
                count = 0
                for offers in GLOBAL_CATALOG.values():
                    for o in offers:
                        if o.get("seller_username") == user:
                            o["loc"] = (new_lat, new_lon)
                            count += 1
                st.success(f"Location updated — applied to {count} offer(s)")
                st.rerun()

    # ─── Bulk CSV Upload ───
    with st.expander("Bulk Upload via CSV", expanded=False):
        st.caption("Required columns: **name**, **price**. Optional: **desc**, **sale_price**")
        file = st.file_uploader("Upload CSV", type="csv")
        if file:
            try:
                df = pd.read_csv(file)
                count = 0
                for _, row in df.iterrows():
                    name = str(row.get("name", "")).strip()
                    if not name:
                        continue
                    price = float(row.get("price", 0))
                    sale_price = float(row.get("sale_price", 0)) if "sale_price" in row else 0
                    is_sale = sale_price > 0 and sale_price < price

                    offer = {
                        "seller_username": user,
                        "store": store["store_name"],
                        "address": store["address"],
                        "loc": store["loc"],
                        "price": price,
                        "sale_price": sale_price if is_sale else None,
                        "is_sale": is_sale,
                        "desc": str(row.get("desc", "")).strip(),
                        "reviews": [],
                        "price_reports": [],
                        "open_hours": store["open_hours"],
                        "open_days": store["open_days"],
                        "in_stock": True
                    }

                    if name not in GLOBAL_CATALOG:
                        GLOBAL_CATALOG[name] = []
                    # Replace existing or append
                    for i, ex in enumerate(GLOBAL_CATALOG[name]):
                        if ex.get("seller_username") == user:
                            GLOBAL_CATALOG[name][i] = offer
                            break
                    else:
                        GLOBAL_CATALOG[name].append(offer)
                    count += 1

                if count > 0:
                    st.success(f"Imported / updated **{count}** products")
                    st.rerun()
                else:
                    st.info("No valid products found in CSV.")
            except Exception as e:
                st.error(f"Error processing CSV: {e}")

    # ─── Add / Edit Single Product ───
    st.subheader("Add or Update Product")
    with st.form("single_product"):
        c1, c2 = st.columns([3, 2])
        name = c1.text_input("Product Name", placeholder="Samsung 253L Double Door Refrigerator")
        price = c2.number_input("Regular Price (₹)", min_value=0.0, step=100.0)
        sale_price = c2.number_input("Sale Price (optional)", min_value=0.0, step=100.0)
        desc = st.text_area("Description", height=120)

        if st.form_submit_button("Save Product", use_container_width=True):
            if not name.strip():
                st.error("Product name is required.")
            else:
                is_sale = sale_price > 0 and sale_price < price
                offer = {
                    "seller_username": user,
                    "store": store["store_name"],
                    "address": store["address"],
                    "loc": store["loc"],
                    "price": price,
                    "sale_price": sale_price if is_sale else None,
                    "is_sale": is_sale,
                    "desc": desc.strip(),
                    "reviews": [],
                    "price_reports": [],
                    "open_hours": store["open_hours"],
                    "open_days": store["open_days"],
                    "in_stock": True
                }

                if name not in GLOBAL_CATALOG:
                    GLOBAL_CATALOG[name] = []

                for i, ex in enumerate(GLOBAL_CATALOG[name]):
                    if ex.get("seller_username") == user:
                        GLOBAL_CATALOG[name][i] = offer
                        st.success(f"**{name}** updated")
                        st.rerun()
                        break
                else:
                    GLOBAL_CATALOG[name].append(offer)
                    st.success(f"**{name}** added")
                    st.rerun()

    # ─── My Products List ───
    st.subheader("My Products")
    my_offers = []
    for prod, offers in GLOBAL_CATALOG.items():
        for o in offers:
            if o.get("seller_username") == user:
                my_offers.append((prod, o))

    if not my_offers:
        st.info("You haven't listed any products yet.")
        return

    for prod_name, offer in my_offers:
        with st.container():
            cols = st.columns([5, 1.2, 1.2])
            current_price = offer.get("sale_price") or offer["price"]
            stock_txt = "In Stock" if offer.get("in_stock", True) else "Out of Stock"

            cols[0].markdown(f"**{prod_name}** ₹{current_price:,.0f} • {stock_txt}")

            if cols[1].button("✏️ Price", key=f"price_{prod_name}_{user}"):
                with st.form(f"price_form_{prod_name}"):
                    np = st.number_input("Regular price", value=float(offer["price"]), step=100.0)
                    nsp = st.number_input("Sale price", value=float(offer.get("sale_price") or 0), step=100.0)
                    if st.form_submit_button("Update Prices"):
                        offer["price"] = np
                        sp = nsp if nsp > 0 and nsp < np else None
                        offer["sale_price"] = sp
                        offer["is_sale"] = sp is not None
                        st.success("Price updated")
                        st.rerun()

            current_stock = offer.get("in_stock", True)
            btn_label = "Out of Stock" if current_stock else "Back In Stock"
            if cols[2].button(btn_label, key=f"stock_{prod_name}_{user}"):
                offer["in_stock"] = not current_stock
                st.success(f"**{prod_name}** is now {stock_txt}")
                st.rerun()

            with st.expander(f"Reviews & Price Reports – {prod_name}"):
                if offer.get("reviews"):
                    for r in offer["reviews"]:
                        st.write(f"• {r['user']}  {r['rating']}★  –  {r['text']}")
                else:
                    st.caption("No reviews yet")

                if offer.get("price_reports"):
                    st.write("**Price reports**")
                    for r in offer["price_reports"]:
                        st.write(f"• {r['user']} paid ₹{r['price']:,}  ({r
