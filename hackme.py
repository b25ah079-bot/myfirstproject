import streamlit as st
import pandas as pd
import difflib
from geopy.distance import geodesic
from datetime import datetime
import streamlit.components.v1 as components
import calendar

# --- CONFIGURATION ---
st.set_page_config(page_title="LowKey Deals", layout="wide", page_icon="✨")

# --- 1. THEME: BROWN, BLACK, WHITE WITH LIVELINESS ---
def apply_theme():
    st.markdown("""
        <style>
        /* Global Text & Label Colors */
        html, body, [data-testid="stHeader"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span, .stRadio p {
            color: #000000 !important;
            font-weight: 500;
        }
        .stApp { background-color: #FFFFFF; }
        /* Enhanced Card Styling with Hover Animation */
        .deal-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 15px;
            border-top: 4px solid #8B4513;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.3s ease-in-out, box-shadow 0.3s;
        }
        .deal-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.1);
        }
        .price-tag {
            color: #8B4513;
            font-size: 1.4rem;
            font-weight: bold;
        }
        /* Status Badge with Pulse Animation */
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: bold;
            text-transform: uppercase;
            background-color: #FFE4B5;
            color: #8B4513;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        input {
            color: #000000 !important;
            background-color: #FFFFFF !important;
            border: 2px solid #8B4513 !important;
        }
        div.stButton > button {
            background-color: #8B4513 !important;
            color: #FFFFFF !important;
            border-radius: 20px;
            font-weight: bold;
            transition: 0.3s;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #A0522D !important;
            transform: scale(1.05);
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
def init_data():
    if 'item_offers' not in st.session_state or not isinstance(st.session_state.item_offers, dict):
        st.session_state.item_offers = {
            "Refrigerator": [
                {
                    "store": "Appliance World",
                    "address": "123 Kochi St, Kerala",
                    "loc": (9.95, 76.29),
                    "price": 25000,
                    "sale_price": None,
                    "is_sale": False,
                    "desc": "Double door, 250L",
                    "reviews": [{"user": "user1", "rating": 4, "text": "Good product"}],
                    "open_hours": (9, 21),
                    "open_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                },
                {
                    "store": "Home Mart",
                    "address": "456 Ernakulam Rd, Kerala",
                    "loc": (9.93, 76.27),
                    "price": 26000,
                    "sale_price": 24000,
                    "is_sale": True,
                    "desc": "Double door, 260L",
                    "reviews": [],
                    "open_hours": (10, 22),
                    "open_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                }
            ],
            "Washing Machine": [
                {
                    "store": "Appliance World",
                    "address": "123 Kochi St, Kerala",
                    "loc": (9.95, 76.29),
                    "price": 18000,
                    "sale_price": None,
                    "is_sale": False,
                    "desc": "Front load, 7kg",
                    "reviews": [],
                    "open_hours": (9, 21),
                    "open_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                },
                {
                    "store": "Home Mart",
                    "address": "456 Ernakulam Rd, Kerala",
                    "loc": (9.93, 76.27),
                    "price": 17000,
                    "sale_price": None,
                    "is_sale": False,
                    "desc": "Front load, 6kg",
                    "reviews": [{"user": "user1", "rating": 5, "text": "Excellent"}],
                    "open_hours": (10, 22),
                    "open_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                }
            ]
        }
    if 'users' not in st.session_state:
        st.session_state.users = {"user1": "pass1"}
    if 'sellers' not in st.session_state:
        st.session_state.sellers = {
            "seller1": {
                "password": "pass1",
                "store_name": "Appliance World",
                "loc": (9.95, 76.29),
                "open_hours": (9, 21),
                "open_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "address": "123 Kochi St, Kerala"
            },
            "seller2": {
                "password": "pass2",
                "store_name": "Home Mart",
                "loc": (9.93, 76.27),
                "open_hours": (10, 22),
                "open_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "address": "456 Ernakulam Rd, Kerala"
            }
        }
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_location' not in st.session_state:
        st.session_state.user_location = (9.9312, 76.2673)  # Kochi, Kerala (default)

# --- 3. UI PAGES ---
def admin_page():
    st.title("📦 Inventory Manager")

    with st.expander("💡 CSV Format Instructions"):
        st.write("Your CSV should have these columns: `name`, `desc`, `price`, `sale_price` (optional)")
    uploaded_file = st.file_uploader("Bulk Upload via CSV", type="csv")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            store_info = st.session_state.store_info
            added_count = 0
            for _, row in df.iterrows():
                name = row['name']
                desc = row['desc']
                price = row['price']
                sale_price = row.get('sale_price', 0)
                is_sale = sale_price > 0 and sale_price < price
                offer = {
                    "store": store_info["store_name"],
                    "address": store_info["address"],
                    "loc": store_info["loc"],
                    "price": price,
                    "sale_price": sale_price if is_sale else None,
                    "is_sale": is_sale,
                    "desc": desc,
                    "reviews": [],  # Reviews not from CSV
                    "open_hours": store_info["open_hours"],
                    "open_days": store_info["open_days"]
                }
                if name not in st.session_state.item_offers:
                    st.session_state.item_offers[name] = []
                # Update if exists for this store, else append
                updated = False
                for idx, o in enumerate(st.session_state.item_offers[name]):
                    if o["store"] == offer["store"]:
                        st.session_state.item_offers[name][idx] = offer
                        updated = True
                        break
                if not updated:
                    st.session_state.item_offers[name].append(offer)
                added_count += 1
            st.success(f"Imported/Updated {added_count} items!")
        except Exception as e:
            st.error(f"Error: {e}")
    st.divider()
    st.subheader("Add/Update Single Item")
    with st.form("manual_add"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Product Name")
        price = c2.number_input("Price (₹)", min_value=0.0)
        sale_price = c2.number_input("Sale Price (optional, ₹)", min_value=0.0)
        desc = st.text_area("Description")
        if st.form_submit_button("Add/Update to Catalog"):
            if name:
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
                    "open_days": store_info["open_days"]
                }
                if name not in st.session_state.item_offers:
                    st.session_state.item_offers[name] = []
                # Update if exists, else append
                updated = False
                for idx, o in enumerate(st.session_state.item_offers[name]):
                    if o["store"] == offer["store"]:
                        st.session_state.item_offers[name][idx] = offer
                        updated = True
                        break
                if not updated:
                    st.session_state.item_offers[name].append(offer)
                st.toast(f"Success! {name} is now live/updated.")
            else:
                st.error("Product name is required.")

def home_page():
    # Live Location Button
    st.subheader("🗺️ Enable Live Location")
    st.write("Click below to share your current location for accurate distances! 📍")
    components.html("""
        <button onclick="getLocation()" style="background-color: #8B4513; color: white; padding: 10px 20px; border: none; border-radius: 20px; cursor: pointer;">Get My Location</button>
        <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(showPosition, showError);
            } else {
                alert("Geolocation is not supported by this browser.");
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
            alert("Error getting location: " + error.message);
        }
        </script>
    """, height=60)

    # Check query params for location (modern Streamlit API)
    query_params = st.query_params

    lat_str = query_params.get('lat')
    lon_str = query_params.get('lon')

    if lat_str and lon_str:
        try:
            lat = float(lat_str[0])
            lon = float(lon_str[0])
            st.session_state.user_location = (lat, lon)
            st.success(f"📍 Live location updated: {lat:.6f}, {lon:.6f}")
        except (ValueError, IndexError):
            st.warning("Could not read location from URL parameters.")

    # Manual Location Update
    with st.expander("Or Update Location Manually"):
        lat = st.number_input("Latitude", value=st.session_state.user_location[0])
        lon = st.number_input("Longitude", value=st.session_state.user_location[1])
        if st.button("Save Manual Location"):
            st.session_state.user_location = (lat, lon)
            st.success("Location updated! 🚀")

    # Hero Section
    col_title, col_loc = st.columns([3, 1])
    with col_title:
        st.title("✨ LowKey Deals")
        st.markdown("### Lowkey the best prices near you. 🛒💸")
    with col_loc:
        st.caption("📍 Current Location")
        st.code(f"Lat: {st.session_state.user_location[0]:.4f}, Lon: {st.session_state.user_location[1]:.4f}")

    # Sales Section
    st.subheader("🔥 Ongoing Sales")
    sales_items = []
    for item_name, offers in st.session_state.item_offers.items():
        for o in offers:
            if o["is_sale"]:
                sales_items.append((item_name, o))
    if sales_items:
        cols = st.columns(3)
        for i, (name, o) in enumerate(sales_items):
            dist = geodesic(st.session_state.user_location, o["loc"]).km
            with cols[i % 3]:
                st.markdown(f"""
                <div class="deal-card">
                    <span class="badge">Sale 🔥</span>
                    <h4>{name}</h4>
                    <p>{o['desc'][:50]}...</p>
                    <del>₹{o['price']:,}</del> <span class="price-tag">₹{o['sale_price']:,}</span>
                    <span style="font-size: 0.8rem; color: #888;">📍 {dist:.1f}km</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"View Deal", key=f"sale_btn_{i}_{name}"):
                    st.session_state.selected_item = name
                    st.rerun()
    else:
        st.info("No sales currently. Check back soon! 😊")

    # Search Bar
    search_input = st.text_input("🔍 Search for appliances...", placeholder="Type 'Refrigerator'...", key="main_search")

    if search_input:
        all_items = list(st.session_state.item_offers.keys())
        suggestions = difflib.get_close_matches(search_input, all_items, n=5, cutoff=0.5)
        if suggestions:
            st.write("Did you mean:")
            cols = st.columns(len(suggestions))
            for i, sug in enumerate(suggestions):
                if cols[i].button(f"👉 {sug}", key=f"sug_btn_{i}_{sug}"):
                    st.session_state.selected_item = sug
                    st.rerun()

    st.divider()

    # Display Logic
    if 'selected_item' in st.session_state:
        item_name = st.session_state.selected_item
        offers = st.session_state.item_offers.get(item_name, [])
        if offers:
            st.header(f"🛍️ {item_name}")
            user_loc = st.session_state.user_location
            current_time = datetime.now()
            current_hour = current_time.hour
            current_day = current_time.strftime("%A")
            annotated_offers = []
            prices = [o["sale_price"] if o["is_sale"] else o["price"] for o in offers]
            min_price = min(prices)
            max_price = max(prices)
            lowest_store = next(o["store"] for o in offers if (o["sale_price"] if o["is_sale"] else o["price"]) == min_price)
            st.info(f"Lowest price at: {lowest_store} (₹{min_price:,}) 💰")
            for o in offers:
                dist = geodesic(user_loc, o["loc"]).km
                reviews = o["reviews"]
                avg_rating = sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0
                price_for_effort = o["sale_price"] if o["is_sale"] else o["price"]
                normalized_price = (price_for_effort - min_price) / (max_price - min_price) if max_price > min_price else 0
                effort = normalized_price * 50 + dist * 0.5 + (5 - avg_rating)
                is_open = current_day in o["open_days"] and o["open_hours"][0] <= current_hour < o["open_hours"][1]
                annotated_offers.append({"offer": o, "dist": dist, "avg_rating": avg_rating, "effort": effort, "is_open": is_open})
            annotated_offers.sort(key=lambda x: x["effort"])
            for ao in annotated_offers:
                o = ao["offer"]
                st.subheader(f"🏪 {o['store']}")
                st.write(f"Address: {o['address']}")
                price = o["sale_price"] if o["is_sale"] else o["price"]
                st.metric("Price", f"₹{price:,}" + (" (Sale! 🔥)" if o["is_sale"] else ""))
                st.write(f"Distance: {ao['dist']:.1f} km 🚗")
                st.write(f"Rating: {ao['avg_rating']:.1f} ⭐" if ao['avg_rating'] > 0 else "No ratings yet 😔")
                status = "Open ✅" if ao["is_open"] else "Closed ❌"
                st.write(f"Status: {status}")
                st.write(f"Open Days: {', '.join(o['open_days'])}")
                st.write(f"Effort Score: {ao['effort']:.2f} (lower is better) 📊")
                img_url = f"https://loremflickr.com/300/200/appliance,{item_name.lower().replace(' ', '_')}"
                st.image(img_url, caption=f"Sample {item_name}")
                # Google Maps Directions Link
                maps_url = f"https://www.google.com/maps/dir/?api=1&origin={user_loc[0]},{user_loc[1]}&destination={o['loc'][0]},{o['loc'][1]}"
                st.markdown(f"[Get Directions on Google Maps 🗺️]({maps_url})")
                with st.expander("Reviews 📝"):
                    if o["reviews"]:
                        for r in o["reviews"]:
                            st.write(f"{r['user']}: {r['rating']} ⭐ - {r['text']}")
                    else:
                        st.write("No reviews yet. Be the first! ✍️")
                if st.session_state.role == "User":
                    with st.form(key=f"review_form_{o['store']}_{item_name}"):
                        st.write("Your Rating")
                        rating_options = ["1 ⭐", "2 ⭐⭐", "3 ⭐⭐⭐", "4 ⭐⭐⭐⭐", "5 ⭐⭐⭐⭐⭐"]
                        rating_str = st.radio("", rating_options, horizontal=True)
                        rating = int(rating_str[0])  # Extract number
                        text = st.text_area("Your Review")
                        if st.form_submit_button("Submit Review"):
                            o["reviews"].append({"user": st.session_state.username, "rating": rating, "text": text})
                            st.success("Review added! Thank you! 🎉")
                            st.rerun()
                    with st.form(key=f"buy_form_{o['store']}_{item_name}"):
                        st.write("Buy and Report Price")
                        bought_price = st.number_input("Price You Paid (₹)", min_value=0.0)
                        bill_upload = st.file_uploader("Upload Bill (for verification)", type=["jpg", "png", "pdf"])
                        if st.form_submit_button("Submit Purchase"):
                            if bought_price > 0 and bill_upload:
                                # Mock verification
                                st.success("Purchase reported and bill verified! Price updated.")
                                o["price"] = bought_price  # Update price (mock)
                            else:
                                st.error("Please enter price and upload bill.")
            if st.button("⬅️ Back to Browse"):
                del st.session_state.selected_item
                st.rerun()
        else:
            st.warning("No offers available for this item. 😕")
    else:
        # Grid View
        st.subheader("🛒 Available Appliances")
        all_items = list(st.session_state.item_offers.keys())
        if not all_items:
            st.warning("The catalog is empty. Sellers, head to 'Manage Inventory' to add deals! 📈")
        else:
            cols = st.columns(3)
            user_loc = st.session_state.user_location
            for i, name in enumerate(all_items):
                offers = st.session_state.item_offers[name]
                prices = [o["sale_price"] if o["is_sale"] else o["price"] for o in offers]
                min_price = min(prices)
                min_dist = min(geodesic(user_loc, o["loc"]).km for o in offers)
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="deal-card">
                        <h4>{name}</h4>
                        <p class="price-tag">From ₹{min_price:,}</p>
                        <span style="font-size: 0.8rem; color: #888;">📍 Closest {min_dist:.1f}km</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Compare Prices", key=f"item_btn_{i}_{name}"):
                        st.session_state.selected_item = name
                        st.rerun()

def auth_page():
    st.title("Welcome to LowKey Deals")
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        role = st.radio("Select Role", ["User", "Seller"], key="login_role")
        username = st.text_input("Username", placeholder="Enter your username...", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password...", key="login_password")
        if st.button("Login"):
            if username and password:
                if role == "User":
                    if username in st.session_state.users and st.session_state.users[username] == password:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.session_state.store_info = None
                        st.rerun()
                    else:
                        st.error("Invalid username or password for User.")
                elif role == "Seller":
                    if username in st.session_state.sellers and st.session_state.sellers[username]["password"] == password:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.session_state.store_info = st.session_state.sellers[username]
                        st.rerun()
                    else:
                        st.error("Invalid username or password for Seller.")
            else:
                st.error("Please enter both username and password.")

    with tab_signup:
        role = st.radio("Select Role", ["User", "Seller"], key="signup_role")
        username = st.text_input("Username", placeholder="Choose a username...", key="signup_username")
        password = st.text_input("Password", type="password", placeholder="Choose a password...", key="signup_password")
        if role == "Seller":
            store_name = st.text_input("Store Name", placeholder="Enter your store name...")
            address = st.text_input("Store Address", placeholder="Enter full address...")
            lat = st.number_input("Store Latitude", value=9.93)
            lon = st.number_input("Store Longitude", value=76.27)
            open_from = st.number_input("Opening Hour (0-23)", min_value=0, max_value=23, value=9)
            open_to = st.number_input("Closing Hour (0-23)", min_value=0, max_value=23, value=21)
            open_days = st.multiselect("Open Days", list(calendar.day_name), default=list(calendar.day_name)[:-1])
        if st.button("Sign Up"):
            if username and password:
                if role == "User":
                    if username in st.session_state.users:
                        st.error("Username already exists.")
                    else:
                        st.session_state.users[username] = password
                        st.success("User signed up! Please login.")
                elif role == "Seller":
                    if username in st.session_state.sellers:
                        st.error("Username already exists.")
                    elif not (store_name and address and open_days):
                        st.error("Store name, address, and open days are required.")
                    else:
                        st.session_state.sellers[username] = {
                            "password": password,
                            "store_name": store_name,
                            "loc": (lat, lon),
                            "open_hours": (open_from, open_to),
                            "open_days": open_days,
                            "address": address
                        }
                        st.success("Seller signed up! Please login.")
            else:
                st.error("Please enter username and password.")

# --- 4. EXECUTION FLOW ---
apply_theme()
init_data()
if not st.session_state.authenticated:
    auth_page()
else:
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username} 👋")
        if st.session_state.role == "Seller":
            nav = st.radio("Dashboard", ["Home", "Manage Inventory"])
        else:
            nav = "Home"

        st.divider()
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if nav == "Manage Inventory":
        admin_page()
    else:
        home_page()
