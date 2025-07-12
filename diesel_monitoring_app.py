import streamlit as st
import sqlite3
from datetime import datetime, timedelta
 
# Initialize SQLite DB
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
st.header("🛠️ Admin Block (Initialization without password)")
with st.expander("Initialize or Update Base Data"):
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
        st.success("✅ Admin data saved. It will reflect in the user entry block now.")
 
# User Block
st.markdown("---")
st.header("📝 User Entry Block")
 
toll_plaza_user = st.selectbox("Select Toll Plaza for Entry", ["TP01", "TP02", "TP03"])
dg_name_user = st.selectbox("Select DG for Entry", ["DG1", "DG2"])
 
# Fetch last relevant entry for initialization
c.execute('''SELECT * FROM diesel_monitoring WHERE toll_plaza=? AND dg_name=? ORDER BY id DESC LIMIT 1''',
          (toll_plaza_user, dg_name_user))
last_entry = c.fetchone()
 
if last_entry:
    last_barrel_stock = last_entry[4]
    last_dg_opening_stock = last_entry[5]
    last_opening_kwh = last_entry[10]
    last_opening_rh = last_entry[13]
else:
    last_barrel_stock = 0
    last_dg_opening_stock = 0
    last_opening_kwh = 0
    last_opening_rh = 0
 
st.success(f"🔹 Last Barrel Stock: **{last_barrel_stock} L**")
st.success(f"🔹 Last DG Opening Diesel Stock: **{last_dg_opening_stock} L**")
st.success(f"🔹 Last Opening KWH: **{last_opening_kwh}**")
st.success(f"🔹 Last Opening RH: **{last_opening_rh} hrs**")
 
diesel_top_up = st.number_input("Enter Diesel Top Up (L)", min_value=0.0, format="%.2f")
diesel_purchase = st.number_input("Enter Diesel Purchase (L)", min_value=0.0, format="%.2f")
diesel_closing_stock = st.number_input("Enter Diesel Closing Stock at DG (L)", min_value=0.0, format="%.2f")
 
st.markdown("### ⚡ KWH Readings")
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Opening KWH:** {last_opening_kwh}")
with col2:
    closing_kwh = st.number_input("Closing KWH", min_value=last_opening_kwh, format="%.2f")
with col3:
    net_kwh = closing_kwh - last_opening_kwh
    st.info(f"**Net KWH:** {net_kwh:.2f}")
 
st.markdown("### 🕒 Running Hours")
col4, col5, col6 = st.columns(3)
with col4:
    st.info(f"**Opening RH:** {last_opening_rh}")
with col5:
    closing_rh = st.number_input("Closing RH", min_value=last_opening_rh, format="%.2f")
with col6:
    net_rh_hours = closing_rh - last_opening_rh
    net_rh_timedelta = timedelta(hours=net_rh_hours)
    net_rh_str = str(net_rh_timedelta)
    st.info(f"**Net RH:** {net_rh_str}")
 
# Diesel consumption calculation
diesel_consumption = (last_dg_opening_stock + diesel_top_up) - diesel_closing_stock
new_barrel_stock = last_barrel_stock - diesel_top_up + diesel_purchase
 
st.success(f"✅ Diesel Consumption (L): {diesel_consumption:.2f}")
st.success(f"✅ Updated Plaza Barrel Stock (L): {new_barrel_stock:.2f}")
 
if st.button("🚀 Submit Entry"):
    c.execute('''INSERT INTO diesel_monitoring (
        date, toll_plaza, dg_name, barrel_stock, dg_opening_stock, diesel_top_up,
        diesel_closing_stock, diesel_purchase, diesel_consumption,
        opening_kwh, closing_kwh, net_kwh, opening_rh, closing_rh, net_rh
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (datetime.today().strftime("%Y-%m-%d"), toll_plaza_user, dg_name_user, new_barrel_stock,
     diesel_closing_stock, diesel_top_up, diesel_closing_stock, diesel_purchase,
     diesel_consumption, last_opening_kwh, closing_kwh, net_kwh, last_opening_rh,
     closing_rh, net_rh_str))
    conn.commit()
    st.success("✅ Entry submitted successfully.")
 
# Display last 5 entries
st.markdown("---")
st.subheader("📊 Last 5 Entries for This DG and Toll Plaza")
c.execute('''SELECT date, diesel_consumption, net_kwh, net_rh FROM diesel_monitoring
             WHERE toll_plaza=? AND dg_name=?
             ORDER BY id DESC LIMIT 5''',
          (toll_plaza_user, dg_name_user))
rows = c.fetchall()
 
if rows:
    for row in rows:
        st.info(f"📅 {row[0]} | ⛽ Diesel: {row[1]:.2f} L | ⚡ KWH: {row[2]:.2f} | 🕒 RH: {row[3]}")
else:
    st.warning("No records yet for this selection.")

 
