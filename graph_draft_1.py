# The Local Graph, Edge Graph Module - by Chase Varvayanis
# 2-20-2025
# Code Linted with Flake8, Spellchecked with Code Spell Checker, and general Cleanup and formatting with ChatGPT where
# noted.

import os
import pandas as pd
from openpyxl import load_workbook


class Graph:
    """
    Represents a directed graph where nodes are locations storing
    travel times between locations. Nodes are unidirectional and only store connections they lead to.
    """
    def __init__(self):
        """Initializes the graph with empty dictionaries for nodes, location data, and node types."""
        self.nodes = {}
        self.location_data = {}  # Stores latitude and longitude for later use
        self.node_type = {}      # Stores node type: True for building, False for intersection

    def add_location(self, name, latitude, longitude, is_building=False):
        """
        Adds a location to the graph with its latitude, longitude, name, and node type.
        is_building: True indicates a building; False indicates an intersection.
        """
        if name not in self.nodes:
            self.nodes[name] = {'name': name, 'connections': {}}
            self.location_data[name] = {'latitude': latitude, 'longitude': longitude}
            self.node_type[name] = is_building

    def add_connection(self, source, destination, time):
        """Creates a unidirectional connection from source to destination with a given travel time.
        
        The time is converted to a Python int to avoid printing np.float64.
        """
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Both locations must be added before connecting them.")
        # Convert the time to a Python int before storing it.
        self.nodes[source]['connections'][destination] = int(time)

    def load_from_excel(self, excel_file='data.xlsx'):
        """
        Loads graph data from an Excel workbook.
        Expects the following sheets:
          - 'coords': Contains coordinate data for each location.
                      Required columns: 'location' and 'coords' (in format "(lat, lon)").
          - 'node_type': Contains the node type data.
                         Required columns: 'location' and 'is_building'.
          - 'time' (optional): An adjacency matrix where the row index represents source nodes,
                      the columns represent destination nodes, and each cell is the travel time.
                      If a cell is blank or NaN, no connection is added.
        """
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Excel file not found at {excel_file}")

        # --- Load node_type sheet ---
        try:
            node_type_df = pd.read_excel(excel_file, sheet_name='node_type', header=0)
            node_type_df.columns = node_type_df.columns.str.strip().str.lower()
        except Exception as e:
            raise Exception(f"Failed to load 'node_type' sheet: {e}")

        node_type_mapping = {}
        for _, row in node_type_df.iterrows():
            location = row['location']
            is_building = row['is_building']
            node_type_mapping[location] = is_building

        # --- Load coords sheet ---
        try:
            coords_df = pd.read_excel(excel_file, sheet_name='coords', header=0)
            coords_df.columns = coords_df.columns.str.strip().str.lower()
        except Exception as e:
            raise Exception(f"Failed to load 'coords' sheet: {e}")

        for _, row in coords_df.iterrows():
            location = row['location']
            coords_str = str(row['coords'])
            coords_str = coords_str.strip("()")
            try:
                lat_str, lon_str = coords_str.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
            except Exception as e:
                raise ValueError(f"Invalid coordinates format for location {location}: {row['coords']}")
            is_building = node_type_mapping.get(location, False)
            self.add_location(location, lat, lon, is_building=is_building)

        # --- Load connection data from the 'time' sheet if it exists ---
        xls = pd.ExcelFile(excel_file)
        if "time" in xls.sheet_names:
            try:
                # Read the time sheet as a matrix using the first column as the row index.
                time_df = pd.read_excel(excel_file, sheet_name='time', header=0, index_col=0)
                # Normalize the index (source nodes) and column names (destination nodes)
                time_df.index = time_df.index.map(lambda x: str(x).strip())
                time_df.columns = [str(col).strip() for col in time_df.columns]
            except Exception as e:
                print(f"Failed to load 'time' sheet, skipping connection data: {e}")
            else:
                for source in time_df.index:
                    for destination in time_df.columns:
                        travel_time = time_df.at[source, destination]
                        # If a travel time is provided (i.e. not NaN), add the connection.
                        if pd.notna(travel_time):
                            if source not in self.nodes:
                                self.add_location(source, None, None, is_building=node_type_mapping.get(source, False))
                            if destination not in self.nodes:
                                self.add_location(destination, None, None, is_building=node_type_mapping.get(destination, False))
                            self.add_connection(source, destination, travel_time)
        else:
            print("No 'time' sheet found, skipping connection data load.")

        print(f"Graph data successfully loaded from {excel_file}")

    def export_to_excel(self, excel_file='data.xlsx'):
        """
        Exports the graph data to an Excel workbook with three sheets:
          - 'coords': Contains coordinates as a tuple (latitude, longitude) for each location.
          - 'node_type': Contains the node type (True for building, False for intersection) for each location.
          - 'time': Contains connection data (source, destination, travel time).
        """
        # Build DataFrame for connection data.
        connection_data = []
        for source, data in self.nodes.items():
            for destination, travel_time in data['connections'].items():
                connection_data.append({'source': source, 'destination': destination, 'time': travel_time})
        time_df = pd.DataFrame(connection_data)

        # Build DataFrame for coordinate data.
        coords_data = []
        for location, coords in self.location_data.items():
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            coords_data.append({'location': location, 'coords': f"({lat}, {lon})"})
        coords_df = pd.DataFrame(coords_data)

        # Build DataFrame for node type data.
        node_type_data = []
        for location, is_building in self.node_type.items():
            node_type_data.append({'location': location, 'is_building': is_building})
        node_type_df = pd.DataFrame(node_type_data)

        # Write the DataFrames to the Excel workbook.
        if os.path.exists(excel_file):
            book = load_workbook(excel_file)
            writer = pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace')
            writer.book = book
        else:
            writer = pd.ExcelWriter(excel_file, engine='openpyxl')

        time_df.to_excel(writer, sheet_name='time', index=False)
        coords_df.to_excel(writer, sheet_name='coords', index=False)
        node_type_df.to_excel(writer, sheet_name='node_type', index=False)

        writer.save()
        writer.close()
        print(f"Graph data successfully exported to {excel_file}")

    def print_raw_graph(self):
        """Prints the raw contents of the graph: nodes, location data, and node types."""
        print("Raw Graph Data:")
        print("Nodes:", self.nodes)
        print("Location Data:", self.location_data)
        print("Node Types:", self.node_type)

    def get_connection_matrix(self):
        """
        Constructs and returns a dictionary representing the connection matrix of the graph.
        Each key is a node, and its value is a dictionary of destination nodes with travel times.
        """
        connection_matrix = {}
        for node, data in self.nodes.items():
            connection_matrix[node] = data['connections']
        return connection_matrix

    def __repr__(self):
        """
        Returns a string representation of the graph, listing each node with its details, including node type,
        and its connections.
        """
        output = "Graph Representation:\n"
        for node, data in self.nodes.items():
            output += f"Location: {data['name']}\n"
            output += f"  Latitude: {self.location_data.get(node, {}).get('latitude', 'N/A')}\n"
            output += f"  Longitude: {self.location_data.get(node, {}).get('longitude', 'N/A')}\n"
            output += f"  Node Type (is_building): {self.node_type.get(node, 'N/A')}\n"
            output += "  Connections:\n"
            for conn, time in data['connections'].items():
                output += f"    -> {conn} (Time: {time} sec)\n"
        return output


class MarcelGraph:
    """
    Represents the connection matrix of a Graph in a dictionary format.
    This object is used for testing and displays the matrix in a formatted manner.
    """
    def __init__(self, connection_matrix):
        self.graph = connection_matrix

    def test_print(self):
        """
        Prints the connection matrix in a formatted manner similar to the example:
        
        graph = {
            'A': {'B': 1},
            'B': {'C': 2, 'D': 1},
            ...
        }
        """
        print("MarcelGraph Connection Matrix:")
        print("{")
        for node, connections in self.graph.items():
            print(f"    '{node}': {connections},")
        print("}")


if __name__ == '__main__':
    graph = Graph()
    try:
        graph.load_from_excel()
    except Exception as e:
        print(f"Error loading Excel data: {e}")
    else:
        print(graph)
        # graph.print_raw_graph()
        # Generate the connection matrix and create a MarcelGraph object.
        connection_matrix = graph.get_connection_matrix()
        marcel_graph = MarcelGraph(connection_matrix)
        # Test method to print the connection matrix in a formatted manner.
        marcel_graph.test_print()
        # Optionally, export the graph data back to Excel.
        # graph.export_to_excel()

