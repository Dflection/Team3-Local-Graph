# The Local Graph, Edge Graph Module - by Chase Varvayanis
# 3-11-2025
# Code Linted with Flake8, Spellchecked with Code Spell Checker, and general Cleanup and formatting with ChatGPT

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
               containing connected node's names as key and its connection weight as value.
      - Location Data: A dictionary that maps each location to its latitude and longitude.
      - Node Type: A dictionary mapping each location to a Boolean indicating whether it's
                   a building (True) or an intersection (False).
    """
    def __init__(self):
        # Initialize empty dictionaries for nodes, location data, and node types.
        self.nodes = {}           # e.g., {'A': {'name': 'A', 'connections': {'B': 5}}}
        self.location_data = {}   # e.g., {'A': {'latitude': 40.7128, 'longitude': -74.0060}}
        self.node_type = {}       # e.g., {'A': True}  (True indicates building)

    def add_location(self, name, latitude, longitude, is_building=False):
        """
        Adds a new location to the graph.

        Parameters:
          - name (str): The name/identifier of the location.
          - latitude (float or None): The latitude coordinate.
          - longitude (float or None): The longitude coordinate.
          - is_building (bool): True if the location is a building; otherwise, False.

        If the location is not already in the graph, the method initializes its entry
        in the nodes, location_data, and node_type dictionaries.
        """
        if name not in self.nodes:
            # Create node entry with an empty connection dictionary.
            self.nodes[name] = {'name': name, 'connections': {}}
            # Store coordinate data.
            self.location_data[name] = {'latitude': latitude, 'longitude': longitude}
            # Store node type data.
            self.node_type[name] = is_building

    def add_connection(self, source, destination, travel_time):
        """
        Creates a unidirectional connection from the source location to the destination location.

        Parameters:
          - source (str): The starting location.
          - destination (str): The target location.
          - travel_time (numeric): The travel time between the source and destination.

        The travel time is converted to an integer to avoid issues with numeric types like np.float64.
        returned by the Excel workbook reader.

        Raises a ValueError if either the source or destination node does not exist.
        """
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Both locations must be added before connecting them.")
        # Store the travel time as an integer.
        self.nodes[source]['connections'][destination] = int(travel_time)

    def get_connection_matrix(self):
        """
        Constructs and returns the connection matrix of the graph.

        Returns:
          A dictionary where each key is a location and its value is a dictionary of destination
          nodes with their corresponding travel times.
        """
        return {node: data['connections'] for node, data in self.nodes.items()}

    def __repr__(self):
        """
        Returns a human-readable string representation of the graph.

        It lists each location with its name, coordinates, node type, and the details of its connections.
        """
        output = "Graph Representation:\n"
        for node, data in self.nodes.items():
            output += f"Location: {data['name']}\n"
            lat = self.location_data.get(node, {}).get('latitude', 'N/A')
            lon = self.location_data.get(node, {}).get('longitude', 'N/A')
            output += f"  Latitude: {lat}\n"
            output += f"  Longitude: {lon}\n"
            output += f"  Node Type (is_building): {self.node_type.get(node, 'N/A')}\n"
            output += "  Connections:\n"
            # Iterate over connections and list travel times.
            for dest, t in data['connections'].items():
                output += f"    -> {dest} (Time: {t} sec)\n"
        return output

# ----------------------------------------------------------------------------------
# ExcelGraphIO Class
# ----------------------------------------------------------------------------------


class ExcelGraphIO:
    """
    Handles all Excel input/output operations for the graph.

    This class contains static methods for loading graph data from an Excel file and
    exporting graph data to an Excel file. The Excel file is expected to have three sheets:
      - 'node_type': Contains location names and a boolean for is_building.
      - 'coords': Contains location names and coordinates in the format "(lat, lon)".
      - 'time' (optional): An adjacency matrix of travel times between locations.
    """

    @staticmethod
    def load_graph_from_excel(graph, excel_file='data.xlsx'):
        """
        Loads graph data from the specified Excel file into the provided Graph object.

        Parameters:
          - graph (Graph): An instance of the Graph class to populate.
          - excel_file (str): Path to the Excel file (default is 'data.xlsx').

        Raises:
          - FileNotFoundError: If the Excel file does not exist.
          - Exception: For issues reading the 'node_type' or 'coords' sheets.
          - ValueError: If coordinate data is in an invalid format.
        """
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Excel file not found at {excel_file}")

        # ---------------------------
        # Load Node Type Data
        # ---------------------------
        try:
            node_type_df = pd.read_excel(excel_file, sheet_name='node_type', header=0)
            # Standardize column names (strip spaces and lower case).
            node_type_df.columns = node_type_df.columns.str.strip().str.lower()
        except Exception as e:
            raise Exception(f"Failed to load 'node_type' sheet: {e}")

        # Create mapping from location to its building status.
        node_type_mapping = {}
        for _, row in node_type_df.iterrows():
            location = row['location']
            is_building = row['is_building']
            node_type_mapping[location] = is_building

        # ---------------------------
        # Load Coordinate Data
        # ---------------------------
        try:
            coords_df = pd.read_excel(excel_file, sheet_name='coords', header=0)
            coords_df.columns = coords_df.columns.str.strip().str.lower()
        except Exception as e:
            raise Exception(f"Failed to load 'coords' sheet: {e}")

        # Process each row to extract latitude and longitude.
        for _, row in coords_df.iterrows():
            location = row['location']
            # Remove surrounding parentheses.
            coords_str = str(row['coords']).strip("()")
            try:
                # Split the coordinate string into latitude and longitude.
                lat_str, lon_str = coords_str.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
            except Exception:
                raise ValueError(f"Invalid coordinates format for location {location}: {row['coords']}")
            # Use node_type mapping to determine if this location is a building.
            is_building = node_type_mapping.get(location, False)
            graph.add_location(location, lat, lon, is_building)

        # ---------------------------
        # Load Connection Data (Time Sheet)
        # ---------------------------
        xls = pd.ExcelFile(excel_file)
        if "time" in xls.sheet_names:
            try:
                # Read the 'time' sheet as an adjacency matrix.
                time_df = pd.read_excel(excel_file, sheet_name='time', header=0, index_col=0)
                # Clean up row and column labels by stripping spaces.
                time_df.index = time_df.index.map(lambda x: str(x).strip())
                time_df.columns = [str(col).strip() for col in time_df.columns]
            except Exception as e:
                print(f"Failed to load 'time' sheet, skipping connection data: {e}")
            else:
                # Iterate over the matrix and add connections where travel time is provided.
                for source in time_df.index:
                    for destination in time_df.columns:
                        travel_time = time_df.at[source, destination]
                        if pd.notna(travel_time):
                            # Ensure both source and destination are in the graph.
                            if source not in graph.nodes:
                                graph.add_location(source, None, None, node_type_mapping.get(source, False))
                            if destination not in graph.nodes:
                                graph.add_location(destination, None, None, node_type_mapping.get(destination, False))
                            graph.add_connection(source, destination, travel_time)
        else:
            # Inform the user that the 'time' sheet is not present.
            print("No 'time' sheet found, skipping connection data load.")

        print(f"Graph data successfully loaded from {excel_file}")

    @staticmethod  # These were kinda neat to learn about, might be a cool python 1 addition
    def export_graph_to_excel(graph, excel_file='data.xlsx'):
        """
        Exports the graph data to an Excel file with three sheets: 'time', 'coords', and 'node_type'.

        Parameters:
          - graph (Graph): The graph object containing the data to export.
          - excel_file (str): The destination Excel file (default is 'data.xlsx')

        The method constructs DataFrames for each aspect of the graph and writes them to the file.
        If the file already exists, it replaces the existing sheets.
        """
        # ---------------------------
        # Prepare Connection Data
        # ---------------------------
        connection_data = []
        for source, data in graph.nodes.items():
            for destination, travel_time in data['connections'].items():
                connection_data.append({'source': source, 'destination': destination, 'time': travel_time})
        time_df = pd.DataFrame(connection_data)

        # ---------------------------
        # Prepare Coordinate Data
        # ---------------------------
        coords_data = []
        for location, coords in graph.location_data.items():
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            coords_data.append({'location': location, 'coords': f"({lat}, {lon})"})
        coords_df = pd.DataFrame(coords_data)

        # ---------------------------
        # Prepare Node Type Data
        # ---------------------------
        node_type_data = []
        for location, is_building in graph.node_type.items():
            node_type_data.append({'location': location, 'is_building': is_building})
        node_type_df = pd.DataFrame(node_type_data)

        # ---------------------------
        # Write DataFrames to Excel
        # ---------------------------
        # If the file exists, open it and replace existing sheets; otherwise, create a new file.
        if os.path.exists(excel_file):
            book = load_workbook(excel_file)
            writer = pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace')
            writer.book = book
        else:
            writer = pd.ExcelWriter(excel_file, engine='openpyxl')

        # Write each DataFrame to its respective sheet.
        time_df.to_excel(writer, sheet_name='time', index=False)
        coords_df.to_excel(writer, sheet_name='coords', index=False)
        node_type_df.to_excel(writer, sheet_name='node_type', index=False)

        writer.save()
        writer.close()
        print(f"Graph data successfully exported to {excel_file}")

# ----------------------------------------------------------------------------------
# Utility Classes for presentation to Marcel's modules
# ----------------------------------------------------------------------------------


class MarcelGraph:
    """
    Utility class for displaying the connection matrix in a formatted manner.

    This is mainly used for testing purposes, allowing a quick view of the connections.
    """
    def __init__(self, connection_matrix):
        self.graph = connection_matrix

    def test_print(self):
        """
        Prints the connection matrix in a readable format, Visualizes the output Marcel requested.

        Example output:
        {
            'A': {'B': 5},
            'B': {'C': 10, 'D': 3},
            ...
        }
        """
        print("MarcelGraph Connection Matrix:")
        print("{")
        for node, connections in self.graph.items():
            print(f"    '{node}': {connections},")
        print("}")


class CoordGraph:
    """
    Stores a mapping from location names to a tuple of (latitude, longitude).

    This class is useful for managing and retrieving coordinate data separately from the graph.
    """
    def __init__(self):
        self.coords = {}  # Dictionary to hold location -> (latitude, longitude)

    def add_location(self, name, latitude, longitude):
        """
        Adds a location's coordinate data.

        Parameters:
          - name (str): The location name.
          - latitude (float or None): The latitude value.
          - longitude (float or None): The longitude value.
        """
        self.coords[name] = (latitude, longitude)

    def get_coords(self):
        """
        Returns the complete dictionary of coordinates.
        """
        return self.coords

    def __repr__(self):
        """
        Returns a formatted string representation of the coordinate mapping.
        """
        output = "CoordGraph:\n"
        for location, coord in self.coords.items():
            output += f"  {location}: {coord}\n"
        return output


class TypeGraph:
    """
    Stores a mapping from location names to a Boolean indicating whether the location is a building. True == Building.

    This class separates building type data for easier management and retrieval.
    """
    def __init__(self):
        self.types = {}  # Dictionary to hold location -> is_building (bool)

    def add_location(self, name, is_building):
        """
        Adds the building type for a given location.

        Parameters:
          - name (str): The location name.
          - is_building (bool): True if the location is a building; otherwise, False.
        """
        self.types[name] = is_building

    def get_types(self):
        """
        Returns the complete dictionary of location types.
        """
        return self.types

    def __repr__(self):
        """
        Returns a formatted string representation of the type mapping.
        """
        output = "TypeGraph:\n"
        for location, is_building in self.types.items():
            output += f"  {location}: {is_building}\n"
        return output

# ----------------------------------------------------------------------------------
# Test Execution
# ----------------------------------------------------------------------------------


if __name__ == '__main__':
    # Instantiate an empty Graph.
    graph = Graph()
    try:
        # Load graph data from the Excel file into the graph using ExcelGraphIO.
        ExcelGraphIO.load_graph_from_excel(graph)
    except Exception as e:
        print(f"Error loading Excel data: {e}")
    else:
        # Display the graph representation.
        print(graph)

        # Retrieve and print the connection matrix using MarcelGraph.
        connection_matrix = graph.get_connection_matrix()
        marcel_graph = MarcelGraph(connection_matrix)
        marcel_graph.test_print()

        # Build and display the CoordGraph by extracting coordinate data from the graph.
        coord_graph = CoordGraph()
        for location, coords in graph.location_data.items():
            coord_graph.add_location(location, coords.get('latitude'), coords.get('longitude'))
        print(coord_graph)

        # Build and display the TypeGraph by extracting node type data from the graph.
        type_graph = TypeGraph()
        for location, is_building in graph.node_type.items():
            type_graph.add_location(location, is_building)
        print(type_graph)

        # Optionally, export the graph data back to Excel.
        # ExcelGraphIO.export_graph_to_excel(graph)
