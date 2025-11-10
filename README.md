This project is a real-time chase simulator built for my Algorithms course at IIT KGP. It models a dynamic pursuit between a team of burglars (Car A) and the police (Car B) through a synthetic, graph-based representation of Paris.

The core of the simulation is a from-scratch implementation of Dijkstra's Algorithm, which both agents use for dynamic pathfinding in an unpredictable environment. The environment is constantly changing with random traffic jams, roadblocks, and one-way street enforcements.

The entire simulation is logged to `simulation.json` and can be replayed using a custom Pygame visualizer.

## 🎥 Visualization

The `visualization.py` script reads the simulation log and generates a smooth, animated replay of the chase.


## ✨ Key Features

* Graph-Based City: The city map is loaded from `graph_with_metadata.json` as a directed, weighted graph.
* Dijkstra's from Scratch: Implements Dijkstra's algorithm (using a `heapq` priority queue) for all pathfinding.
* Dynamic Environment: At each timestep, there is a 30% chance of a random event altering the graph
    * Traffic Jam: Multiplies an edge's weight (travel time).
    * Blockage: Temporarily removes an edge from the graph.
    * One-Way: Removes the reverse edge of a road.
* Dynamic Path Replanning: Both agents have unique AI and must adapt to the changing graph.
    * Car A (Thief): Knows the exit node (48). It follows its path and will only replan if an event forces it to, or if its current path becomes blocked.
    * Car B (Police): Starts from the station (49) after a 3-timestep delay and is 1.5x faster. It knows Car A's position and replans at every node to find the shortest path to intercept.
* JSON Logging: The entire step-by-step history of the simulation, including car positions, progress, and active events, is saved to `simulation.json`.
* Pygame Visualization: A separate visualizer (`visualization.py`) parses the JSON log to provide a smooth, animated replay with status readouts, car-shaped pointers, and path tracing.

## 📦 Dependencies

The core simulation (`code.py`) only requires standard Python libraries.

The visualization (`visualization.py`) requires `pygame` and `networkx`. You can install them via pip:

```bash
pip install pygame networkx
