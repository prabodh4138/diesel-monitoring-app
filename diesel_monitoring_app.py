import streamlit as st
import pandas as pd
from datetime import datetime
 
# Load or Initialize Plaza Barrel Stock
try:
    stock_df = pd.read_csv("plaza_barrel_stock.csv", index_col=0)
except FileNotFoundError:
    stock_df = pd.DataFrame({
        "Toll Plaza": ["TP01", "TP02", "TP03"],
        "BarrelStock": [500, 450, 400]
    }).set_index("Toll Plaza")
    stock_df.to_csv("plaza_barrel_stock.csv")
 
# Load or Initialize DG Opening Stock
try:
    dg_df = pd.read_csv("dg_opening_stock.csv", index_col=[0,1])
except FileNotFoundError:
    idx = pd.MultiIndex.from_tuples([
        ("TP01", "DG1"), ("TP01", "DG2"),
        ("TP02", "DG1"), ("TP02", "DG2"),
        ("TP03", "DG1"), ("TP03", "DG2")
    ], names=["Toll Plaza", "DG"])
    dg_df = pd.DataFrame({"DG_Opening_Stock": [200, 180, 190, 170, 185, 165]}, index=idx)
    dg_df.to_csv("dg_opening_stock.csv")
 
st.title("🛢️ Diesel Monitoring App (Developer + User)")
 
# Developer/Admin Panel
if st.checkbox("🛠️ Developer: Update Plaza Barrel & DG Opening Stock"):
    st.subheader("Update Plaza Barrel Stock")
    for plaza in stock_df.index:
        new_value = st.number_input(f"{plaza} Barrel Stock (L)", min_value=0.0, step=1.0, value=float(stock_df.loc[plaza, "BarrelStock"]))
        stock_df.loc[plaza, "BarrelStock"] = new_value
 
    st.subheader("Update DG Opening Diesel Stock")
    for (plaza, dg) in dg_df.index:
        current_value = float(dg_df.loc[(plaza, dg), "DG_Opening_Stock"])
        new_dg_value = st.number_input(f"{plaza} - {dg} Opening Diesel Stock (L)", min_value=0.0, step=1.0, value=current_value)
        dg_df.loc[(plaza, dg), "DG_Opening_Stock"] = new_dg_value
 
    if st.button("Save Developer Updates"):
        stock_df.to_csv("plaza_barrel_stock.csv")
        dg_df.to_csv("dg_opening_stock.csv")
        st.success("✅ Developer data saved successfully!")
 
st.header("📋 Diesel Monitoring Entry")
 
# Timestamp
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"**Timestamp:** {timestamp}")
 
# Date
date = st.date_input("Select Date")
 
# Toll Plaza
plaza = st.selectbox("Select Toll Plaza", options=stock_df.index)
 
# DG Selection
dg_options = ["DG1", "DG2"]
dg = st.selectbox("Select DG", options=dg_options)
 
# Auto Fetch Plaza Barrel Stock
barrel_stock = stock_df.loc[plaza, "BarrelStock"]
st.info(f"Current Plaza Barrel Stock: {barrel_stock} L")
 
# Auto Fetch DG Opening Stock
dg_opening_stock = dg_df.loc[(plaza, dg), "DG_Opening_Stock"]
st.info(f"DG Opening Diesel Stock: {dg_opening_stock} L")
 
# User Inputs
diesel_top_up = st.number_input("Diesel Top Up (L)", min_value=0.0, step=0.1)
diesel_closing_stock = st.number_input("Diesel Closing Stock (L)", min_value=0.0, max_value=dg_opening_stock + diesel_top_up, step=0.1)
 
opening_kwh = st.number_input("Opening KWH", min_value=0.0, step=0.1)
closing_kwh = st.number_input("Closing KWH", min_value=opening_kwh, step=0.1)
 
opening_rh = st.number_input("Opening Running Hours", min_value=0.0, step=0.01)
closing_rh = st.number_input("Closing Running Hours", min_value=opening_rh, step=0.01)
 
diesel_purchase = st.number_input("Diesel Purchase (L)", min_value=0.0, step=0.1)
max_demand = st.number_input("Maximum Demand (kW)", min_value=0.0, step=0.1)
 
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
 
# Submit Entry
if st.button("Submit Entry"):
    if diesel_closing_stock > dg_opening_stock + diesel_top_up:
        st.error("Closing Diesel Stock cannot exceed Opening Stock + Top Up.")
    elif closing_kwh < opening_kwh:
        st.error("Closing KWH must be >= Opening KWH.")
    elif closing_rh < opening_rh:
        st.error("Closing RH must be >= Opening RH.")
    else:
        # Prepare record
        record = {
            "Timestamp": timestamp,
            "Date": date,
            "Toll Plaza": plaza,
            "DG": dg,
            "Plaza Barrel Stock (prev)": barrel_stock,
            "DG Opening Diesel Stock": dg_opening_stock,
            "Diesel Top Up": diesel_top_up,
            "Diesel Closing Stock": diesel_closing_stock,
            "Opening KWH": opening_kwh,
            "Closing KWH": closing_kwh,
            "Opening RH": opening_rh,
            "Closing RH": closing_rh,
            "Diesel Purchase": diesel_purchase,
            "Maximum Demand": max_demand,
            "Diesel Consumption": diesel_consumption,
            "Running Hours": running_hours_formatted,
            "Plaza Barrel Stock (new)": new_barrel_stock
        }
        # Save entry
        try:
            df = pd.read_csv("diesel_monitoring_records.csv")
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([record])
        df.to_csv("diesel_monitoring_records.csv", index=False)
 
        # Update barrel stock persistently
        stock_df.loc[plaza, "BarrelStock"] = new_barrel_stock
        stock_df.to_csv("plaza_barrel_stock.csv")
 
        st.success("✅ Entry saved and barrel stock updated successfully!")
 
# Show Records
if st.checkbox("📑 Show Existing Records"):
    try:
        df = pd.read_csv("diesel_monitoring_records.csv")
        st.dataframe(df)
    except FileNotFoundError:
        st.info("No records found yet.")
 
