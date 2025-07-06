import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import json
import base64
 
st.set_page_config(page_title="Diesel Monitoring App", layout="centered")
 
# ---------------------------
# 1️⃣ GOOGLE SHEETS CONNECTION
# ---------------------------
 
# Decode JSON credentials from base64
encoded = st.secrets["gcp_service_account_encoded"]
decoded_json = base64.b64decode(encoded).decode("utf-8")
creds_dict = json.loads(decoded_json)
 
gc = gspread.service_account_from_dict(creds_dict)
sheet = gc.open(st.secrets["Diesel Monitoring Data"]).sheet1
 
# ---------------------------
# 2️⃣ FETCH EXISTING STOCKS
# ---------------------------
 
def fetch_initial_stocks():
    records = sheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        return df
    else:
        return pd.DataFrame(columns=[
            "Timestamp", "Date", "Toll Plaza", "DG", "Plaza Barrel Stock",
            "Diesel Stock at DG Opening", "Diesel Top Up", "Diesel Stock at Closing",
            "Opening KWH", "Closing KWH", "Opening RH", "Closing RH", "Diesel Purchase",
            "Maximum Demand", "Diesel Consumption", "Running Hours (hh:mm)"
        ])
 
df_existing = fetch_initial_stocks()
 
# ---------------------------
# 3️⃣ APP HEADER
# ---------------------------
 
st.title("⛽ Diesel Monitoring App")
 
menu = st.sidebar.radio("Select Mode", ["Field Staff Entry", "Admin Initialization"])
 
# ---------------------------
# 4️⃣ ADMIN INITIALIZATION
# ---------------------------
 
if menu == "Admin Initialization":
    st.subheader("🔑 Admin: Initialize Stocks")
 
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"])
    plaza_barrel_stock = st.number_input("Enter Plaza Barrel Stock (Liters)", min_value=0)
    dg_opening_stock = st.number_input("Enter Diesel Stock at DG Opening (Liters)", min_value=0)
 
    if st.button("Save Initialization"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")
        new_row = [
            now, today, toll_plaza, dg_name, plaza_barrel_stock,
            dg_opening_stock, "", "", "", "", "", "", "", "", "", ""
        ]
        sheet.append_row(new_row)
        st.success("✅ Initialization saved successfully to Google Sheet.")
 
# ---------------------------
# 5️⃣ FIELD STAFF ENTRY
# ---------------------------
 
elif menu == "Field Staff Entry":
    st.subheader("🛠️ Field Staff: Data Entry")
 
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    toll_plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
    dg_name = st.selectbox("Select DG", ["DG1", "DG2"])
 
    # Auto fetch latest plaza barrel stock & DG opening stock
    filtered_df = df_existing[
        (df_existing["Toll Plaza"] == toll_plaza) &
        (df_existing["DG"] == dg_name)
    ].sort_values("Timestamp", ascending=False)
 
    if not filtered_df.empty:
        last_row = filtered_df.iloc[0]
        plaza_barrel_stock = last_row["Plaza Barrel Stock"]
        dg_opening_stock = last_row["Diesel Stock at DG Opening"]
    else:
        plaza_barrel_stock = 0
        dg_opening_stock = 0
 
    st.info(f"Auto-fetched Plaza Barrel Stock: {plaza_barrel_stock} L")
    st.info(f"Auto-fetched Diesel Stock at DG Opening: {dg_opening_stock} L")
 
    diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0)
    diesel_stock_closing = st.number_input("Diesel Stock at Closing (L)", min_value=0, max_value=dg_opening_stock)
 
    opening_kwh = st.number_input("Opening KWH", min_value=0)
    closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh)
 
    opening_rh = st.number_input("Opening Running Hours", min_value=0.0, format="%.2f")
    closing_rh = st.number_input("Closing Running Hours", min_value=opening_rh, format="%.2f")
 
    diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0)
    maximum_demand = st.number_input("Maximum Demand (kVA)", min_value=0.0, format="%.2f")
 
    # Calculate virtual columns
    diesel_consumption = (diesel_top_up + dg_opening_stock) - diesel_stock_closing
    rh_diff = closing_rh - opening_rh
    rh_hours = int(rh_diff)
    rh_minutes = int(round((rh_diff - rh_hours) * 60))
    running_hours_fmt = f"{rh_hours:02d}:{rh_minutes:02d}"
 
    st.write(f"🛢️ **Calculated Diesel Consumption:** {diesel_consumption} L")
    st.write(f"⏱️ **Calculated Running Hours:** {running_hours_fmt} (hh:mm)")
 
    if st.button("Submit Data"):
        new_plaza_stock = plaza_barrel_stock - diesel_top_up + diesel_purchase
        new_row = [
            now, today, toll_plaza, dg_name, new_plaza_stock,
            dg_opening_stock, diesel_top_up, diesel_stock_closing,
            opening_kwh, closing_kwh, opening_rh, closing_rh,
            diesel_purchase, maximum_demand,
            diesel_consumption, running_hours_fmt
        ]
        sheet.append_row(new_row)
        st.success("✅ Entry submitted successfully to Google Sheet.")
 
# ---------------------------
# 6️⃣ VIEW DATA OPTION
# ---------------------------
 
with st.expander("📊 View Latest Diesel Monitoring Data"):
    st.dataframe(df_existing.tail(20))
 
