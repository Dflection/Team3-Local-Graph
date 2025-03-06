# dijkstras_algorithm.py

import heapq
# Import the MarcelGraph class from graph_draft_1.py
from graph_draft_1 import MarcelGraph

def dijkstra(graph, start, destination):
    """
    Implements Dijkstra's algorithm to find the shortest path from a start node to a destination node in a weighted graph.

    Args:
        graph (dict): A dictionary representing the graph where keys are nodes and values are dictionaries 
        representing neighbors and their edge weights.
                      Example: {'A': {'B': 1, 'C': 3}, 'B': {'C': 1}, ...}
        start (str): The name of the starting node.
        destination (str): The name of the destination node.

    Returns:
        tuple: A tuple containing:
            - path_distances (dict): A dictionary representing the shortest path, where keys are edge pairs (e.g., "A-B") and values are edge weights.
            - shortest_distance (float): The total shortest distance from the start to the destination.
            If no path is found, returns ({}, float('inf')).
    """

    # Initialize distances to infinity for all nodes except the start node, which is set to 0.
    distances = {node: float('inf') for node in graph}
    distances[start] = 0

    # Initialize previous_nodes to None, which will store the preceding node in the shortest path.
    previous_nodes = {node: None for node in graph}

    # Initialize a priority queue (min-heap) to store nodes to be processed, prioritized by their current distance.
    # Each element in the queue is a tuple (distance, node).
    priority_queue = [(0, start)]

    # Main loop: continue until the priority queue is empty.
    while priority_queue:
        # Get the node with the smallest current distance from the priority queue.
        current_distance, current_node = heapq.heappop(priority_queue)

        # If we have reached the destination node, reconstruct and return the path and its distance.
        if current_node == destination:
            path_distances = {}
            current = destination

            # Backtrack from the destination to the start node to build the shortest path.
            while current != start:
                previous = previous_nodes[current]

                # If no previous node is found, it means there's no path, so return default values.
                if previous is None:
                    return {}, float('inf')

                # Calculate the edge weight and store it in the path_distances dictionary.
                path_distances[f"{previous}-{current}"] = graph[previous][current]
                current = previous

            # Reverse the path_distances dictionary to get the path in the correct order (start to destination).
            path_distances = dict(reversed(list(path_distances.items())))
            return path_distances, distances[destination]

        # If the current distance is greater than the known shortest distance to the current node, skip it.
        # This prevents processing outdated queue entries.
        if current_distance > distances[current_node]:
            continue

        # Iterate through the neighbors of the current node.
        for neighbor, weight in graph[current_node].items():
            # Calculate the distance to the neighbor through the current node.
            distance = current_distance + weight

            # If the calculated distance is shorter than the current shortest distance to the neighbor, update it.
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                # Add the neighbor to the priority queue with its new distance.
                heapq.heappush(priority_queue, (distance, neighbor))

    # If the destination node is not reached, it means there is no path, so return default values.
    return {}, float('inf')

# Example Usage (now using the MarcelGraph from graph_draft_1.py)
if __name__ == "__main__":
    # Import Graph from graph_draft_1.py for the ability to import from excel.
    from graph_draft_1 import Graph
    graph_loader = Graph()
    try:
        graph_loader.load_from_excel()
    except Exception as e:
        print(f"Error loading Excel data: {e}")
        exit()

    connection_matrix = graph_loader.get_connection_matrix()
    marcel_graph = MarcelGraph(connection_matrix)
    # The dictionary within MarcelGraph, which is stored as self.graph, is now used by Dijkstra's.
    graph_data = marcel_graph.graph


    # Define the start and destination nodes.
    start_node = 'Manzanita'
    destination_node = 'Node A'

    # Run Dijkstra's algorithm and get the shortest path and distance.
    path, shortest_distance = dijkstra(graph_data, start_node, destination_node)

    # Print the results.
    if shortest_distance == float('inf'):
        print(f"No path found from {start_node} to {destination_node}")
    else:
        print(f"Shortest path from {start_node} to {destination_node}: {path}, Total Distance: {shortest_distance}")
