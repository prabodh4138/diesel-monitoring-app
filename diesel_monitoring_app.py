import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# DB INIT
conn = sqlite3.connect("diesel_monitoring.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS diesel_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    toll_plaza TEXT,
    dg TEXT,
    barrel_stock REAL,
    diesel_topup REAL,
    diesel_purchase REAL,
    updated_barrel_stock REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    net_kwh REAL,
    opening_rh REAL,
    closing_rh REAL,
    net_rh TEXT,
    max_demand REAL,
    diesel_opening_stock REAL,
    diesel_closing_stock REAL,
    diesel_consumption REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# UTILITY FUNCTIONS
def get_last_value(toll_plaza, dg, column):
    c.execute(f"SELECT {column} FROM diesel_monitoring WHERE toll_plaza=? AND dg=? ORDER BY id DESC LIMIT 1", (toll_plaza, dg))
    result = c.fetchone()
    return float(result[0]) if result and result[0] is not None else 0.0

def get_last_barrel_stock(toll_plaza):
    c.execute("SELECT updated_barrel_stock FROM diesel_monitoring WHERE toll_plaza=? ORDER BY id DESC LIMIT 1", (toll_plaza,))
    result = c.fetchone()
    return float(result[0]) if result and result[0] is not None else 0.0

# SIDEBAR
st.sidebar.title("Navigation")
option = st.sidebar.radio("Go to", ["User Entry", "Admin Initialization", "Download Data", "View Last 10 Entries"])

# ADMIN BLOCK
if option == "Admin Initialization":
    st.header("🔐 Admin Initialization")
    st.info("Enter initialization data. Password required.")
    tp_admin = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="admin_tp")
    dg_admin = st.selectbox("Select DG", ["DG1", "DG2"], key="admin_dg")
    barrel_stock = st.number_input("Plaza Barrel Stock (L)", min_value=0.0, step=1.0, key="admin_barrel")
    opening_diesel_stock = st.number_input("Opening Diesel Stock at DG (L)", min_value=0.0, step=1.0, key="admin_open_diesel")
    opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=1.0, key="admin_open_kwh")
    opening_rh = st.number_input("Opening RH", min_value=0.0, step=0.1, key="admin_open_rh")
    password = st.text_input("Enter Password", type="password", key="admin_pwd")
    
    if st.button("Save Initialization"):
        if password == "Sekura@2025":
            c.execute("""
                INSERT INTO diesel_monitoring 
                (date, toll_plaza, dg, barrel_stock, opening_kwh, opening_rh, diesel_opening_stock, closing_kwh, closing_rh, max_demand, diesel_closing_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d"), tp_admin, dg_admin, barrel_stock, opening_kwh, opening_rh, opening_diesel_stock, opening_kwh, opening_rh, 0, opening_diesel_stock))
            conn.commit()
            st.success("✅ Initialization saved and synchronized to user block.")
        else:
            st.error("❌ Incorrect password. Initialization failed.")

# USER ENTRY BLOCK
elif option == "User Entry":
    st.header("🛠️ Diesel Monitoring Entry")

    today = datetime.now()
    date = st.date_input("Select Date", today, key="user_date")
    tp_user = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="user_tp")
    dg_user = st.selectbox("Select DG", ["DG1", "DG2"], key="user_dg")

    # Virtual Auto Values
    barrel_stock_virtual = get_last_barrel_stock(tp_user)
    diesel_opening_stock_virtual = get_last_value(tp_user, dg_user, "diesel_closing_stock")
    opening_kwh_virtual = get_last_value(tp_user, dg_user, "closing_kwh")
    opening_rh_virtual = get_last_value(tp_user, dg_user, "closing_rh")

    st.write(f"**Plaza Barrel Stock:** {barrel_stock_virtual} L")
    st.write(f"**Opening Diesel Stock at DG:** {diesel_opening_stock_virtual} L")
    st.write(f"**Opening KWH:** {opening_kwh_virtual}")
    st.write(f"**Opening RH:** {opening_rh_virtual}")

    diesel_topup = st.number_input("Diesel Top Up at DG (L)", min_value=0.0, step=1.0, key="user_topup")
    diesel_purchase = st.number_input("Diesel Purchase at Plaza (L)", min_value=0.0, step=1.0, key="user_purchase")

    updated_barrel_stock = barrel_stock_virtual + diesel_purchase - diesel_topup
    st.write(f"**Updated Plaza Barrel Stock:** {updated_barrel_stock} L")

    closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh_virtual, step=1.0, key="user_close_kwh")
    net_kwh = closing_kwh - opening_kwh_virtual
    st.write(f"**Net KWH:** {net_kwh}")

    closing_rh = st.number_input("Closing RH", min_value=opening_rh_virtual, step=0.1, key="user_close_rh")
    net_rh = calculate_net_rh(opening_rh_virtual, closing_rh)
    st.write(f"**Net Running Hours:** {net_rh}")

    diesel_closing_stock = st.number_input("Closing Diesel Stock at DG (L)", min_value=0.0, step=1.0, key="user_close_diesel")
    diesel_consumption = diesel_opening_stock_virtual + diesel_topup - diesel_closing_stock
    st.write(f"**Diesel Consumption:** {diesel_consumption} L")

    max_demand = st.number_input("Maximum Demand (kVA)", min_value=0.0, step=0.1, key="user_md")

    if st.button("Submit Entry"):
        c.execute("""
            INSERT INTO diesel_monitoring
            (date, toll_plaza, dg, barrel_stock, diesel_topup, diesel_purchase, updated_barrel_stock,
            opening_kwh, closing_kwh, net_kwh, opening_rh, closing_rh, net_rh,
            max_demand, diesel_opening_stock, diesel_closing_stock, diesel_consumption)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date.strftime("%Y-%m-%d"), tp_user, dg_user, barrel_stock_virtual, diesel_topup, diesel_purchase, updated_barrel_stock,
              opening_kwh_virtual, closing_kwh, net_kwh, opening_rh_virtual, closing_rh, net_rh,
              max_demand, diesel_opening_stock_virtual, diesel_closing_stock, diesel_consumption))
        conn.commit()
        st.success("✅ Entry saved successfully.")

    if st.button("🔄 Refresh", key="refresh_user"):
        st.experimental_rerun()

# DOWNLOAD DATA BLOCK
elif option == "Download Data":
    st.header("📥 Download Data")

    from_date = st.date_input("From Date", today - timedelta(days=7), key="download_from")
    to_date = st.date_input("To Date", today, key="download_to")

    if st.button("Download CSV"):
        df = pd.read_sql_query("""
            SELECT * FROM diesel_monitoring
            WHERE date BETWEEN ? AND ?
        """, conn, params=(from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV File", csv, "diesel_monitoring_data.csv", "text/csv")
        st.success("✅ Download prepared.")

# LAST 10 ENTRIES BLOCK
elif option == "View Last 10 Entries":
    st.header("📊 Last 10 Entries")
    tp_disp = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="disp_tp")
    dg_disp = st.selectbox("Select DG", ["DG1", "DG2"], key="disp_dg")

    df = pd.read_sql_query("""
        SELECT * FROM diesel_monitoring
        WHERE toll_plaza=? AND dg=?
        ORDER BY id DESC LIMIT 10
    """, conn, params=(tp_disp, dg_disp))

    st.dataframe(df)
