import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ---------------- Database Setup -------------------
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS diesel_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    date TEXT,
    toll_plaza TEXT,
    dg_name TEXT,
    diesel_top_up REAL,
    diesel_purchase REAL,
    dg_closing_stock REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    net_kwh REAL,
    opening_rh REAL,
    closing_rh REAL,
    net_rh TEXT,
    diesel_consumption REAL,
    plaza_barrel_stock REAL
)
""")
conn.commit()

# ---------------- Helper Functions -------------------
def get_latest_plaza_stock(toll_plaza):
    cursor.execute("""
        SELECT plaza_barrel_stock FROM diesel_monitoring
        WHERE toll_plaza = ?
        ORDER BY id DESC LIMIT 1
    """, (toll_plaza,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_latest_dg_stock(toll_plaza, dg_name):
    cursor.execute("""
        SELECT dg_closing_stock FROM diesel_monitoring
        WHERE toll_plaza = ? AND dg_name = ?
        ORDER BY id DESC LIMIT 1
    """, (toll_plaza, dg_name))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_latest_kwh(toll_plaza, dg_name):
    cursor.execute("""
        SELECT closing_kwh FROM diesel_monitoring
        WHERE toll_plaza = ? AND dg_name = ?
        ORDER BY id DESC LIMIT 1
    """, (toll_plaza, dg_name))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_latest_rh(toll_plaza, dg_name):
    cursor.execute("""
        SELECT closing_rh FROM diesel_monitoring
        WHERE toll_plaza = ? AND dg_name = ?
        ORDER BY id DESC LIMIT 1
    """, (toll_plaza, dg_name))
    result = cursor.fetchone()
    return result[0] if result else 0

# -------------------- Streamlit UI --------------------

st.title("⛽ Diesel Monitoring App - Toll Plaza Operations")

st.markdown("### 🚩 Diesel Monitoring Entry")

date = st.date_input("Date", datetime.now()).strftime("%Y-%m-%d")
toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
dg_name = st.selectbox("Select DG", ["DG1", "DG2"])

# Fetch virtual auto values
plaza_barrel_stock = get_latest_plaza_stock(toll_plaza)
dg_opening_stock = get_latest_dg_stock(toll_plaza, dg_name)
opening_kwh = get_latest_kwh(toll_plaza, dg_name)
opening_rh = get_latest_rh(toll_plaza, dg_name)

st.info(f"🔹 Current Plaza Barrel Stock: **{plaza_barrel_stock} L**")
st.info(f"🔹 DG Opening Diesel Stock: **{dg_opening_stock} L**")
st.info(f"🔹 Opening KWH: **{opening_kwh}**")
st.info(f"🔹 Opening RH: **{opening_rh}**")

diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0.0, step=0.1)
diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=0.1)
dg_closing_stock = st.number_input("DG Closing Diesel Stock (L)", min_value=0.0, step=0.1)

closing_kwh = st.number_input("Closing KWH", min_value=0.0, step=0.1)
closing_rh = st.number_input("Closing RH", min_value=0.0, step=0.1)

# Calculations:
net_kwh = closing_kwh - opening_kwh
rh_diff = closing_rh - opening_rh
net_rh_td = timedelta(hours=rh_diff)
net_rh_str = f"{int(net_rh_td.total_seconds() // 3600):02}:{int((net_rh_td.total_seconds() % 3600) // 60):02}"

diesel_consumption = (dg_opening_stock + diesel_top_up) - dg_closing_stock
new_plaza_barrel_stock = plaza_barrel_stock - diesel_top_up + diesel_purchase

st.success(f"✅ Net KWH: **{net_kwh}**")
st.success(f"✅ Net Running Hours: **{net_rh_str} (HH:MM)**")
st.success(f"✅ Diesel Consumption: **{diesel_consumption} L**")
st.success(f"✅ New Plaza Barrel Stock: **{new_plaza_barrel_stock} L**")

if st.button("Submit Entry"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO diesel_monitoring (
            timestamp, date, toll_plaza, dg_name, diesel_top_up, diesel_purchase,
            dg_closing_stock, opening_kwh, closing_kwh, net_kwh,
            opening_rh, closing_rh, net_rh, diesel_consumption, plaza_barrel_stock
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, date, toll_plaza, dg_name, diesel_top_up, diesel_purchase,
        dg_closing_stock, opening_kwh, closing_kwh, net_kwh,
        opening_rh, closing_rh, net_rh_str, diesel_consumption, new_plaza_barrel_stock
    ))
    conn.commit()
    st.success("✅ Data saved successfully!")

st.markdown("---")
st.markdown("### 🕒 Last 5 Entries")

df = pd.read_sql_query("""
    SELECT timestamp, date, toll_plaza, dg_name, diesel_top_up, diesel_purchase,
           dg_closing_stock, opening_kwh, closing_kwh, net_kwh,
           opening_rh, closing_rh, net_rh, diesel_consumption, plaza_barrel_stock
    FROM diesel_monitoring
    WHERE toll_plaza = ? AND dg_name = ?
    ORDER BY id DESC LIMIT 5
""", conn, params=(toll_plaza, dg_name))

st.dataframe(df)
