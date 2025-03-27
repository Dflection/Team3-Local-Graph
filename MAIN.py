# created by both Ashton and Dylan.
# I, Ashton did the base gui and Dylan added AI to the gui and did refinements


import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
import math
from edgegraph import Graph
from dijkstras_algorithm import dijkstra


# ----------------------------------------------------------------------------------
# Utility: Load and Save Voice Updates (JSON)
# ----------------------------------------------------------------------------------


def load_voice_update(file_path="voice_update.json"):
    """Load voice update data from a JSON file if it exists."""
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
    """Save voice update data to a JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error writing to {file_path}: {e}")


# ----------------------------------------------------------------------------------
# Helper: Format time and distance
# ----------------------------------------------------------------------------------


def format_time_in_minutes_seconds(total_seconds: float) -> str:
    """Convert seconds to a formatted string in minutes and seconds."""
    total_seconds = int(total_seconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    if minutes > 0 and seconds > 0:
        return f"{minutes} minutes and {seconds} seconds"
    elif minutes > 0:
        return f"{minutes} minutes"
    else:
        return f"{seconds} seconds"


def format_distance_in_feet(distance_km: float) -> str:
    """Convert distance from kilometers to feet and return as string."""
    feet = distance_km * 3280.84
    return f"{int(feet)} feet"


# ----------------------------------------------------------------------------------
# Helper functions for snapping (buffered matching)
# ----------------------------------------------------------------------------------


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance (in meters) between two lat/lon points using the Haversine formula."""
    R = 6371000  # Earth radius in meters
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_closest_node(lat, lon, node_data, threshold=5.0):
    """
    Find the closest node from node_data to the given lat/lon within a threshold (meters).
    Returns the node name if within threshold, otherwise None.
    """
    closest_node = None
    min_dist = float("inf")
    for node_name, coords in node_data.items():
        nlat = coords.get("latitude")
        nlon = coords.get("longitude")
        if nlat is None or nlon is None:
            continue
        dist = haversine_distance(lat, lon, nlat, nlon)
        if dist < min_dist:
            min_dist = dist
            closest_node = node_name
    if min_dist <= threshold:
        return closest_node
    else:
        return None


# ----------------------------------------------------------------------------------
# GeometryGraph: Build a graph from red lines in GeoJSON data
# ----------------------------------------------------------------------------------


class GeometryGraph:
    """
    Build a graph from GeoJSON red lines, splitting them at known campus nodes.
    Each segment is stored as an edge with coordinates and distance.
    """
    def __init__(self, node_data, geojson_data, threshold=5.0):
        self.adj = {}
        self.node_data = node_data
        self.threshold = threshold
        self.build_geometry_graph(geojson_data)

    def add_edge(self, nodeA, nodeB, coords):
        """Add a bidirectional edge between nodeA and nodeB with computed distance."""
        distance_m = 0.0
        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i+1]
            distance_m += haversine_distance(lat1, lon1, lat2, lon2)

        if nodeA not in self.adj:
            self.adj[nodeA] = {}
        if nodeB not in self.adj:
            self.adj[nodeB] = {}

        self.adj[nodeA][nodeB] = {"coords": coords, "distance": distance_m}
        self.adj[nodeB][nodeA] = {"coords": list(reversed(coords)), "distance": distance_m}

    def build_geometry_graph(self, geojson_data):
        """Parse GeoJSON features and build the geometry graph."""
        for feature in geojson_data["features"]:
            geom = feature.get("geometry", {})
            if geom.get("type") != "LineString":
                continue
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            # Identify breakpoints along the line for snapping nodes
            break_indices = [0]
            for i, (lon, lat) in enumerate(coords):
                if i == 0 or i == len(coords) - 1:
                    continue
                snapped_node = find_closest_node(lat, lon, self.node_data, self.threshold)
                if snapped_node:
                    break_indices.append(i)
            break_indices.append(len(coords) - 1)
            # Create segments between breakpoints
            for idx in range(len(break_indices) - 1):
                start_i = break_indices[idx]
                end_i = break_indices[idx + 1]
                segment_coords = coords[start_i:end_i + 1]
                first_lon, first_lat = segment_coords[0]
                last_lon, last_lat = segment_coords[-1]
                nodeA = find_closest_node(first_lat, first_lon, self.node_data, self.threshold)
                nodeB = find_closest_node(last_lat, last_lon, self.node_data, self.threshold)
                if nodeA and nodeB and nodeA != nodeB:
                    self.add_edge(nodeA, nodeB, segment_coords)


# ----------------------------------------------------------------------------------
# Dijkstra for GeometryGraph
# ----------------------------------------------------------------------------------


def geometry_dijkstra(geom_graph, start_node, end_node):
    """
    Run a mini Dijkstra algorithm on a GeometryGraph to find a path between nodes.
    Returns a list of edge tuples (nodeA, nodeB) for the shortest path.
    """
    import heapq
    dist = {}
    prev = {}
    for node in geom_graph.adj:
        dist[node] = float('inf')
        prev[node] = None
    if start_node not in geom_graph.adj or end_node not in geom_graph.adj:
        return None
    dist[start_node] = 0
    visited = set()
    heap = [(0, start_node)]
    while heap:
        current_dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == end_node:
            break
        for neighbor, info in geom_graph.adj[node].items():
            edge_dist = info["distance"]
            alt = current_dist + edge_dist
            if alt < dist[neighbor]:
                dist[neighbor] = alt
                prev[neighbor] = node
                heapq.heappush(heap, (alt, neighbor))
    if dist[end_node] == float('inf'):
        return None
    path_edges = []
    cur = end_node
    while prev[cur] is not None:
        path_edges.append((prev[cur], cur))
        cur = prev[cur]
    path_edges.reverse()
    return path_edges


# ----------------------------------------------------------------------------------
# Enhanced CampusMap Class: Display map with paths and buildings
# ----------------------------------------------------------------------------------


class CampusMap:
    """Handles rendering of the campus map with GeoJSON data and graph routes."""
    def __init__(self, geojson_data, graph):
        self.geojson_data = geojson_data
        self.graph = graph

        self.map = folium.Map(
            location=[38.031, -120.3877],
            zoom_start=15,
            control_scale=True
        )

        self.route_group = folium.FeatureGroup(name="Route")
        self.map.add_child(self.route_group)

        self.red_paths_group = folium.FeatureGroup(name="RedPaths")
        self.edge_geometry = {}
        self.parse_line_features()

        self.geometry_graph = GeometryGraph(graph.location_data, geojson_data, threshold=5.0)

    def style_function(self, feature):
        """Return a style dict based on feature type."""
        props = feature.get("properties", {})
        bldg_type = props.get("type", "").lower()
        if bldg_type == "dorm":
            return {"fillColor": "purple", "color": "purple", "weight": 2, "fillOpacity": 0.4}
        elif bldg_type == "lab":
            return {"fillColor": "orange", "color": "orange", "weight": 2, "fillOpacity": 0.4}
        else:
            return {"fillColor": "blue", "color": "red", "weight": 2, "fillOpacity": 0.4}

    def add_base_layers(self):
        """Add GeoJSON layers to the map based on geometry type."""
        for feature in self.geojson_data["features"]:
            geom_type = feature["geometry"]["type"]
            if geom_type == "Polygon":
                folium.GeoJson(feature, style_function=self.style_function).add_to(self.map)
            elif geom_type == "LineString":
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {"color": "red", "weight": 4, "opacity": 0.8}
                ).add_to(self.red_paths_group)

    def toggle_red_paths(self, show: bool):
        """Show or hide red paths on the map."""
        group_name = self.red_paths_group.get_name()
        if show:
            if group_name not in self.map._children:
                self.map.add_child(self.red_paths_group)
        else:
            if group_name in self.map._children:
                del self.map._children[group_name]

    def clear_route(self):
        """Clear the current route from the map."""
        route_group_name = self.route_group.get_name()
        if route_group_name in self.map._children:
            del self.map._children[route_group_name]
        self.route_group = folium.FeatureGroup(name="Route")
        self.map.add_child(self.route_group)

    def parse_line_features(self):
        """Extract edge geometries from GeoJSON features for later use."""
        node_data = self.graph.location_data
        for feature in self.geojson_data["features"]:
            geom = feature.get("geometry", {})
            if geom.get("type") != "LineString":
                continue
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            first_lon, first_lat = coords[0]
            last_lon, last_lat = coords[-1]
            node1 = find_closest_node(first_lat, first_lon, node_data, threshold=5.0)
            node2 = find_closest_node(last_lat, last_lon, node_data, threshold=5.0)
            if node1 and node2 and node1 != node2:
                edge_key = frozenset([node1, node2])
                self.edge_geometry[edge_key] = geom

    def draw_geometry_path(self, path_edges):
        """Combine coordinates for a series of geometry edges to form a continuous path."""
        all_coords = []
        for (A, B) in path_edges:
            seg_info = self.geometry_graph.adj[A][B]
            if not all_coords:
                all_coords.extend(seg_info["coords"])
            else:
                all_coords.extend(seg_info["coords"][1:])
        return all_coords

    def draw_route_from_geojson(self, route_edges):
        """Draw a route on the map using GeoJSON edge data, with fallbacks if needed."""
        self.clear_route()
        if not route_edges:
            return

        all_coords_for_bounds = []
        for i, edge in enumerate(route_edges):
            try:
                node1, node2 = edge.split("-")
                edge_key = frozenset([node1, node2])
                geometry = self.edge_geometry.get(edge_key)
                if geometry:
                    folium.GeoJson(
                        geometry,
                        style_function=lambda x: {"color": "green", "weight": 6, "opacity": 0.9},
                        name=f"Segment {i+1}"
                    ).add_to(self.route_group)
                    for lon, lat in geometry["coordinates"]:
                        all_coords_for_bounds.append([lat, lon])
                else:
                    # Use geometry_dijkstra as a fallback to draw the segment
                    path_edges_geom = geometry_dijkstra(self.geometry_graph, node1, node2)
                    if path_edges_geom:
                        combined_coords = self.draw_geometry_path(path_edges_geom)
                        if combined_coords:
                            latlon_list = [[c[1], c[0]] for c in combined_coords]
                            folium.PolyLine(
                                locations=latlon_list,
                                color="green",
                                weight=6,
                                opacity=0.9
                            ).add_to(self.route_group)
                            all_coords_for_bounds.extend(latlon_list)
                        else:
                            st.warning(f"No sub-segment coords found for fallback route {node1}-{node2}")
                    else:
                        st.warning(f"No direct or geometry-based path found for {edge}. Drawing straight line.")
                        loc1 = self.graph.location_data.get(node1)
                        loc2 = self.graph.location_data.get(node2)
                        if not loc1 or not loc2:
                            st.warning(f"Missing location data for '{node1}' or '{node2}'.")
                            continue
                        lat1, lon1 = loc1["latitude"], loc1["longitude"]
                        lat2, lon2 = loc2["latitude"], loc2["longitude"]
                        folium.PolyLine(
                            locations=[[lat1, lon1], [lat2, lon2]],
                            color="green",
                            weight=6,
                            opacity=0.9
                        ).add_to(self.route_group)
                        all_coords_for_bounds.append([lat1, lon1])
                        all_coords_for_bounds.append([lat2, lon2])
            except Exception as exc:
                st.error(f"Error processing edge '{edge}': {exc}")

        # Fit map to the route bounds and add start/end markers
        if len(all_coords_for_bounds) >= 2:
            first_edge = route_edges[0]
            last_edge = route_edges[-1]
            start_node_name = first_edge.split("-")[0]
            end_node_name = last_edge.split("-")[1]
            start_coords = self.graph.location_data.get(start_node_name)
            end_coords = self.graph.location_data.get(end_node_name)
            if not start_coords or not end_coords:
                st.warning(f"Missing location data for {start_node_name} or {end_node_name}.")
            else:
                folium.Marker(
                    location=[start_coords["latitude"], start_coords["longitude"]],
                    popup=start_node_name,
                    icon=folium.Icon(color='green', icon='flag')
                ).add_to(self.route_group)
                folium.Marker(
                    location=[end_coords["latitude"], end_coords["longitude"]],
                    popup=end_node_name,
                    icon=folium.Icon(color='red', icon='flag')
                ).add_to(self.route_group)
            self.map.fit_bounds(all_coords_for_bounds)

    def draw_route(self, route_edges):
        """Draw a simple straight-line route between nodes."""
        self.clear_route()
        if not route_edges:
            return
        full_coords = []
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
            except Exception as exc:
                st.error(f"Error processing edge '{edge}': {exc}")
        if len(full_coords) >= 2:
            folium.PolyLine(
                locations=full_coords,
                color='green',
                weight=10,
                opacity=0.7
            ).add_to(self.route_group)
            self.map.fit_bounds(full_coords)


# ----------------------------------------------------------------------------------
# Cache-Enabled Data Loader: Load GeoJSON and graph data
# ----------------------------------------------------------------------------------


@st.cache_data
def load_data(geojson_path, excel_path):
    """Load GeoJSON data and Excel-based graph, returning both."""
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
# Compute Multi-Leg Route with Dijkstra
# ----------------------------------------------------------------------------------


def compute_full_route(graph, start, waypoints, end, metric_choice):
    """
    Compute a full route from start to end with optional waypoints using Dijkstra.
    Returns the combined edges and the total metric (time or distance).
    """
    adjacency = graph.get_connection_matrix()
    all_edges = []
    total_metric = 0.0
    current = start
    route_ok = True
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
    """Main function to run the Streamlit application."""
    st.title("The Local Graph")

    # Initialize session state variables
    if 'current_route_edges' not in st.session_state:
        st.session_state.current_route_edges = []
    if 'current_route_metric' not in st.session_state:
        st.session_state.current_route_metric = 0.0
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None
    if 'show_red_paths' not in st.session_state:
        st.session_state.show_red_paths = False

    geojson_data, graph = load_data("qgis_1.json", "compendium.xlsx")
    if not geojson_data or not graph:
        return

    campus_map = CampusMap(geojson_data, graph)
    campus_map.add_base_layers()
    campus_map.toggle_red_paths(st.session_state.show_red_paths)

    # Check for voice update input
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
        # Calculate route using voice data
        route_edges, travel_time = compute_full_route(
            graph, start_from_voice, [], end_from_voice, metric_choice="time"
        )
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
                f"Voice route found! Travel time: {formatted_time}, covering {formatted_distance}."
            )
        save_voice_update({"start": None, "end": None, "confirmed": False})

    campus_map.draw_route_from_geojson(st.session_state.current_route_edges)

    # --- Add blue markers for each optional waypoint ---
    if 'selected_waypoints' in st.session_state:
        for wp in st.session_state.selected_waypoints:
            wp_coords = graph.location_data.get(wp)
            if wp_coords:
                folium.Marker(
                    location=[wp_coords["latitude"], wp_coords["longitude"]],
                    popup=wp,
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(campus_map.route_group)

    st_folium(
        campus_map.map,
        width=700,
        height=500,
        key="main_map"
    )

    if st.session_state.success_message:
        st.success(st.session_state.success_message)

    st.subheader("Select Start & End Buildings")
    col1, col2 = st.columns(2)
    building_options = []
    if graph and graph.location_data:
        building_options = sorted(
            n for n, is_bldg in graph.node_type.items()
            if is_bldg and n in graph.location_data
        )

    with col1:
        search_start = st.text_input("Search for a start building:")
        filtered_start_buildings = [
            b for b in building_options if search_start.lower() in b.lower()
        ]
        start_building = (
            st.selectbox("Start Building", options=filtered_start_buildings)
            if filtered_start_buildings
            else None
        )
    with col2:
        search_end = st.text_input("Search for an end building:")
        filtered_end_buildings = [b for b in building_options if search_end.lower() in b.lower()]
        end_building = st.selectbox("End Building", options=filtered_end_buildings) if filtered_end_buildings else None

    st.subheader("Optional Waypoints")
    search_waypoint = st.text_input("Search for waypoints:")
    if search_waypoint:
        filtered_waypoint_buildings = [b for b in building_options if search_waypoint.lower() in b.lower()]
    else:
        filtered_waypoint_buildings = building_options
    selected_waypoints = st.multiselect(
        "Add any number of waypoints in the order you want to visit them:",
        options=filtered_waypoint_buildings,
        key="selected_waypoints"
    )

    st.subheader("Calculate Path")
    col_find, col_clear, col_toggle = st.columns(3)
    with col_find:
        if st.button("Find Route"):
            if not start_building or not end_building:
                st.error("Please select valid Start and End buildings.")
            else:
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
                    st.session_state.current_route_edges = route_edges_time
                    st.session_state.current_route_metric = travel_time
                    formatted_time = format_time_in_minutes_seconds(travel_time)
                    formatted_distance = format_distance_in_feet(travel_distance)
                    st.session_state.success_message = (
                        f"Route found! Travel time: {formatted_time}, Distance: {formatted_distance}.  \n"
                        f"**Zoom in on the map to see the route.**"
                    )
    with col_clear:
        if st.button("Clear Path"):
            st.session_state.current_route_edges = []
            st.session_state.current_route_metric = 0.0
            st.session_state.success_message = None
            # Remove selected waypoints from session state
            if "selected_waypoints" in st.session_state:
                del st.session_state["selected_waypoints"]

    with col_toggle:
        show_red = st.checkbox("All Path Data", value=st.session_state.show_red_paths)
        st.session_state.show_red_paths = show_red
        campus_map.toggle_red_paths(show_red)

    if st.session_state.success_message:
        st.success(st.session_state.success_message)


if __name__ == "__main__":
    main()
