import osmnx as ox
import networkx as nx
import pandas as pd
import os
import time
import requests

from datetime import datetime
from geopy.geocoders import Nominatim

# =====================================
# GEOCODER
# =====================================
geolocator = Nominatim(user_agent="urban_surgeon_ai")

# =====================================
# ZONES
# =====================================
zones = {
    "Port Harcourt": "Port Harcourt, Rivers State, Nigeria",
    "Obio/Akpor": "Obio-Akpor, Rivers State, Nigeria"
}

# =====================================
# MAIN LOOP
# =====================================
while True:

    print("\n===================================")
    print("RUNNING AUTOMATIC HOTSPOT SCAN...")
    print("===================================\n")

    for zone_name, place in zones.items():

        try:

            print(f"Loading {zone_name} road network...")

            # ---------------------------------
            # LOAD GRAPH
            # ---------------------------------
            G = ox.graph_from_place(
                place,
                network_type="drive"
            )

            # ---------------------------------
            # SIMPLE GRAPH
            # ---------------------------------
            G_simple = nx.Graph(G)

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
            )[:10]

            hotspot_data = []

            # ---------------------------------
            # BUILD DATA
            # ---------------------------------
            for node in top_nodes:

                lat = G.nodes[node]["y"]
                lon = G.nodes[node]["x"]

                # ---------------------------------
                # LIVE TRAFFIC DATA
                # ---------------------------------
                api_key = "GBCC2VIMIdsT3SSPzcnJiQO4QazAaI2Z"

                traffic_url = (
                    f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
                    f"?key={api_key}&point={lat},{lon}"
                )

                traffic_response = requests.get(
                    traffic_url,
		    timeout=10
                )

                traffic_data = traffic_response.json()

                try:

                    current_speed = traffic_data["flowSegmentData"]["currentSpeed"]

                    free_flow_speed = traffic_data["flowSegmentData"]["freeFlowSpeed"]

                    congestion = round(
                        100 - (current_speed / free_flow_speed * 100),
                        2
                    )

                except:

                    current_speed = None
                    free_flow_speed = None
                    congestion = None

                # ---------------------------------
                # LOCATION DATA
                # ---------------------------------
                try:

                    location = geolocator.reverse(
                        (lat, lon),
                        timeout=10
                    )

                    if location:

                        address = location.raw.get(
                            "address",
                            {}
                        )

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

                    "zone": zone_name,
                    "location": place_name,
                    "lat": lat,
                    "lon": lon,
                    "score": centrality[node],
                    "timestamp": datetime.now(),

                    "current_speed": current_speed,
                    "free_flow_speed": free_flow_speed,
                    "congestion": congestion

                })
		

            # ---------------------------------
            # DATAFRAME
            # ---------------------------------
            df = pd.DataFrame(hotspot_data)

            # ---------------------------------
            # SAVE CSV
            # ---------------------------------
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

            print(f"{zone_name} saved successfully")

        except Exception as e:

            print(f"Error in {zone_name}: {e}")

    # =====================================
    # WAIT 30 minutes
    # =====================================
    print("\nWaiting 30 minutes before next scan...\n")

    time.sleep(1800)