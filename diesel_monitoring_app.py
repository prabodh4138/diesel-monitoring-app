import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# -------------------- Database Setup --------------------
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
cursor = conn.cursor()

# Main data table
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

# Initialization table
cursor.execute("""
CREATE TABLE IF NOT EXISTS initialization (
    toll_plaza TEXT,
    dg_name TEXT,
    plaza_barrel_stock REAL,
    dg_opening_stock REAL,
    opening_kwh REAL,
    opening_rh REAL,
    PRIMARY KEY (toll_plaza, dg_name)
)
""")
conn.commit()

# -------------------- Helper Functions --------------------
def initialize_data(toll_plaza, dg_name, plaza_stock, dg_stock, opening_kwh, opening_rh):
    cursor.execute("""
        INSERT OR REPLACE INTO initialization (toll_plaza, dg_name, plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (toll_plaza, dg_name, plaza_stock, dg_stock, opening_kwh, opening_rh))
    conn.commit()

def get_initialized_value(toll_plaza, dg_name):
    cursor.execute("""
        SELECT plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh
        FROM initialization WHERE toll_plaza = ? AND dg_name = ? LIMIT 1
    """, (toll_plaza, dg_name))
    result = cursor.fetchone()
    return result if result else (0, 0, 0, 0)

def get_plaza_adjustment(toll_plaza):
    cursor.execute("""
        SELECT SUM(diesel_purchase) - SUM(diesel_top_up) FROM diesel_monitoring WHERE toll_plaza = ?
    """, (toll_plaza,))
    adj = cursor.fetchone()[0]
    return adj if adj else 0

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Diesel Monitoring - Toll Plaza Ops", page_icon="⛽", layout="centered")
st.title("⛽ Diesel Monitoring App - Toll Plaza Operations")

tabs = st.tabs(["📋 User Entry", "🛠️ Admin Initialization"])

# ---------------- Admin Initialization --------------------
with tabs[1]:
    st.header("🛠️ Admin Initialization")

    if st.button("🔄 Refresh Admin Block"):
        st.experimental_rerun()

    toll_plaza_admin = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="admin_tp")
    dg_name_admin = st.selectbox("Select DG", ["DG1", "DG2"], key="admin_dg")

    plaza_stock_input = st.number_input("Plaza Barrel Stock (L)", min_value=0.0, step=0.1)
    dg_stock_input = st.number_input("DG Opening Diesel Stock (L)", min_value=0.0, step=0.1)
    opening_kwh_input = st.number_input("Opening KWH", min_value=0.0, step=0.1)
    opening_rh_input = st.number_input("Opening RH", min_value=0.0, step=0.1)

    if st.button("Save Initialization"):
        passcode = st.text_input("Enter Admin Passcode to Confirm Save", type="password")
        if passcode == "admin@tollplaza":
            initialize_data(toll_plaza_admin, dg_name_admin, plaza_stock_input, dg_stock_input, opening_kwh_input, opening_rh_input)
            st.success(f"✅ Initialization saved successfully for {toll_plaza_admin} - {dg_name_admin}.")
        else:
            st.error("❌ Incorrect passcode. Initialization not saved.")

# ---------------- User Entry --------------------
with tabs[0]:
    st.header("📋 Diesel Monitoring Entry")

    if st.button("🔄 Refresh User Block"):
        st.experimental_rerun()

    date = st.date_input("Date", datetime.now()).strftime("%Y-%m-%d")
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="user_tp")
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"], key="user_dg")

    # Fetch initialized values:
    plaza_stock, dg_stock, opening_kwh, opening_rh = get_initialized_value(toll_plaza, dg_name)
    plaza_adjustment = get_plaza_adjustment(toll_plaza)
    current_plaza_stock = plaza_stock + plaza_adjustment

    st.info(f"🔹 Plaza Barrel Stock: **{current_plaza_stock:.2f} L**")
    st.info(f"🔹 DG Opening Diesel Stock: **{dg_stock:.2f} L**")
    st.info(f"🔹 Opening KWH: **{opening_kwh:.2f}**")
    st.info(f"🔹 Opening RH: **{opening_rh:.2f}**")

    diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0.0, step=0.1)
    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=0.1)
    dg_closing_stock = st.number_input("DG Closing Diesel Stock (L)", min_value=0.0, step=0.1, placeholder="Required")
    closing_kwh = st.number_input("Closing KWH", min_value=0.0, step=0.1, placeholder="Required")
    closing_rh = st.number_input("Closing RH", min_value=0.0, step=0.1, placeholder="Required")

    # Validations:
    if st.button("Submit Entry"):
        if dg_closing_stock == 0 or closing_kwh == 0 or closing_rh == 0:
            st.error("❌ Please fill in all mandatory fields: DG Closing Stock, Closing KWH, Closing RH.")
        else:
            net_kwh = closing_kwh - opening_kwh
            rh_diff = closing_rh - opening_rh
            net_rh_td = timedelta(hours=rh_diff)
            net_rh_str = f"{int(net_rh_td.total_seconds() // 3600):02}:{int((net_rh_td.total_seconds() % 3600) // 60):02}"

            diesel_consumption = (dg_stock + diesel_top_up) - dg_closing_stock
            updated_plaza_stock = current_plaza_stock - diesel_top_up + diesel_purchase

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
                opening_rh, closing_rh, net_rh_str, diesel_consumption, updated_plaza_stock
            ))
            conn.commit()
            st.success("✅ Data saved successfully!")

    st.markdown("---")
    st.subheader("🕒 Last 5 Entries")
    df = pd.read_sql_query("""
        SELECT timestamp, date, toll_plaza, dg_name, diesel_top_up, diesel_purchase,
               dg_closing_stock, opening_kwh, closing_kwh, net_kwh,
               opening_rh, closing_rh, net_rh, diesel_consumption, plaza_barrel_stock
        FROM diesel_monitoring
        WHERE toll_plaza = ? AND dg_name = ?
        ORDER BY id DESC LIMIT 5
    """, conn, params=(toll_plaza, dg_name))
    st.dataframe(df)
