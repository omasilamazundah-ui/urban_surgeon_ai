import os
import time
import requests
import pandas as pd
import osmnx as ox

from sqlalchemy import create_engine
from datetime import datetime

# =========================
# TOMTOM API KEY
# =========================
TOMTOM_API_KEY = "GBCC2VIMIdsT3SSPzcnJiQO4QazAaI2Z"

# =========================
# DATABASE CONNECTION
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# =========================
# MAIN LOOP
# =========================
while True:

    print("\n==============================")
    print("RUNNING AUTOMATIC HOTSPOT SCAN")
    print("==============================\n")

    cities = [
        "Port Harcourt, Rivers State, Nigeria",
        "Obio-Akpor, Rivers State, Nigeria"
    ]

    for city in cities:

        try:

            print(f"Loading road network for {city}...")

            # LOAD ROAD NETWORK
            G = ox.graph_from_place(
                city,
                network_type="drive"
            )

            hotspot_data = []

            # CONVERT GRAPH TO ROAD DATA
            edges = ox.graph_to_gdfs(
                G,
                nodes=False
            )

            # SAMPLE 50 ROADS
            sampled_edges = edges.head(50)

            for _, edge in sampled_edges.iterrows():

                # GET ROAD NAME
                street_name = edge.get(
                    "name",
                    "Unknown Road"
                )

                # HANDLE MULTIPLE ROAD NAMES
                if isinstance(street_name, list):
                    street_name = street_name[0]

                # ROAD GEOMETRY
                geometry = edge.geometry

                # GET CENTER POINT
                center = geometry.centroid

                lat = center.y
                lon = center.x

                # TOMTOM TRAFFIC REQUEST
                url = (
                    f"https://api.tomtom.com/traffic/services/4/"
                    f"flowSegmentData/absolute/10/json"
                    f"?point={lat},{lon}"
                    f"&key={TOMTOM_API_KEY}"
                )

                response = requests.get(url)

                traffic = response.json()

                # SKIP INVALID RESPONSES
                if "flowSegmentData" not in traffic:
                    continue

                flow = traffic["flowSegmentData"]

                current_speed = flow["currentSpeed"]

                free_flow_speed = flow["freeFlowSpeed"]

                current_travel_time = flow["currentTravelTime"]

                free_flow_travel_time = flow["freeFlowTravelTime"]

                # CALCULATE CONGESTION %
                congestion = round(
                    (
                        (free_flow_speed - current_speed)
                        / free_flow_speed
                    ) * 100,
                    2
                )

                # SAVE DATA
                hotspot_data.append({

                    "zone": city,
                    "location": street_name,
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": datetime.now(),
                    "current_speed": current_speed,
                    "free_flow_speed": free_flow_speed,
                    "current_travel_time": current_travel_time,
                    "free_flow_travel_time": free_flow_travel_time,
                    "congestion": congestion

                })

            # CREATE DATAFRAME
            df = pd.DataFrame(hotspot_data)

            # SAVE TO POSTGRESQL
            df.to_sql(
                "traffic_data_v4",
                engine,
                if_exists="append",
                index=False
            )

            print(f"{city} saved successfully")

        except Exception as e:

            print(f"Error in {city}: {e}")

    print("\nWaiting 15 minutes...\n")

    time.sleep(900)
