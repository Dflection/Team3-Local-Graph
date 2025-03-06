"""
this window is for handling streamlit experiments
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import json


# Load GeoJSON file
PATHS_ON_CAMPUS = "campus_map_1.json"

# Read JSON file
with open(PATHS_ON_CAMPUS, "r") as f:
    data = json.load(f)

# Extract features
features = data["features"]

# processes the features into DataFrame
paths_data = []
for feature in features:
    if feature["geometry"]["type"] == "LineString":
        path = [[coord[0], coord[1]] for coord in feature["geometry"]["coordinates"]]
        paths_data.append({"path": path})

# converts the paths to DataFrame
paths_df = pd.DataFrame(paths_data)


# sets the starting view point in pydeck
initial_view_state = pdk.ViewState(
    latitude=38.031, longitude=-120.3877, zoom=15
)

# Creates a layer for the paths
path_layer = pdk.Layer(
    "PathLayer",
    data=paths_df,
    pickable=True,
    get_color=[0, 0, 155],  # Red color
    width_scale=1,
    width_min_pixels=2,
    get_path="path",
    get_width=3,
)


# start of point plotting
file_path = "output.xlsx"
sheet_name = "Sheet1"
column_name = "LatLon"

# Reads the Excel sheet
df = pd.read_excel(file_path, sheet_name=sheet_name, usecols=[column_name])

# Converts column values to list of tuples
column_list = [tuple(map(float, val.split(','))) for val in df[column_name].dropna()]

# Converts list of tuples into DataFrame
df = pd.DataFrame(column_list, columns=['lat', 'lon'])

# Create ScatterplotLayer for points
scatter_layer = pdk.Layer(
    'ScatterplotLayer',
    df,
    get_position='[lon, lat]',
    # sets the color of the points
    get_color='[200, 30, 0, 160]',
    get_radius=2,
    pickable=True
)

# Sets the viewport location
view_state = pdk.ViewState(
    longitude=-120.388428,
    latitude=38.030901,
    zoom=14,
    pitch=50
)

# Renders the map with PyDeck (both paths & points)
st.pydeck_chart(pdk.Deck(
    layers=[scatter_layer, path_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v10"
))
