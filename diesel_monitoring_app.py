import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
 
# ----------------- Database Initialization -----------------
conn = sqlite3.connect('dg_reading.db', check_same_thread=False)
c = conn.cursor()
 
# Create necessary tables
c.execute('''
CREATE TABLE IF NOT EXISTS dg_reading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    date TEXT,
    toll_plaza TEXT,
    dg_name TEXT,
    opening_diesel_stock REAL,
    diesel_top_up REAL,
    diesel_closing_stock REAL,
    diesel_consumption REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    running_hours_opening REAL,
    running_hours_closing REAL,
    net_running_hours REAL,
    diesel_purchase REAL,
    max_demand REAL,
    remarks TEXT
)
''')
 
c.execute('''
CREATE TABLE IF NOT EXISTS initialization (
    toll_plaza TEXT,
    dg_name TEXT,
    barrel_stock REAL,
    opening_diesel_stock REAL,
    PRIMARY KEY (toll_plaza, dg_name)
)
''')
conn.commit()
 
# ----------------- App Styling -----------------
st.set_page_config(page_title="DG Monitoring", page_icon="⛽", layout="centered")
 
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {background-color: #2E8B57; color: white; font-weight: bold; border-radius: 8px;}
    .stTextInput>div>div>input {border-radius: 5px;}
    .stNumberInput>div>div>input {border-radius: 5px;}
    .css-1aumxhk {background-color: #f0f2f6;}
    </style>
""", unsafe_allow_html=True)
 
# ----------------- Title -----------------
st.title("⛽ DG Monitoring - Toll Operations")
 
# ----------------- Admin Block -----------------
with st.expander("🛠️ Admin Initialization", expanded=False):
    st.info("Initialize Barrel Stock and DG Opening Diesel Stock")
 
    toll_plaza_init = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="toll_plaza_admin")
    dg_name_init = st.selectbox("Select DG", ["DG1", "DG2"], key="dg_name_admin")
    barrel_stock = st.number_input("Enter Barrel Stock (L)", min_value=0.0, step=0.1, key="barrel_stock")
    opening_diesel_stock = st.number_input("Enter DG Opening Diesel Stock (L)", min_value=0.0, step=0.1, key="dg_opening_stock")
 
    if st.button("💾 Save Initialization"):
        c.execute('''
            INSERT OR REPLACE INTO initialization (toll_plaza, dg_name, barrel_stock, opening_diesel_stock)
            VALUES (?, ?, ?, ?)
        ''', (toll_plaza_init, dg_name_init, barrel_stock, opening_diesel_stock))
        conn.commit()
        st.success("✅ Initialization data saved successfully!")
 
# ----------------- User Block -----------------
st.header("📲 DG Reading Entry (Field Staff)")
 
toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="toll_plaza_user")
dg_name = st.selectbox("Select DG", ["DG1", "DG2"], key="dg_name_user")
 
# Fetch initialization data
c.execute('''
SELECT barrel_stock, opening_diesel_stock FROM initialization
WHERE toll_plaza = ? AND dg_name = ?
''', (toll_plaza, dg_name))
init_vals = c.fetchone()
barrel_stock_init, opening_diesel_stock_init = init_vals if init_vals else (0.0, 0.0)
 
# Fetch last entry
c.execute('''
SELECT diesel_closing_stock, closing_kwh, running_hours_closing
FROM dg_reading
WHERE toll_plaza = ? AND dg_name = ?
ORDER BY id DESC LIMIT 1
''', (toll_plaza, dg_name))
last = c.fetchone()
last_diesel_closing_stock = last[0] if last else opening_diesel_stock_init
last_closing_kwh = last[1] if last else 0.0
last_running_hours_closing = last[2] if last else 0.0
 
# Virtual Calculations
virtual_opening_diesel_stock = last_diesel_closing_stock + 0  # Updated after diesel purchase in entry
st.info(f"**🔹 Current Barrel Stock:** {barrel_stock_init} L")
st.info(f"**🔹 Last DG Opening Diesel Stock:** {last_diesel_closing_stock} L")
st.info(f"**🔹 Last Closing KWH:** {last_closing_kwh}")
st.info(f"**🔹 Last Closing RH:** {last_running_hours_closing}")
 
# Entry Fields
date = st.date_input("📅 Date", datetime.today())
diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0.0, step=0.1)
diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=0.1)
diesel_closing_stock = st.number_input("Diesel Closing Stock at DG (L)", min_value=0.0, step=0.1)
 
closing_kwh = st.number_input("Closing KWH", min_value=last_closing_kwh, step=0.1)
running_hours_closing = st.number_input("Closing RH", min_value=last_running_hours_closing, step=0.1)
max_demand = st.number_input("Maximum Demand", min_value=0.0, step=0.1)
remarks = st.text_input("Remarks")
 
# Auto Calculations
opening_diesel_stock = last_diesel_closing_stock + diesel_purchase
diesel_consumption = opening_diesel_stock + diesel_top_up - diesel_closing_stock
net_running_hours = running_hours_closing - last_running_hours_closing
 
st.success(f"**🛢️ Virtual Opening Diesel Stock:** {opening_diesel_stock} L")
st.success(f"**⛽ Diesel Consumption:** {diesel_consumption} L")
st.success(f"**⏱️ Net Running Hours:** {net_running_hours} hr")
 
# Submit
if st.button("✅ Submit DG Reading"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO dg_reading (
            timestamp, date, toll_plaza, dg_name,
            opening_diesel_stock, diesel_top_up, diesel_closing_stock, diesel_consumption,
            opening_kwh, closing_kwh,
            running_hours_opening, running_hours_closing, net_running_hours,
            diesel_purchase, max_demand, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp, str(date), toll_plaza, dg_name,
        opening_diesel_stock, diesel_top_up, diesel_closing_stock, diesel_consumption,
        last_closing_kwh, closing_kwh,
        last_running_hours_closing, running_hours_closing, net_running_hours,
        diesel_purchase, max_demand, remarks
    ))
    conn.commit()
    st.success("✅ Data submitted successfully! Page will refresh for the next entry.")
    st.rerun()
 
# ----------------- Last 5 Entries -----------------
st.header("📄 Last 5 DG Reading Entries")
 
query = '''
SELECT timestamp, date, toll_plaza, dg_name,
opening_diesel_stock, diesel_top_up, diesel_closing_stock, diesel_consumption,
opening_kwh, closing_kwh,
running_hours_opening, running_hours_closing, net_running_hours,
diesel_purchase, max_demand, remarks
FROM dg_reading
WHERE toll_plaza = ? AND dg_name = ?
ORDER BY id DESC LIMIT 5
'''
df = pd.read_sql_query(query, conn, params=(toll_plaza, dg_name))
st.dataframe(df, use_container_width=True)
 
