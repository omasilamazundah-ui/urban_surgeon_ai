import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Urban Surgeon AI",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("🚦 Urban Surgeon AI")
st.subheader("Port Harcourt Traffic Intelligence Dashboard")

# ============================================
# LOAD HOTSPOT DATA
# ============================================

if os.path.exists("traffic_hotspots.csv"):

    df = pd.read_csv("traffic_hotspots.csv")

    # ========================================
    # METRICS
    # ========================================

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Records",
            len(df)
        )

    with col2:
        st.metric(
            "Unique Locations",
            df["location"].nunique()
        )

    with col3:

        if "congestion" in df.columns:

            avg_congestion = round(
                df["congestion"].mean(),
                2
            )

            st.metric(
                "Average Congestion",
                f"{avg_congestion}%"
            )

    # ========================================
    # TABLE
    # ========================================

    st.subheader("📊 Traffic Hotspot Data")

    st.dataframe(df)
    st.write(df["zone"].unique())
    # ============================================
# MAP VISUALIZATION
# ============================================

st.subheader("🗺️ Traffic Hotspot Map")

fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    hover_name="location",
    hover_data=["zone", "score"],
    color="score",
    size="score",
    zoom=11,
    height=600
)

fig.update_layout(
    mapbox_style="open-street-map",
    margin={"r":0,"t":0,"l":0,"b":0}
)

st.plotly_chart(fig, use_container_width=True)
    

    # ========================================
    # CONGESTION CHART
    # ========================================

if "congestion" in df.columns:

        chart = px.bar(
            df.tail(20),
            x="location",
            y="congestion",
            color="zone",
            title="Traffic Congestion Levels"
        )

        st.plotly_chart(
            chart,
            use_container_width=True
        )

