# Thanks to Marcel
import heapq
from edgegraph import MarcelGraph, Graph

def dijkstra(graph, start, destination, metric='time'):
    """
    Implements Dijkstra's algorithm to find the shortest path from a start node
    to a destination node using the specified metric.
    
    Args:
        graph (dict):
            A dictionary representing your graph, where each key is a node
            and each value is a dictionary of neighbors. Each neighbor’s value
            is itself a dictionary of metrics (e.g. {'time': 5, 'distance': 10, ...}).
        start (str): 
            The name of the starting node.
        destination (str): 
            The name of the destination node.
        metric (str, optional): 
            The metric you want to optimize. For example: 'time', 'distance',
            'gain', or 'loss'. Defaults to 'time'.
    
    Returns:
        tuple(dict, float):
            (path_metrics, total_metric), where:
              - path_metrics is an ordered dictionary of edges on the path 
                (e.g. {"Start-A": 3, "A-B": 5, ...}), with the chosen metric value.
              - total_metric is the total accumulated metric along the path.
            If no path is found, returns ({}, float('inf')).
    """
    # Initialize all distances to infinity, except for the start node
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous_nodes = {node: None for node in graph}
    priority_queue = [(0, start)]
    
    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        
        # If we've reached the destination, reconstruct the path
        if current_node == destination:
            path_metrics = {}
            current = destination
            while current != start:
                prev = previous_nodes[current]
                if prev is None:
                    return {}, float('inf')
                # The edge between prev -> current has a dict of metrics
                edge = graph[prev][current]
                value = edge.get(metric, float('inf'))
                path_metrics[f"{prev}-{current}"] = value
                current = prev
            # Reverse the path so it goes in the correct forward order
            path_metrics = dict(reversed(list(path_metrics.items())))
            return path_metrics, distances[destination]
        
        # If the current node's distance is outdated, skip it
        if current_distance > distances[current_node]:
            continue
        
        # Check neighbors
        for neighbor, edge_metrics in graph[current_node].items():
            # If this neighbor doesn't have the chosen metric, skip it
            edge_cost = edge_metrics.get(metric)
            if edge_cost is None:
                continue
            new_distance = current_distance + edge_cost
            
            # Relaxation step
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))
    
    # If we exhaust the queue without finding the destination
    return {}, float('inf')


# Example usage
if __name__ == "__main__":
    graph_loader = Graph()
    try:
        graph_loader.load_from_excel('compendium.xlsx')
    except Exception as e:
        print(f"Error loading Excel data: {e}")
        exit()
    
    # -------------------------------------------
    # DEBUG: Confirm node coords and building status
    # -------------------------------------------
    print("=== Checking node coordinates ===")
    for node_name, coord_data in graph_loader.location_data.items():
        lat = coord_data.get('latitude')
        lon = coord_data.get('longitude')
        print(f"  {node_name}: lat={lat}, lon={lon}")

    print("\n=== Checking node building status ===")
    for node_name, is_building in graph_loader.node_type.items():
        print(f"  {node_name}: {is_building}")

    # Retrieve the dictionary of {node: {neighbor: metrics}}
    connection_matrix = graph_loader.get_connection_matrix()
    marcel_graph = MarcelGraph(connection_matrix)
    graph_data = marcel_graph.graph  # Dictionary of nodes/connections with metrics.
    
    start_node = 'Manzanita'
    destination_node = 'Node A'  # Replace with an actual node name from your Excel file.
    
    path, shortest_metric = dijkstra(graph_data, start_node, destination_node, metric='time')
    
    if shortest_metric == float('inf'):
        print(f"\nNo path found from '{start_node}' to '{destination_node}' using metric 'time'.")
    else:
        print(f"\nShortest path from '{start_node}' to '{destination_node}' using 'time':")
        for edge, cost in path.items():
            print(f"  {edge} : {cost}")
        print(f"Total {shortest_metric}")
