"""
this window is for handling streamlit experiments
"""
import folium
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import json

# loads the geojson file and aliases it to PATHS_ON_CAMPUS
PATHS_ON_CAMPUS = "qgis_1.geojson"

# reads the geojson file for the paths
with open(PATHS_ON_CAMPUS, "r") as f:
    data = json.load(f)

# extracts the features, not to crazy
features = data["features"]

# process the pathways into a DataFrame
paths_data = []
for feature in features:
    if feature["geometry"]["type"] == "LineString":
        path = [[coord[1], coord[0]] for coord in feature["geometry"]["coordinates"]]  # Folium expects [lat, lon]
        paths_data.append({"path": path})

# converts the paths into a DataFrame
paths_df = pd.DataFrame(paths_data)

# gives the directions to the specific column needed in the excel spreadsheet
file_path = "output.xlsx"
sheet_name = "Sheet1"
column_name = "LatLon"

# reads the excel sheet and gets the information from the coordinate column
df = pd.read_excel(file_path, sheet_name=sheet_name, usecols=[column_name])
# creates a list of tuples from the column
column_list = [tuple(map(float, val.split(','))) for val in df[column_name].dropna()]
# converts the list of tuples into a DataFrame
df = pd.DataFrame(column_list, columns=['lat', 'lon'])

# initializes the folium map
m = folium.Map(location=[38.031, -120.3877], zoom_start=15, control_scale=True)

# adds the paths to the map to show available paths
for i, row in paths_df.iterrows():
    folium.PolyLine(
        # Uses the list of coordinate points for creating the lines
        locations=row["path"],
        # sets the path color
        color="red",
        # sets the thickness of the pathway
        weight=4,
        opacity=0.8
    ).add_to(m)

# adds all of the nodes to the map
for i, row in df.iterrows():
    # creates a generic marker name for interum purposes
    html = "marker"
    folium.CircleMarker(

        location=[row["lat"], row["lon"]],  # Place point at the correct location
        # sets point radius
        radius=4,
        # sets the color of the points
        color="blue",
        fill=True,
        # sets internal color of the points
        popup=html,
        fill_color="white",
        fill_opacity=0.7,
    ).add_to(m)

# creates the folium map in streamlit
m = st_folium(m, width=700)

# creates dropdown menu boxes for selecting the locations for navigation
start_point = st.selectbox('where would you like to start from?', ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion'))
end_point = st.selectbox('where would you like to go?', ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion'))


if st.button("Confirm Route"):
    # Store values in session state
    st.session_state.saved_start = start_point
    st.session_state.saved_end = end_point

    # Print the confirmation message
    st.success(f"Navigating from {st.session_state.saved_start} to {st.session_state.saved_end}")
    st.write(f"**Start Point:** {st.session_state.saved_start}")
    st.write(f"**End Point:** {st.session_state.saved_end}")
