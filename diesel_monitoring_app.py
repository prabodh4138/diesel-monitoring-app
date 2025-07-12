import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --------------- Database Setup -----------------
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS diesel_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    date TEXT,
    toll_plaza TEXT,
    dg_name TEXT,
    diesel_top_up REAL,
    diesel_purchase REAL,
    updated_plaza_stock REAL,
    dg_closing_stock REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    net_kwh REAL,
    opening_rh REAL,
    closing_rh REAL,
    net_rh TEXT,
    max_demand REAL
)
""")

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

# --------------- Helper Functions -----------------
def initialize_data(toll_plaza, dg_name, plaza_stock, dg_stock, opening_kwh, opening_rh):
    cursor.execute("""
        INSERT OR REPLACE INTO initialization (toll_plaza, dg_name, plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (toll_plaza, dg_name, plaza_stock, dg_stock, opening_kwh, opening_rh))
    conn.commit()

def get_initialized_values(toll_plaza, dg_name):
    cursor.execute("""
        SELECT plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh
        FROM initialization WHERE toll_plaza = ? AND dg_name = ?
    """, (toll_plaza, dg_name))
    result = cursor.fetchone()
    return result if result else (0, 0, 0, 0)

def update_initialization_after_entry(toll_plaza, dg_name, new_plaza_stock, new_dg_stock, new_kwh, new_rh):
    cursor.execute("""
        UPDATE initialization
        SET plaza_barrel_stock = ?, dg_opening_stock = ?, opening_kwh = ?, opening_rh = ?
        WHERE toll_plaza = ? AND dg_name = ?
    """, (new_plaza_stock, new_dg_stock, new_kwh, new_rh, toll_plaza, dg_name))
    conn.commit()

# --------------- Streamlit UI -----------------
st.set_page_config(page_title="Diesel Monitoring - Toll Operations", layout="centered")
st.title("⛽ Diesel Monitoring - Toll Operations")

tabs = st.tabs(["🛠️ Admin Block", "📝 User Block", "📥 CSV Download", "📊 Last 10 Entries"])

# --------------- Admin Block -----------------
with tabs[0]:
    st.header("🛠️ Admin Initialization Block")

    tp_admin = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_admin = st.selectbox("Select DG", ["DG1", "DG2"])

    plaza_stock_input = st.number_input("Plaza Barrel Stock (L)", min_value=0.0)
    dg_stock_input = st.number_input("DG Opening Diesel Stock (L)", min_value=0.0)
    opening_kwh_input = st.number_input("Opening KWH", min_value=0.0)
    opening_rh_input = st.number_input("Opening RH", min_value=0.0)

    password = st.text_input("Enter Admin Password", type="password")

    if password == "Sekura@2025":
        if st.button("Save Initialization"):
            initialize_data(tp_admin, dg_admin, plaza_stock_input, dg_stock_input, opening_kwh_input, opening_rh_input)
            st.success("✅ Initialization saved and synced with User Block.")
    elif password != "":
        st.error("❌ Incorrect password.")

# --------------- User Block -----------------
with tabs[1]:
    st.header("📝 User Data Entry Block")

    date = st.date_input("Select Date", datetime.now()).strftime("%Y-%m-%d")
    tp_user = st.selectbox("Toll Plaza", ["TP01", "TP02", "TP03"], key="user_tp")
    dg_user = st.selectbox("DG", ["DG1", "DG2"], key="user_dg")

    plaza_stock, dg_stock, opening_kwh, opening_rh = get_initialized_values(tp_user, dg_user)
    st.info(f"Plaza Barrel Stock: {plaza_stock} L")
    st.info(f"DG Opening Diesel Stock: {dg_stock} L")
    st.info(f"Opening KWH: {opening_kwh}")
    st.info(f"Opening RH: {opening_rh}")

    diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0.0)
    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0)
    updated_plaza_stock = (plaza_stock + diesel_purchase) - diesel_top_up
    st.success(f"Updated Plaza Barrel Stock: {updated_plaza_stock:.2f} L")

    closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh)
    net_kwh = closing_kwh - opening_kwh
    st.info(f"Net KWH: {net_kwh}")

    closing_rh = st.number_input("Closing RH", min_value=opening_rh)
    rh_diff = closing_rh - opening_rh
    net_rh_td = timedelta(hours=rh_diff)
    net_rh_str = f"{int(net_rh_td.total_seconds() // 3600):02}:{int((net_rh_td.total_seconds() % 3600) // 60):02}"
    st.info(f"Net Running Hours: {net_rh_str}")

    max_demand = st.number_input("Maximum Demand (kW)", min_value=0.0)

    dg_closing_stock = st.number_input("DG Closing Diesel Stock (L)", min_value=0.0)

    if st.button("Submit Entry"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO diesel_monitoring (
                timestamp, date, toll_plaza, dg_name, diesel_top_up, diesel_purchase,
                updated_plaza_stock, dg_closing_stock, opening_kwh, closing_kwh, net_kwh,
                opening_rh, closing_rh, net_rh, max_demand
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, date, tp_user, dg_user, diesel_top_up, diesel_purchase,
            updated_plaza_stock, dg_closing_stock, opening_kwh, closing_kwh, net_kwh,
            opening_rh, closing_rh, net_rh_str, max_demand
        ))
        conn.commit()

        update_initialization_after_entry(tp_user, dg_user, updated_plaza_stock, dg_closing_stock, closing_kwh, closing_rh)

        st.success("✅ Entry saved successfully!")

# --------------- CSV Download -----------------
with tabs[2]:
    st.header("📥 Download Data as CSV")

    from_date = st.date_input("From Date", datetime.now() - timedelta(days=7))
    to_date = st.date_input("To Date", datetime.now())

    tp_filter = st.selectbox("Filter Toll Plaza", ["All", "TP01", "TP02", "TP03"])
    dg_filter = st.selectbox("Filter DG", ["All", "DG1", "DG2"])

    if st.button("Download CSV"):
        query = "SELECT * FROM diesel_monitoring WHERE date BETWEEN ? AND ?"
        params = [from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")]

        if tp_filter != "All":
            query += " AND toll_plaza = ?"
            params.append(tp_filter)
        if dg_filter != "All":
            query += " AND dg_name = ?"
            params.append(dg_filter)

        df = pd.read_sql_query(query, conn, params=params)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV File", csv, "diesel_monitoring_data.csv", "text/csv")
        st.success("✅ CSV generated successfully!")

# --------------- Last 10 Rows -----------------
with tabs[3]:
    st.header("📊 Last 10 Entries")

    tp_disp = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_disp = st.selectbox("Select DG", ["DG1", "DG2"])

    df_last10 = pd.read_sql_query("""
        SELECT * FROM diesel_monitoring
        WHERE toll_plaza = ? AND dg_name = ?
        ORDER BY id DESC LIMIT 10
    """, conn, params=(tp_disp, dg_disp))

    st.dataframe(df_last10)
