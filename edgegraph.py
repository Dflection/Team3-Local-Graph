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

    The graph stores:
      - Nodes: A dictionary where each key is a location name and the value is a dictionary
               containing connected node's names as key and its edge weight (a dictionary of metrics) as value.
      - Location Data: A dictionary mapping each location to its latitude and longitude.
      - Node Type: A dictionary mapping each location to a Boolean indicating whether it's a building.
      - (All edge metrics are stored per edge.)
    """
    def __init__(self):
        self.nodes = {}           # e.g., {'A': {'name': 'A', 'connections': {...}}}
        self.location_data = {}   # e.g., {'A': {'latitude': 38.0, 'longitude': -120.0}}
        self.node_type = {}       # e.g., {'A': True or False}

    def add_location(self, name, latitude, longitude, is_building=False):
        if name not in self.nodes:
            self.nodes[name] = {'name': name, 'connections': {}}
            self.location_data[name] = {'latitude': latitude, 'longitude': longitude}
            self.node_type[name] = is_building

    def add_connection(self, source, destination, weight):
        """
        Adds a connection from source to destination.
        The weight can be a dictionary of metrics (time, distance, etc.).
        """
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Both locations must be added before connecting them.")
        if isinstance(weight, dict):
            self.nodes[source]['connections'][destination] = weight
        else:
            self.nodes[source]['connections'][destination] = float(weight)

    def get_connection_matrix(self):
        """
        Returns a dictionary mapping each node to its connections and associated metrics.
        """
        return {node: data['connections'] for node, data in self.nodes.items()}

    def load_from_excel(self, excel_file='compendium.xlsx'):
        """
        Loads the graph from an Excel file. It expects:
          - Sheets named "time", "distance", "gain", "loss" (for metrics)
          - A sheet named "coords" with columns "node" and "coords" (like "38.031, -120.3877")
          - A sheet named "node_type" with columns "node" and "is_building"
        """
        ExcelGraphIO.load_graph_from_excel(self, excel_file)

    def __repr__(self):
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
    This version assumes your Excel file (compendium.xlsx) has:
      - 4 sheets named: "time", "distance", "gain", "loss" (each is an adjacency matrix).
      - 1 sheet named "coords" (columns "node" and "coords" in the format "lat, lon").
      - 1 sheet named "node_type" (columns "node" and "is_building").
    """
    @staticmethod
    def load_graph_from_excel(graph, excel_file='compendium.xlsx'):
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Excel file not found at {excel_file}")

        # Load metric sheets
        metrics_list = ['time', 'distance', 'gain', 'loss']
        sheets = {}
        for metric in metrics_list:
            try:
                df = pd.read_excel(excel_file, sheet_name=metric, header=0, index_col=0)
                # Clean up row & column labels
                df.index = df.index.map(lambda x: str(x).strip())
                df.columns = [str(col).strip() for col in df.columns]
                sheets[metric] = df
            except Exception as e:
                sheets[metric] = None
                print(f"Warning: could not load sheet '{metric}': {e}")

        # Load coords and node_type sheets
        coords_df, node_type_df = None, None

        try:
            coords_df = pd.read_excel(excel_file, sheet_name="coords", header=0)
            # Expect columns "node", "coords"
            coords_df["node"] = coords_df["node"].astype(str).str.strip()
        except Exception as e:
            print(f"Warning: could not load sheet 'coords': {e}")

        try:
            node_type_df = pd.read_excel(excel_file, sheet_name="node_type", header=0)
            # Expect columns "node", "is_building"
            node_type_df["node"] = node_type_df["node"].astype(str).str.strip()
        except Exception as e:
            print(f"Warning: could not load sheet 'node_type': {e}")

        # Gather all nodes from the metric sheets plus coords/node_type
        all_nodes = set()
        for m in metrics_list:
            if sheets[m] is not None:
                all_nodes |= set(sheets[m].index.tolist())
                all_nodes |= set(sheets[m].columns.tolist())

        if coords_df is not None:
            all_nodes |= set(coords_df["node"].tolist())

        if node_type_df is not None:
            all_nodes |= set(node_type_df["node"].tolist())

        # Populate the graph with each node's info
        for node in all_nodes:
            latitude, longitude = None, None
            is_building = False

            # Pull coordinate data if it exists
            if coords_df is not None:
                row = coords_df[coords_df["node"] == node]
                if not row.empty:
                    coords_str = row["coords"].iloc[0]
                    try:
                        # Split on comma (e.g. "38.031, -120.3877")
                        lat_str, lon_str = coords_str.split(",")
                        latitude = float(lat_str.strip())
                        longitude = float(lon_str.strip())
                    except Exception as ex:
                        print(f"Error parsing coords '{coords_str}' for node {node}: {ex}")

            # Pull building info if it exists
            if node_type_df is not None:
                row = node_type_df[node_type_df["node"] == node]
                if not row.empty:
                    is_building = bool(row["is_building"].iloc[0])

            graph.add_location(node, latitude, longitude, is_building)

        # Build the connections with all available metrics
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
        Exports connection data along with node info to an Excel file.
        This will write the connection matrix (all metrics),
        plus the coords and node_type sheets.
        """
        # Build a dataframe of edges with metrics
        connection_data = []
        for source, data in graph.nodes.items():
            for destination, metrics in data['connections'].items():
                row = {'source': source, 'destination': destination}
                for key, value in metrics.items():
                    row[key] = value
                connection_data.append(row)
        conn_df = pd.DataFrame(connection_data)

        # Build coords dataframe
        coords_data = []
        for node, coords in graph.location_data.items():
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            coords_data.append({'node': node, 'coords': f"{lat}, {lon}"})
        coords_df = pd.DataFrame(coords_data)

        # Build node_type dataframe
        node_type_data = []
        for node, is_building in graph.node_type.items():
            node_type_data.append({'node': node, 'is_building': is_building})
        type_df = pd.DataFrame(node_type_data)

        # Write to Excel
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
    Utility class for displaying the connection matrix.
    """
    def __init__(self, connection_matrix):
        self.graph = connection_matrix

    def test_print(self):
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
        self.coords[name] = (latitude, longitude)

    def get_coords(self):
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
        self.types[name] = is_building

    def get_types(self):
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
    graph = Graph()
    try:
        graph.load_from_excel('compendium.xlsx')
    except Exception as e:
        print(f"Error loading Excel data: {e}")
    else:
        print(graph)
        connection_matrix = graph.get_connection_matrix()
        marcel_graph = MarcelGraph(connection_matrix)
        marcel_graph.test_print()

        coord_graph = CoordGraph()
        for location, coords in graph.location_data.items():
            coord_graph.add_location(location, coords.get('latitude'), coords.get('longitude'))
        print(coord_graph)

        type_graph = TypeGraph()
        for location, is_building in graph.node_type.items():
            type_graph.add_location(location, is_building)
        print(type_graph)
        # Optionally, export the graph data back to Excel:
        # ExcelGraphIO.export_graph_to_excel(graph)
