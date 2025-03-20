"""
This window is for handling Streamlit experiments
"""
import folium
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import json


# creates a class for generating the map of the campus in streamlit
class CampusMap:
    # assigns input requirements to generate the map and get the points out of the excel sheet
    def __init__(self, geojson_path, excel_path, sheet_name, column_name):
        """
        Initializes the CampusMap with file paths and data loading.
        """
        self.geojson_path = geojson_path
        self.excel_path = excel_path
        self.sheet_name = sheet_name
        self.column_name = column_name
        self.map = folium.Map(location=[38.031, -120.3877], zoom_start=15, control_scale=True)
        self.data = self.load_geojson()
        self.paths_df = self.process_paths()
        self.nodes_df = self.load_nodes()

    def load_geojson(self):
        """reads the geojson file that comes from caltopo"""
        with open(self.geojson_path, "r") as f:
            return json.load(f)

    def process_paths(self):
        """uses the geojson and extracts the data on the paths"""
        paths_data = []
        for feature in self.data["features"]:
            if feature["geometry"]["type"] == "LineString":
                path = [[coord[1], coord[0]] for coord in feature["geometry"]["coordinates"]]
                paths_data.append({"path": path})
        return pd.DataFrame(paths_data)

    def load_nodes(self):
        """pulls nodes from an excel sheet for reference"""
        df = pd.read_excel(self.excel_path, sheet_name=self.sheet_name, usecols=[self.column_name])
        column_list = [tuple(map(float, val.split(','))) for val in df[self.column_name].dropna()]
        return pd.DataFrame(column_list, columns=['lat', 'lon'])

    def add_polygons(self):
        """adds all of the polygons that look like the different areas of interest.
        These include buildings and parking lots
        """
        for feature in self.data["features"]:
            if feature["geometry"]["type"] == "Polygon":
                folium.GeoJson(
                    feature,
                    name="Polygons",
                    style_function=lambda x: {
                        "fillColor": "blue",
                        "color": "red",
                        "weight": 2,
                        "fillOpacity": 0.4
                    },
                    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Region:"]),
                ).add_to(self.map)

    def add_paths(self):
        """overlays all of the paths onto the map in red to show all of the available pathways"""
        for feature in self.data["features"]:
            if feature["geometry"]["type"] == "LineString":
                folium.GeoJson(
                    feature,
                    name="Paths",
                    style_function=lambda x: {
                        "color": "red",
                        "weight": 4,
                        "opacity": 0.8
                    },
                    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Path:"]),
                ).add_to(self.map)

    def add_nodes(self):
        """adds all of the nodes to the map for all of the intersections and buildings"""
        for _, row in self.nodes_df.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5,
                color="blue",
                fill=True,
                fill_color="white",
                fill_opacity=0.9,
                popup=f"Node: ({row['lat']}, {row['lon']})",
            ).add_to(self.map)

    def display_map(self):
        """creates a streamlit webpage to display the map"""
        return st_folium(self.map, width=700)


class User_input:
    def __init__(self, campus_map):
        """
        creates a dropdown menu and takes the campus map and creates the start and end points
        """
        self.campus_map = campus_map
        self.start_point = None
        self.end_point = None
        self.setup_ui()

    def setup_ui(self):
        """creates the dropdown boxes for selecting the start and end points"""
        self.start_point = st.selectbox(
            'Where would you like to start from?',
            ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion')
        )
        self.end_point = st.selectbox(
            'Where would you like to go?',
            ('Manzanita', 'Sequoiyah', 'Sugarpine', 'Fir', 'Juniper', 'Poison Oak', 'short term parking', 'long term parking', 'Oak Pavilion')
        )

        # creates a grid system for the buttons
        col1, col2 = st.columns(2)

        # creates a button for the standard route
        if col1.button("Standard Route"):
            self.confirm_route("Standard")

        # creates a button for the wheelchair route in the case that the user can't walk
        if col2.button("Wheelchair Route"):
            self.confirm_route("Wheelchair")

    def confirm_route(self, route_type):
        """prints out the user's selected route by naming off the two points"""
        st.session_state.saved_start = self.start_point
        st.session_state.saved_end = self.end_point
        if route_type == "Standard":
            st.success(f"Navigating from {st.session_state.saved_start} to {st.session_state.saved_end}")
        else:
            st.success(f"Navigating from {st.session_state.saved_start} to {st.session_state.saved_end} with a wheelchair accessible route")

        # st.write(f"**Start Point:** {st.session_state.saved_start}")
        # st.write(f"**End Point:** {st.session_state.saved_end}")


# runs if this is the main program
if __name__ == "__main__":
    # Initialize the campus map
    campus_map = CampusMap(
        geojson_path="qgis_1.geojson",
        excel_path="output.xlsx",
        sheet_name="Sheet1",
        column_name="LatLon"
    )

    # Add elements to the map
    campus_map.add_polygons()
    campus_map.add_paths()
    # campus_map.add_nodes()

    # Display the map
    campus_map.display_map()

    # Initialize and run the navigation UI
    User_input(campus_map)
