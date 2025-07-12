import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
 
# Initialize SQLite database
conn = sqlite3.connect('dg_reading.db', check_same_thread=False)
c = conn.cursor()
 
# Create table if not exists
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
conn.commit()
 
st.title("🚩 DG Reading Entry - Toll Operations")
 
# ----------------- ADMIN INITIALIZATION -----------------
with st.expander("🔒 Admin Initialization"):
    admin_password = st.text_input("Enter Admin Password:", type="password")
    if st.button("Initialize / Reset Database"):
        if admin_password == "admin@toll":  # Set your admin password here
            c.execute("DELETE FROM dg_reading")
            conn.commit()
            st.success("✅ Initialization completed. All records cleared.")
        else:
            st.error("❌ Incorrect admin password. Access denied.")
 
# ----------------- FIELD STAFF ENTRY -----------------
st.subheader("🛠️ DG Reading Entry")
 
toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
dg_name = st.selectbox("Select DG", ["DG1", "DG2"])
 
# Fetch last entry for virtual columns
c.execute('''
SELECT diesel_closing_stock, closing_kwh, running_hours_closing
FROM dg_reading
WHERE toll_plaza = ? AND dg_name = ?
ORDER BY id DESC LIMIT 1
''', (toll_plaza, dg_name))
last = c.fetchone()
 
if last:
    last_diesel_closing_stock = last[0]
    last_closing_kwh = last[1]
    last_running_hours_closing = last[2]
else:
    last_diesel_closing_stock = 0.0
    last_closing_kwh = 0.0
    last_running_hours_closing = 0.0
 
st.info(f"🔹 Previous DG Closing Diesel Stock (L): {last_diesel_closing_stock}")
st.info(f"🔹 Previous Closing KWH: {last_closing_kwh}")
st.info(f"🔹 Previous Closing RH: {last_running_hours_closing}")
 
date = st.date_input("Date", datetime.today())
diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0.0, step=0.1)
diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=0.1)
diesel_closing_stock = st.number_input("Diesel Closing Stock at DG (L)", min_value=0.0, step=0.1)
 
opening_kwh = last_closing_kwh
closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh, step=0.1)
 
running_hours_opening = last_running_hours_closing
running_hours_closing = st.number_input("Closing RH", min_value=running_hours_opening, step=0.1)
 
max_demand = st.number_input("Maximum Demand", min_value=0.0, step=0.1)
remarks = st.text_input("Remarks")
 
# Virtual Calculations
opening_diesel_stock = last_diesel_closing_stock + diesel_purchase
diesel_consumption = opening_diesel_stock + diesel_top_up - diesel_closing_stock
net_running_hours = running_hours_closing - running_hours_opening
 
st.success(f"🔹 Virtual Opening Diesel Stock (L): {opening_diesel_stock}")
st.success(f"🔹 Diesel Consumption (L): {diesel_consumption}")
st.success(f"🔹 Net Running Hours: {net_running_hours} hrs")
 
# ----------------- SUBMIT -----------------
if st.button("Submit Entry"):
    if diesel_closing_stock > (opening_diesel_stock + diesel_top_up):
        st.error("❌ Diesel Closing Stock cannot exceed Opening Stock + Top Up.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            INSERT INTO dg_reading (
                timestamp, date, toll_plaza, dg_name,
                opening_diesel_stock, diesel_top_up, diesel_closing_stock, diesel_consumption,
                opening_kwh, closing_kwh,
                running_hours_opening, running_hours_closing, net_running_hours,
                diesel_purchase, max_demand, remarks
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, date, toll_plaza, dg_name,
            opening_diesel_stock, diesel_top_up, diesel_closing_stock, diesel_consumption,
            opening_kwh, closing_kwh,
            running_hours_opening, running_hours_closing, net_running_hours,
            diesel_purchase, max_demand, remarks
        ))
        conn.commit()
        st.success("✅ Data entered and saved successfully!")
        st.experimental_rerun()
 
# ----------------- LAST ENTRIES VIEW -----------------
st.subheader("📄 Last 5 DG Reading Entries")
df = pd.read_sql_query("SELECT * FROM dg_reading ORDER BY id DESC LIMIT 5", conn)
st.dataframe(df)
