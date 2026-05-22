import osmnx as ox
import networkx as nx
import pandas as pd
import os
import time
import requests

from sqlalchemy import create_engine
from datetime import datetime
from geopy.geocoders import Nominatim

TOMTOM_API_KEY = "GBCC2VIMIdsT3SSPzcnJiQO4QazAaI2Z"

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

    
            # GET CENTER COORDINATES
center_node = list(G.nodes())[0]

lat = G.nodes[center_node]["y"]
lon = G.nodes[center_node]["x"]

# TOMTOM TRAFFIC API
url = (
    f"https://api.tomtom.com/traffic/services/4/"
    f"flowSegmentData/absolute/10/json"
    f"?point={lat},{lon}"
    f"&key={TOMTOM_API_KEY}"
)

response = requests.get(url)

traffic = response.json()

flow = traffic["flowSegmentData"]

current_speed = flow["currentSpeed"]
free_flow_speed = flow["freeFlowSpeed"]
current_travel_time = flow["currentTravelTime"]
free_flow_travel_time = flow["freeFlowTravelTime"]

# CONGESTION %
congestion = round(
    (
        (free_flow_speed - current_speed)
        / free_flow_speed
    ) * 100,
    2
)
           hotspot_data.append({
               "zone": zone_name,
               "latitude": lat,
               "longitude": lon,
               "timestamp": datetime.now(),
               "current_speed": current_speed,
               "free_flow_speed": free_flow_speed,
               "current_travel_time": current_travel_time,
               "free_flow_travel_time": free_flow_travel_time,
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
