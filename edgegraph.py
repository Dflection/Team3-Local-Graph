# The Local Graph, Edge Graph Module - by Chase Varvayanis
# 3-11-2025
# Code Linted with Flake8, Spellchecked with Code Spell Checker,
# and general Cleanup and formatting with ChatGPT

import os
import pandas as pd
from openpyxl import load_workbook


# ----------------------------------------------------------------------------------
# Graph Class
# ----------------------------------------------------------------------------------


class Graph:
    """
    Represents a directed graph of locations and connections between them.

    Stores:
      - nodes: Each node with its connections and metrics.
      - location_data: Mapping of locations to their latitude and longitude.
      - node_type: Mapping indicating whether a location is a building.
    """
    def __init__(self):
        self.nodes = {}           # e.g., {'A': {'name': 'A', 'connections': {...}}}
        self.location_data = {}   # e.g., {'A': {'latitude': 38.0, 'longitude': -120.0}}
        self.node_type = {}       # e.g., {'A': True or False}

    def add_location(self, name, latitude, longitude, is_building=False):
        """Adds a new location and its metadata to the graph."""
        if name not in self.nodes:
            self.nodes[name] = {'name': name, 'connections': {}}
            self.location_data[name] = {'latitude': latitude, 'longitude': longitude}
            self.node_type[name] = is_building

    def add_connection(self, source, destination, weight):
        """
        Adds a connection from source to destination.
        The weight can be a dictionary of metrics (e.g. time, distance) or a float.
        """
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Both locations must be added before connecting them.")
        if isinstance(weight, dict):
            self.nodes[source]['connections'][destination] = weight
        else:
            self.nodes[source]['connections'][destination] = float(weight)

    def get_connection_matrix(self):
        """Returns a mapping of each node to its connections and associated metrics."""
        return {node: data['connections'] for node, data in self.nodes.items()}

    def load_from_excel(self, excel_file='compendium.xlsx'):
        """
        Loads the graph from an Excel file.
        Expects:
          - Sheets: "time", "distance", "gain", "loss" for metrics.
          - Sheet "coords": columns "node" and "coords" (e.g. "38.031, -120.3877").
          - Sheet "node_type": columns "node" and "is_building".
        """
        ExcelGraphIO.load_graph_from_excel(self, excel_file)

    def __repr__(self):
        """Return a formatted string representation of the graph."""
        output = "Graph Representation:\n"
        for node, data in self.nodes.items():
            output += f"Location: {data['name']}\n"
            lat = self.location_data.get(node, {}).get('latitude', 'N/A')
            lon = self.location_data.get(node, {}).get('longitude', 'N/A')
            output += f"  Latitude: {lat}\n"
            output += f"  Longitude: {lon}\n"
            output += f"  Node Type (is_building): {self.node_type.get(node, 'N/A')}\n"
            output += "  Connections:\n"
            for dest, metrics in data['connections'].items():
                output += f"    -> {dest} (Metrics: {metrics})\n"
        return output


# ----------------------------------------------------------------------------------
# ExcelGraphIO Class
# ----------------------------------------------------------------------------------
class ExcelGraphIO:
    """
    Handles Excel I/O operations for the graph.

    The Excel file has:
      - 4 sheets: "time", "distance", "gain", "loss" (adjacency matrices).
      - Sheet "coords" with columns "node" and "coords" (tuple).
      - Sheet "node_type" with columns "node" and "is_building".
    """
    @staticmethod  # https://www.geeksforgeeks.org/class-method-vs-static-method-python/
    def load_graph_from_excel(graph, excel_file='compendium.xlsx'):
        """Loads graph data from the Excel file."""
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Excel file not found at {excel_file}")

        # Load metric sheets into dataframes
        metrics_list = ['time', 'distance', 'gain', 'loss']
        sheets = {}
        for metric in metrics_list:
            try:
                df = pd.read_excel(excel_file, sheet_name=metric, header=0, index_col=0)
                # Clean up row and column labels
                df.index = df.index.map(lambda x: str(x).strip())
                df.columns = [str(col).strip() for col in df.columns]
                sheets[metric] = df
            except Exception as e:
                sheets[metric] = None
                print(f"Warning: could not load sheet '{metric}': {e}")

        # Load coordinates and node type sheets
        coords_df, node_type_df = None, None
        try:
            coords_df = pd.read_excel(excel_file, sheet_name="coords", header=0)
            coords_df["node"] = coords_df["node"].astype(str).str.strip()
        except Exception as e:
            print(f"Warning: could not load sheet 'coords': {e}")

        try:
            node_type_df = pd.read_excel(excel_file, sheet_name="node_type", header=0)
            node_type_df["node"] = node_type_df["node"].astype(str).str.strip()
        except Exception as e:
            print(f"Warning: could not load sheet 'node_type': {e}")

        # Gather all nodes from metric sheets, coords, and node_type data
        all_nodes = set()
        for m in metrics_list:
            if sheets[m] is not None:
                all_nodes |= set(sheets[m].index.tolist())
                all_nodes |= set(sheets[m].columns.tolist())

        if coords_df is not None:
            all_nodes |= set(coords_df["node"].tolist())
        if node_type_df is not None:
            all_nodes |= set(node_type_df["node"].tolist())

        # Populate the graph with each node's information
        for node in all_nodes:
            latitude, longitude = None, None
            is_building = False

            # Parse coordinates if available
            if coords_df is not None:
                row = coords_df[coords_df["node"] == node]
                if not row.empty:
                    coords_str = row["coords"].iloc[0]
                    try:
                        lat_str, lon_str = coords_str.split(",")  # Expected format: "lat, lon" (decimal tuple)
                        latitude = float(lat_str.strip())
                        longitude = float(lon_str.strip())
                    except Exception as ex:
                        print(f"Error parsing coords '{coords_str}' for node {node}: {ex}")

            # Parse node type if available
            if node_type_df is not None:
                row = node_type_df[node_type_df["node"] == node]
                if not row.empty:
                    is_building = bool(row["is_building"].iloc[0])

            graph.add_location(node, latitude, longitude, is_building)

        # Build connections using available metrics
        for source in all_nodes:
            for destination in all_nodes:
                edge_dict = {}
                for metric in metrics_list:
                    if sheets[metric] is not None:
                        try:
                            value = sheets[metric].at[source, destination]
                            if pd.notna(value):
                                edge_dict[metric] = float(value)
                        except Exception:
                            pass
                if edge_dict:
                    graph.add_connection(source, destination, edge_dict)

        print(f"Graph data successfully loaded from {excel_file} with metrics: {metrics_list}")

    @staticmethod
    def export_graph_to_excel(graph, excel_file='compendium.xlsx'):
        """
        Exports the graph data to an Excel file.
        Writes the connection matrix along with coordinates and node type data.
        """
        # Build a dataframe for connection data
        connection_data = []
        for source, data in graph.nodes.items():
            for destination, metrics in data['connections'].items():
                row = {'source': source, 'destination': destination}
                for key, value in metrics.items():
                    row[key] = value
                connection_data.append(row)
        conn_df = pd.DataFrame(connection_data)

        # Build a dataframe for coordinates
        coords_data = []
        for node, coords in graph.location_data.items():
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            coords_data.append({'node': node, 'coords': f"{lat}, {lon}"})
        coords_df = pd.DataFrame(coords_data)

        # Build a dataframe for node type data
        node_type_data = []
        for node, is_building in graph.node_type.items():
            node_type_data.append({'node': node, 'is_building': is_building})
        type_df = pd.DataFrame(node_type_data)

        # Write data to Excel
        if os.path.exists(excel_file):
            book = load_workbook(excel_file)
            writer = pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace')
            writer.book = book
        else:
            writer = pd.ExcelWriter(excel_file, engine='openpyxl')

        conn_df.to_excel(writer, sheet_name='connections', index=False)
        coords_df.to_excel(writer, sheet_name='coords', index=False)
        type_df.to_excel(writer, sheet_name='node_type', index=False)

        writer.save()
        writer.close()
        print(f"Graph data successfully exported to {excel_file}")


# ----------------------------------------------------------------------------------
# Utility Classes for presentation to Marcel's modules
# ----------------------------------------------------------------------------------
class MarcelGraph:
    """
    Utility class for displaying the connection matrix for Marcel's Dijkstra's Algorithm.
    """
    def __init__(self, connection_matrix):
        self.graph = connection_matrix

    def test_print(self):
        """Prints the connection matrix in a formatted manner."""
        print("MarcelGraph Connection Matrix:")
        print("{")
        for node, connections in self.graph.items():
            print(f"    '{node}': {connections},")
        print("}")


class CoordGraph:
    """
    Stores a mapping from location names to (latitude, longitude).
    """
    def __init__(self):
        self.coords = {}

    def add_location(self, name, latitude, longitude):
        """Adds a location and its coordinates to the mapping."""
        self.coords[name] = (latitude, longitude)

    def get_coords(self):
        """Returns the mapping of locations to coordinates."""
        return self.coords

    def __repr__(self):
        output = "CoordGraph:\n"
        for location, coord in self.coords.items():
            output += f"  {location}: {coord}\n"
        return output


class TypeGraph:
    """
    Stores a mapping from location names to a Boolean indicating if the location is a building.
    """
    def __init__(self):
        self.types = {}

    def add_location(self, name, is_building):
        """Adds a location and its building status to the mapping."""
        self.types[name] = is_building

    def get_types(self):
        """Returns the mapping of locations to their building status."""
        return self.types

    def __repr__(self):
        output = "TypeGraph:\n"
        for location, is_building in self.types.items():
            output += f"  {location}: {is_building}\n"
        return output


# ----------------------------------------------------------------------------------
# Test Execution
# ----------------------------------------------------------------------------------


if __name__ == '__main__':
    # Initialize a graph and load data from Excel
    graph = Graph()
    try:
        graph.load_from_excel('compendium.xlsx')
    except Exception as e:
        print(f"Error loading Excel data: {e}")
    else:
        # Print the graph representation
        print(graph)
        connection_matrix = graph.get_connection_matrix()

        # Display the connection matrix using MarcelGraph
        marcel_graph = MarcelGraph(connection_matrix)
        marcel_graph.test_print()

        # Build and print the CoordGraph
        coord_graph = CoordGraph()
        for location, coords in graph.location_data.items():
            coord_graph.add_location(location, coords.get('latitude'), coords.get('longitude'))
        print(coord_graph)

        # Build and print the TypeGraph
        type_graph = TypeGraph()
        for location, is_building in graph.node_type.items():
            type_graph.add_location(location, is_building)
        print(type_graph)
        # Optionally, export the graph data back to Excel:
        # ExcelGraphIO.export_graph_to_excel(graph)
