import os
import pandas as pd
import osmnx as ox
import networkx as nx

from sqlalchemy import create_engine

# =====================================
# DATABASE CONNECTION
# =====================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# =====================================
# LOAD LIVE TRAFFIC DATA
# =====================================

print("Loading live traffic data...")

df = pd.read_sql(
    "SELECT * FROM traffic_data_final",
    engine
)

print("Traffic data loaded successfully")

# =====================================
# LOAD ROAD NETWORK
# =====================================

place = "Port Harcourt, Rivers State, Nigeria"

print(f"Loading road network for {place}...")

G = ox.graph_from_place(
    place,
    network_type="drive"
)

print("Road network loaded")

# =====================================
# APPLY LIVE TRAFFIC WEIGHTS
# =====================================

print("Applying dynamic traffic weights...")

for u, v, key, data in G.edges(keys=True, data=True):

    road_name = data.get("name")

    if road_name is None:
        continue

    # HANDLE MULTIPLE ROAD NAMES
    if isinstance(road_name, list):
        road_name = road_name[0]

    # MATCH ROAD IN DATABASE
    matching_rows = df[
        df["location"] == road_name
    ]

    if len(matching_rows) > 0:

        congestion_value = matching_rows.iloc[0][
            "congestion_percent"
        ]

        # REMOVE %
        congestion_value = float(
            str(congestion_value).replace("%", "")
        )

        # ASSIGN TRAFFIC WEIGHT
        data["weight"] = congestion_value

    else:

        # DEFAULT LOW TRAFFIC
        data["weight"] = 10

print("Dynamic graph updated successfully")

# =====================================
# ROUTE OPTIMIZATION
# =====================================

nodes = list(G.nodes)

# SAMPLE START/END
start_node = nodes[0]

end_node = nodes[500]

print("Running Dijkstra route optimization...")

route = nx.shortest_path(

    G,
    source=start_node,
    target=end_node,
    weight="weight"

)

print("\nOptimized Route Generated\n")

print(route)
