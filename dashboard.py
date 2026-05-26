import osmnx as ox
import networkx as nx
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium

from sqlalchemy import create_engine

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(

    page_title="AI Traffic Intelligence System",

    layout="wide"

)

# =====================================
# DATABASE CONNECTION
# =====================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# =====================================
# LOAD DATA
# =====================================

@st.cache_data
def load_data():

    query = """
        SELECT *
        FROM traffic_data_final
    """

    df = pd.read_sql(
        query,
        engine
    )

    return df

df = load_data()

# =====================================
# DASHBOARD TITLE
# =====================================

st.title(
    "AI Traffic Intelligence Dashboard"
)

st.markdown(
    """
    Live traffic monitoring and
    smart mobility analytics for
    Port Harcourt and Obio/Akpor.
    """
)

# =====================================
# METRICS
# =====================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(

        "Total Traffic Records",

        len(df)

    )

with col2:

    avg_congestion = round(

        df["congestion_percent"]
        .str.replace("%", "")
        .astype(float)
        .mean(),

        2

    )

    st.metric(

        "Average Congestion",

        f"{avg_congestion}%"

    )

with col3:

    total_roads = df[
        "location"
    ].nunique()

    st.metric(

        "Roads Monitored",

        total_roads

    )

# =====================================
# CONGESTION DISTRIBUTION
# =====================================

st.subheader(
    "Traffic Congestion Distribution"
)

df["congestion_value"] = df[
    "congestion_percent"
].str.replace(
    "%",
    "",
    regex=False
).astype(float)

fig = px.histogram(

    df,

    x="congestion_value",

    nbins=20,

    title="Congestion Distribution"

)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================
# TOP CONGESTED ROADS
# =====================================

st.subheader(
    "Top Congested Roads"
)

top_roads = (

    df.groupby("location")[
        "congestion_value"
    ]

    .mean()

    .sort_values(
        ascending=False
    )

    .head(10)

    .reset_index()

)

fig2 = px.bar(

    top_roads,

    x="location",

    y="congestion_value",

    title="Highest Congestion Roads"

)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# =====================================
# LIVE TRAFFIC TABLE
# =====================================

st.subheader(
    "Live Traffic Data"
)

st.dataframe(df)
# =====================================
# LIVE TRAFFIC MAP
# =====================================

st.subheader(
    "Live Traffic Map"
)

# CENTER MAP
traffic_map = folium.Map(

    location=[4.8156, 7.0498],

    zoom_start=12

)

# ADD TRAFFIC POINTS
for _, row in df.iterrows():

    try:

        lat = float(row["latitude"])

        lon = float(row["longitude"])

        congestion = float(

            str(
                row["congestion_percent"]
            ).replace("%", "")

        )

        location_name = row["location"]

        # COLOR LOGIC
        if congestion < 30:

            color = "green"

        elif congestion < 60:

            color = "orange"

        else:

            color = "red"

        folium.CircleMarker(

            location=[lat, lon],

            radius=6,

            popup=(

                f"{location_name}<br>"
                f"Congestion: {congestion}%"

            ),

            color=color,

            fill=True,

            fill_color=color,

            fill_opacity=0.7

        ).add_to(traffic_map)

    except:

        continue

# DISPLAY MAP
st_folium(

    traffic_map,

    width=1200,

    height=600

)

# =====================================
# LIVE ROUTE OPTIMIZATION
# =====================================

st.subheader(
    "Smart Route Optimization"
)

# LOAD ROAD NETWORK
G = ox.graph_from_place(

    "Port Harcourt, Rivers State, Nigeria",

    network_type="drive"

)

# APPLY TRAFFIC WEIGHTS
for u, v, key, data in G.edges(
    keys=True,
    data=True
):

    road_name = data.get("name")

    if road_name is None:
        continue

    if isinstance(road_name, list):
        road_name = road_name[0]

    matching_rows = df[
        df["location"] == road_name
    ]

    if len(matching_rows) > 0:

        congestion_value = matching_rows.iloc[0][
            "congestion_value"
        ]

        data["weight"] = congestion_value

    else:

        data["weight"] = 10

# LOCATION OPTIONS
locations = sorted(
    df["location"].dropna().unique()
)

# USER INPUTS
start_location = st.selectbox(

    "Select Start Location",

    locations

)

destination_location = st.selectbox(

    "Select Destination",

    locations

)

# GET COORDINATES
start_row = df[
    df["location"] == start_location
].iloc[0]

end_row = df[
    df["location"] == destination_location
].iloc[0]

# NEAREST GRAPH NODES
start_node = ox.distance.nearest_nodes(

    G,

    X=float(start_row["longitude"]),

    Y=float(start_row["latitude"])

)

end_node = ox.distance.nearest_nodes(

    G,

    X=float(end_row["longitude"]),

    Y=float(end_row["latitude"])

)

# GENERATE ROUTE
try:

    route = nx.shortest_path(

        G,

        source=start_node,

        target=end_node,

        weight="weight"

    )

    st.success(
        "Optimized low-congestion route generated"
    )

    # ROUTE MAP
    fig, ax = ox.plot_graph_route(

        G,

        route,

        route_linewidth=4,

        node_size=0,

        bgcolor="white",

        show=False,

        close=False

    )

    st.pyplot(fig)

except:

    st.error(
        "Unable to generate route"
    )
