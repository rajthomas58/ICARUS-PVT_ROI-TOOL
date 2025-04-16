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
    "Los Angeles, CA": 750,
    "New York, NY": 650,
    "Chicago, IL": 640,
    "Houston, TX": 600,
    "Phoenix, AZ": 800,
    "Custom": None
}
location = st.sidebar.selectbox("Select Location", list(location_options.keys()))
annual_irradiance_default = location_options[location] if location_options[location] else 1700.0
user_irradiance = st.sidebar.number_input("Annual Solar Irradiance (kWh/m²/year)", value=annual_irradiance_default, key="irradiance_input")
system_size_kw = st.sidebar.number_input("System Size (kW)", value=5.0)
thermal_efficiency = st.sidebar.number_input("Thermal Efficiency (%)", value=50.0)
system_cost_per_w = st.sidebar.number_input("System Cost ($/W)", value=2.5)
incentive_pct = st.sidebar.slider("Incentive / Tax Credit (%)", 0, 100, 30)

st.sidebar.header("Energy Pricing & Carbon Factors")
electricity_rate = st.sidebar.number_input("Electricity Rate ($/kWh)", value=0.15)
grid_emission_factor = st.sidebar.number_input("Grid CO₂ Emission Factor (kg/kWh)", value=0.4)

st.sidebar.header("Optional: Natural Gas Replacement")
include_gas_savings = st.sidebar.checkbox("Include Natural Gas Replacement Savings?")
if include_gas_savings:
    gas_rate = st.sidebar.number_input("Natural Gas Rate ($/therm)", value=1.5)
    thermal_offset_pct = st.sidebar.slider("Thermal Load Offset by PV/T (%)", 0, 100, 70)

if st.sidebar.button("Calculate ROI"):
    st.header("Calculation Results")
    annual_irradiance_kwh_m2 = user_irradiance
    pv_output_kwh = system_size_kw * annual_irradiance_kwh_m2
    thermal_output_kwh = pv_output_kwh * (thermal_efficiency / 100)
    installation_cost = system_size_kw * 1000 * system_cost_per_w
    net_system_cost = installation_cost * (1 - incentive_pct / 100)
    electricity_savings = pv_output_kwh * electricity_rate
    gas_savings = 0
    if include_gas_savings:
        therms_saved = (thermal_output_kwh * (thermal_offset_pct / 100)) / 29.3
        gas_savings = therms_saved * gas_rate
    total_annual_savings = electricity_savings + gas_savings
    payback_period = net_system_cost / total_annual_savings if total_annual_savings else float("inf")
    co2_savings = (pv_output_kwh + thermal_output_kwh) * grid_emission_factor

    st.subheader("Summary")
    st.write(f"**Annual PV Output:** {pv_output_kwh:,.0f} kWh")
    st.write(f"**Annual Thermal Output:** {thermal_output_kwh:,.0f} kWh")
    st.write(f"**Electricity Savings:** ${electricity_savings:,.2f}")
    if include_gas_savings:
        st.write(f"**Natural Gas Savings:** ${gas_savings:,.2f}")
    st.write(f"**Total Annual Savings:** ${total_annual_savings:,.2f}")
    st.write(f"**Payback Period:** {payback_period:.1f} years")
    st.write(f"**Annual CO₂ Saved:** {co2_savings:,.0f} kg")
    # Charts
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("### Chart 1: Energy & Carbon Breakdown")
        df1 = pd.DataFrame({
            'Category': ['PV Energy (kWh)', 'Thermal Energy (kWh)', 'CO₂ Savings (kg)'],
            'Value': [pv_output_kwh, thermal_output_kwh, co2_savings]
        })
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        ax1.bar(df1['Category'], df1['Value'], color=["#1f77b4", "#ff7f0e", "#2ca02c"])
        ax1.set_ylabel("Amount")
        ax1.set_title("Energy & Carbon Breakdown")
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
        pdf.cell(200, 10, f"Electricity Savings: ${electricity_savings:,.2f}", ln=True)
        if include_gas_savings:
            pdf.cell(200, 10, f"Natural Gas Savings: ${gas_savings:,.2f}", ln=True)
        pdf.cell(200, 10, f"Total Savings: ${total_annual_savings:,.2f}", ln=True)
        pdf.cell(200, 10, f"Payback Period: {payback_period:.1f} years", ln=True)
        pdf.cell(200, 10, f"CO2 Savings: {co2_savings:,.0f} kg/year", ln=True)

        for fig in [fig1, fig2, fig3]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_temp:
                fig.savefig(img_temp.name, bbox_inches="tight")
                pdf.add_page()
                pdf.image(img_temp.name, x=10, w=190)

        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="icarus_pvt_roi_report.pdf")
# Walkthrough Demo
with st.expander("🚀 Walkthrough Demo"):
    st.markdown("""
### Step-by-Step Guide
1. Select your location
2. Enter system size, efficiency, and cost values
3. Optionally include gas savings
4. Click 'Calculate ROI'
5. View charts and metrics
6. Download your PDF report
""")

# Sidebar FAQ & Glossary
st.sidebar.header("🧭 Help")

with st.sidebar.expander("❓ FAQ"):
    st.markdown("""
**What is a PV/T system?**  
A hybrid solar panel system that produces both electricity and heat.

**What is a therm?**  
A therm is a unit of heat energy equal to 29.3 kWh.

**Why include natural gas savings?**  
If your system replaces a gas-powered water heater or boiler, you save additional fuel cost.

**What’s a good payback period?**  
Many systems break even within 5–10 years depending on incentives and energy prices.
""")

with st.sidebar.expander("📘 Glossary"):
    st.markdown("""
**System Size (kW):** The peak output of your solar system.  
**Irradiance (kWh/m²/year):** The amount of solar energy received per square meter annually.  
**Efficiency (%):** The proportion of sunlight converted to energy.  
**Grid Emissions Factor:** Average CO₂ emissions per kWh from your utility.  
**Thermal Offset:** % of your heating load displaced by thermal energy.  
**Payback Period:** Time needed to recover the initial investment via savings.  
**ROI:** Return on Investment based on lifetime cost and savings.
""")

# How It Works Section
with st.expander("📘 How It Works"):
    st.markdown("""
### Key Formulas:
- **PV Output = System Size × Irradiance**
- **Thermal Output = PV Output × Thermal Efficiency**
- **Electricity Savings = PV Output × Electricity Rate**
- **Gas Savings = (Thermal Output × Offset ÷ 29.3) × Gas Rate**
- **Total Savings = Electricity + Gas Savings**
- **Payback Period = Net Cost ÷ Annual Savings**
- **CO₂ Savings = (PV + Thermal Output) × Grid Emissions Factor**
""")
