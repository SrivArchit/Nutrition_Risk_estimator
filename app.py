import streamlit as st
import pandas as pd

from src.menu_aggregation import analyze_menu

# Page Configuration
st.set_page_config(
    page_title="Mess Nutrition Risk Analyzer",
    layout="centered"
)

st.title("🍽️ Mess Nutrition Risk Analyzer")
st.write(
    "Upload a mess menu and analyze nutritional balance risk "
    "using macro deviation and reference-range awareness."
)

# Sidebar Settings
st.sidebar.header("Analysis Settings")

window = st.sidebar.selectbox(
    "Rolling Window",
    options=["day", "week", "month"],
    index=1
)

# -------------------------------
# File Upload
# -------------------------------
uploaded_file = st.file_uploader(
    "Upload Mess Menu CSV",
    type=["csv"]
)

if uploaded_file:
    menu_df = pd.read_csv(uploaded_file)

    st.subheader("Uploaded Menu Preview")
    st.dataframe(menu_df.head())

    if st.button("Analyze Menu"):

        with st.spinner("Analyzing nutrition risk..."):
            result = analyze_menu(menu_df, window=window)

        st.success("Analysis complete")

        # Risk Score Section
        st.subheader("Nutrition Risk Score")

        st.metric(
            label="Risk Score (1–100)",
            value=result["risk_score"]
        )

        st.progress(min(result["risk_score"], 100) / 100)

        # Risk Interpretation
        st.subheader("Risk Interpretation")

        if result["risk_level"] == "Low":
            st.success(f"Risk Level: {result['risk_level']}")
            st.success("Low nutrition risk – menu is stable and balanced.")

        elif result["risk_level"] == "Moderate":
            st.warning(f"Risk Level: {result['risk_level']}")
            st.warning("Moderate risk – emerging nutritional imbalance detected.")

        else:
            st.error(f"Risk Level: {result['risk_level']}")
            st.error("High risk – sustained nutritional imbalance detected.")

        # Always show explanation
        st.write(result["explanation"])

        # Macro Distribution
        st.subheader("Macro Distribution (%)")

        macro_df = pd.DataFrame(
            result["macro_pct"].items(),
            columns=["Macro", "Percentage"]
        )

        st.bar_chart(macro_df.set_index("Macro"))

        # Flags Section
        st.subheader("Detected Flags")

        if "Within reference range" in result["flags"]:
            st.success("Menu composition is within recommended reference ranges.")
        else:
            for flag in result["flags"]:
                st.warning(flag)

        # Deviation Info
        st.caption(
            f"Deviation Score: {result['deviation_score']} "
            "(Higher values indicate greater deviation from recommended macro balance)"
        )

else:
    st.info(
        "Please upload a CSV file with columns: "
        "`date`, `dish`, `quantity_g`"
    )
