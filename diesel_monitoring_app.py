import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# -------------- Database Connection --------------
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
c = conn.cursor()

# Create diesel_data for history
c.execute('''
CREATE TABLE IF NOT EXISTS diesel_data (
    date TEXT, toll_plaza TEXT, dg_name TEXT,
    plaza_barrel_stock REAL, diesel_topup REAL, diesel_purchase REAL, updated_plaza_barrel_stock REAL,
    opening_kwh REAL, closing_kwh REAL, net_kwh REAL,
    opening_dg_stock REAL, closing_dg_stock REAL, diesel_consumption REAL,
    opening_rh TEXT, closing_rh TEXT, net_rh TEXT, max_demand REAL
)
''')

# Create live_values table for dynamic latest values
c.execute('''
CREATE TABLE IF NOT EXISTS live_values (
    toll_plaza TEXT, dg_name TEXT,
    plaza_barrel_stock REAL,
    opening_dg_stock REAL,
    opening_kwh REAL,
    opening_rh TEXT,
    last_updated TEXT,
    PRIMARY KEY (toll_plaza, dg_name)
)
''')
conn.commit()

# -------------- Utility Functions --------------
def calculate_net_rh(opening_rh, closing_rh):
    fmt = "%H:%M"
    tdelta = datetime.strptime(closing_rh, fmt) - datetime.strptime(opening_rh, fmt)
    if tdelta.days < 0:
        tdelta = timedelta(days=0, seconds=tdelta.seconds, microseconds=tdelta.microseconds)
    total_minutes = tdelta.seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02}:{minutes:02}"

def fetch_live_values(toll_plaza, dg_name):
    c.execute('''
        SELECT plaza_barrel_stock, opening_dg_stock, opening_kwh, opening_rh
        FROM live_values
        WHERE toll_plaza=? AND dg_name=?
    ''', (toll_plaza, dg_name))
    row = c.fetchone()
    if row:
        return {
            "plaza_barrel_stock": row[0],
            "opening_dg_stock": row[1],
            "opening_kwh": row[2],
            "opening_rh": row[3]
        }
    else:
        return {
            "plaza_barrel_stock": 0.0,
            "opening_dg_stock": 0.0,
            "opening_kwh": 0.0,
            "opening_rh": "00:00"
        }

def update_live_values(toll_plaza, dg_name, plaza_barrel_stock, opening_dg_stock, opening_kwh, opening_rh):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO live_values (toll_plaza, dg_name, plaza_barrel_stock, opening_dg_stock, opening_kwh, opening_rh, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(toll_plaza, dg_name) DO UPDATE SET
            plaza_barrel_stock=excluded.plaza_barrel_stock,
            opening_dg_stock=excluded.opening_dg_stock,
            opening_kwh=excluded.opening_kwh,
            opening_rh=excluded.opening_rh,
            last_updated=excluded.last_updated
    ''', (toll_plaza, dg_name, plaza_barrel_stock, opening_dg_stock, opening_kwh, opening_rh, now))
    conn.commit()

# -------------- Modules --------------

def admin_block():
    st.subheader("🛠️ Admin Initialization Block")

    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"])
    plaza_barrel_stock = st.number_input("Set Plaza Barrel Stock (L)", min_value=0.0, step=1.0)
    opening_dg_stock = st.number_input("Set Opening Diesel Stock at DG (L)", min_value=0.0, step=1.0)
    opening_kwh = st.number_input("Set Opening KWH", min_value=0.0, step=1.0)
    opening_rh = st.text_input("Set Opening RH (HH:MM)", value="00:00")

    password = st.text_input("Enter Admin Password", type="password")
    if st.button("💾 Save Initialization"):
        if password == "Sekura@2025":
            update_live_values(toll_plaza, dg_name, plaza_barrel_stock, opening_dg_stock, opening_kwh, opening_rh)
            st.success("✅ Initialization saved and synced for next user entry.")
            st.experimental_rerun()
        else:
            st.error("❌ Incorrect Password")

def user_block():
    st.subheader("📲 User Entry Block")

    date = st.date_input("Date", datetime.today())
    toll_plaza = st.selectbox("Toll Plaza", ["TP01", "TP02", "TP03"], key="user_tp")
    dg_name = st.selectbox("DG Name", ["DG1", "DG2"], key="user_dg")

    live = fetch_live_values(toll_plaza, dg_name)
    st.info(f"🛢️ Current Plaza Barrel Stock: {live['plaza_barrel_stock']} L")
    diesel_topup = st.number_input("Diesel Top Up (L)", min_value=0.0, value=0.0)
    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, value=0.0)
    updated_plaza_barrel_stock = live["plaza_barrel_stock"] + diesel_purchase - diesel_topup
    st.info(f"🛢️ Updated Plaza Barrel Stock: {updated_plaza_barrel_stock} L")

    st.info(f"🔋 Opening KWH: {live['opening_kwh']}")
    closing_kwh = st.number_input("Closing KWH", min_value=live["opening_kwh"])
    net_kwh = closing_kwh - live["opening_kwh"]
    st.info(f"⚡ Net KWH: {net_kwh}")

    st.info(f"⛽ Opening Diesel Stock at DG: {live['opening_dg_stock']} L")
    closing_dg_stock = st.number_input("Closing Diesel Stock at DG (L)", min_value=0.0)
    diesel_consumption = (live["opening_dg_stock"] + diesel_topup) - closing_dg_stock
    st.info(f"🛢️ Diesel Consumption: {diesel_consumption} L")

    st.info(f"⏱️ Opening RH: {live['opening_rh']}")
    closing_rh = st.text_input("Closing RH (HH:MM)", value=live["opening_rh"])
    net_rh = calculate_net_rh(live["opening_rh"], closing_rh)
    st.info(f"🕒 Net RH: {net_rh}")

    max_demand = st.number_input("Maximum Demand (kW)", min_value=0.0, value=0.0)

    if st.button("✅ Submit Entry"):
        c.execute('''
            INSERT INTO diesel_data (
                date, toll_plaza, dg_name,
                plaza_barrel_stock, diesel_topup, diesel_purchase, updated_plaza_barrel_stock,
                opening_kwh, closing_kwh, net_kwh,
                opening_dg_stock, closing_dg_stock, diesel_consumption,
                opening_rh, closing_rh, net_rh, max_demand
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            str(date), toll_plaza, dg_name,
            live["plaza_barrel_stock"], diesel_topup, diesel_purchase, updated_plaza_barrel_stock,
            live["opening_kwh"], closing_kwh, net_kwh,
            live["opening_dg_stock"], closing_dg_stock, diesel_consumption,
            live["opening_rh"], closing_rh, net_rh, max_demand
        ))
        conn.commit()

        # Update live_values table for next entry
        update_live_values(
            toll_plaza, dg_name,
            updated_plaza_barrel_stock,
            closing_dg_stock,
            closing_kwh,
            closing_rh
        )
        st.success("✅ Entry saved! Values updated for the next entry.")
        st.experimental_rerun()

def view_last_entries():
    st.subheader("📈 Last 10 Entries")
    df = pd.read_sql_query("SELECT * FROM diesel_data ORDER BY date DESC LIMIT 10", conn)
    st.dataframe(df)

def download_csv():
    st.subheader("⬇️ Download Full Data")
    df = pd.read_sql_query("SELECT * FROM diesel_data", conn)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "diesel_monitoring_data.csv", "text/csv")

# -------------- Streamlit App Layout --------------
st.title("⛽ Diesel Monitoring - Toll Plaza Operations")

choice = st.sidebar.radio(
    "Select Module",
    ["Admin Block", "User Block", "View Last 10 Entries", "Download CSV"]
)

if choice == "Admin Block":
    admin_block()
elif choice == "User Block":
    user_block()
elif choice == "View Last 10 Entries":
    view_last_entries()
elif choice == "Download CSV":
    download_csv()
