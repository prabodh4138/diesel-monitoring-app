import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
 
# ---------------- Google Sheets Authentication ---------------- #
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
 
sheet_main = client.open(st.secrets["sheet_name"]).sheet1
sheet_init = client.open(st.secrets["sheet_name"]).worksheet("AdminInit")
 
# ---------------- Fetch Initialization Data ---------------- #
init_records = sheet_init.get_all_records()
init_df = pd.DataFrame(init_records)
 
# ---------------- UI ---------------- #
st.title("🛢️ Diesel Monitoring App")
 
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"**Timestamp:** {timestamp}")
 
date = st.date_input("Select Date")
plaza = st.selectbox("Select Toll Plaza", ["TP01", "TP02", "TP03"])
dg = st.selectbox("Select DG", ["DG1", "DG2"])
 
# Fetch initialized stocks
init_row = init_df[(init_df["Plaza"] == plaza) & (init_df["DG"] == dg)]
if not init_row.empty:
    init_barrel_stock = float(init_row["Plaza Barrel Stock"].values[0])
    init_dg_stock = float(init_row["DG Opening Diesel Stock"].values[0])
else:
    init_barrel_stock = 0.0
    init_dg_stock = 0.0
 
barrel_stock_prev = st.number_input("Plaza Barrel Stock (Auto/Editable)", min_value=0.0, step=0.1, value=init_barrel_stock)
dg_opening_stock = st.number_input("DG Opening Diesel Stock (Auto/Editable)", min_value=0.0, step=0.1, value=init_dg_stock)
 
diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0.0, step=0.1)
diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=0.1)
diesel_closing_stock = st.number_input("Diesel Closing Stock (L)", min_value=0.0, step=0.1)
 
opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=0.1)
closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh, step=0.1)
 
opening_rh = st.number_input("Opening Running Hours", min_value=0.0, step=0.01)
closing_rh = st.number_input("Closing Running Hours", min_value=opening_rh, step=0.01)
 
max_demand = st.number_input("Maximum Demand (kW)", min_value=0.0, step=0.1)
 
# ---------------- Calculations ---------------- #
diesel_consumption = diesel_top_up + dg_opening_stock - diesel_closing_stock
rh_diff = closing_rh - opening_rh
hours = int(rh_diff)
minutes = int(round((rh_diff - hours) * 60))
running_hours_formatted = f"{hours} hr {minutes} min"
new_barrel_stock = barrel_stock_prev - diesel_top_up + diesel_purchase
 
# Display Calculations
st.success(f"Diesel Consumption: {diesel_consumption:.2f} L")
st.success(f"Running Hours: {running_hours_formatted}")
st.info(f"New Plaza Barrel Stock: {new_barrel_stock:.2f} L")
 
# ---------------- Submit Button ---------------- #
if st.button("Submit Diesel Monitoring Data"):
    if diesel_closing_stock > dg_opening_stock + diesel_top_up:
        st.error("❌ Closing Diesel Stock cannot exceed Opening + Top Up.")
    elif closing_kwh < opening_kwh:
        st.error("❌ Closing KWH must be greater than or equal to Opening KWH.")
    elif closing_rh < opening_rh:
        st.error("❌ Closing Running Hours must be greater than or equal to Opening Running Hours.")
    else:
        new_row = [
            timestamp, str(date), plaza, dg, barrel_stock_prev,
            dg_opening_stock, diesel_top_up, diesel_closing_stock,
            opening_kwh, closing_kwh, opening_rh, closing_rh,
            diesel_purchase, max_demand, diesel_consumption,
            running_hours_formatted, new_barrel_stock
        ]
        sheet_main.append_row(new_row)
        st.success("✅ Data submitted successfully to Google Sheets!")
 
# ---------------- View Existing Records ---------------- #
if st.checkbox("📄 Show Existing Records"):
    records = sheet_main.get_all_records()
    df = pd.DataFrame(records)
    st.dataframe(df)
 
