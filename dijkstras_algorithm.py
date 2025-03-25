import heapq
from edgegraph import MarcelGraph, Graph


def dijkstra(graph, start, destination, metric='time'):
    """
    Implements Dijkstra's algorithm to find the shortest path from a start node
    to a destination node using the specified metric.

    Args:
        graph (dict): A dictionary representing the graph. Each key is a node,
                      and each value is a dictionary of neighbor nodes with a
                      dictionary of metrics (e.g., {'time': 5, 'distance': 10, ...}).
        start (str): The name of the starting node.
        destination (str): The name of the destination node.
        metric (str, optional): The metric to optimize (e.g. 'time', 'distance').
                                Defaults to 'time'.

    Returns:
        tuple(dict, float): A tuple (path_metrics, total_metric) where:
            - path_metrics is an ordered dictionary of edges in the format {"A-B": cost, ...}
            - total_metric is the total accumulated cost along the path.
        If no path is found, returns ({}, float('inf')).
    """
    # Initialize distances and previous nodes
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous_nodes = {node: None for node in graph}
    priority_queue = [(0, start)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        # Check if destination is reached
        if current_node == destination:
            path_metrics = {}
            current = destination
            # Reconstruct the path backwards
            while current != start:
                prev = previous_nodes[current]
                if prev is None:
                    return {}, float('inf')
                # Retrieve the cost for the edge from prev to current
                edge = graph[prev][current]
                value = edge.get(metric, float('inf'))
                path_metrics[f"{prev}-{current}"] = value
                current = prev
            # Reverse the order to get forward path
            path_metrics = dict(reversed(list(path_metrics.items())))
            return path_metrics, distances[destination]

        # Skip outdated entries in the queue
        if current_distance > distances[current_node]:
            continue

        # Evaluate all neighbors for potential relaxation
        for neighbor, edge_metrics in graph[current_node].items():
            edge_cost = edge_metrics.get(metric)
            if edge_cost is None:
                continue  # Skip if chosen metric is missing
            new_distance = current_distance + edge_cost

            # Relaxation: update distance if a shorter path is found
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))

    # No path found if loop exits without returning
    return {}, float('inf')


# Example usage
if __name__ == "__main__":
    # Load the graph data from Excel
    graph_loader = Graph()
    try:
        graph_loader.load_from_excel('compendium.xlsx')
    except Exception as e:
        print(f"Error loading Excel data: {e}")
        exit()

    # -------------------------------------------
    # DEBUG: Print node coordinates and building status
    # -------------------------------------------
    print("=== Checking node coordinates ===")
    for node_name, coord_data in graph_loader.location_data.items():
        lat = coord_data.get('latitude')
        lon = coord_data.get('longitude')
        print(f"  {node_name}: lat={lat}, lon={lon}")

    print("\n=== Checking node building status ===")
    for node_name, is_building in graph_loader.node_type.items():
        print(f"  {node_name}: {is_building}")

    # Retrieve the graph connection matrix and wrap it for display
    connection_matrix = graph_loader.get_connection_matrix()
    marcel_graph = MarcelGraph(connection_matrix)
    graph_data = marcel_graph.graph  # Dictionary with nodes and metrics

    # Define start and destination nodes (adjust as needed)
    start_node = 'Manzanita'
    destination_node = 'Node A'  # Replace with an actual node name from your Excel file.

    # Run Dijkstra's algorithm for the specified metric
    path, shortest_metric = dijkstra(graph_data, start_node, destination_node, metric='time')

    if shortest_metric == float('inf'):
        print(f"\nNo path found from '{start_node}' to '{destination_node}' using metric 'time'.")
    else:
        print(f"\nShortest path from '{start_node}' to '{destination_node}' using 'time':")
        for edge, cost in path.items():
            print(f"  {edge} : {cost}")
        print(f"Total: {shortest_metric}")
