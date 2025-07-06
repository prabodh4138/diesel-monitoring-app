      import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
 
# Authenticate with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
 
# Open your Google Sheet
sheet = client.open(st.secrets["sheet_name"]).sheet1
 
st.title("🛢️ Diesel Monitoring App (Google Sheets Integrated)")
 
# Timestamp
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"**Timestamp:** {timestamp}")
 
# Date
date = st.date_input("Select Date")
 
# Toll Plaza
plazas = ["TP01", "TP02", "TP03"]
plaza = st.selectbox("Select Toll Plaza", options=plazas)
 
# DG
dg_options = ["DG1", "DG2"]
dg = st.selectbox("Select DG", options=dg_options)
 
# Plaza Barrel Stock (prev)
barrel_stock = st.number_input("Plaza Barrel Stock (Previous) - L", min_value=0.0, step=1.0)
 
# DG Opening Diesel Stock
dg_opening_stock = st.number_input("DG Opening Diesel Stock - L", min_value=0.0, step=0.1)
 
# Diesel Top Up
diesel_top_up = st.number_input("Diesel Top Up - L", min_value=0.0, step=0.1)
 
# Diesel Closing Stock
diesel_closing_stock = st.number_input("Diesel Closing Stock - L", min_value=0.0, max_value=dg_opening_stock + diesel_top_up, step=0.1)
 
# Opening KWH
opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=0.1)
 
# Closing KWH
closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh, step=0.1)
 
# Opening RH
opening_rh = st.number_input("Opening Running Hours", min_value=0.0, step=0.01)
 
# Closing RH
closing_rh = st.number_input("Closing Running Hours", min_value=opening_rh, step=0.01)
 
# Diesel Purchase
diesel_purchase = st.number_input("Diesel Purchase - L", min_value=0.0, step=0.1)
 
# Maximum Demand
max_demand = st.number_input("Maximum Demand - kW", min_value=0.0, step=0.1)
 
# Calculations
diesel_consumption = diesel_top_up + dg_opening_stock - diesel_closing_stock
rh_diff = closing_rh - opening_rh
hours = int(rh_diff)
minutes = int(round((rh_diff - hours) * 60))
running_hours_formatted = f"{hours} hr {minutes} min"
 
new_barrel_stock = barrel_stock - diesel_top_up + diesel_purchase
 
st.success(f"Diesel Consumption: {diesel_consumption:.2f} L")
st.success(f"Running Hours: {running_hours_formatted}")
st.info(f"New Plaza Barrel Stock (virtual): {new_barrel_stock:.2f} L")
 
if st.button("Submit Entry"):
    if diesel_closing_stock > dg_opening_stock + diesel_top_up:
        st.error("❌ Closing Diesel Stock cannot exceed Opening Stock + Top Up.")
    elif closing_kwh < opening_kwh:
        st.error("❌ Closing KWH must be greater than or equal to Opening KWH.")
    elif closing_rh < opening_rh:
        st.error("❌ Closing RH must be greater than or equal to Opening RH.")
    else:
        row = [
            timestamp,
            str(date),
            plaza,
            dg,
            barrel_stock,
            dg_opening_stock,
            diesel_top_up,
            diesel_closing_stock,
            opening_kwh,
            closing_kwh,
            opening_rh,
            closing_rh,
            diesel_purchase,
            max_demand,
            diesel_consumption,
            running_hours_formatted,
            new_barrel_stock
        ]
        sheet.append_row(row)
        st.success("✅ Entry successfully submitted to Google Sheets!")
 
if st.checkbox("📄 Show Existing Records"):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    st.dataframe(df)
 
