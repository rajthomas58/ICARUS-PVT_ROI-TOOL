import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile

class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Disclaimer: This ROI Calculator is for estimation purposes only. Please contact Icarus RT for more details.", 0, 0, "C")

st.set_page_config(page_title="ICARUS PV/T ROI Calculator", layout="wide")
st.markdown("<h1 style='text-align: center;'>ICARUS PV/T ROI Calculator</h1>", unsafe_allow_html=True)

# Sidebar Inputs
st.sidebar.header("System Configuration")
location_options = {
    "Los Angeles, CA": 1750,
    "New York, NY": 1500,
    "Chicago, IL": 1400,
    "Houston, TX": 1600,
    "Phoenix, AZ": 1800,
    "Custom": None,
}
location = st.sidebar.selectbox("Select Location", list(location_options.keys()))
annual_irradiance_default = location_options.get(location) or 1700.0
user_irradiance = st.sidebar.number_input(
    "Annual Solar Irradiance (kWh/m²/year)",
    value=annual_irradiance_default,
    key="irradiance_input"
)
system_size_kw = st.sidebar.number_input("System Size (kW)", value=5.0)
pv_boost_pct = st.sidebar.number_input("PV Boost (%)", value=0.0)
thermal_efficiency = st.sidebar.number_input("Thermal Efficiency (%)", value=50.0)
system_cost_per_w = st.sidebar.number_input("System Cost ($/W)", value=2.5)
incentive_pct = st.sidebar.slider("Incentive / Tax Credit (%)", 0, 100, 30)

water_temp_in = st.sidebar.number_input("Water In Temperature (°F)", value=60.0)
water_temp_out = st.sidebar.number_input("Water Out Temperature (°F)", value=120.0)

electricity_rate = st.sidebar.number_input("Electricity Rate ($/kWh)", value=0.15)
grid_emission_factor = st.sidebar.number_input("Grid CO₂ Emission Factor (kg/kWh)", value=0.4)

st.sidebar.header("Optional: Natural Gas Replacement")
include_gas_savings = st.sidebar.checkbox("Include Natural Gas Replacement Savings?")
if include_gas_savings:
    gas_rate = st.sidebar.number_input("Natural Gas Rate ($/MMBTU)", value=8.0)
    thermal_offset_pct = st.sidebar.slider("Thermal Load Offset by PV/T (%)", 0, 100, 70)

# Calculate and display when button is clicked
if st.sidebar.button("Calculate ROI"):
    # Calculations
    annual_irradiance_kwh_m2 = user_irradiance
    pv_output_kwh = system_size_kw * annual_irradiance_kwh_m2 * (1 + pv_boost_pct / 100)
    thermal_output_kwh = pv_output_kwh * (thermal_efficiency / 100)

    hot_water_gallons = 0
    if water_temp_out > water_temp_in:
        hot_water_gallons = (thermal_output_kwh * 3412) / (8.34 * (water_temp_out - water_temp_in))

    installation_cost = system_size_kw * 1000 * system_cost_per_w
    net_system_cost = installation_cost * (1 - incentive_pct / 100)

    electricity_savings = pv_ou
