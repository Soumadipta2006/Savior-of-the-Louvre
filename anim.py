import matplotlib.pyplot as plt
import matplotlib.animation
import networkx as nx
import json
import warnings

# --- 1. `load_graph` FUNCTION ---
def load_graph(filename="graph_with_metadata.json"):
    with open(filename, "r") as f:
        data = json.load(f)
    adjacency_raw = data["adjacency"]
    adjacency = {int(k): [(int(n), w) for n, w in v] for k, v in adjacency_raw.items()}
    positions = {int(k): tuple(v) for k, v in data["positions"].items()}
    metadata = data.get("metadata", {})
    end_nodes_loaded = metadata.get("exit_nodes", [])
    exit_nodes = end_nodes_loaded[1:]
    G_loaded = nx.DiGraph()
    for node, neighbors in adjacency.items():
        for nbr, weight in neighbors:
            G_loaded.add_edge(node, nbr, weight=weight)
    return G_loaded, adjacency, positions, metadata, exit_nodes

# --- 2. HELPER FUNCTION (for smooth movement) ---
def get_car_xy(car_state, pos, graph):
    """
    Helper function to calculate the exact (x, y) coords of a car.
    """
    if car_state['edge_from'] is not None and car_state['edge_to'] is not None:
        try:
            u, v = car_state['edge_from'], car_state['edge_to']
            pos_u, pos_v = pos[u], pos[v]
            
            weight = graph[u][v].get('weight', 1.0)
            percent_progress = max(0.0, min(1.0, car_state['progress'] / weight))
            
            interp_x = (1 - percent_progress) * pos_u[0] + percent_progress * pos_v[0]
            interp_y = (1 - percent_progress) * pos_u[1] + percent_progress * pos_v[1]
            
            return (interp_x, interp_y)
        
        except (KeyError, ZeroDivisionError):
            return pos[car_state['pos']]
    
    return pos[car_state['pos']]

# --- 3. MAIN VISUALIZATION ---
def main():
    # --- Load Data ---
    try:
        G_loaded, adjacency, positions, metadata, exit_nodes = load_graph()
        with open("simulation.json", "r") as f:
            history = json.load(f)
    except FileNotFoundError as e:
        print(f"Error! Could not load file: {e}")
        return

    # Define start nodes and delay
    CAR_A_START_NODE = 0
    CAR_B_START_NODE = 49
    DELAY_B = 3
    if history:
        DELAY_B = history[0]['carB'].get('delay', 3)

    # --- THIS IS THE FIX ---
    # Create a "Step 0" initial state, as the log starts *after* the first move.
    
    # Get the *first* path Car A has (from the first log entry)
    initial_path = history[0]['carA']['Dijkstra_path']
    # Add the start node back to the front of the path for this frame
    if initial_path and initial_path[0] != CAR_A_START_NODE:
        initial_path.insert(0, CAR_A_START_NODE)

    initial_carA_state = {
        "pos": CAR_A_START_NODE,
        "edge_from": None,
        "edge_to": None,
        "progress": 0.0,
        "Dijkstra_path": initial_path
    }
    initial_carB_state = {
        "pos": CAR_B_START_NODE,
        "edge_from": None,
        "edge_to": None,
        "progress": 0.0,
        "Dijkstra_path": []
    }
    
    # Create the manufactured first frame
    step_initial = {
        "step": 0, # We'll call this "Step 0"
        "carA": initial_carA_state,
        "carB": initial_carB_state,
        "caught": False,
        "reached": False,
        "log_events": []
    }
    
    # Insert this new frame at the very beginning of the history list
    history.insert(0, step_initial)
    
    # Re-number the "step" display for all subsequent frames
    for i, step_data in enumerate(history):
        if i > 0:
            step_data['step_display'] = step_data['step']
    history[0]['step_display'] = 0 # Our initial frame is also "step 0"

    # --- Define the Basic Drawing Function (UPDATED) ---
    def draw_frame_basic(step_data):
        plt.clf() 
        
        step_display = step_data['step_display'] # Use our new display number
        carA_state = step_data['carA']
        carB_state = step_data['carB']

        # 1. Draw the base graph
        nx.draw_networkx_edges(G_loaded, positions, alpha=0.2, edge_color="gray")
        nx.draw_networkx_nodes(G_loaded, positions, node_size=100, node_color="#cccccc")
        nx.draw_networkx_labels(G_loaded, positions, font_size=8, font_color="black")
        
        # 2. Highlight exit
        nx.draw_networkx_nodes(G_loaded, positions, nodelist=exit_nodes, node_size=200, node_color="lime")
        
        # 3. Get smooth positions
        carA_xy = get_car_xy(carA_state, positions, G_loaded)
        
        # 4. Draw Car A
        nx.draw_networkx_nodes(G_loaded, {"A_pos": carA_xy}, nodelist=["A_pos"], node_size=200, node_color="red")
        
        # 5. Draw Car B
        # Use the *original* step number for the delay logic
        if step_data['step'] >= DELAY_B or step_data['step'] == 0:
            carB_xy = get_car_xy(carB_state, positions, G_loaded)
            nx.draw_networkx_nodes(G_loaded, {"B_pos": carB_xy}, nodelist=["B_pos"], node_size=200, node_color="blue")
            
        plt.title(f"Louvre Chase - Step: {step_display}")
        plt.axis('off')

    # --- Set up the Animation ---
    fig, ax = plt.subplots(figsize=(10, 10))

    def animate_basic(i):
        draw_frame_basic(history[i])

    ani = matplotlib.animation.FuncAnimation(
        fig, 
        animate_basic, 
        frames=len(history), 
        interval=200, 
        repeat=False
    )

    # --- Save the Animation as an HTML File ---
    print("Saving basic_animation.html... This might take a moment.")
    try:
        html_output = ani.to_jshtml()
        with open("basic_animation.html", "w") as f:
            f.write(html_output)
            
        print("\nAnimation saved as 'basic_animation.html'.")

    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"Could not save animation as HTML: {e}")

    plt.close()
    
# --- Run the program ---
if __name__ == "__main__":
    main()