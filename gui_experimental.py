"""
this window is for handling streamlit experiments
"""
import folium
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import json

# Load GeoJSON file
PATHS_ON_CAMPUS = "Tuolumne_County_Track_Me.json"

# Read JSON file
with open(PATHS_ON_CAMPUS, "r") as f:
    data = json.load(f)

# Extract features
features = data["features"]

# Process the pathways into DataFrame
paths_data = []
for feature in features:
    if feature["geometry"]["type"] == "LineString":
        path = [[coord[1], coord[0]] for coord in feature["geometry"]["coordinates"]]  # Folium expects [lat, lon]
        paths_data.append({"path": path})

# Convert the paths to DataFrame
paths_df = pd.DataFrame(paths_data)

file_path = "output.xlsx"
sheet_name = "Sheet1"
column_name = "LatLon"

# Read only the specified sheet
df = pd.read_excel(file_path, sheet_name=sheet_name, usecols=[column_name])

# Create a list of tuples from the column
column_list = [tuple(map(float, val.split(','))) for val in df[column_name].dropna()]

# Convert the list of tuples into a DataFrame
df = pd.DataFrame(column_list, columns=['lat', 'lon'])

# Initializes the map
m = folium.Map(location=[38.031, -120.3877], zoom_start=15, control_scale=True)

# Add paths (lines) to the map
for i, row in paths_df.iterrows():
    folium.PolyLine(
        # Uses the list of coordinate points for creating the lines
        locations=row["path"],
        # Sets the path color
        color="red",
        # Sets the thickness of the pathway
        weight=4,
        opacity=0.8
    ).add_to(m)

# Add points to the map
for i, row in df.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],  # Place point at the correct location
        # sets point radius
        radius=4,
        # sets the color of the points
        color="blue",
        fill=True,
        # sets internal color of the points
        fill_color="white",
        fill_opacity=0.7,
    ).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700)

# creates dropdown menu boxes for selecting the locations for navigation
start_point = st.selectbox('where would you like to start from?', ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion'))
end_point = st.selectbox('where would you like to go?', ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion'))
