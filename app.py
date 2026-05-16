import streamlit as st
import osmnx as ox
import networkx as nx
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="urban_surgeon_ai")
# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="Urban Surgeon AI",
    layout="wide"
)

st.title("🏙️ Urban Surgeon AI")
st.write("Interactive Traffic Hotspot Mapping System")

# =====================================
# ZONES
# =====================================
zones = {
    "Port Harcourt": "Port Harcourt, Rivers State, Nigeria",
    "Obio/Akpor": "Obio-Akpor, Rivers State, Nigeria"
}

# =====================================
# SELECT ZONE
# =====================================
selected_zone = st.selectbox(
    "Select Zone",
    list(zones.keys())
)

# =====================================
# CACHE GRAPH
# =====================================
@st.cache_resource
def load_graph(place):
    return ox.graph_from_place(
        place,
        network_type="drive"
    )

# =====================================
# RUN ANALYSIS
# =====================================
if st.button("RUN HOTSPOT MAP"):

    try:

        place = zones[selected_zone]

        st.write(f"Loading {selected_zone} road network...")

        # ---------------------------------
        # LOAD GRAPH
        # ---------------------------------
        G = load_graph(place)

        st.success("Road network loaded")

        # ---------------------------------
        # SIMPLE GRAPH
        # ---------------------------------
        G_simple = nx.Graph(G)

        st.write("Calculating hotspot importance...")

        # ---------------------------------
        # CENTRALITY
        # ---------------------------------
        centrality = nx.betweenness_centrality(
            G_simple,
            k=20,
            seed=42
        )

        # ---------------------------------
        # TOP HOTSPOTS
        # ---------------------------------
        top_nodes = sorted(
            centrality,
            key=centrality.get,
            reverse=True
        )[:30]

        # ---------------------------------
        # BUILD DATAFRAME
        # ---------------------------------
        hotspot_data = []
        
        for node in top_nodes:

            lat = G.nodes[node]["y"]
            lon = G.nodes[node]["x"]

            try:
                location = geolocator.reverse((lat, lon), timeout=10)

                if location:

                address = location.raw.get("address", {})

                place_name = (
                    address.get("road")
                    or address.get("suburb")
                    or address.get("neighbourhood")
                    or address.get("city")
                    or "Unknown Area"
                )

            else:
                place_name = "Unknown Area"

            except:
                place_name = "Unknown Area"

            hotspot_data.append({
                "node": node,
                "lat": lat,
                "lon": lon,
                "score": centrality[node],
                "location": place_name
            })
            df = pd.DataFrame(hotspot_data)
            df["timestamp"] = datetime.now()

            df["zone"] = selected_zone

            file_name = "traffic_hotspots.csv"

            if os.path.exists(file_name):

                df.to_csv(
                    file_name,
                    mode="a",
                    header=False,
                    index=False
                )

        else:

            df.to_csv(
                file_name,
                index=False
            )

        st.success("Hotspot data saved successfully")
        # ---------------------------------
        # MAP
        # ---------------------------------
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            size="score",
            color="score",
            hover_data=["node", "score"],
            zoom=11,
            height=700
        )

        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        # ---------------------------------
        # DISPLAY MAP
        # ---------------------------------
        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ---------------------------------
        # HOTSPOT TABLE
        # ---------------------------------
        st.subheader("🔥 Top Traffic Hotspots")

        st.dataframe(df)

    except Exception as e:
        st.error(f"System Error: {e}")
