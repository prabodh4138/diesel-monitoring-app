import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ---------- DB SETUP ----------
conn = sqlite3.connect('diesel_monitoring.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS diesel_data (
    date TEXT, toll_plaza TEXT, dg_name TEXT,
    plaza_barrel_stock REAL, diesel_topup REAL,
    diesel_purchase REAL, updated_plaza_barrel_stock REAL,
    opening_kwh REAL, closing_kwh REAL, net_kwh REAL,
    opening_dg_stock REAL, closing_dg_stock REAL,
    diesel_consumption REAL, opening_rh TEXT,
    closing_rh TEXT, net_rh TEXT, max_demand REAL
)
''')
conn.commit()

# ---------- ADMIN CSV ----------
admin_csv_file = "admin_data.csv"
admin_columns = [
    "Date", "Toll Plaza", "DG Name",
    "Plaza Barrel Stock", "Opening Diesel Stock at DG",
    "Opening KWH", "Opening RH"
]

if not os.path.exists(admin_csv_file):
    admin_df = pd.DataFrame(columns=admin_columns)
    admin_df.to_csv(admin_csv_file, index=False)
else:
    admin_df = pd.read_csv(admin_csv_file)

# ---------- FUNCTIONS ----------

def calculate_net_rh(opening_rh, closing_rh):
    try:
        fmt = "%H:%M"
        tdelta = datetime.strptime(closing_rh, fmt) - datetime.strptime(opening_rh, fmt)
        total_minutes = tdelta.seconds // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02}:{minutes:02}"
    except Exception:
        return "00:00"

def get_last_admin_values(toll_plaza, dg_name):
    admin_df = pd.read_csv(admin_csv_file)
    filtered = admin_df[(admin_df["Toll Plaza"] == toll_plaza) & (admin_df["DG Name"] == dg_name)]
    if not filtered.empty:
        last_entry = filtered.iloc[-1]
        return (
            last_entry["Plaza Barrel Stock"],
            last_entry["Opening Diesel Stock at DG"],
            last_entry["Opening KWH"],
            last_entry["Opening RH"]
        )
    else:
        return 0.0, 0.0, 0.0, "00:00"

# ---------- MODULES ----------

def admin_block():
    st.subheader("🛠️ Admin Initialization Block")
    password = st.text_input("Enter Admin Password", type="password")

    if password == "Sekura@2025":
        st.success("Password Correct. You can initialize data.")
        toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="admin_tp")
        dg_name = st.selectbox("Select DG", ["DG1", "DG2"], key="admin_dg")
        plaza_barrel_stock = st.number_input("Plaza Barrel Stock (L)", min_value=0.0, step=1.0)
        opening_dg_stock = st.number_input("Opening Diesel Stock at DG (L)", min_value=0.0, step=1.0)
        opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=1.0)
        opening_rh = st.text_input("Opening RH (HH:MM)", value="00:00")

        if st.button("💾 Save Initialization"):
            new_entry = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Toll Plaza": toll_plaza,
                "DG Name": dg_name,
                "Plaza Barrel Stock": plaza_barrel_stock,
                "Opening Diesel Stock at DG": opening_dg_stock,
                "Opening KWH": opening_kwh,
                "Opening RH": opening_rh
            }
            admin_df = pd.read_csv(admin_csv_file)
            admin_df = pd.concat([admin_df, pd.DataFrame([new_entry])], ignore_index=True)
            admin_df.to_csv(admin_csv_file, index=False)
            st.success("✅ Data Initialized Successfully!")
            st.experimental_rerun()
    elif password != "":
        st.error("❌ Incorrect Password")

def user_block():
    st.subheader("📲 User Entry Block")
    date = st.date_input("Select Date", datetime.today())
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"], key="user_tp")
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"], key="user_dg")

    # Get last admin data
    plaza_barrel_stock, opening_dg_stock, opening_kwh, opening_rh = get_last_admin_values(toll_plaza, dg_name)

    st.info(f"📊 Plaza Barrel Stock: {plaza_barrel_stock} L")
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
    closing_rh = st.text_input("Closing RH (HH:MM)", value="00:00")
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
        st.success("✅ Data Saved Successfully!")
        st.rerun()

def view_last_entries():
    st.subheader("📈 Last 10 Entries")
    df = pd.read_sql_query("SELECT * FROM diesel_data ORDER BY rowid DESC LIMIT 10", conn)
    st.dataframe(df)

def download_csv():
    st.subheader("⬇️ Download Full Data as CSV")
    df = pd.read_sql_query("SELECT * FROM diesel_data", conn)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "diesel_monitoring_data.csv", "text/csv")

# ---------- MAIN APP ----------
st.title("⛽ Diesel Monitoring | Toll Plaza Operations")

choice = st.sidebar.radio(
    "Choose Module",
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
