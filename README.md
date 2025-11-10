This project is a real-time chase simulator built for my Algorithms course at IIT KGP. [cite_start]It models a dynamic pursuit between a team of burglars (Car A) and the police (Car B) through a synthetic, graph-based representation of Paris [cite: 4-7].

The core of the simulation is a from-scratch implementation of **Dijkstra's Algorithm**, which both agents use for dynamic pathfinding in an unpredictable environment. [cite_start]The environment is constantly changing with random **traffic jams**, **roadblocks**, and **one-way street enforcements**[cite: 8].

The entire simulation is logged to `simulation.json` and can be replayed using a custom **Pygame visualizer**.

## 🎥 Visualization

The `visualization.py` script reads the simulation log and generates a smooth, animated replay of the chase.


## ✨ Key Features

* [cite_start]**Graph-Based City:** The city map is loaded from `graph_with_metadata.json` as a directed, weighted graph[cite: 11].
* [cite_start]**Dijkstra's from Scratch:** Implements Dijkstra's algorithm (using a `heapq` priority queue) for all pathfinding[cite: 28].
* [cite_start]**Dynamic Environment:** At each timestep, there is a 30% chance of a random event altering the graph[cite: 37]:
    * [cite_start]**Traffic Jam:** Multiplies an edge's weight (travel time)[cite: 44].
    * [cite_start]**Blockage:** Temporarily removes an edge from the graph[cite: 44].
    * [cite_start]**One-Way:** Removes the reverse edge of a road[cite: 45].
* **Dynamic Path Replanning:** Both agents have unique AI and must adapt to the changing graph.
    * [cite_start]**Car A (Thief):** Knows the exit node (48)[cite: 16]. [cite_start]It follows its path and will only replan if an event forces it to, or if its current path becomes blocked [cite: 55-57].
    * [cite_start]**Car B (Police):** Starts from the station (49) after a 3-timestep delay and is 1.5x faster [cite: 17, 33-35]. [cite_start]It knows Car A's position and replans at every node to find the shortest path to intercept[cite: 63, 69].
* [cite_start]**JSON Logging:** The entire step-by-step history of the simulation, including car positions, progress, and active events, is saved to `simulation.json` [cite: 98-119].
* **Pygame Visualization:** A separate visualizer (`visualization.py`) parses the JSON log to provide a smooth, animated replay with status readouts, car-shaped pointers, and path tracing.

## 📦 Dependencies

The core simulation (`code.py`) only requires standard Python libraries.

The visualization (`visualization.py`) requires `pygame` and `networkx`. You can install them via pip:

```bash
pip install pygame networkx
