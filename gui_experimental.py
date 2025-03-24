#Thanks to Ashton
import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
from folium.features import DivIcon  # <-- For text labels on the map
from edgegraph import Graph
from dijkstras_algorithm import dijkstra

# ----------------------------------------------------------------------------------
# Utility: Load and Save Voice Updates (JSON)
# ----------------------------------------------------------------------------------
def load_voice_update(file_path="voice_update.json"):
    """Reads the JSON file if it exists and returns the dict or None."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data
    except Exception as e:
        st.error(f"Error reading {file_path}: {e}")
        return None

def save_voice_update(data: dict, file_path="voice_update.json"):
    """Writes the dict to JSON, used to clear or update voice instructions."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error writing to {file_path}: {e}")

# ----------------------------------------------------------------------------------
# Helper function: Format time from seconds to minutes and seconds
# ----------------------------------------------------------------------------------
def format_time_in_minutes_seconds(total_seconds: float) -> str:
    """Converts time in seconds to a string 'X minutes and Y seconds'."""
    total_seconds = int(total_seconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    if minutes > 0 and seconds > 0:
        return f"{minutes} minutes and {seconds} seconds"
    elif minutes > 0:
        return f"{minutes} minutes"
    else:
        return f"{seconds} seconds"

# ----------------------------------------------------------------------------------
# Helper function: Convert distance from meters to feet
# ----------------------------------------------------------------------------------
def format_distance_in_feet(distance_km: float) -> str:
    feet = distance_km * 3280.84
    return f"{int(feet)} feet"


# ----------------------------------------------------------------------------------
# Enhanced CampusMap Class (with edge label nameplates)
# ----------------------------------------------------------------------------------
class CampusMap:
    def __init__(self, geojson_data, graph):
        self.geojson_data = geojson_data
        self.graph = graph
        
        # Initialize the Folium map around your campus
        self.map = folium.Map(
            location=[38.031, -120.3877],
            zoom_start=15,
            control_scale=True
        )
        
        # Add the base layers (buildings, polygons, etc.)
        self.add_base_layers()
        
        # A feature group for routes
        self.route_group = folium.FeatureGroup(name="Route")
        self.map.add_child(self.route_group)

        # Optionally place building markers
        self.add_building_markers()

    def style_function(self, feature):
        props = feature.get("properties", {})
        bldg_type = props.get("type", "").lower()

        if bldg_type == "dorm":
            return {"fillColor": "purple", "color": "purple", "weight": 2, "fillOpacity": 0.4}
        elif bldg_type == "lab":
            return {"fillColor": "orange", "color": "orange", "weight": 2, "fillOpacity": 0.4}
        else:
            return {"fillColor": "blue", "color": "red", "weight": 2, "fillOpacity": 0.4}

    def add_base_layers(self):
        for feature in self.geojson_data["features"]:
            geom_type = feature["geometry"]["type"]
            if geom_type == "Polygon":
                folium.GeoJson(feature, style_function=self.style_function).add_to(self.map)
            elif geom_type == "LineString":
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {"color": "red", "weight": 4, "opacity": 0.8}
                ).add_to(self.map)

    def add_building_markers(self):
        """Place a marker for each building node from the graph."""
        for node, loc_data in self.graph.location_data.items():
            if self.graph.node_type.get(node, False):  # is_building == True
                lat, lon = loc_data.get('latitude'), loc_data.get('longitude')
                if lat is not None and lon is not None:
                    folium.Marker(
                        location=[lat, lon],
                        popup=node,
                        icon=folium.Icon(icon='info-sign')
                    ).add_to(self.map)

    def clear_route(self):
        """Removes any existing route group from the map's _children."""
        route_group_name = self.route_group.get_name()
        if route_group_name in self.map._children:
            del self.map._children[route_group_name]
        self.route_group = folium.FeatureGroup(name="Route")
        self.map.add_child(self.route_group)

    def draw_route(self, route_edges):
        """
        Draw a single green polyline for the entire route, 
        plus nameplates for each segment on the map.
        """
        self.clear_route()
        if not route_edges:
            return

        # Build a list of all coordinates for the main polyline
        full_coords = []
        # Loop over each edge to build a continuous route and label each edge
        for i, edge in enumerate(route_edges):
            try:
                node1, node2 = edge.split('-')
                loc1 = self.graph.location_data.get(node1, {})
                loc2 = self.graph.location_data.get(node2, {})

                lat1, lon1 = loc1.get('latitude'), loc1.get('longitude')
                lat2, lon2 = loc2.get('latitude'), loc2.get('longitude')
                
                if None in (lat1, lon1, lat2, lon2):
                    st.warning(f"Skipping edge {edge} due to missing coords.")
                    continue

                if not full_coords or full_coords[-1] != [lat1, lon1]:
                    full_coords.append([lat1, lon1])
                full_coords.append([lat2, lon2])

                # Label this edge at its midpoint
                mid_lat = (lat1 + lat2) / 2
                mid_lon = (lon1 + lon2) / 2
                edge_label = f"{i+1}) {node1}–{node2}"

                folium.Marker(
                    location=[mid_lat, mid_lon],
                    icon=DivIcon(
                        icon_size=(150, 36),
                        icon_anchor=(0, 0),
                        html=f'<div style="font-size: 12pt; color: blue;">{edge_label}</div>'
                    )
                ).add_to(self.route_group)

            except Exception as exc:
                st.error(f"Error processing edge '{edge}': {exc}")

        if len(full_coords) >= 2:
            folium.PolyLine(
                locations=full_coords,
                color='green',
                weight=10,
                opacity=0.7
            ).add_to(self.route_group)

            # Add Start/End markers
            start_coord = full_coords[0]
            end_coord = full_coords[-1]

            folium.Marker(
                location=start_coord,
                popup="START",
                icon=folium.Icon(color='green', icon='flag')
            ).add_to(self.route_group)

            folium.Marker(
                location=end_coord,
                popup="END",
                icon=folium.Icon(color='red', icon='flag')
            ).add_to(self.route_group)

            self.map.fit_bounds(full_coords)

# ----------------------------------------------------------------------------------
# Cache-Enabled Data Loader
# ----------------------------------------------------------------------------------
@st.cache_data
def load_data(geojson_path, excel_path):
    """Loads GeoJSON + Graph from Excel-based adjacency data."""
    try:
        with open(geojson_path) as f:
            geojson_data = json.load(f)
        graph = Graph()
        graph.load_from_excel(excel_path)
        return geojson_data, graph
    except Exception as e:
        st.error(f"Data loading error: {str(e)}")
        return None, None

# ----------------------------------------------------------------------------------
# Multi-Leg Route Calculation with Dijkstra
# ----------------------------------------------------------------------------------
def compute_full_route(graph, start, waypoints, end, metric_choice):
    adjacency = graph.get_connection_matrix()
    all_edges = []
    total_metric = 0.0
    current = start
    route_ok = True

    # Chain route: start -> waypoints[...] -> end
    for wp in waypoints:
        path, metric_val = dijkstra(adjacency, current, wp, metric=metric_choice)
        if metric_val == float('inf'):
            route_ok = False
            break
        all_edges.extend(list(path.keys()))
        total_metric += metric_val
        current = wp

    if route_ok:
        path, metric_val = dijkstra(adjacency, current, end, metric=metric_choice)
        if metric_val == float('inf'):
            route_ok = False
        else:
            all_edges.extend(list(path.keys()))
            total_metric += metric_val

    if not route_ok:
        return None, float('inf')
    return all_edges, total_metric

# ----------------------------------------------------------------------------------
# Main Streamlit App
# ----------------------------------------------------------------------------------
def main():
    st.title("The Local Graph")

    # ---- Initialize Session State FIRST ---- #
    if 'current_route_edges' not in st.session_state:
        st.session_state.current_route_edges = []
    if 'current_route_metric' not in st.session_state:
        st.session_state.current_route_metric = 0.0
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None

    # ---- Your existing logic begins here ---- #

    # 1) Load data
    geojson_data, graph = load_data("qgis_1.geojson", "compendium.xlsx")
    if not geojson_data or not graph:
        return  # Stop if data fails to load

    # 2) Initialize CampusMap
    campus_map = CampusMap(geojson_data, graph)

    # 3) Check for voice update and set route if available
    voice_data = load_voice_update()
    if voice_data:
        start_from_voice = voice_data.get("start")
        end_from_voice = voice_data.get("end")
        confirmed = voice_data.get("confirmed", False)
    else:
        start_from_voice = None
        end_from_voice = None
        confirmed = False

    if start_from_voice and end_from_voice and confirmed:
        # Calculate route by time
        route_edges, travel_time = compute_full_route(
            graph, start_from_voice, [], end_from_voice, metric_choice="time"
        )
        # Calculate route by distance
        _, travel_distance = compute_full_route(
            graph, start_from_voice, [], end_from_voice, metric_choice="distance"
        )

        if route_edges is None or travel_time == float('inf'):
            st.error(f"No valid path found via voice for {start_from_voice} → {end_from_voice}.")
            st.session_state.current_route_edges = []
            st.session_state.current_route_metric = 0.0
            st.session_state.success_message = None
        else:
            st.session_state.current_route_edges = route_edges
            st.session_state.current_route_metric = travel_time
            formatted_time = format_time_in_minutes_seconds(travel_time)
            formatted_distance = format_distance_in_feet(travel_distance)
            st.session_state.success_message = (
                f"Voice route found! Travel time: {formatted_time}, "
                f"covering {formatted_distance}."
            )
        # Clear voice update after use
        save_voice_update({"start": None, "end": None, "confirmed": False})

    # Draw/update the route on the map with segment nameplates
    campus_map.draw_route(st.session_state.current_route_edges)

    # ----------------------------------------------------------------------
    # Display the Map above the manual selection buttons
    # ----------------------------------------------------------------------
    st_folium(
        campus_map.map,
        width=700,
        height=500,
        key="main_map"
    )

    # Display success message if it exists
    if st.session_state.success_message:
        st.success(st.session_state.success_message)


    # ----------------------------------------------------------------------
    # Manual Selection UI for Route Calculation
    # ----------------------------------------------------------------------
    st.subheader("Select Start & End Buildings")
    col1, col2 = st.columns(2)

    # Prepare building list (start and end drop-downs work perfectly)
    building_options = []
    if graph and graph.location_data:
        building_options = sorted(
            n for n, is_bldg in graph.node_type.items()
            if is_bldg and n in graph.location_data
        )

    with col1:
        search_start = st.text_input("Search for a start building:")
        filtered_start_buildings = [b for b in building_options if search_start.lower() in b.lower()]
        start_building = st.selectbox("Start Building", options=filtered_start_buildings) if filtered_start_buildings else None

    with col2:
        search_end = st.text_input("Search for an end building:")
        filtered_end_buildings = [b for b in building_options if search_end.lower() in b.lower()]
        end_building = st.selectbox("End Building", options=filtered_end_buildings) if filtered_end_buildings else None

    # Optional Waypoints Multiselect (fixed)
    st.subheader("Optional Waypoints")
    search_waypoint = st.text_input("Search for waypoints:")
    if search_waypoint:
        filtered_waypoint_buildings = [b for b in building_options if search_waypoint.lower() in b.lower()]
    else:
        filtered_waypoint_buildings = building_options
    selected_waypoints = st.multiselect("Add any number of waypoints in the order you want to visit them:",
                                        options=filtered_waypoint_buildings,
                                        key="waypoints")

    # # Choose Route Metric
    # st.subheader("Choose Route Metric")
    # metric_choice = st.radio("Route Preference:", ["time", "distance"], index=0)

    # Session state initialization for route
    if 'current_route_edges' not in st.session_state:
        st.session_state.current_route_edges = []
    if 'current_route_metric' not in st.session_state:
        st.session_state.current_route_metric = 0.0
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None

       # Buttons for manual route calculation
    # Calculate Path Section
    st.subheader("Calculate Path")

    # Session state initialization for route
    if 'current_route_edges' not in st.session_state:
        st.session_state.current_route_edges = []
    if 'current_route_metric' not in st.session_state:
        st.session_state.current_route_metric = 0.0
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None

    # Buttons placed horizontally
    col_find, col_clear = st.columns(2)

    with col_find:
        if st.button("Find Route"):
            if not start_building or not end_building:
                st.error("Please select valid Start and End buildings.")
            else:
                # Always calculate BOTH metrics:
                route_edges_time, travel_time = compute_full_route(
                    graph, start_building, selected_waypoints, end_building, metric_choice="time"
                )
                route_edges_dist, travel_distance = compute_full_route(
                    graph, start_building, selected_waypoints, end_building, metric_choice="distance"
                )

                if route_edges_time is None or travel_time == float('inf'):
                    st.error("No valid path found.")
                    st.session_state.current_route_edges = []
                    st.session_state.current_route_metric = 0.0
                    st.session_state.success_message = None
                else:
                    # Default to displaying the time-based route
                    st.session_state.current_route_edges = route_edges_time
                    st.session_state.current_route_metric = travel_time

                    # Format both metrics clearly
                    formatted_time = format_time_in_minutes_seconds(travel_time)
                    formatted_distance = format_distance_in_feet(travel_distance)

                    # Set success message with both metrics
                    st.session_state.success_message = (
                    f"Route found! Travel time: {formatted_time}, Distance: {formatted_distance}.  \n"
                    f"**Zoom in on the map to see the route.**"
                )


    with col_clear:
        if st.button("Clear Path"):
            st.session_state.current_route_edges = []
            st.session_state.current_route_metric = 0.0
            st.session_state.success_message = None

    # Display success message
    if st.session_state.success_message:
        st.success(st.session_state.success_message)

    # Display route steps if available
    if st.session_state.current_route_edges:
        st.markdown("### Route Steps")
        for i, edge in enumerate(st.session_state.current_route_edges):
            st.write(f"{i+1}. {edge}")


    # Uncomment if needed:
    # st.write("Reading voice_update.json from:", os.path.abspath("voice_update.json"))

if __name__ == "__main__":
    main()
