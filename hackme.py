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
        }
        .in-stock { background: #28a745; color: white; }
        .out-of-stock { background: #dc3545; color: white; }
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
            width: 100%;
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
# SELLER — MANAGE INVENTORY (with refresh & delete fixed)
# ────────────────────────────────────────────────
def admin_page():
    st.title("📦 Manage Inventory")

    if 'store_info' not in st.session_state or not st.session_state.store_info:
        st.error("Store information missing. Please log out and log in again.")
        return

    store = st.session_state.store_info
    current_user = st.session_state.username

    st.markdown(f"**Store:** {store['store_name']}  •  {store['address']}")

    # Update Store Location
    st.divider()
    st.subheader("Update Store Location")

    current_lat, current_lon = store.get("loc", (9.93, 76.27))

    with st.form("update_store_location"):
        new_lat = st.number_input("Latitude", value=current_lat, format="%.6f", step=0.000001)
        new_lon = st.number_input("Longitude", value=current_lon, format="%.6f", step=0.000001)

        if st.form_submit_button("Save New Location"):
            store["loc"] = (new_lat, new_lon)
            st.session_state.store_info = store

            updated_count = 0
            for product_name, offers in GLOBAL_CATALOG.items():
                for offer in offers:
                    if offer.get("seller_username") == current_user:
                        offer["loc"] = (new_lat, new_lon)
                        updated_count += 1

            st.success(f"Store location updated! Applied to {updated_count} offers.")
            st.rerun()

    # CSV Bulk Upload
    with st.expander("Bulk upload via CSV", expanded=False):
        st.caption("Columns: name, desc, price, sale_price (optional)")
        uploaded = st.file_uploader("Choose CSV file", type="csv", key="csv_upload")

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
                        "seller_username": current_user,
                        "store": store["store_name"],
                        "address": store["address"],
                        "loc": store["loc"],
                        "price": price,
                        "sale_price": sale_price_val if is_sale else None,
                        "is_sale": is_sale,
                        "desc": str(row.get("desc", "")).strip(),
                        "reviews": [],
                        "open_hours": store["open_hours"],
                        "open_days": store["open_days"],
                        "in_stock": True
                    }

                    if name not in GLOBAL_CATALOG:
                        GLOBAL_CATALOG[name] = []

                    replaced = False
                    for i, ex in enumerate(GLOBAL_CATALOG[name]):
                        if ex.get("seller_username") == current_user:
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
                st.error(f"CSV processing error: {e}")

    st.divider()

    # Add / Update single product
    st.subheader("Add or update single product")

    with st.form("single_item_form"):
        c1, c2 = st.columns([3,2])
        raw_name = c1.text_input("Product name", placeholder="e.g. Samsung Double Door Refrigerator")
        price     = c2.number_input("Regular price (₹)", min_value=0.0, step=100.0)
        sale_price_input = c2.number_input("Sale price (optional)", min_value=0.0, step=100.0)

        description = st.text_area("Description", height=110)

        submitted = st.form_submit_button("Save Product", use_container_width=True)

        if submitted and raw_name.strip():
            name = raw_name.strip()

            is_sale = sale_price_input > 0 and sale_price_input < price

            offer = {
                "seller_username": current_user,
                "store": store["store_name"],
                "address": store["address"],
                "loc": store["loc"],
                "price": price,
                "sale_price": sale_price_input if is_sale else None,
                "is_sale": is_sale,
                "desc": description.strip(),
                "reviews": [],
                "open_hours": store["open_hours"],
                "open_days": store["open_days"],
                "in_stock": True
            }

            if name not in GLOBAL_CATALOG:
                GLOBAL_CATALOG[name] = []

            updated = False
            for i, ex in enumerate(GLOBAL_CATALOG[name]):
                if ex.get("seller_username") == current_user:
                    GLOBAL_CATALOG[name][i] = offer
                    updated = True
                    break
            if not updated:
                GLOBAL_CATALOG[name].append(offer)

            st.success(f"✓ Product **{raw_name}** saved / updated")
            st.rerun()
        elif submitted:
            st.error("Product name is required")

    # ───── My Added Products ───── with Refresh + Delete
    st.divider()
    st.subheader("My Added Products")

    # Refresh button - forces full list rebuild
    if st.button("🔄 Refresh Product List"):
        st.rerun()

    # Build product list
    my_products = []
    for product_name, offers in GLOBAL_CATALOG.items():
        for offer in offers:
            if offer.get("seller_username") == current_user:
                my_products.append({
                    "product_name": product_name,
                    "offer": offer
                })

    if not my_products:
        st.info("You haven't added any products yet.")
    else:
        for idx, item in enumerate(my_products):
            name = item["product_name"]
            offer = item["offer"]

            key_prefix = f"prod_{idx}_{name.replace(' ', '_')}_{current_user}"

            cols = st.columns([4, 1, 1])
            with cols[0]:
                current_price = offer.get('sale_price') or offer['price']
                stock_status = "In Stock ✅" if offer.get("in_stock", True) else "Out of Stock ❌"
                st.markdown(f"**{name}** — ₹{current_price:,}  •  {stock_status}")

            with cols[1]:
                if st.button("✏️ Update Price", key=f"upd_btn_{key_prefix}"):
                    with st.form(key=f"upd_form_{key_prefix}"):
                        new_regular = st.number_input("New regular price (₹)", 
                                                     value=float(offer["price"]), 
                                                     min_value=0.0, 
                                                     step=100.0,
                                                     key=f"reg_{key_prefix}")

                        new_sale = st.number_input("New sale price (optional)", 
                                                  value=float(offer.get("sale_price") or 0), 
                                                  min_value=0.0, 
                                                  step=100.0,
                                                  key=f"sale_{key_prefix}")

                        if st.form_submit_button("Save New Prices"):
                            offer["price"] = new_regular
                            if new_sale > 0 and new_sale < new_regular:
                                offer["sale_price"] = new_sale
                                offer["is_sale"] = True
                            else:
                                offer["sale_price"] = None
                                offer["is_sale"] = False

                            st.success(f"Price updated → ₹{new_regular:,}")
                            st.rerun()

            with cols[2]:
                current_stock = offer.get("in_stock", True)
                btn_text = "Mark Out of Stock" if current_stock else "Mark In Stock"
                if st.button(btn_text, key=f"stock_{key_prefix}"):
                    offer["in_stock"] = not current_stock
                    st.success(f"**{name}** marked as {'In Stock' if offer['in_stock'] else 'Out of Stock'}")
                    st.rerun()

                # Delete button
                if st.button("🗑️ Delete", key=f"del_{key_prefix}", type="primary"):
                    GLOBAL_CATALOG[name] = [
                        ex for ex in GLOBAL_CATALOG[name]
                        if ex.get("seller_username") != current_user
                    ]
                    if not GLOBAL_CATALOG[name]:
                        del GLOBAL_CATALOG[name]
                    st.success(f"Product **{name}** deleted.")
                    st.rerun()

    # Reviews & Price Reports
    st.divider()
    st.subheader("My Reviews & Reports")

    has_content = False
    for product_name, offers in GLOBAL_CATALOG.items():
        for offer in offers:
            if offer.get("seller_username") == current_user:
                reviews = offer.get("reviews", [])
                price_reports = offer.get("price_reports", [])

                if reviews or price_reports:
                    has_content = True
                    with st.expander(f"{product_name} - Reviews & Reports"):
                        if reviews:
                            st.write("**Reviews:**")
                            for r in reviews:
                                st.write(f"- {r['user']}: {r['rating']} ⭐ – {r['text']}")

                        if price_reports:
                            st.write("**Price Reports:**")
                            for r in price_reports:
                                st.write(f"- {r['user']} paid ₹{r['price']:,} on {r['timestamp']}")
                                if r.get("bill_filename"):
                                    st.caption(f"Bill: {r['bill_filename']}")

    if not has_content:
        st.info("No reviews or price reports yet on your products.")

# ────────────────────────────────────────────────
# USER — HOME / BROWSING PAGE
# ────────────────────────────────────────────────
def home_page():
    st.title("✨ LowKey Deals")
    st.caption("Discover the best local appliance prices near you")

    # Location section — only for users
    if st.session_state.get("role") == "User":
        st.subheader("📍 Your Location")

        components.html("""
            <button id="getLocBtn" style="background:#8B4513;color:white;padding:12px 24px;border:none;border-radius:999px;cursor:pointer;font-weight:bold;">
                Get My Location
            </button>

            <div id="locStatus" style="margin-top:10px;color:#555;font-size:0.95rem;"></div>

            <script>
            document.getElementById("getLocBtn").onclick = function() {
                const status = document.getElementById("locStatus");
                status.innerHTML = "Requesting location... Please allow access.";

                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            const lat = position.coords.latitude.toFixed(6);
                            const lon = position.coords.longitude.toFixed(6);
                            status.innerHTML = "Location acquired! Updating page...";
                            const url = new URL(window.location);
                            url.searchParams.set('lat', lat);
                            url.searchParams.set('lon', lon);
                            window.location = url;
                        },
                        (error) => {
                            let msg = "Could not get location.";
                            switch(error.code) {
                                case error.PERMISSION_DENIED:
                                    msg = "Location permission denied.";
                                    break;
                                case error.POSITION_UNAVAILABLE:
                                    msg = "Location unavailable.";
                                    break;
                                case error.TIMEOUT:
                                    msg = "Timed out.";
                                    break;
                            }
                            status.innerHTML = msg;
                            alert(msg + "\\nEnable location in settings.");
                        },
                        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
                    );
                } else {
                    status.innerHTML = "Geolocation not supported.";
                    alert("Browser does not support geolocation.");
                }
            };
            </script>
        """, height=140)

        q = st.query_params
        if 'lat' in q and 'lon' in q:
            try:
                lat = float(q['lat'][0])
                lon = float(q['lon'][0])
                st.session_state.user_location = (lat, lon)
                st.success(f"Location updated: {lat:.6f}, {lon:.6f}")
            except:
                st.warning("Could not read location.")

        with st.expander("Or set location manually"):
            lat = st.number_input("Latitude", value=st.session_state.user_location[0], step=0.00001, format="%.6f")
            lon = st.number_input("Longitude", value=st.session_state.user_location[1], step=0.00001, format="%.6f")
            if st.button("Save"):
                st.session_state.user_location = (lat, lon)
                st.rerun()

        st.divider()

    # Hot sales
    st.subheader("🔥 Ongoing Sales")
    sales_items = []
    for item_name, offers in GLOBAL_CATALOG.items():
        for o in offers:
            if o.get("is_sale", False) and o.get("in_stock", True):
                sales_items.append((item_name, o))

    if sales_items:
        cols = st.columns(3)
        for i, (name, o) in enumerate(sales_items):
            dist = geodesic(st.session_state.user_location, o["loc"]).km
            with cols[i % 3]:
                stock_badge = '<span class="badge in-stock">In Stock</span>' if o.get("in_stock", True) else '<span class="badge out-of-stock">Out of Stock</span>'
                st.markdown(f"""
                <div class="deal-card">
                    {stock_badge}
                    <span class="badge">Sale 🔥</span>
                    <h4>{name}</h4>
                    <p>{o['desc'][:60]}{'...' if len(o['desc']) > 60 else ''}</p>
                    <del>₹{o['price']:,}</del> <span class="price-tag">₹{o['sale_price']:,}</span>
                    <div style="font-size:0.85rem;color:#666;margin-top:8px;">≈ {dist:.1f} km</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View Deal", key=f"sale_btn_{i}_{name}"):
                    st.session_state.selected_item = name
                    st.rerun()
    else:
        st.info("No active sales at the moment.")

    # Search
    search_term = st.text_input("🔍 Search appliances...", placeholder="e.g. Refrigerator, Washing Machine")
    if search_term:
        all_names = list(GLOBAL_CATALOG.keys())
        suggestions = difflib.get_close_matches(search_term, all_names, n=5, cutoff=0.5)
        if suggestions:
            st.write("Did you mean:")
            cols = st.columns(min(5, len(suggestions)))
            for i, sug in enumerate(suggestions):
                if cols[i].button(f"👉 {sug}", key=f"sug_btn_{i}_{sug}"):
                    st.session_state.selected_item = sug
                    st.rerun()

    st.divider()

    # Product detail view
    if 'selected_item' in st.session_state:
        item_name = st.session_state.selected_item
        offers = GLOBAL_CATALOG.get(item_name, [])

        if offers:
            st.header(f"🛍️ {item_name}")

            user_loc = st.session_state.user_location
            now = datetime.now()
            current_hour = now.hour
            current_day = now.strftime("%A")

            prices = [o["sale_price"] if o.get("is_sale") else o["price"] for o in offers if o.get("in_stock", True)]
            min_price = min(prices) if prices else 0
            lowest_store = next((o["store"] for o in offers if (o["sale_price"] if o.get("is_sale") else o["price"]) == min_price and o.get("in_stock", True)), "—")

            st.info(f"Lowest price at: **{lowest_store}** (₹{min_price:,}) 💰")

            annotated_offers = []
            for o in offers:
                if not o.get("in_stock", True):
                    continue
                dist = geodesic(user_loc, o["loc"]).km
                reviews = o.get("reviews", [])
                avg_rating = sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0
                price_val = o["sale_price"] if o.get("is_sale") else o["price"]
                price_normalized = (price_val - min_price) / (max(prices) - min_price) if max(prices) > min_price else 0
                effort = price_normalized * 50 + dist * 0.5 + (5 - avg_rating)
                is_open = current_day in o["open_days"] and o["open_hours"][0] <= current_hour < o["open_hours"][1]

                annotated_offers.append({
                    "offer": o,
                    "dist": dist,
                    "avg_rating": avg_rating,
                    "effort": effort,
                    "is_open": is_open
                })

            annotated_offers.sort(key=lambda x: x["effort"])

            # Community average price
            all_reports = []
            for o in offers:
                all_reports.extend(o.get("price_reports", []))
            if all_reports:
                avg_reported = sum(r["price"] for r in all_reports) / len(all_reports)
                st.caption(f"Community average paid: ₹{avg_reported:,.0f} (based on {len(all_reports)} reports)")

            for entry in annotated_offers:
                o = entry["offer"]
                st.subheader(f"🏪 {o['store']}")
                st.write(f"**Address:** {o['address']}")
                price_display = f"₹{o['sale_price']:,} (Sale!)" if o.get("is_sale") else f"₹{o['price']:,}"
                st.metric("Price", price_display)
                st.write(f"**Distance:** {entry['dist']:.1f} km")
                st.write(f"**Rating:** {entry['avg_rating']:.1f} ⭐" if entry['avg_rating'] > 0 else "No ratings yet")
                st.write("**Open now** ✅" if entry["is_open"] else "**Closed** ❌")
                st.write(f"Open: {', '.join(o['open_days'])}  |  {o['open_hours'][0]}–{o['open_hours'][1]}")

                stock_status = "In Stock ✅" if o.get("in_stock", True) else "Out of Stock ❌"
                st.markdown(f"**Status:** {stock_status}")

                img_url = f"https://loremflickr.com/320/180/appliance,{item_name.lower().replace(' ','_')}"
                st.image(img_url, use_column_width=True)

                maps_url = f"https://www.google.com/maps/dir/?api=1&origin={user_loc[0]},{user_loc[1]}&destination={o['loc'][0]},{o['loc'][1]}"
                st.markdown(
                    f'<a href="{maps_url}" target="_blank" rel="noopener noreferrer">'
                    f'<button style="background:#1e90ff;color:white;border:none;border-radius:999px;padding:0.6rem 1.4rem;font-weight:600;width:100%;cursor:pointer;">'
                    f'Get Directions on Google Maps 🗺️'
                    f'</button></a>',
                    unsafe_allow_html=True
                )

                with st.expander("Reviews 📝"):
                    if o.get("reviews"):
                        for r in o["reviews"]:
                            st.write(f"**{r['user']}**: {r['rating']} ⭐ – {r['text']}")
                    else:
                        st.write("No reviews yet.")

                    if st.session_state.role == "User":
                        with st.form(key=f"review_form_{o['store']}_{item_name}"):
                            rating_str = st.radio("Your rating", ["1 ⭐","2 ⭐⭐","3 ⭐⭐⭐","4 ⭐⭐⭐⭐","5 ⭐⭐⭐⭐⭐"], horizontal=True)
                            rating = int(rating_str[0])
                            comment = st.text_area("Your comment")
                            if st.form_submit_button("Submit Review"):
                                if "reviews" not in o:
                                    o["reviews"] = []
                                o["reviews"].append({
                                    "user": st.session_state.username,
                                    "rating": rating,
                                    "text": comment
                                })
                                st.success("Review added! Thank you!")
                                st.rerun()

                # Price Report Section
                if st.session_state.role == "User":
                    with st.expander("Report the price you actually paid"):
                        st.write("Help keep prices accurate — share what you paid (optional bill upload).")
                        paid_price = st.number_input("Price you paid (₹)", min_value=0.0, step=100.0, key=f"paid_{o['store']}_{item_name}")
                        bill_file = st.file_uploader("Upload bill photo/PDF (optional)", type=["jpg", "png", "pdf", "jpeg"], key=f"bill_{o['store']}_{item_name}")
                        if st.button("Submit Price Report", key=f"report_price_{o['store']}_{item_name}"):
                            if paid_price > 0:
                                report = {
                                    "user": st.session_state.username,
                                    "price": paid_price,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "bill_filename": bill_file.name if bill_file else None
                                }
                                if "price_reports" not in o:
                                    o["price_reports"] = []
                                o["price_reports"].append(report)

                                if bill_file:
                                    st.info(f"Bill '{bill_file.name}' received (verification pending)")

                                st.success("Price report submitted — thank you!")
                                st.rerun()
                            else:
                                st.error("Please enter a valid price.")

                if "price_reports" in o and o["price_reports"]:
                    with st.expander("Community reported prices", expanded=False):
                        for r in o["price_reports"]:
                            st.write(f"{r['user']} paid ₹{r['price']:,} on {r['timestamp']}")
                            if r.get("bill_filename"):
                                st.caption(f"Bill uploaded: {r['bill_filename']}")

            if st.button("← Back to browse"):
                if 'selected_item' in st.session_state:
                    del st.session_state.selected_item
                st.rerun()

        else:
            st.warning("No offers available for this item.")

    else:
        st.subheader("🛒 Available Appliances")
        all_items = list(GLOBAL_CATALOG.keys())
        if not all_items:
            st.info("No products in catalog yet. Sellers can add items in Manage Inventory.")
        else:
            cols = st.columns(3)
            for i, name in enumerate(all_items):
                offers = GLOBAL_CATALOG[name]
                in_stock_offers = [o for o in offers if o.get("in_stock", True)]
                if not in_stock_offers:
                    continue
                prices = [o["sale_price"] if o.get("is_sale") else o["price"] for o in in_stock_offers]
                min_p = min(prices) if prices else 0
                min_d = min(geodesic(st.session_state.user_location, o["loc"]).km for o in in_stock_offers)

                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="deal-card">
                        <h4>{name}</h4>
                        <p class="price-tag">From ₹{min_p:,}</p>
                        <div style="color:#666;font-size:0.9rem;">Closest ≈ {min_d:.1f} km</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Compare Prices", key=f"item_btn_{i}_{name}"):
                        st.session_state.selected_item = name
                        st.rerun()

# ────────────────────────────────────────────────
# AUTHENTICATION PAGE
# ────────────────────────────────────────────────
def auth_page():
    st.title("Welcome to LowKey Deals")
    st.markdown("**Lowkey the best prices near you** 💸", unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        role = st.radio("Select Role", ["User", "Seller"], key="login_role")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if username and password:
                if role == "User":
                    if username in st.session_state.users and st.session_state.users[username] == password:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                elif role == "Seller":
                    if username in st.session_state.sellers and st.session_state.sellers[username]["password"] == password:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.session_state.store_info = st.session_state.sellers[username]
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
            else:
                st.error("Please enter both username and password.")

    with tab_signup:
        role = st.radio("Sign up as", ["User", "Seller"], key="signup_role")
        username = st.text_input("Choose username", key="signup_username")
        password = st.text_input("Choose password", type="password", key="signup_password")

        store_info = {}
        if role == "Seller":
            store_info["store_name"] = st.text_input("Store Name")
            store_info["address"] = st.text_input("Store Address")
            store_info["loc"] = (
                st.number_input("Store Latitude", value=9.93),
                st.number_input("Store Longitude", value=76.27)
            )
            store_info["open_hours"] = (
                st.number_input("Opening Hour (0-23)", min_value=0, max_value=23, value=9),
                st.number_input("Closing Hour (0-23)", min_value=0, max_value=23, value=21)
            )
            store_info["open_days"] = st.multiselect(
                "Open Days",
                list(calendar.day_name),
                default=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
            )

        if st.button("Sign Up"):
            if username and password:
                if role == "User":
                    if username in st.session_state.users:
                        st.error("Username already exists.")
                    else:
                        st.session_state.users[username] = password
                        st.success("User account created! Please login.")
                elif role == "Seller":
                    if username in st.session_state.sellers:
                        st.error("Username already exists.")
                    elif not (store_info.get("store_name") and store_info.get("address") and store_info.get("open_days")):
                        st.error("Please fill all required store details.")
                    else:
                        st.session_state.sellers[username] = {
                            "password": password,
                            **store_info
                        }
                        st.success("Seller account created! Please login.")
            else:
                st.error("Username and password are required.")

# ────────────────────────────────────────────────
# MAIN APPLICATION FLOW
# ────────────────────────────────────────────────
apply_theme()
init_data()

if not st.session_state.authenticated:
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
