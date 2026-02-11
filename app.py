import streamlit as st
import pandas as pd

from src.menu_aggregation import analyze_menu

st.set_page_config(
    page_title="Mess Nutrition Risk Analyzer",
    layout="centered"
)

st.title("🍽️ Mess Nutrition Risk Analyzer")
st.write(
    "Upload a mess menu and analyze nutritional balance risk "
    "using trend deviation and reference-range awareness."
)

st.sidebar.header("Analysis Settings")

window = st.sidebar.selectbox(
    "Rolling Window",
    options=["day", "week", "month"],
    index=1
)

# --- File upload ---
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

        # --- Results ---
        st.metric(
            label="Nutrition Risk Score",
            value=result["risk_score"]
        )
        st.subheader("Risk Interpretation")

        if result["risk_level"] == "Low":
            st.success(f"Risk Level: {result['risk_level']}")
        elif result["risk_level"] == "Moderate":
            st.warning(f"Risk Level: {result['risk_level']}")
        else:
            st.error(f"Risk Level: {result['risk_level']}")

            st.write(result["explanation"])

        if result["risk_score"] < 30:
            st.success("Low nutrition risk – menu is stable and balanced.")
        elif result["risk_score"] < 60:
            st.warning("Moderate risk – emerging imbalance detected.")
        else:
             st.error("High risk – sustained nutritional imbalance detected.")


        st.subheader("Macro Distribution (%)")
        st.json(result["macro_pct"])
        st.bar_chart(result["macro_pct"])


        st.subheader("Detected Flags")
        if "Within reference range" in result["flags"]:
            st.success("Menu composition is within reference ranges")
        else:
            for flag in result["flags"]:
                st.warning(flag)

        st.caption(
            f"Deviation Score: {result['deviation_score']} "
            "(higher means more deviation from historical pattern)"
        )

else:
    st.info(
        "Please upload a CSV file with columns: "
        "`date`, `dish`, `quantity_g`"
    )

