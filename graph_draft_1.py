# The Local Graph, Edge Graph Module - by Chase Varvayanis
# 2-20-2025
# Code Linted with Flake8, Spellchecked with Code Spell Checker, and general Cleanup and formatting with ChatGPT where
# noted.

import csv
import os


class Graph:
    """
    Represents a directed graph where nodes are locations storing
    travel times between locations. Nodes are unidirectional and only store connections they lead to,
    not those leading to them.
    """
    def __init__(self):
        """Initializes the graph with empty dictionaries for nodes and location data."""
        self.nodes = {}
        self.location_data = {}  # Stores latitude and longitude for later use

    def add_location(self, name, latitude, longitude):
        """Adds a location to the graph with its latitude, longitude, and name."""
        if name not in self.nodes:
            self.nodes[name] = {'name': name, 'connections': {}}
            self.location_data[name] = {'latitude': latitude, 'longitude': longitude}

    def add_connection(self, source, destination, time):
        """Creates a unidirectional connection from source to destination with a given travel time."""
        if source not in self.nodes or destination not in self.nodes:
            raise ValueError("Both locations must be added before connecting them.")

        self.nodes[source]['connections'][destination] = time  # Unidirectional path away from node

    def load_from_csv(self):
        """
        Loads location and connection data from a CSV file located in the parent directory.
        The CSV file should contain:
        - Location names in the first column
        - Latitude and longitude in the next two columns
        - Travel time (seconds) between locations in subsequent columns
        - Heading will look something like this:
              ",Latitude,Longitude,Location-1-Name,Location-2-Name,Location-3-Name,Location-4-Name,..."
              (Do not forget leading comma in heading)
        """
        file_path = os.path.join(os.path.dirname(__file__), '.', 'localgraph.csv')
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            locations = headers[3:]  # Columns 3 and beyond

            for row in reader:
                source = row[0]
                latitude = row[1]
                longitude = row[2]
                self.add_location(source, latitude, longitude)

                for i, destination in enumerate(locations, start=3):  # Adds destinations to nodes
                    if row[i].strip():  # Ignore blank values, values without connection
                        time = float(row[i])
                        self.add_location(destination, None, None)  # Add destination if not already added
                        self.add_connection(source, destination, time)

    def print_raw_graph(self):
        """Prints the raw contents of the graph, nodes and location data."""
        print("Raw Graph Data:")
        print("Nodes:", self.nodes)
        print("Location Data:", self.location_data)

    def __repr__(self):
        """
        Returns a string representation of the graph, listing each node with its data and connections.
        Prettified w/ ChatGPT
        """
        output = "Graph Representation:\n"
        for node, data in self.nodes.items():
            output += f"Location: {data['name']}\n"
            output += f"  Latitude: {self.location_data.get(node, {}).get('latitude', 'N/A')}\n"
            output += f"  Longitude: {self.location_data.get(node, {}).get('longitude', 'N/A')}\n"
            output += "  Connections:\n"
            for conn, time in data['connections'].items():
                output += f"    -> {conn} (Time: {time} sec)\n"
        return output


if __name__ == '__main__':
    graph = Graph()
    graph.load_from_csv()
    print(graph)
    graph.print_raw_graph()
