import streamlit as st
import sqlite3
from datetime import datetime, timedelta
 
# Initialize DB
conn = sqlite3.connect("diesel_monitoring.db", check_same_thread=False)
c = conn.cursor()
 
# Create table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS diesel_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        date TEXT,
        toll_plaza TEXT,
        dg_name TEXT,
        barrel_stock REAL,
        dg_opening_stock REAL,
        diesel_topup REAL,
        diesel_closing_stock REAL,
        diesel_purchase REAL,
        diesel_consumption REAL,
        opening_kwh REAL,
        closing_kwh REAL,
        net_kwh REAL,
        opening_rh REAL,
        closing_rh REAL,
        net_running_hr TEXT,
        remarks TEXT
    )
''')
conn.commit()
 
st.title("⛽ Diesel Monitoring App (with Dynamic KWH & RH)")
 
menu = ["Field Staff Entry", "Admin Block", "View Last Entries"]
choice = st.sidebar.selectbox("Select Option", menu)
 
if choice == "Admin Block":
    st.header("🔐 Admin Block - Initialize Data")
 
    date = st.date_input("Date", datetime.today())
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"])
    barrel_stock = st.number_input("Set Plaza Barrel Stock (L)", min_value=0.0, format="%.2f")
    dg_opening_stock = st.number_input("Set DG Opening Diesel Stock (L)", min_value=0.0, format="%.2f")
    opening_kwh = st.number_input("Set DG Opening KWH", min_value=0.0, format="%.2f")
    opening_rh = st.number_input("Set DG Opening Running Hours", min_value=0.0, format="%.2f")
 
    if st.button("💾 Save Initialization Data"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO diesel_log (
                        timestamp, date, toll_plaza, dg_name,
                        barrel_stock, dg_opening_stock,
                        diesel_topup, diesel_closing_stock,
                        diesel_purchase, diesel_consumption,
                        opening_kwh, closing_kwh, net_kwh,
                        opening_rh, closing_rh, net_running_hr,
                        remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (timestamp, str(date), toll_plaza, dg_name,
                   barrel_stock, dg_opening_stock,
                   0, 0, 0, 0,
                   opening_kwh, 0, 0,
                   opening_rh, 0, "",
                   "Initialized by Admin"))
        conn.commit()
        st.success("✅ Initialization Data Saved Successfully.")
        st.rerun()
 
elif choice == "Field Staff Entry":
    st.header("🛠️ Field Staff DG Reading Entry")
 
    date = st.date_input("Date", datetime.today())
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"])
 
    # Fetch last data for dynamic opening KWH & RH
    c.execute('''SELECT barrel_stock, dg_opening_stock, closing_kwh, closing_rh
                 FROM diesel_log
                 WHERE toll_plaza = ? AND dg_name = ?
                 ORDER BY id DESC LIMIT 1''', (toll_plaza, dg_name))
    data = c.fetchone()
    last_barrel_stock = data[0] if data else 0
    last_dg_opening_stock = data[1] if data else 0
    opening_kwh_value = data[2] if data and data[2] else 0
    opening_rh_value = data[3] if data and data[3] else 0
 
    st.info(f"🔹 Current Plaza Barrel Stock: {last_barrel_stock} L")
    st.info(f"🔹 Last DG Opening Diesel Stock: {last_dg_opening_stock} L")
 
    diesel_topup = st.number_input("Diesel Top Up into DG (L)", min_value=0.0, format="%.2f")
    diesel_closing_stock = st.number_input("Diesel Closing Stock at DG (L)", min_value=0.0, format="%.2f")
    diesel_purchase = st.number_input("Diesel Purchased (L)", min_value=0.0, format="%.2f")
 
    diesel_consumption = (last_dg_opening_stock + diesel_topup) - diesel_closing_stock
    st.info(f"🛢️ Diesel Consumption (Auto): {diesel_consumption:.2f} L")
 
    updated_barrel_stock = last_barrel_stock - diesel_topup + diesel_purchase
    st.info(f"🛢️ Updated Plaza Barrel Stock (Auto): {updated_barrel_stock:.2f} L")
 
    # KWH Section
    st.subheader("⚡ Energy Readings (KWH)")
    st.write(f"🟢 Opening KWH (Auto): {opening_kwh_value:.2f}")
    closing_kwh = st.number_input("Enter Closing KWH", min_value=opening_kwh_value, format="%.2f")
    net_kwh = closing_kwh - opening_kwh_value
    st.success(f"✅ Net KWH (Auto): {net_kwh:.2f}")
 
    # RH Section
    st.subheader("⏱️ Running Hours (RH)")
    st.write(f"🟢 Opening RH (Auto): {opening_rh_value:.2f}")
    closing_rh = st.number_input("Enter Closing RH", min_value=opening_rh_value, format="%.2f")
    net_rh_value = closing_rh - opening_rh_value
    net_rh_td = timedelta(hours=net_rh_value)
    net_rh_str = f"{int(net_rh_td.seconds // 3600)}h {int((net_rh_td.seconds % 3600) // 60)}m"
    st.success(f"✅ Net Running Hours (Auto): {net_rh_str}")
 
    remarks = st.text_area("Remarks")
 
    if st.button("✅ Submit DG Reading"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO diesel_log (
                        timestamp, date, toll_plaza, dg_name,
                        barrel_stock, dg_opening_stock,
                        diesel_topup, diesel_closing_stock,
                        diesel_purchase, diesel_consumption,
                        opening_kwh, closing_kwh, net_kwh,
                        opening_rh, closing_rh, net_running_hr,
                        remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (timestamp, str(date), toll_plaza, dg_name,
                   updated_barrel_stock, last_dg_opening_stock,
                   diesel_topup, diesel_closing_stock,
                   diesel_purchase, diesel_consumption,
                   opening_kwh_value, closing_kwh, net_kwh,
                   opening_rh_value, closing_rh, net_rh_str,
                   remarks))
        conn.commit()
        st.success("✅ Data submitted successfully!")
        st.rerun()
 
elif choice == "View Last Entries":
    st.header("📄 Last 5 Entries for Selected Toll Plaza and DG")
 
    toll_plaza = st.selectbox("Select Toll Plaza for View", ["TP01", "TP02", "TP03"])
    dg_name = st.selectbox("Select DG for View", ["DG1", "DG2"])
 
    c.execute('''SELECT date, toll_plaza, dg_name,
                        barrel_stock, dg_opening_stock,
                        diesel_topup, diesel_closing_stock,
                        diesel_purchase, diesel_consumption,
                        opening_kwh, closing_kwh, net_kwh,
                        opening_rh, closing_rh, net_running_hr,
                        remarks, timestamp
                 FROM diesel_log
                 WHERE toll_plaza = ? AND dg_name = ?
                 ORDER BY id DESC LIMIT 5''', (toll_plaza, dg_name))
    rows = c.fetchall()
 
    if rows:
        st.table(rows)
    else:
        st.info("ℹ️ No data found for this selection yet.")
COBI
 
