import streamlit as st
import pandas as pd
import difflib
from geopy.distance import geodesic

# --- CONFIGURATION ---
st.set_page_config(page_title="LowKey Deals", layout="wide", page_icon="✨")

# --- 1. THEME: MODERN & ACCESSIBLE ---
def apply_theme():
    st.markdown("""
        <style>
        /* Global Text & Label Colors */
        html, body, [data-testid="stHeader"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span, .stRadio p {
            color: #000000 !important;
            font-weight: 500;
        }

        .stApp { background-color: #FFFFFF; }

        /* Enhanced Card Styling */
        .deal-card {
            background-color: #F8F9FA;
            padding: 20px;
            border-radius: 15px;
            border-top: 4px solid #8B4513;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        
        .price-tag {
            color: #8B4513;
            font-size: 1.4rem;
            font-weight: bold;
        }

        /* Status Badge */
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: bold;
            text-transform: uppercase;
            background-color: #FFE4B5;
            color: #8B4513;
        }

        input {
            color: #000000 !important;
            background-color: #F0F2F6 !important;
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
            transform: scale(1.02);
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
def init_data():
    # Force 'items' to be a dictionary if it's missing or corrupted
    if 'items' not in st.session_state or not isinstance(st.session_state.items, dict):
        st.session_state.items = {
            "Refrigerator": {"desc": "Double door, 250L", "price": 25000, "loc": (18.52, 73.85), "trend": "🔥 Hot Deal"},
            "Washing Machine": {"desc": "Front load, 7kg", "price": 18000, "loc": (18.53, 73.86), "trend": "📉 Price Drop"}
        }
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_location' not in st.session_state:
        st.session_state.user_location = (18.5204, 73.8567)


# --- 3. UI PAGES ---

def admin_page():
    st.title("📦 Inventory Manager")
    
    with st.expander("💡 CSV Format Instructions"):
        st.write("Your CSV should have these columns: `name`, `desc`, `price`, `lat`, `lon`")

    uploaded_file = st.file_uploader("Bulk Upload via CSV", type="csv")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            for _, row in df.iterrows():
                st.session_state.items[row['name']] = {
                    "desc": row['desc'], 
                    "price": row['price'],
                    "loc": (row['lat'], row['lon']),
                    "trend": "📦 Bulk Stock"
                }
            st.success(f"Imported {len(df)} items!")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    st.subheader("Add Single Item")
    with st.form("manual_add"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Product Name")
        price = c2.number_input("Price (₹)", min_value=0)
        desc = st.text_area("Description")
        
        st.write("Set Shop Location (Mock Coordinates)")
        lat = st.number_input("Latitude", value=18.52, format="%.4f")
        lon = st.number_input("Longitude", value=73.85, format="%.4f")
        
        if st.form_submit_button("Add to Catalog"):
            if name:
                st.session_state.items[name] = {
                    "desc": desc, 
                    "price": price, 
                    "loc": (lat, lon),
                    "trend": "🆕 Just Added"
                }
                st.toast(f"Success! {name} is now live.")

def home_page():
    # --- STEP 1: SAFETY CHECK ---
    # Re-build data if it vanished during a refresh
    if 'items' not in st.session_state or not isinstance(st.session_state.items, dict):
        init_data()

    # --- STEP 2: HERO & LOCATION ---
    col_title, col_loc = st.columns([3, 1])
    with col_title:
        st.title("✨ LowKey Deals")
        st.markdown("### *Highkey savings on local appliances.*")
    with col_loc:
        st.caption("📍 Current Location")
        st.code("Pune, MH (Mocked)")

    # --- STEP 3: SEARCH LOGIC ---
    search_input = st.text_input("🔍 Search for appliances...", placeholder="Type 'Fridge'...", key="main_search")
    
    if search_input:
        current_items = st.session_state.get('items', {})
        all_items = list(current_items.keys())
        suggestions = difflib.get_close_matches(search_input, all_items, n=3, cutoff=0.3)
        
        if suggestions:
            st.write("Did you mean:")
            cols = st.columns(len(suggestions))
            for i, sug in enumerate(suggestions):
                if cols[i].button(f"👉 {sug}", key=f"sug_{sug}"):
                    st.session_state.selected_item = sug
                    st.rerun()

    st.divider()
    
    # --- STEP 4: DISPLAY DETAILS OR GRID ---
    if 'selected_item' in st.session_state and st.session_state.selected_item in st.session_state.items:
        # DETAIL VIEW
        item_name = st.session_state.selected_item
        item = st.session_state.items[item_name]
        
        c1, c2 = st.columns(2)
        with c1:
            # Dynamic mock image based on item name
            img_url = f"https://loremflickr.com/400/300/appliance,{item_name.lower()}"
            st.image(img_url, use_container_width=True)
        with c2:
            st.header(item_name)
            st.write(item.get('desc', 'Quality appliance at a lowkey price.'))
            st.metric("Price", f"₹{item.get('price', 0):,}")
            
            # Distance logic using geopy
            if 'loc' in item:
                dist = geodesic(st.session_state.user_location, item['loc']).km
                st.write(f"📍 **{dist:.1f} km** from your location")

            if st.button("Reserve Deal"):
                st.balloons()
                st.success("Reserved! Check your messages for the shop address.")
            
            if st.button("⬅️ Back to Browse"):
                del st.session_state.selected_item
                st.rerun()
    else:
        # GRID VIEW
        items_dict = st.session_state.get('items', {})
        if not items_dict:
            st.warning("The catalog is empty. Sellers, head to 'Manage Inventory' to add deals!")
        else:
            cols = st.columns(3)
            for i, (name, info) in enumerate(items_dict.items()):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="deal-card">
                        <h4 style="margin:0;">{name}</h4>
                        <p style="font-size: 0.8rem; color: #555;">{info.get('desc', '')[:50]}...</p>
                        <p style="font-weight: bold; color: #8B4513;">₹{info.get('price', 0):,}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"View {name}", key=f"btn_{name}"):
                        st.session_state.selected_item = name
                        st.rerun()
    
    if 'selected_item' in st.session_state:
        item_name = st.session_state.selected_item
        item = st.session_state.items[item_name]
        
        # Calculate Distance
        dist = geodesic(st.session_state.user_location, item['loc']).km

        c1, c2 = st.columns([1, 1])
        with c1:
            st.image(f"https://loremflickr.com/400/300/appliance,{item_name.lower().replace(' ', '')}", use_container_width=True)
        with c2:
            st.markdown(f"<span class='badge'>{item['trend']}</span>", unsafe_allow_html=True)
            st.header(item_name)
            st.write(item['desc'])
            st.metric("Best Price", f"₹{item['price']:,}")
            st.write(f"📍 Location: **{dist:.1f} km away**")
            
            if st.button("Reserve This Deal"):
                with st.status("Verifying stock with seller..."):
                    st.write("Checking availability...")
                    st.write("Generating coupon code...")
                st.balloons()
                st.success(f"Success! Show code **LOWKEY-{item_name[:3].upper()}** at the shop.")
            
            if st.button("⬅️ Back to Browse"):
                del st.session_state.selected_item
                st.rerun()
    else:
        # Product Grid
        items = st.session_state.items
        cols = st.columns(3)
        for i, (name, info) in enumerate(items.items()):
            # Calculate distance for each card
            dist = geodesic(st.session_state.user_location, info['loc']).km
            
            with cols[i % 3]:
                st.markdown(f"""
                <div class="deal-card">
                    <span class="badge">{info['trend']}</span>
                    <h4 style="margin-top:10px;">{name}</h4>
                    <p style="font-size: 0.85rem; color: #555;">{info['desc']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="price-tag">₹{info['price']:,}</span>
                        <span style="font-size: 0.8rem; color: #888;">📍 {dist:.1f}km</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"View Details", key=f"btn_{name}"):
                    st.session_state.selected_item = name
                    st.rerun()
def login_page():
    st.title("Welcome to LowKey Deals")
    
    # Selection for User or Seller roles
    role = st.radio("Select Role", ["User", "Seller"], key="role_selection")
    
    # Input fields for login
    user = st.text_input("Username", placeholder="Enter your name...")
    
    if st.button("Login"):
        if user:
            # Set session state variables to maintain the login session
            st.session_state.authenticated = True
            st.session_state.username = user
            st.session_state.role = role
            st.rerun() # Refresh the app to show the logged-in view
        else:
            st.error("Please enter a username to continue.")             

# --- 4. EXECUTION FLOW ---
apply_theme()
init_data()

if not st.session_state.authenticated:
    login_page()
else:
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}")
        if st.session_state.role == "Seller":
            nav = st.radio("Dashboard", ["View Store", "Manage Inventory"])
        else:
            nav = "View Store"
            
        st.divider()
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
            
    if nav == "Manage Inventory":
        admin_page()
    else:
        home_page()
