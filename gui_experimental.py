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

# initializes session state variables
if "selected_node" not in st.session_state:
    st.session_state.selected_node = None


# generates unique IDs for each node
def generate_node_id(index):
    return f"Node-{index+1}"


# creates the folium map in streamlit
m = st_folium(m, width=700)

# if there is a map, it gets the last clicked coordinate values
if m and m.get("last_clicked"):
    # gets the tuple values for the coordinates
    clicked_coords = tuple(m["last_clicked"].values())
    # stores the selected node
    st.session_state.selected_node = clicked_coords


# empties the stored coordinate values from previous navigation
if "starting_node" not in st.session_state:
    st.session_state.starting_node = None
if "ending_node" not in st.session_state:
    st.session_state.ending_node = None
if "selected_node" not in st.session_state:
    st.session_state.selected_node = None

# creates a button to save the starting node
if st.button("Start point"):
    if st.session_state.selected_node:
        st.session_state.starting_node = st.session_state.selected_node
        st.success(f"Starting location saved: {st.session_state.starting_node}")
    else:
        st.warning("Error... click on a node first")

# creates a button to save the ending node
if st.button("End point"):
    if st.session_state.selected_node:
        st.session_state.ending_node = st.session_state.selected_node  # Save selection
        st.success(f"Ending location saved: {st.session_state.ending_node}")
    else:
        st.warning("Error... click on a node first")

# prints the stored nodes
if st.session_state.starting_node:
    st.write(f"**Stored Starting Location:** {st.session_state.starting_node}")
if st.session_state.ending_node:
    st.write(f"**Stored Ending Location:** {st.session_state.ending_node}")

# creates a button to activate dixtras
if st.button("Start Navigation"):
    if st.session_state.starting_node and st.session_state.ending_node:
        st.write(f"Running Dijkstra's algorithm between {st.session_state.starting_node} and {st.session_state.ending_node}")
    else:
        st.warning("Error... please set both a starting and an ending node first!")

# creates dropdown menu boxes for selecting the locations for navigation
start_point = st.selectbox('where would you like to start from?', ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion'))
end_point = st.selectbox('where would you like to go?', ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion'))

# creates a seperate button to activate dixtras from the dropdown menu
if st.button("start navigation"):
    if st.session_state.selected_node:
        st.write("running dixtras")
    else:
        st.warning("error... click on a node first")
