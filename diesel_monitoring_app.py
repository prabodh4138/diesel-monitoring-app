import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ---------------- Database Setup ---------------- #
conn = sqlite3.connect("diesel_monitoring.db", check_same_thread=False)
c = conn.cursor()

# Table creation
c.execute('''CREATE TABLE IF NOT EXISTS diesel_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    date TEXT,
    toll_plaza TEXT,
    dg TEXT,
    plaza_barrel_stock REAL,
    diesel_purchase REAL,
    diesel_topup REAL,
    updated_plaza_barrel_stock REAL,
    dg_opening_stock REAL,
    diesel_closing_stock REAL,
    diesel_consumption REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    net_kwh REAL,
    opening_rh TEXT,
    closing_rh TEXT,
    net_rh TEXT,
    maximum_demand REAL
)''')

c.execute('''CREATE TABLE IF NOT EXISTS admin_init (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    toll_plaza TEXT,
    dg TEXT,
    plaza_barrel_stock REAL,
    dg_opening_stock REAL,
    opening_kwh REAL,
    opening_rh TEXT
)''')
conn.commit()

# ---------------- Utility Functions ---------------- #
def calculate_net_rh(opening_rh, closing_rh):
    fmt = "%H:%M"
    try:
        tdelta = datetime.strptime(closing_rh, fmt) - datetime.strptime(opening_rh, fmt)
        if tdelta.days < 0:
            tdelta += timedelta(days=1)
        total_minutes = tdelta.total_seconds() // 60
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return f"{hours:02d}:{minutes:02d}"
    except:
        return "00:00"

def get_admin_init(tp, dg):
    c.execute("SELECT plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh FROM admin_init WHERE toll_plaza=? AND dg=?",(tp, dg))
    return c.fetchone()

def get_last_reading(tp, dg):
    c.execute("SELECT * FROM diesel_monitoring WHERE toll_plaza=? AND dg=? ORDER BY id DESC LIMIT 1", (tp, dg))
    return c.fetchone()

# ---------------- Streamlit UI ---------------- #
st.title("⛽ Diesel Monitoring App - Toll Operations")

menu = ["Admin Block", "User Block", "Download CSV", "View Last 10 Records"]
choice = st.sidebar.selectbox("Select Action", menu)

# ---------------- Admin Block ---------------- #
if choice == "Admin Block":
    st.header("🛠️ Admin Initialization (Secured)")
    password = st.text_input("Enter Admin Password", type="password")
    if password == "Sekura@2025":
        st.success("Password Verified ✅")

        col1, col2 = st.columns(2)
        with col1:
            toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
        with col2:
            dg = st.selectbox("Select DG", ["DG1", "DG2"])

        col3, col4 = st.columns(2)
        with col3:
            plaza_barrel_stock = st.number_input("Plaza Barrel Stock (L)", min_value=0.0, step=1.0)
        with col4:
            dg_opening_stock = st.number_input("DG Opening Diesel Stock (L)", min_value=0.0, step=1.0)

        col5, col6 = st.columns(2)
        with col5:
            opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=1.0)
        with col6:
            opening_rh = st.text_input("Opening RH (HH:MM)", value="00:00")

        if st.button("💾 Save Initialization"):
            c.execute("SELECT id FROM admin_init WHERE toll_plaza=? AND dg=?", (toll_plaza, dg))
            exists = c.fetchone()
            if exists:
                c.execute("""UPDATE admin_init SET plaza_barrel_stock=?, dg_opening_stock=?, opening_kwh=?, opening_rh=?
                             WHERE toll_plaza=? AND dg=?""",
                          (plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh, toll_plaza, dg))
            else:
                c.execute("""INSERT INTO admin_init (toll_plaza, dg, plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh)
                             VALUES (?, ?, ?, ?, ?, ?)""",
                          (toll_plaza, dg, plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh))
            conn.commit()
            st.success("✅ Initialization Saved & Synced for Users.")
    elif password != "":
        st.error("❌ Incorrect Password")

# ---------------- User Block ---------------- #
elif choice == "User Block":
    st.header("📋 User Data Entry Block")
    date = st.date_input("Select Date", datetime.today())
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="user_tp")
    dg = st.selectbox("Select DG", ["DG1", "DG2"], key="user_dg")

    admin_data = get_admin_init(toll_plaza, dg)
    if admin_data:
        plaza_barrel_stock, dg_opening_stock, opening_kwh, opening_rh = admin_data
    else:
        plaza_barrel_stock = dg_opening_stock = opening_kwh = 0.0
        opening_rh = "00:00"

    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=1.0)
    diesel_topup = st.number_input("Diesel Top-Up (L)", min_value=0.0, step=1.0)
    updated_plaza_barrel_stock = plaza_barrel_stock + diesel_purchase - diesel_topup
    st.info(f"Updated Plaza Barrel Stock: {updated_plaza_barrel_stock} L")

    st.markdown("---")
    st.markdown("### DG Meter Readings")

    st.write(f"Opening KWH (auto): `{opening_kwh}`")
    closing_kwh = st.number_input("Closing KWH (mandatory, ≥ Opening)", min_value=opening_kwh, step=1.0)
    net_kwh = closing_kwh - opening_kwh
    st.success(f"Net KWH: {net_kwh}")

    st.write(f"Opening RH (auto): `{opening_rh}`")
    closing_rh = st.text_input("Closing RH (HH:MM, mandatory)")
    net_rh = calculate_net_rh(opening_rh, closing_rh)
    st.success(f"Net RH: {net_rh}")

    diesel_closing_stock = st.number_input("Diesel Closing Stock at DG (mandatory, L)", min_value=0.0, step=1.0)
    diesel_consumption = (dg_opening_stock + diesel_topup) - diesel_closing_stock
    st.success(f"Diesel Consumption: {diesel_consumption} L")

    maximum_demand = st.number_input("Maximum Demand", min_value=0.0, step=0.1)

    if st.button("✅ Submit Entry"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO diesel_monitoring (
                        timestamp, date, toll_plaza, dg, plaza_barrel_stock, diesel_purchase, diesel_topup,
                        updated_plaza_barrel_stock, dg_opening_stock, diesel_closing_stock, diesel_consumption,
                        opening_kwh, closing_kwh, net_kwh, opening_rh, closing_rh, net_rh, maximum_demand
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (timestamp, date.strftime("%Y-%m-%d"), toll_plaza, dg, plaza_barrel_stock, diesel_purchase, diesel_topup,
                   updated_plaza_barrel_stock, dg_opening_stock, diesel_closing_stock, diesel_consumption,
                   opening_kwh, closing_kwh, net_kwh, opening_rh, closing_rh, net_rh, maximum_demand))
        conn.commit()
        st.success("✅ Entry Saved Successfully")

# ---------------- CSV Download ---------------- #
elif choice == "Download CSV":
    st.header("📥 Download All Diesel Monitoring Data")
    df = pd.read_sql_query("SELECT * FROM diesel_monitoring", conn)
    st.dataframe(df.tail(10))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Full CSV",
        csv,
        "diesel_monitoring_full.csv",
        "text/csv",
        key='download-csv'
    )

# ---------------- View Last 10 Records ---------------- #
elif choice == "View Last 10 Records":
    st.header("📊 Last 10 Records (Toll Plaza & DG Wise)")

    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="view_tp")
    dg = st.selectbox("Select DG", ["DG1", "DG2"], key="view_dg")

    df = pd.read_sql_query(
        "SELECT * FROM diesel_monitoring WHERE toll_plaza=? AND dg=? ORDER BY id DESC LIMIT 10",
        conn,
        params=(toll_plaza, dg)
    )
    st.dataframe(df)
