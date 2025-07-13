import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ---------------- Database Setup ---------------- #
conn = sqlite3.connect("diesel_monitoring.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables if not exist
cursor.execute('''CREATE TABLE IF NOT EXISTS diesel_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    toll_plaza TEXT,
    dg_name TEXT,
    plaza_barrel_stock REAL,
    diesel_topup REAL,
    diesel_purchase REAL,
    updated_plaza_barrel_stock REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    net_kwh REAL,
    opening_rh TEXT,
    closing_rh TEXT,
    net_rh TEXT,
    max_demand REAL,
    diesel_closing_stock REAL,
    updated_diesel_stock REAL,
    timestamp TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS live_status (
    toll_plaza TEXT,
    dg_name TEXT,
    updated_plaza_barrel_stock REAL,
    updated_diesel_stock REAL,
    updated_opening_kwh REAL,
    updated_opening_rh TEXT,
    PRIMARY KEY (toll_plaza, dg_name)
)''')
conn.commit()

# Initialize live_status if empty
for plaza in ['TP01', 'TP02', 'TP03']:
    for dg in ['DG1', 'DG2']:
        cursor.execute('''INSERT OR IGNORE INTO live_status
            (toll_plaza, dg_name, updated_plaza_barrel_stock, updated_diesel_stock, updated_opening_kwh, updated_opening_rh)
            VALUES (?, ?, ?, ?, ?, ?)''', (plaza, dg, 0, 0, 0, "00:00"))
conn.commit()

# ---------------- Utility Functions ---------------- #
def calculate_net_rh(opening, closing):
    try:
        fmt = '%H:%M'
        tdelta = datetime.strptime(closing, fmt) - datetime.strptime(opening, fmt)
        if tdelta.total_seconds() < 0:
            return None
        return str(timedelta(seconds=tdelta.total_seconds()))[:-3]
    except:
        return None

def get_last_n_transactions(n=10, plaza=None, dg=None):
    query = "SELECT * FROM diesel_data"
    params = []
    if plaza and dg:
        query += " WHERE toll_plaza=? AND dg_name=? ORDER BY id DESC LIMIT ?"
        params = [plaza, dg, n]
    else:
        query += " ORDER BY id DESC LIMIT ?"
        params = [n]
    df = pd.read_sql_query(query, conn, params=params)
    return df

# ---------------- App Layout ---------------- #
st.title("🛠️ Diesel Monitoring App - Sekura")

menu = ["User Entry", "Admin Initialization", "Download CSV", "Last 10 Transactions"]
choice = st.sidebar.selectbox("Select Action", menu)

# ---------------- Admin Block ---------------- #
if choice == "Admin Initialization":
    st.subheader("🔐 Admin Initialization Block")
    password = st.text_input("Enter Admin Password", type="password")
    if password == "Sekura@2025":
        st.success("Password Correct. You can initialize data.")
        plaza = st.selectbox("Select Toll Plaza", ['TP01', 'TP02', 'TP03'])
        dg = st.selectbox("Select DG", ['DG1', 'DG2'])
        barrel_stock = st.number_input("Enter Plaza Barrel Stock (L)", min_value=0.0, step=1.0)
        diesel_stock = st.number_input("Enter DG Opening Diesel Stock (L)", min_value=0.0, step=1.0)
        opening_kwh = st.number_input("Enter Opening KWH", min_value=0.0, step=1.0)
        opening_rh = st.text_input("Enter Opening RH (HH:MM)", value="00:00")

        if st.button("Save Initialization"):
            cursor.execute('''INSERT OR REPLACE INTO live_status 
                (toll_plaza, dg_name, updated_plaza_barrel_stock, updated_diesel_stock, updated_opening_kwh, updated_opening_rh)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (plaza, dg, barrel_stock, diesel_stock, opening_kwh, opening_rh))
            conn.commit()
            st.success("✅ Data Initialized Successfully.")
            st.rerun()
    else:
        st.warning("Enter correct password to initialize.")

# ---------------- User Entry Block ---------------- #
elif choice == "User Entry":
    st.subheader("🛠️ User Entry Block")

    today = datetime.today().strftime("%Y-%m-%d")
    date = st.date_input("Select Date", datetime.today())

    plaza = st.selectbox("Select Toll Plaza", ['TP01', 'TP02', 'TP03'])
    dg = st.selectbox("Select DG", ['DG1', 'DG2'])

    cursor.execute('''SELECT * FROM live_status WHERE toll_plaza=? AND dg_name=?''', (plaza, dg))
    live = cursor.fetchone()
    if live:
        _, _, live_barrel_stock, live_diesel_stock, live_kwh, live_rh = live
    else:
        live_barrel_stock = live_diesel_stock = live_kwh = 0
        live_rh = "00:00"

    st.info(f"📌 Plaza Barrel Stock: {live_barrel_stock} L")
    st.info(f"📌 DG Opening Diesel Stock: {live_diesel_stock} L")
    st.info(f"📌 Opening KWH: {live_kwh}")
    st.info(f"📌 Opening RH: {live_rh}")

    diesel_topup = st.number_input("Diesel Top Up (L)", min_value=0.0, step=0.5)
    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=0.5)
    closing_kwh = st.number_input("Closing KWH", min_value=live_kwh, step=0.5)
    closing_rh = st.text_input("Closing RH (HH:MM)")

    max_demand = st.number_input("Maximum Demand (kW)", min_value=0.0, step=0.5)
    diesel_closing_stock = st.number_input("Diesel Closing Stock (L)", min_value=0.0, step=0.5)

    updated_barrel_stock = live_barrel_stock + diesel_purchase - diesel_topup
    diesel_consumption = (live_diesel_stock + diesel_topup) - diesel_closing_stock
    net_kwh = closing_kwh - live_kwh
    net_rh = calculate_net_rh(live_rh, closing_rh)

    if net_rh is None:
        st.warning("⚠️ Invalid RH format or Closing RH < Opening RH.")
    else:
        st.info(f"✅ Diesel Consumption: {diesel_consumption} L")
        st.info(f"✅ Net KWH: {net_kwh}")
        st.info(f"✅ Net RH: {net_rh}")

        if st.button("Submit Entry"):
            if diesel_consumption < 0:
                st.error("❌ Diesel consumption cannot be negative. Check your entries.")
            elif net_kwh < 0:
                st.error("❌ Net KWH cannot be negative.")
            else:
                cursor.execute('''INSERT INTO diesel_data 
                    (date, toll_plaza, dg_name, plaza_barrel_stock, diesel_topup, diesel_purchase, updated_plaza_barrel_stock,
                    opening_kwh, closing_kwh, net_kwh, opening_rh, closing_rh, net_rh, max_demand, diesel_closing_stock, updated_diesel_stock, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (date.strftime("%Y-%m-%d"), plaza, dg, live_barrel_stock, diesel_topup, diesel_purchase, updated_barrel_stock,
                    live_kwh, closing_kwh, net_kwh, live_rh, closing_rh, net_rh, max_demand, diesel_closing_stock, diesel_closing_stock, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                cursor.execute('''UPDATE live_status SET 
                    updated_plaza_barrel_stock=?, updated_diesel_stock=?, updated_opening_kwh=?, updated_opening_rh=?
                    WHERE toll_plaza=? AND dg_name=?''',
                    (updated_barrel_stock, diesel_closing_stock, closing_kwh, closing_rh, plaza, dg))
                conn.commit()
                st.success("✅ Entry Submitted Successfully.")
                st.rerun()

# ---------------- CSV Download Block ---------------- #
elif choice == "Download CSV":
    st.subheader("📥 Download CSV Data")
    df = pd.read_sql_query("SELECT * FROM diesel_data", conn)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Full CSV", csv, "diesel_monitoring_data.csv", "text/csv")
    st.dataframe(df)

# ---------------- Last 10 Transactions ---------------- #
elif choice == "Last 10 Transactions":
    st.subheader("📊 Last 10 Transactions")
    plaza = st.selectbox("Select Toll Plaza for View", ['TP01', 'TP02', 'TP03'])
    dg = st.selectbox("Select DG for View", ['DG1', 'DG2'])
    df = get_last_n_transactions(10, plaza, dg)
    st.dataframe(df)
