import streamlit as st
import sqlite3
from datetime import datetime, timedelta
 
# Initialize DB
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS diesel_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    toll_plaza TEXT,
    dg_name TEXT,
    barrel_stock REAL,
    dg_opening_stock REAL,
    diesel_top_up REAL,
    diesel_closing_stock REAL,
    diesel_purchase REAL,
    diesel_consumption REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    net_kwh REAL,
    opening_rh REAL,
    closing_rh REAL,
    net_rh TEXT
)''')
conn.commit()
 
st.title("🚩 Diesel Monitoring App - Toll Operations")
 
# Admin Block
st.markdown("---")
st.header("🛠️ Admin Block (Initialization)")
with st.expander("Click here to initialize or update base data"):
    today = datetime.today().strftime("%Y-%m-%d")
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"])
    barrel_stock = st.number_input("Set Plaza Barrel Stock (L)", min_value=0.0, format="%.2f")
    dg_opening_stock = st.number_input("Set DG Opening Diesel Stock (L)", min_value=0.0, format="%.2f")
    opening_kwh = st.number_input("Set DG Opening KWH", min_value=0.0, format="%.2f")
    opening_rh = st.number_input("Set DG Opening Running Hours", min_value=0.0, format="%.2f")
 
    if st.button("💾 Save Admin Data"):
        c.execute('''INSERT INTO diesel_monitoring (
            date, toll_plaza, dg_name, barrel_stock, dg_opening_stock, opening_kwh, opening_rh,
            diesel_top_up, diesel_closing_stock, diesel_purchase, diesel_consumption,
            closing_kwh, net_kwh, closing_rh, net_rh
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (today, toll_plaza, dg_name, barrel_stock, dg_opening_stock, opening_kwh, opening_rh,
         0, 0, 0, 0, 0, 0, 0, "0:00"))
        conn.commit()
        st.success("✅ Admin initialization data saved successfully.")
 
# User Block
st.markdown("---")
st.header("📝 User Entry Block")
 
toll_plaza_user = st.selectbox("Select Toll Plaza (User)", ["TP01", "TP02", "TP03"])
dg_name_user = st.selectbox("Select DG (User)", ["DG1", "DG2"])
 
# Fetch last entry for this toll plaza & DG
c.execute('''SELECT * FROM diesel_monitoring WHERE toll_plaza=? AND dg_name=? ORDER BY id DESC LIMIT 1''',
          (toll_plaza_user, dg_name_user))
last_entry = c.fetchone()
 
if last_entry:
    last_barrel_stock = last_entry[4]
    last_dg_opening_stock = last_entry[5]
    last_opening_kwh = last_entry[8]
    last_opening_rh = last_entry[11]
else:
    last_barrel_stock = 0
    last_dg_opening_stock = 0
    last_opening_kwh = 0
    last_opening_rh = 0
 
st.info(f"🔹 Last Barrel Stock: **{last_barrel_stock} L**")
st.info(f"🔹 Last DG Opening Diesel Stock: **{last_dg_opening_stock} L**")
st.info(f"🔹 Last Opening KWH: **{last_opening_kwh}**")
st.info(f"🔹 Last Opening RH: **{last_opening_rh} hrs**")
 
diesel_top_up = st.number_input("Enter Diesel Top Up (L)", min_value=0.0, format="%.2f")
diesel_purchase = st.number_input("Enter Diesel Purchase (L)", min_value=0.0, format="%.2f")
diesel_closing_stock = st.number_input("Enter Diesel Closing Stock at DG (L)", min_value=0.0, format="%.2f")
 
closing_kwh = st.number_input("Enter Closing KWH", min_value=last_opening_kwh, format="%.2f")
closing_rh = st.number_input("Enter Closing Running Hours", min_value=last_opening_rh, format="%.2f")
 
# Calculations
diesel_consumption = (last_dg_opening_stock + diesel_top_up) - diesel_closing_stock
net_kwh = closing_kwh - last_opening_kwh
net_rh_float = closing_rh - last_opening_rh
net_rh_timedelta = timedelta(hours=net_rh_float)
net_rh_str = str(net_rh_timedelta)
 
new_barrel_stock = last_barrel_stock - diesel_top_up + diesel_purchase
 
st.success(f"✅ Diesel Consumption (L): {diesel_consumption:.2f}")
st.success(f"✅ Net KWH: {net_kwh:.2f}")
st.success(f"✅ Net Running Hours: {net_rh_str}")
st.success(f"✅ Updated Plaza Barrel Stock: {new_barrel_stock:.2f} L")
 
if st.button("🚀 Submit Entry"):
    c.execute('''INSERT INTO diesel_monitoring (
        date, toll_plaza, dg_name, barrel_stock, dg_opening_stock, opening_kwh, opening_rh,
        diesel_top_up, diesel_closing_stock, diesel_purchase, diesel_consumption,
        closing_kwh, net_kwh, closing_rh, net_rh
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (datetime.today().strftime("%Y-%m-%d"), toll_plaza_user, dg_name_user, new_barrel_stock,
     diesel_closing_stock, last_opening_kwh, last_opening_rh,
     diesel_top_up, diesel_closing_stock, diesel_purchase, diesel_consumption,
     closing_kwh, net_kwh, closing_rh, net_rh_str))
    conn.commit()
    st.success("✅ Data saved successfully!")
 
# Last 5 records display
st.markdown("---")
st.subheader("📊 Last 5 Entries for this Toll Plaza & DG")
c.execute('''SELECT date, diesel_consumption, net_kwh, net_rh FROM diesel_monitoring
             WHERE toll_plaza=? AND dg_name=? ORDER BY id DESC LIMIT 5''',
             (toll_plaza_user, dg_name_user))
rows = c.fetchall()
 
if rows:
    for row in rows:
        st.info(f"📅 Date: {row[0]} | ⛽ Diesel Consumption: {row[1]:.2f} L | ⚡ Net KWH: {row[2]:.2f} | 🕒 Net RH: {row[3]}")
else:
    st.warning("No data available yet for this Toll Plaza and DG.")
COBI
 
