import os
import time
import requests
import pandas as pd
import osmnx as ox

from sqlalchemy import create_engine
from datetime import datetime

# =====================================
# TOMTOM API KEY
# =====================================

TOMTOM_API_KEY = "GBCC2VIMIdsT3SSPzcnJiQO4QazAaI2Z"

# =====================================
# DATABASE CONNECTION
# =====================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# =====================================
# MAIN LOOP
# =====================================

while True:

    print("\n===================================")
    print("RUNNING LIVE TRAFFIC COLLECTION")
    print("===================================\n")

    cities = [
        "Port Harcourt, Rivers State, Nigeria",
        "Obio-Akpor, Rivers State, Nigeria"
    ]

    all_data = []

    for city in cities:

        try:

            print(f"Loading road network for {city}...")

            # LOAD ROAD NETWORK
            G = ox.graph_from_place(
                city,
                network_type="drive"
            )

            # CONVERT GRAPH TO DATAFRAME
            edges = ox.graph_to_gdfs(
                G,
                nodes=False
            )

            # SAMPLE MANY ROADS
            sampled_edges = edges.head(50)

            for _, edge in sampled_edges.iterrows():

                try:

                    # ROAD NAME
                    street_name = edge.get(
                        "name",
                        "Unknown Road"
                    )

                    # HANDLE MULTIPLE NAMES
                    if isinstance(street_name, list):
                        street_name = street_name[0]

                    # GEOMETRY
                    geometry = edge.geometry

                    # CENTER COORDINATES
                    center = geometry.centroid

                    lat = center.y
                    lon = center.x

                    # TOMTOM API REQUEST
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

                    # SPEEDS
                    current_speed = flow["currentSpeed"]

                    free_flow_speed = flow["freeFlowSpeed"]

                    # TRAVEL TIMES → MINUTES
                    current_travel_time = round(
                        flow["currentTravelTime"] / 60,
                        2
                    )

                    free_flow_travel_time = round(
                        flow["freeFlowTravelTime"] / 60,
                        2
                    )

                    # CONGESTION %
                    congestion = round(
                        (
                            (free_flow_speed - current_speed)
                            / free_flow_speed
                        ) * 100,
                        2
                    )

                    # SAVE ROW
                    all_data.append({

                        "zone": city,

                        "location": street_name,

                        "latitude": round(lat, 6),

                        "longitude": round(lon, 6),

                        "timestamp": datetime.now(),

                        "current_speed_kmh":
                            f"{current_speed} km/h",

                        "free_flow_speed_kmh":
                            f"{free_flow_speed} km/h",

                        "current_travel_time_minutes":
                            f"{current_travel_time} mins",

                        "free_flow_travel_time_minutes":
                            f"{free_flow_travel_time} mins",

                        "congestion_percent":
                            f"{congestion}%"

                    })

                except Exception as road_error:

                    print(f"Road skipped: {road_error}")

        except Exception as city_error:

            print(f"Error in {city}: {city_error}")

    # =====================================
    # SAVE TO DATABASE
    # =====================================

    if len(all_data) > 0:

        df = pd.DataFrame(all_data)

        df.to_sql(
            "traffic_data_final",
            engine,
            if_exists="append",
            index=False
        )

        print(f"\nSaved {len(all_data)} traffic records\n")

    else:

        print("\nNo traffic data collected\n")

    print("Waiting 15 minutes...\n")

    time.sleep(900)
