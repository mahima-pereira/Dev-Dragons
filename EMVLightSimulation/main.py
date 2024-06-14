import torch
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from graph import Graph
from traffic_env import TrafficEnv
from agent import Agent

# Initialize graph (road network)
graph = Graph(num_nodes=6)
graph.add_edge(0, 1, 7)
graph.add_edge(0, 2, 9)
graph.add_edge(0, 5, 14)
graph.add_edge(1, 2, 10)
graph.add_edge(1, 3, 15)
graph.add_edge(2, 3, 11)
graph.add_edge(2, 5, 2)
graph.add_edge(3, 4, 6)
graph.add_edge(4, 5, 9)

# Patient and hospital nodes
patient_node = 0
hospital_node = 4

# Find shortest path
shortest_path = graph.dijkstra(patient_node, hospital_node)

# Visualization
fig, ax = plt.subplots()
nodes = list(range(6))
positions = {0: (0, 0), 1: (1, 1), 2: (1, -1), 3: (2, 1), 4: (3, 0), 5: (2, -1)}

def update(frame):
    ax.clear()
    for node in nodes:
        color = 'green' if node == patient_node else 'red' if node == hospital_node else 'blue'
        ax.scatter(*positions[node], c=color)
    for u in positions:
        for v, weight in graph.edges[u]:
            ax.plot([positions[u][0], positions[v][0]], [positions[u][1], positions[v][1]], 'k-')
    # Highlight the shortest path
    path_positions = [positions[node] for node in shortest_path[:frame+1]]
    if len(path_positions) > 1:
        ax.plot([pos[0] for pos in path_positions], [pos[1] for pos in path_positions], 'r-', linewidth=2)
    ax.set_title(f'Step {frame}')
    plt.pause(0.1)

animation = FuncAnimation(fig, update, frames=len(shortest_path), repeat=False)
plt.show()
