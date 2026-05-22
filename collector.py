import osmnx as ox
import networkx as nx
import pandas as pd
import os
import time
import requests

from sqlalchemy import create_engine
from datetime import datetime
from geopy.geocoders import Nominatim

# DATABASE CONNECTION
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# GEOCODER
geolocator = Nominatim(user_agent="urban_surgeon_ai")

# ZONES
zones = {
    "Port Harcourt": "Port Harcourt, Rivers State, Nigeria",
    "Obio/Akpor": "Obio-Akpor, Rivers State, Nigeria"
}

# MAIN LOOP
while True:

    print("\n==============================")
    print("RUNNING AUTOMATIC HOTSPOT SCAN...")
    print("==============================\n")

    for zone_name, place in zones.items():

        try:

            print(f"Loading {zone_name} road network...")

            hotspot_data = []

            # LOAD GRAPH
            G = ox.graph_from_place(place, network_type="drive")

            # BASIC ANALYSIS
            num_nodes = len(G.nodes)
            num_edges = len(G.edges)

            congestion = round((num_edges / num_nodes) * 10, 2)

            hotspot_data.append({
                "zone": zone_name,
                "timestamp": datetime.now(),
                "current_speed": num_edges,
                "free_flow_speed": num_nodes,
                "congestion": congestion
            })

            # DATAFRAME
            df = pd.DataFrame(hotspot_data)

            # SAVE TO POSTGRESQL
            df.to_sql(
                "traffic_data",
                engine,
                if_exists="append",
                index=False
            )

            print(f"{zone_name} saved successfully to PostgreSQL")

        except Exception as e:

            print(f"Error in {zone_name}: {e}")

    # WAIT 15 MINUTES
    print("\nWaiting 15 minutes before next scan...\n")

    time.sleep(900)
