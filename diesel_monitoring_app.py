import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# ---------- DB SETUP ----------
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS diesel_data (
    date TEXT, toll_plaza TEXT, dg_name TEXT,
    plaza_barrel_stock REAL, diesel_topup REAL, diesel_purchase REAL, updated_plaza_barrel_stock REAL,
    opening_kwh REAL, closing_kwh REAL, net_kwh REAL,
    opening_dg_stock REAL, closing_dg_stock REAL, diesel_consumption REAL,
    opening_rh TEXT, closing_rh TEXT, net_rh TEXT, max_demand REAL
)
''')
conn.commit()

# ---------- FUNCTIONS ----------
def calculate_net_rh(opening_rh, closing_rh):
    try:
        fmt = "%H:%M"
        tdelta = datetime.strptime(closing_rh, fmt) - datetime.strptime(opening_rh, fmt)
        if tdelta.days < 0:
            tdelta = timedelta(days=0, seconds=tdelta.seconds, microseconds=tdelta.microseconds)
        total_minutes = tdelta.seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02}:{minutes:02}"
    except:
        return "00:00"

def get_last_entry(toll_plaza, dg_name):
    c.execute('''
        SELECT * FROM diesel_data
        WHERE toll_plaza=? AND dg_name=?
        ORDER BY date DESC LIMIT 1
    ''', (toll_plaza, dg_name))
    row = c.fetchone()
    if row:
        return {
            "date": row[0],
            "plaza_barrel_stock": row[6],
            "opening_dg_stock": row[11],
            "opening_kwh": row[8],
            "opening_rh": row[13],
            "closing_dg_stock": row[11],
            "closing_kwh": row[8],
            "closing_rh": row[13]
        }
    else:
        return None

def get_plaza_barrel_stock(toll_plaza):
    c.execute('''
        SELECT updated_plaza_barrel_stock, date FROM diesel_data
        WHERE toll_plaza=?
        ORDER BY date DESC LIMIT 1
    ''', (toll_plaza,))
    row = c.fetchone()
    if row:
        return row[0], row[1]
    else:
        return 0.0, None

# ---------- MODULES ----------
def admin_block():
    st.subheader("🛠️ Admin Block")
    password = st.text_input("Enter Admin Password", type="password")
    if password == "Sekura@2025":
        st.success("Password Correct.")
        toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="admin_tp")
        dg_name = st.selectbox("Select DG", ["DG1", "DG2"], key="admin_dg")
        plaza_barrel_stock = st.number_input("Initialize Plaza Barrel Stock (shared across DG1 and DG2)", min_value=0.0, step=1.0)
        opening_dg_stock = st.number_input("Opening Diesel Stock at DG (L)", min_value=0.0, step=1.0)
        opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=1.0)
        opening_rh = st.text_input("Opening RH (HH:MM)", value="00:00")

        if st.button("💾 Save Initialization"):
            today = datetime.today().strftime("%Y-%m-%d")
            c.execute('''
                INSERT INTO diesel_data (
                    date, toll_plaza, dg_name,
                    plaza_barrel_stock, diesel_topup, diesel_purchase, updated_plaza_barrel_stock,
                    opening_kwh, closing_kwh, net_kwh,
                    opening_dg_stock, closing_dg_stock, diesel_consumption,
                    opening_rh, closing_rh, net_rh, max_demand
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                today, toll_plaza, dg_name,
                plaza_barrel_stock, 0.0, 0.0, plaza_barrel_stock,
                opening_kwh, opening_kwh, 0.0,
                opening_dg_stock, opening_dg_stock, 0.0,
                opening_rh, opening_rh, "00:00",
                0.0
            ))
            conn.commit()
            st.success("✅ Initialization data saved and synced.")
            st.experimental_rerun()
    elif password != "":
        st.error("❌ Incorrect Password")

def user_block():
    st.subheader("📲 User Entry Block")
    date = st.date_input("Select Date", datetime.today())
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="user_tp")
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"], key="user_dg")

    last_entry = get_last_entry(toll_plaza, dg_name)
    last_plaza_stock, last_plaza_date = get_plaza_barrel_stock(toll_plaza)

    # Determine if date is next date for update or fresh
    if last_entry:
        last_date_obj = datetime.strptime(last_entry["date"], "%Y-%m-%d")
        if date == (last_date_obj + timedelta(days=1)).date():
            opening_dg_stock = last_entry["closing_dg_stock"]
            opening_kwh = last_entry["closing_kwh"]
            opening_rh = last_entry["closing_rh"]
            plaza_barrel_stock = last_plaza_stock
        else:
            opening_dg_stock = last_entry["opening_dg_stock"]
            opening_kwh = last_entry["opening_kwh"]
            opening_rh = last_entry["opening_rh"]
            plaza_barrel_stock = last_plaza_stock
    else:
        opening_dg_stock = 0.0
        opening_kwh = 0.0
        opening_rh = "00:00"
        plaza_barrel_stock = last_plaza_stock

    st.info(f"🛢️ Plaza Barrel Stock: {plaza_barrel_stock} L")
    diesel_topup = st.number_input("Diesel Top Up (L)", min_value=0.0, value=0.0)
    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, value=0.0)
    updated_plaza_barrel_stock = plaza_barrel_stock + diesel_purchase - diesel_topup
    st.info(f"🛢️ Updated Plaza Barrel Stock: {updated_plaza_barrel_stock} L")

    st.info(f"🔋 Opening KWH: {opening_kwh}")
    closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh, value=opening_kwh)
    net_kwh = closing_kwh - opening_kwh
    st.info(f"⚡ Net KWH: {net_kwh}")

    st.info(f"⛽ Opening Diesel Stock at DG: {opening_dg_stock} L")
    closing_dg_stock = st.number_input("Closing Diesel Stock at DG (L)", min_value=0.0, value=0.0)
    diesel_consumption = (opening_dg_stock + diesel_topup) - closing_dg_stock
    st.info(f"🛢️ Diesel Consumption: {diesel_consumption} L")

    st.info(f"⏱️ Opening RH: {opening_rh}")
    closing_rh = st.text_input("Closing RH (HH:MM)", value=opening_rh)
    net_rh = calculate_net_rh(opening_rh, closing_rh)
    st.info(f"🕒 Net Running Hours: {net_rh}")

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
            plaza_barrel_stock, diesel_topup, diesel_purchase, updated_plaza_barrel_stock,
            opening_kwh, closing_kwh, net_kwh,
            opening_dg_stock, closing_dg_stock, diesel_consumption,
            opening_rh, closing_rh, net_rh, max_demand
        ))
        conn.commit()
        st.success("✅ Entry Saved! Values will sync for the next entry.")
        st.experimental_rerun()

def view_last_entries():
    st.subheader("📈 Last 10 Entries")
    df = pd.read_sql_query("SELECT * FROM diesel_data ORDER BY date DESC LIMIT 10", conn)
    st.dataframe(df)

def download_csv():
    st.subheader("⬇️ Download Full Data as CSV")
    df = pd.read_sql_query("SELECT * FROM diesel_data", conn)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "diesel_monitoring_data.csv", "text/csv")

# ---------- MAIN ----------
st.title("⛽ Diesel Monitoring | Toll Plaza Operations")

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
