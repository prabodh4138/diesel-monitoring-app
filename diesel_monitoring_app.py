import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# Connect DB
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
c = conn.cursor()

# Create Table
c.execute('''CREATE TABLE IF NOT EXISTS diesel_monitoring (
    id INTEGER PRIMARY KEY,
    date TEXT,
    toll_plaza TEXT,
    dg TEXT,
    barrel_stock REAL,
    diesel_purchase REAL,
    diesel_topup REAL,
    updated_barrel_stock REAL,
    diesel_opening_stock REAL,
    diesel_closing_stock REAL,
    diesel_consumption REAL,
    opening_kwh REAL,
    closing_kwh REAL,
    net_kwh REAL,
    opening_rh TEXT,
    closing_rh TEXT,
    net_rh TEXT,
    md REAL,
    remarks TEXT,
    entry_time TEXT
)''')
conn.commit()

# Utility Functions
def get_last_value(toll_plaza, dg, column):
    c.execute(f"SELECT {column} FROM diesel_monitoring WHERE toll_plaza=? AND dg=? ORDER BY id DESC LIMIT 1", (toll_plaza, dg))
    result = c.fetchone()
    return float(result[0]) if result and result[0] is not None else 0.0

def get_last_barrel_stock(toll_plaza):
    c.execute("SELECT updated_barrel_stock FROM diesel_monitoring WHERE toll_plaza=? ORDER BY id DESC LIMIT 1", (toll_plaza,))
    result = c.fetchone()
    return float(result[0]) if result and result[0] is not None else 0.0

def calculate_net_rh(opening_rh, closing_rh):
    try:
        fmt = "%H:%M"
        tdelta = datetime.strptime(closing_rh, fmt) - datetime.strptime(opening_rh, fmt)
        total_seconds = tdelta.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours:02}:{minutes:02}"
    except:
        return "00:00"

# App Layout
st.title("🛠️ Diesel Monitoring App - Toll Plaza Operations")
menu = ["User Block", "Admin Block"]
choice = st.sidebar.selectbox("Go to", menu)

if choice == "Admin Block":
    st.header("🔐 Admin Initialization")
    st.info("Only for initialization and corrections.")

    tp_admin = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="tp_admin")
    dg_admin = st.selectbox("Select DG", ["DG1", "DG2"], key="dg_admin")

    barrel_stock = st.number_input("Initialize Plaza Barrel Stock (L)", min_value=0.0, step=1.0, key="barrel_stock")
    diesel_opening_stock = st.number_input("Initialize DG Opening Diesel Stock (L)", min_value=0.0, step=1.0, key="diesel_opening_stock")
    opening_kwh = st.number_input("Initialize Opening KWH", min_value=0.0, step=1.0, key="opening_kwh")
    opening_rh = st.text_input("Initialize Opening RH (HH:MM)", value="00:00", key="opening_rh")

    password = st.text_input("Enter Admin Password", type="password", key="admin_pass")

    if st.button("💾 Save Initialization", key="save_admin"):
        if password == "Sekura@2025":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('''INSERT INTO diesel_monitoring (
                date, toll_plaza, dg, barrel_stock, diesel_purchase, diesel_topup,
                updated_barrel_stock, diesel_opening_stock, diesel_closing_stock,
                diesel_consumption, opening_kwh, closing_kwh, net_kwh,
                opening_rh, closing_rh, net_rh, md, remarks, entry_time
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (now.split()[0], tp_admin, dg_admin, barrel_stock, 0, 0,
            barrel_stock, diesel_opening_stock, 0, 0, opening_kwh, 0, 0,
            opening_rh, "00:00", "00:00", 0, "Initialized by Admin", now))
            conn.commit()
            st.success("✅ Initialization saved successfully.")
        else:
            st.error("❌ Incorrect password.")

    if st.button("🔄 Refresh Admin Block", key="refresh_admin"):
        st.experimental_rerun()

if choice == "User Block":
    st.header("📝 Field Data Entry")
    date = st.date_input("Date", datetime.today(), key="date_user")
    tp_user = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="tp_user")
    dg_user = st.selectbox("Select DG", ["DG1", "DG2"], key="dg_user")

    barrel_stock_virtual = get_last_barrel_stock(tp_user)
    diesel_opening_stock_virtual = get_last_value(tp_user, dg_user, "diesel_closing_stock")
    opening_kwh_virtual = get_last_value(tp_user, dg_user, "closing_kwh")
    opening_rh_virtual = get_last_value(tp_user, dg_user, "closing_rh")

    st.info(f"**Virtual Barrel Stock:** {barrel_stock_virtual} L")
    st.info(f"**Virtual DG Opening Diesel Stock:** {diesel_opening_stock_virtual} L")
    st.info(f"**Virtual Opening KWH:** {opening_kwh_virtual} ")
    st.info(f"**Virtual Opening RH:** {opening_rh_virtual if opening_rh_virtual else '00:00'} ")

    diesel_topup = st.number_input("Diesel Top Up (L)", min_value=0.0, step=1.0)
    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=1.0)

    updated_barrel_stock = barrel_stock_virtual + diesel_purchase - diesel_topup
    st.success(f"🔄 Updated Plaza Barrel Stock: {updated_barrel_stock} L")

    closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh_virtual, step=1.0, key="closing_kwh")
    net_kwh = closing_kwh - opening_kwh_virtual
    st.success(f"⚡ Net KWH: {net_kwh}")

    closing_rh = st.text_input("Closing RH (HH:MM)", value="00:00", key="closing_rh")
    net_rh = calculate_net_rh(opening_rh_virtual if opening_rh_virtual else "00:00", closing_rh)
    st.success(f"🕒 Net RH: {net_rh}")

    diesel_closing_stock = st.number_input("Diesel Closing Stock at DG (L)", min_value=0.0, step=1.0, key="diesel_closing_stock")
    md = st.number_input("Maximum Demand", min_value=0.0, step=0.1)
    remarks = st.text_input("Remarks (Optional)")

    diesel_consumption = (diesel_opening_stock_virtual + diesel_topup) - diesel_closing_stock

    if st.button("✅ Submit Entry", key="submit_user"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO diesel_monitoring (
            date, toll_plaza, dg, barrel_stock, diesel_purchase, diesel_topup,
            updated_barrel_stock, diesel_opening_stock, diesel_closing_stock,
            diesel_consumption, opening_kwh, closing_kwh, net_kwh,
            opening_rh, closing_rh, net_rh, md, remarks, entry_time
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (date.strftime("%Y-%m-%d"), tp_user, dg_user, barrel_stock_virtual, diesel_purchase, diesel_topup,
        updated_barrel_stock, diesel_opening_stock_virtual, diesel_closing_stock,
        diesel_consumption, opening_kwh_virtual, closing_kwh, net_kwh,
        opening_rh_virtual if opening_rh_virtual else "00:00", closing_rh, net_rh, md, remarks, now))
        conn.commit()
        st.success("✅ Entry saved successfully.")

    if st.button("🔄 Refresh User Block", key="refresh_user"):
        st.experimental_rerun()

    st.subheader("📄 Last 10 Entries")
    c.execute("SELECT date, toll_plaza, dg, updated_barrel_stock, diesel_opening_stock, diesel_closing_stock, diesel_consumption, opening_kwh, closing_kwh, net_kwh, opening_rh, closing_rh, net_rh, md FROM diesel_monitoring WHERE toll_plaza=? AND dg=? ORDER BY id DESC LIMIT 10", (tp_user, dg_user))
    rows = c.fetchall()
    st.table(rows)
