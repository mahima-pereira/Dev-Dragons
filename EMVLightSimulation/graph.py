import heapq
from geopy.distance import geodesic

class Graph:
    def __init__(self):
        self.edges = {}
        self.nodes = {}

    def add_node(self, node, coordinates):
        self.nodes[node] = coordinates

    def add_edge(self, u, v):
        distance = geodesic(self.nodes[u], self.nodes[v]).meters
        if u not in self.edges:
            self.edges[u] = []
        if v not in self.edges:
            self.edges[v] = []
        self.edges[u].append((v, distance))
        self.edges[v].append((u, distance))

    def dijkstra(self, start, end):
        queue = [(0, start)]
        distances = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        previous_nodes = {node: None for node in self.nodes}

        while queue:
            current_distance, current_node = heapq.heappop(queue)

            if current_distance > distances[current_node]:
                continue

            for neighbor, weight in self.edges.get(current_node, []):
                distance = current_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(queue, (distance, neighbor))

        path, current_node = [], end
        while previous_nodes[current_node] is not None:
            path.insert(0, current_node)
            current_node = previous_nodes[current_node]
        if path:
            path.insert(0, current_node)
        return path
