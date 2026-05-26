import os
import time
import requests
import pandas as pd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

from collections import defaultdict
from sqlalchemy import create_engine
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error

# =====================================
# TOMTOM API KEY
# =====================================

TOMTOM_API_KEY = "PASTE_YOUR_TOMTOM_API_KEY_HERE"

# =====================================
# DATABASE CONNECTION
# =====================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

print("Database connected successfully")

# =====================================
# LIVE TRAFFIC COLLECTION
# =====================================

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

        # SAMPLE ROADS
        sampled_edges = edges.head(50)

        for _, edge in sampled_edges.iterrows():

            try:

                # ROAD NAME
                street_name = edge.get(
                    "name",
                    "Unknown Road"
                )

                if isinstance(street_name, list):
                    street_name = street_name[0]

                # GEOMETRY
                geometry = edge.geometry

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

                if "flowSegmentData" not in traffic:
                    continue

                flow = traffic["flowSegmentData"]

                current_speed = flow["currentSpeed"]

                free_flow_speed = flow["freeFlowSpeed"]

                current_travel_time = round(
                    flow["currentTravelTime"] / 60,
                    2
                )

                free_flow_travel_time = round(
                    flow["freeFlowTravelTime"] / 60,
                    2
                )

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
            "congestion_percent"
        ]

        congestion_value = float(
            str(congestion_value).replace("%", "")
        )

        data["weight"] = congestion_value

    else:

        data["weight"] = 10

print("Dynamic graph updated successfully")

# =====================================
# REAL LOCATIONS
# =====================================

start_location = "Garrison"

destination_location = "Rumuokoro"

# LONGITUDE = X
# LATITUDE = Y

start_node = ox.distance.nearest_nodes(
    G,
    X=7.0136,
    Y=4.8155
)

end_node = ox.distance.nearest_nodes(
    G,
    X=6.9842,
    Y=4.8924
)

# =====================================
# DETECT HIGH CONGESTION ROADS
# =====================================

print("Analyzing congestion hotspots...\n")

high_congestion_roads = []

for u, v, key, data in G.edges(
    keys=True,
    data=True
):

    weight = data.get("weight", 0)

    road_name = data.get("name")

    if road_name is None:
        continue

    if isinstance(road_name, list):
        road_name = road_name[0]

    if weight >= 60:

        high_congestion_roads.append({

            "road": road_name,
            "congestion": weight

        })

seen = set()

filtered_roads = []

for road in high_congestion_roads:

    if road["road"] not in seen:

        filtered_roads.append(road)

        seen.add(road["road"])

print("HIGH CONGESTION ROADS:\n")

for road in filtered_roads[:10]:

    print(
        f"{road['road']} "
        f"→ {road['congestion']}% congestion"
    )

# =====================================
# ROUTE OPTIMIZATION
# =====================================

print("Generating congestion-aware route...\n")

try:

    route = nx.shortest_path(

        G,
        source=start_node,
        target=end_node,
        weight="weight"

    )

    print("Optimized low-congestion route found\n")

except nx.NetworkXNoPath:

    print("No valid route found")

    route = []

# =====================================
# ROUTE ANALYSIS
# =====================================

total_weight = 0

for i in range(len(route) - 1):

    u = route[i]

    v = route[i + 1]

    edge_data = G.get_edge_data(u, v)

    if edge_data:

        first_edge = list(edge_data.values())[0]

        weight = first_edge.get("weight", 10)

        total_weight += weight

print(f"Total Route Congestion Score: {round(total_weight, 2)}")

# =====================================
# ALTERNATIVE ROUTE ANALYSIS
# =====================================

print("\nGenerating alternative routes...\n")

alternative_routes = list(

    nx.shortest_simple_paths(

        G,
        start_node,
        end_node,
        weight="weight"

    )

)

alternative_routes = alternative_routes[:3]

route_scores = []

for idx, alt_route in enumerate(alternative_routes):

    total_score = 0

    for i in range(len(alt_route) - 1):

        u = alt_route[i]

        v = alt_route[i + 1]

        edge_data = G.get_edge_data(u, v)

        if edge_data:

            first_edge = list(
                edge_data.values()
            )[0]

            weight = first_edge.get(
                "weight",
                10
            )

            total_score += weight

    route_scores.append({

        "route_number": idx + 1,
        "score": round(total_score, 2)

    })

print("ALTERNATIVE ROUTE SCORES:\n")

for route_info in route_scores:

    print(

        f"Route "
        f"{route_info['route_number']} "
        f"→ Congestion Score: "
        f"{route_info['score']}"

    )

# =====================================
# TRAFFIC HEATMAP VISUALIZATION
# =====================================

print("\nGenerating congestion heatmap...\n")

edge_colors = []

for u, v, key, data in G.edges(
    keys=True,
    data=True
):

    weight = data.get("weight", 10)

    if weight < 30:

        edge_colors.append("green")

    elif weight < 60:

        edge_colors.append("orange")

    else:

        edge_colors.append("red")

fig, ax = ox.plot_graph(

    G,

    edge_color=edge_colors,

    edge_linewidth=1,

    node_size=0,

    bgcolor="white",

    show=False,

    close=False

)

plt.show()

print("Congestion heatmap generated")

# =====================================
# INFRASTRUCTURE RECOMMENDATION ENGINE
# =====================================

print("\nGenerating infrastructure recommendations...\n")

recommendations = []

for road in filtered_roads:

    congestion = road["congestion"]

    road_name = road["road"]

    if congestion >= 80:

        recommendation = (
            "Consider road expansion "
            "or flyover construction"
        )

    elif congestion >= 60:

        recommendation = (
            "Consider traffic light "
            "optimization or rerouting"
        )

    else:

        recommendation = (
            "Monitor traffic conditions"
        )

    recommendations.append({

        "road": road_name,

        "congestion": congestion,

        "recommendation": recommendation

    })

print("INFRASTRUCTURE RECOMMENDATIONS:\n")

for item in recommendations[:10]:

    print(

        f"{item['road']} "
        f"({item['congestion']}%) "
        f"→ {item['recommendation']}"

    )

# =====================================
# HISTORICAL CONGESTION ANALYSIS
# =====================================

print("\nAnalyzing persistent congestion patterns...\n")

road_history = defaultdict(list)

for _, row in df.iterrows():

    road_name = row["location"]

    congestion = row["congestion_percent"]

    congestion = float(
        str(congestion).replace("%", "")
    )

    road_history[road_name].append(congestion)

persistent_hotspots = []

for road, values in road_history.items():

    average_congestion = round(

        sum(values) / len(values),

        2

    )

    if average_congestion >= 60:

        persistent_hotspots.append({

            "road": road,

            "average_congestion":
                average_congestion

        })

print("PERSISTENT TRAFFIC HOTSPOTS:\n")

for hotspot in persistent_hotspots[:10]:

    print(

        f"{hotspot['road']} "
        f"→ Average Congestion: "
        f"{hotspot['average_congestion']}%"

    )

# =====================================
# PREDICTIVE TRAFFIC INTELLIGENCE
# =====================================

print("\nTraining traffic prediction model...\n")

df["congestion_value"] = df[
    "congestion_percent"
].str.replace(
    "%",
    "",
    regex=False
).astype(float)

encoder = LabelEncoder()

df["location_encoded"] = encoder.fit_transform(
    df["location"]
)

X = df[[

    "location_encoded"

]]

y = df["congestion_value"]

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.2,

    random_state=42

)

model = RandomForestRegressor(

    n_estimators=100,

    random_state=42

)

model.fit(

    X_train,
    y_train

)

predictions = model.predict(X_test)

error = mean_absolute_error(

    y_test,
    predictions

)

print(

    f"Prediction Error: "
    f"{round(error, 2)}"

)

sample_road = df.iloc[0]["location"]

encoded_road = encoder.transform(
    [sample_road]
)[0]

future_prediction = model.predict([[
    encoded_road
]])[0]

print(

    f"\nPredicted Future Congestion "
    f"for {sample_road}: "
    f"{round(future_prediction, 2)}%"

)
