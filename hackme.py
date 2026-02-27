import streamlit as st
import pandas as pd
import difflib
from geopy.distance import geodesic
from datetime import datetime
import streamlit.components.v1 as components
import calendar
import json
import os

# Data file for persistence across sessions
DATA_FILE = "app_data.json"

def load_persistent_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            for key in ['item_offers', 'users', 'sellers']:
                if key in data:
                    st.session_state[key] = data[key]
        except Exception as e:
            st.error(f"Error loading data: {e}")

def save_persistent_data():
    data = {
        'item_offers': st.session_state.get('item_offers', {}),
        'users': st.session_state.get('users', {}),
        'sellers': st.session_state.get('sellers', {})
    }
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {e}")

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
        .deal-card
