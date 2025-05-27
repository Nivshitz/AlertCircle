import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
EC2_EXTERNAL_IP = os.getenv("EC2_EXTERNAL_IP")

# MongoDB setup
MONGO_URI = f"mongodb://{EC2_EXTERNAL_IP}:27017"
DB_NAME = "AlertCircleProject"
COLLECTION_NAME = "alerts_live"

client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

# === Streamlit Page Config ===
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center;'>📡 AlertCircle - Real-Time Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# === Refresh Tracking ===
if "last_refresh_time" not in st.session_state:
    st.session_state["last_refresh_time"] = datetime.now()

# === Left-Aligned Refresh Button and Time ===
btn_col1, btn_col2 = st.columns([1, 5])
with btn_col1:
    if st.button("🔄 Refresh"):
        st.session_state["last_refresh_time"] = datetime.now()
        st.experimental_rerun()
with btn_col2:
    last_refresh_str = st.session_state["last_refresh_time"].strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"<div style='color: gray; padding-top: 0.6rem;'>Last refreshed: {last_refresh_str}</div>", unsafe_allow_html=True)

# === Fetch Alerts ===
alerts = list(collection.find().sort("ingestion_time", -1))

# === Split Layout: Map | Feed ===
col_map, col_feed = st.columns([2, 1], gap="large")

# === MAP COLUMN ===
with col_map:
    m = folium.Map(location=[32.0853, 34.7818], zoom_start=13, width='100%', height='100%')

    for alert in alerts:
        lat = alert.get("latitude")
        lon = alert.get("longitude")
        desc = alert.get("description", "No description provided.")
        user_list = alert.get("notified_users", [])
        user_str = ", ".join(user_list) if user_list else "No users"

        if lat and lon:
            folium.Marker(
                location=[lat, lon],
                tooltip="🐕 Bylaw Dog Inspector Alert 🚨",
                popup=folium.Popup(
                    html=f"<b>{desc}</b><br>👥 Notified: {user_str}",
                    max_width=300
                ),
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)

    st_folium(m, width=900, height=500)

# === NOTIFICATION FEED COLUMN ===
with col_feed:
    st.markdown("<h3 style='text-align: center;'>🔔 Notification Feed</h3>", unsafe_allow_html=True)

    # Darker background + larger text
    st.markdown("""
        <style>
        .alert-box {
            background-color: #222;
            color: #f5f5f5;
            border-left: 5px solid #ff4b4b;
            padding: 15px 20px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 17px;
        }
        </style>
    """, unsafe_allow_html=True)

    if not alerts:
        st.info("No alerts in the last 10 minutes.")
    else:
        st.markdown("<div style='max-height: 500px; overflow-y: auto; padding-right: 10px;'>", unsafe_allow_html=True)

        for alert in alerts:
            event_time = alert.get("event_time", "")
            if isinstance(event_time, datetime):
                event_time = event_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                event_time = str(event_time)[:19].replace("T", " ")

            desc = alert.get("description", "No description")
            user_list = alert.get("notified_users", [])
            user_str = ", ".join(user_list) if user_list else "No users"

            st.markdown(
                f"<div class='alert-box'><strong>{event_time}</strong><br>"
                f"<code>{desc}</code><br>👥 Notified: <strong>{user_str}</strong></div>",
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)
