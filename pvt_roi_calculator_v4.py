import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

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
annual_irradiance_default = location_options[location] if location_options[location] else 1700.0
user_irradiance = st.sidebar.number_input("Annual Solar Irradiance (kWh/m²/year)", value=annual_irradiance_default, key="irradiance_input")
system_size_kw = st.sidebar.number_input("System Size (kW)", value=5.0)
pv_boost_pct = st.sidebar.number_input("PV Boost (%)", value=0.0)
thermal_efficiency = st.sidebar.number_input("Thermal Efficiency (%)", value=50.0)
system_cost_per_w = st.sidebar.number_input("System Cost ($/W)", value=2.5)
incentive_pct = st.sidebar.slider("Incentive / Tax Credit (%)", 0, 100, 30)

water_temp_in = st.sidebar.number_input("Water In Temperature (°F)", value=60.0)
water_temp_out = st.sidebar.number_input("Water Out Temperature (°F)", value=120.0)

electricity_rate = st.sidebar.number_input("Electricity Rate ($/kWh)", value=0.15)
grid_emission_factor = st.sidebar.number_input("Grid CO2 Emission Factor (kg/kWh)", value=0.4)

st.sidebar.header("Optional: Natural Gas Replacement")
include_gas_savings = st.sidebar.checkbox("Include Natural Gas Replacement Savings?")
if include_gas_savings:
    gas_rate = st.sidebar.number_input("Natural Gas Rate ($/MMBTU)", value=8.0)
    thermal_offset_pct = st.sidebar.slider("Thermal Load Offset by PV/T (%)", 0, 100, 70)

if st.sidebar.button("Calculate ROI"):
    st.header("Calculation Results")
    annual_irradiance_kwh_m2 = user_irradiance
    pv_output_kwh = system_size_kw * annual_irradiance_kwh_m2
    pv_output_kwh *= (1 + pv_boost_pct / 100)
    thermal_output_kwh = pv_output_kwh * (thermal_efficiency / 100)
    
    # Hot water gallons calculation
    if water_temp_out > water_temp_in:
        hot_water_gallons = (thermal_output_kwh * 3412) / (8.34 * (water_temp_out - water_temp_in))
    else:
        hot_water_gallons = 0

    installation_cost = system_size_kw * 1000 * system_cost_per_w
    net_system_cost = installation_cost * (1 - incentive_pct / 100)

    electricity_savings = pv_output_kwh * electricity_rate
    gas_savings = 0
    if include_gas_savings:
        mmbtu_saved = (thermal_output_kwh * (thermal_offset_pct / 100)) / 3412
        gas_savings = mmbtu_saved * gas_rate

    total_annual_savings = electricity_savings + gas_savings
    payback_period = net_system_cost / total_annual_savings if total_annual_savings else float("inf")
    co2_savings_kg = (pv_output_kwh + thermal_output_kwh) * grid_emission_factor
    co2_savings_ton = co2_savings_kg / 1000

    st.subheader("Summary")
    st.write(f"**Annual PV Output:** {pv_output_kwh:,.0f} kWh")
    st.write(f"**Annual Thermal Output:** {thermal_output_kwh:,.0f} kWh")
    st.write(f"**Hot Water Generated:** {hot_water_gallons:,.0f} gallons")
    st.write(f"**Electricity Savings:** ${electricity_savings:,.2f}")
    if include_gas_savings:
        st.write(f"**Natural Gas Savings:** ${gas_savings:,.2f}")
    st.write(f"**Total Annual Savings:** ${total_annual_savings:,.2f}")
    st.write(f"**Payback Period:** {payback_period:.1f} years")
    st.write(f"**Annual CO2 Saved:** {co2_savings_ton:,.2f} metric tons")

    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("### Chart 1: Energy, Water & Carbon")
        df1 = pd.DataFrame({
            'Category': ['PV Energy (kWh)', 'Thermal Energy (kWh)', 'Hot Water (gal)', 'CO2 Savings (tons)'],
            'Value': [pv_output_kwh, thermal_output_kwh, hot_water_gallons, co2_savings_ton]
        })
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        ax1.bar(df1['Category'], df1['Value'], color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])
        ax1.set_ylabel("Amount")
        ax1.set_title("Energy, Water & Carbon Breakdown")
        st.pyplot(fig1)

    with chart2:
        st.markdown("### Chart 2: Annual Savings Breakdown")
        df2 = pd.DataFrame({
            'Type': ['Electricity Savings ($)', 'Gas Savings ($)'],
            'Value': [electricity_savings, gas_savings if include_gas_savings else 0]
        })
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        ax2.bar(df2['Type'], df2['Value'], color=["#4daf4a", "#984ea3"])
        ax2.set_ylabel("Savings ($)")
        ax2.set_title("Annual Savings Breakdown")
        st.pyplot(fig2)

    st.markdown("### Chart 3: Cumulative Cash Flow Over 25 Years")
    years = np.arange(1, 26)
    cumulative_cash_flow = np.cumsum([total_annual_savings] * 25) - net_system_cost
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.plot(years, cumulative_cash_flow, marker='o')
    ax3.axhline(0, color='gray', linestyle='--')
    if payback_period != float("inf") and 1 <= payback_period <= 25:
        ax3.axvline(x=payback_period, color='red', linestyle=':', label=f"Payback: {payback_period:.1f} yrs")
        ax3.legend()
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Cumulative Cash Flow ($)")
    ax3.set_title("Cumulative Cash Flow Over 25 Years")
    ax3.grid(True)
    st.pyplot(fig3)

    # PDF Export
    st.markdown("### 📄 Download PDF Report")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "ICARUS PV/T ROI Report", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.ln(5)
        pdf.cell(200, 10, f"Location: {location}", ln=True)
        pdf.cell(200, 10, f"System Size: {system_size_kw} kW", ln=True)
        pdf.cell(200, 10, f"Annual PV Output: {pv_output_kwh:,.0f} kWh", ln=True)
        pdf.cell(200, 10, f"Annual Thermal Output: {thermal_output_kwh:,.0f} kWh", ln=True)
        pdf.cell(200, 10, f"Hot Water Generated: {hot_water_gallons:,.0f} gallons", ln=True)
        pdf.cell(200, 10, f"Electricity Savings: ${electricity_savings:,.2f}", ln=True)
        if include_gas_savings:
            pdf.cell(200, 10, f"Natural Gas Savings: ${gas_savings:,.2f}", ln=True)
        pdf.cell(200, 10, f"Total Savings: ${total_annual_savings:,.2f}", ln=True)
        pdf.cell(200, 10, f"Payback Period: {payback_period:.1f} years", ln=True)
        pdf.cell(200, 10, f"CO2 Savings: {co2_savings_ton:,.2f} metric tons", ln=True)

        for fig in [fig1, fig2, fig3]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_temp:
                fig.savefig(img_temp.name, bbox_inches="tight")
                pdf.add_page()
                pdf.image(img_temp.name, x=10, w=190)

        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="icarus_pvt_roi_report.pdf")
