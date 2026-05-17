import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="InfraFlow",
    layout="wide"
)

# ==================================================
# TITLE
# ==================================================

st.title("🏗 InfraFlow")

st.subheader(
    "Smart Mobility & Infrastructure Intelligence"
)

# ==================================================
# LOAD TRAFFIC DATA
# ==================================================

if os.path.exists("traffic_hotspots.csv"):

    try:

        df = pd.read_csv("traffic_hotspots.csv")

        # ==========================================
        # SYSTEM METRICS
        # ==========================================

        st.subheader("📈 System Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Total Records",
                len(df)
            )

        with col2:

            if "zone" in df.columns:

                st.metric(
                    "Zones Monitored",
                    df["zone"].nunique()
                )

        with col3:

            if "timestamp" in df.columns:

                st.metric(
                    "Latest Update",
                    str(df["timestamp"].iloc[-1])
                )

        # ==========================================
        # LIVE HOTSPOT TABLE
        # ==========================================

        st.subheader("📊 Live Traffic Hotspots")

        st.dataframe(df)

        # ==========================================
        # LIVE HOTSPOT MAP
        # ==========================================

        st.subheader("🗺 Live Hotspot Map")

        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            hover_name="location",
            hover_data=["zone", "score"],
            color="zone",
            size="score",
            zoom=10,
            height=650
        )

        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0, "t":0, "l":0, "b":0}
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ==========================================
        # CONGESTION ANALYSIS
        # ==========================================

        if "congestion" in df.columns:

            st.subheader("🚦 Congestion Analysis")

            congestion_chart = px.bar(
                df,
                x="location",
                y="congestion",
                color="zone",
                title="Traffic Congestion Levels"
            )

            st.plotly_chart(
                congestion_chart,
                use_container_width=True
            )

        # ==========================================
        # FUTURE GRAPH INTELLIGENCE
        # ==========================================

        st.subheader(
            "🧠 Directed Weighted Graph Intelligence"
        )

        st.info(
            "Future congestion-aware graph analysis "
            "and weighted routing intelligence "
            "will appear here after sufficient "
            "data accumulation."
        )

        # ==========================================
        # FUTURE ROUTE OPTIMIZATION
        # ==========================================

        st.subheader(
            "🚗 Route Optimization Engine"
        )

        st.info(
            "Future shortest-path routing, "
            "rerouting intelligence, and "
            "dynamic traffic optimization "
            "will appear here."
        )

        # ==========================================
        # FUTURE INFRASTRUCTURE RECOMMENDATIONS
        # ==========================================

        st.subheader(
            "🏗 Infrastructure Recommendation Engine"
        )

        st.info(
            "Future infrastructure recommendations "
            "based on persistent congestion "
            "patterns and weighted graph analysis "
            "will appear here."
        )

    except Exception as e:

        st.error(f"System Error: {e}")

else:

    st.warning(
        "traffic_hotspots.csv not found."
    )