import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
 
# Database Connection
conn = sqlite3.connect('dg_reading.db', check_same_thread=False)
c = conn.cursor()
 
# Table Creation
c.execute('''
CREATE TABLE IF NOT EXISTS plaza_barrel_stock (
    toll_plaza TEXT PRIMARY KEY,
    barrel_stock REAL
)
''')
 
c.execute('''
CREATE TABLE IF NOT EXISTS dg_stock (
    toll_plaza TEXT,
    dg_name TEXT,
    dg_opening_stock REAL,
    PRIMARY KEY (toll_plaza, dg_name)
)
''')
 
c.execute('''
CREATE TABLE IF NOT EXISTS dg_reading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    date TEXT,
    toll_plaza TEXT,
    dg_name TEXT,
    opening_kwh REAL,
    closing_kwh REAL,
    opening_rh REAL,
    closing_rh REAL,
    diesel_topup REAL,
    diesel_purchase REAL,
    diesel_closing_stock REAL,
    max_demand REAL,
    remarks TEXT
)
''')
 
conn.commit()
 
# UI
st.title("🚩 Toll Operations - DG Reading Module")
 
# Admin Initialization
st.header("🛠️ Admin: Initialize Stocks")
with st.expander("Admin Panel"):
    toll_plaza_admin = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="admin_plaza")
    barrel_stock_admin = st.number_input("Plaza Barrel Stock (L)", min_value=0.0, step=0.1, key="admin_barrel")
    dg_name_admin = st.selectbox("Select DG", ["DG1", "DG2"], key="admin_dg")
    dg_opening_stock_admin = st.number_input("DG Opening Diesel Stock (L)", min_value=0.0, step=0.1, key="admin_dg_stock")
    
    if st.button("💾 Save Stocks (Admin)"):
        c.execute("INSERT OR REPLACE INTO plaza_barrel_stock (toll_plaza, barrel_stock) VALUES (?, ?)", 
                  (toll_plaza_admin, barrel_stock_admin))
        c.execute("INSERT OR REPLACE INTO dg_stock (toll_plaza, dg_name, dg_opening_stock) VALUES (?, ?, ?)",
                  (toll_plaza_admin, dg_name_admin, dg_opening_stock_admin))
        conn.commit()
        st.success("✅ Stocks initialized/updated successfully.")
 
# DG Reading Entry for Field Staff
st.header("📝 DG Reading Entry")
 
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
date = st.date_input("Date", datetime.now().date())
toll_plaza = st.selectbox("Toll Plaza", ["TP01", "TP02", "TP03"])
dg_name = st.selectbox("DG Name", ["DG1", "DG2"])
 
# Fetch Previous Stock
c.execute("SELECT barrel_stock FROM plaza_barrel_stock WHERE toll_plaza = ?", (toll_plaza,))
prev_barrel_row = c.fetchone()
prev_barrel_stock = prev_barrel_row[0] if prev_barrel_row else 0.0
st.info(f"💡 Previous Plaza Barrel Stock: {prev_barrel_stock} L")
 
c.execute("SELECT dg_opening_stock FROM dg_stock WHERE toll_plaza = ? AND dg_name = ?", (toll_plaza, dg_name))
prev_dg_row = c.fetchone()
prev_dg_stock = prev_dg_row[0] if prev_dg_row else 0.0
st.info(f"💡 DG Opening Diesel Stock: {prev_dg_stock} L")
 
# Inputs
opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=0.1)
closing_kwh = st.number_input("Closing KWH (>= Opening)", min_value=opening_kwh, step=0.1)
 
opening_rh = st.number_input("Opening RH", min_value=0.0, step=0.1)
closing_rh = st.number_input("Closing RH (>= Opening)", min_value=opening_rh, step=0.1)
 
diesel_topup = st.number_input("Diesel Top-up to DG (L)", min_value=0.0, step=0.1)
diesel_purchase = st.number_input("Diesel Purchased for Plaza (L)", min_value=0.0, step=0.1)
 
new_barrel_stock = prev_barrel_stock - diesel_topup + diesel_purchase
st.info(f"💡 Updated Plaza Barrel Stock after entry: {new_barrel_stock} L")
 
diesel_closing_stock = st.number_input("Diesel Closing Stock at DG (L)", min_value=0.0, step=0.1)
max_demand = st.number_input("Maximum Demand", min_value=0.0, step=0.1)
remarks = st.text_area("Remarks (Optional)")
 
if st.button("✅ Submit DG Reading"):
    c.execute('''
    INSERT INTO dg_reading (
        timestamp, date, toll_plaza, dg_name, opening_kwh, closing_kwh,
        opening_rh, closing_rh, diesel_topup, diesel_purchase,
        diesel_closing_stock, max_demand, remarks
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp, date.strftime("%Y-%m-%d"), toll_plaza, dg_name, opening_kwh, closing_kwh,
        opening_rh, closing_rh, diesel_topup, diesel_purchase,
        diesel_closing_stock, max_demand, remarks
    ))
 
    # Update Stocks
    c.execute("INSERT OR REPLACE INTO plaza_barrel_stock (toll_plaza, barrel_stock) VALUES (?, ?)",
              (toll_plaza, new_barrel_stock))
    new_dg_stock = prev_dg_stock + diesel_topup - diesel_closing_stock
    c.execute("INSERT OR REPLACE INTO dg_stock (toll_plaza, dg_name, dg_opening_stock) VALUES (?, ?, ?)",
              (toll_plaza, dg_name, new_dg_stock))
    
    conn.commit()
    st.success("✅ Data entered and saved successfully.")
 
# Data View
with st.expander("🔍 View DG Readings (Admin)"):
    df = pd.read_sql_query("SELECT * FROM dg_reading ORDER BY id DESC", conn)
    st.dataframe(df)
 
