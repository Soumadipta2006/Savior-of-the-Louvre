import pygame
import json
import math
import networkx as nx 

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
PADDING = 50
FPS = 0.5

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREY = (211, 211, 211)
COLOR_EXIT = (0, 200, 0)
# Car Colors
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_RED_LIGHT = (255, 150, 150)  
COLOR_BLUE_LIGHT = (150, 150, 255) 

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

def scale(val, min_val, max_val, min_out, max_out):
    if max_val == min_val: return min_out
    return (val - min_val) * (max_out - min_out) / (max_val - min_val) + min_out

def scale_positions(pos_dict, width, height, padding):
    scaled_pos = {}
    min_x = min(v[0] for v in pos_dict.values())
    max_x = max(v[0] for v in pos_dict.values())
    min_y = min(v[1] for v in pos_dict.values())
    max_y = max(v[1] for v in pos_dict.values())
    for node, (x, y) in pos_dict.items():
        screen_x = int(scale(x, min_x, max_x, padding, width - padding))
        screen_y = int(scale(y, min_y, max_y, height - padding, padding))
        scaled_pos[node] = (screen_x, screen_y)
    return scaled_pos

def draw_dotted_line(surface, color, start, end, dash_length=5):
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = math.hypot(dx, dy)
    if distance == 0: return
    dashes = int(distance / dash_length)
    if dashes == 0: dashes = 1
    for i in range(dashes):
        if i % 2 == 0:
            start_pos = (start[0] + dx * i / dashes, start[1] + dy * i / dashes)
            end_pos = (start[0] + dx * (i + 1) / dashes, start[1] + dy * (i + 1) / dashes)
            pygame.draw.line(surface, color, start_pos, end_pos, 1)

def create_static_background(graph, positions, adj_dict, exit_nodes, font):
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill(COLOR_WHITE)
    for node_start, neighbors in adj_dict.items():
        start_pos = positions.get(node_start)
        if start_pos is None: continue
        for node_end, weight in neighbors:
            end_pos = positions.get(node_end)
            if end_pos is None: continue
            draw_dotted_line(background, COLOR_GREY, start_pos, end_pos)
    for node, pos in positions.items():
        pygame.draw.circle(background, COLOR_BLACK, pos, 10, 2)
        text_surface = font.render(str(node), True, COLOR_BLACK)
        text_rect = text_surface.get_rect(center=pos)
        background.blit(text_surface, text_rect)
    for node in exit_nodes:
        pos = positions.get(node)
        if pos: pygame.draw.circle(background, COLOR_EXIT, pos, 12, 3)
    return background

def get_car_pos_and_angle(car_state, scaled_pos, graph):
    if car_state['edge_from'] is None or car_state['edge_to'] is None:
        return scaled_pos[car_state['pos']], None
    try:
        u, v = car_state['edge_from'], car_state['edge_to']
        pos_u, pos_v = scaled_pos[u], scaled_pos[v]
        dx = pos_v[0] - pos_u[0]
        dy = pos_v[1] - pos_u[1]
        angle = math.degrees(math.atan2(-dy, dx))
        weight = graph[u][v].get('weight', 1.0)
        percent_progress = max(0.0, min(1.0, car_state['progress'] / weight))
        interp_x = int((1 - percent_progress) * pos_u[0] + percent_progress * pos_v[0])
        interp_y = int((1 - percent_progress) * pos_u[1] + percent_progress * pos_v[1])
        return (interp_x, interp_y), angle
    except (KeyError, ZeroDivisionError):
        return scaled_pos[car_state['pos']], None

def draw_car(surface, pos, angle, color):
    """Draws a rotated "car" (a triangle)."""
    base_shape = [(12, 0), (-6, -6), (-6, 6)]
    rad = math.radians(angle)
    rotated_shape = []
    for x, y in base_shape:
        new_x = x * math.cos(rad) - y * math.sin(rad)
        new_y = x * math.sin(rad) + y * math.cos(rad)
        final_x = new_x + pos[0]
        final_y = new_y + pos[1]
        rotated_shape.append((final_x, final_y))
    
    pygame.draw.polygon(surface, color, rotated_shape)



def main():
    try:
        G_loaded, adjacency, positions_raw, metadata, exit_nodes = load_graph()
        with open("simulation.json", "r") as f:
            history = json.load(f)
    except FileNotFoundError as e:
        print(f"Error! Could not load file: {e}")
        return
        
    DELAY_B = 3
    if history: DELAY_B = history[0]['carB'].get('delay', 3)
    CAR_A_START_NODE = 0 
    CAR_B_START_NODE = 49

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Savior of the Louvre - Chase Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 10, bold=True)
    ui_font = pygame.font.SysFont("Arial", 20, bold=True)
    status_font = pygame.font.SysFont("Arial", 16)
    
    positions = scale_positions(positions_raw, SCREEN_WIDTH, SCREEN_HEIGHT, PADDING)

    background_surface = create_static_background(G_loaded, positions, adjacency, exit_nodes, font)

    running = True
    paused = False
    current_step = 0
    path_a_points = [positions[CAR_A_START_NODE]] 
    path_b_points = [positions[CAR_B_START_NODE]] 
    last_carA_angle = 0
    last_carB_angle = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: paused = not paused
                if event.key == pygame.K_r:
                    current_step = 0
                    path_a_points = [positions[CAR_A_START_NODE]]
                    path_b_points = [positions[CAR_B_START_NODE]]
                    last_carA_angle, last_carB_angle = 0, 0
                    paused = False
        
        if paused:
            pygame.display.flip()
            clock.tick(FPS)
            continue

        if current_step >= len(history):
            paused = True
            current_step = len(history) - 1
        
        step_data = history[current_step]

        carA_state = step_data['carA']
        carB_state = step_data['carB']
        
        carA_xy, carA_angle = get_car_pos_and_angle(carA_state, positions, G_loaded)
        carB_xy, carB_angle = (positions[CAR_B_START_NODE], 0) 
        
        if step_data['step'] >= DELAY_B:
            carB_xy, carB_angle = get_car_pos_and_angle(carB_state, positions, G_loaded)

        if carA_angle is not None: last_carA_angle = carA_angle
        else: carA_angle = last_carA_angle
            
        if carB_angle is not None: last_carB_angle = carB_angle
        else: carB_angle = last_carB_angle

        carA_in_transit = carA_state['edge_from'] is not None
        carB_in_transit = carB_state['edge_from'] is not None

        if path_a_points[-1] != carA_xy:
            path_a_points.append(carA_xy)
        if step_data['step'] >= DELAY_B and path_b_points[-1] != carB_xy:
            path_b_points.append(carB_xy)

        
        screen.blit(background_surface, (0, 0))

        if len(path_a_points) > 1:
            pygame.draw.lines(screen, COLOR_RED, False, path_a_points, 3)
        if len(path_b_points) > 1:
            pygame.draw.lines(screen, COLOR_BLUE, False, path_b_points, 3)

        carA_color = COLOR_RED_LIGHT if carA_in_transit else COLOR_RED
        draw_car(screen, carA_xy, carA_angle, carA_color)
        
        if step_data['step'] >= DELAY_B:
            carB_color = COLOR_BLUE_LIGHT if carB_in_transit else COLOR_BLUE
            draw_car(screen, carB_xy, carB_angle, carB_color)

        step_text = ui_font.render(f"Step: {step_data['step']}", True, COLOR_BLACK)
        screen.blit(step_text, (10, 10))
        
        # Car A
        carA_status_str = "Car A: On Edge" if carA_in_transit else "Car A: At Node"
        carA_pos_str = f"Car A Pos: {carA_state['pos']}"
        carA_edge_str = "Car A Edge: ---"
        if carA_in_transit:
            carA_edge_str = f"Car A Edge: ({carA_state['edge_from']} -> {carA_state['edge_to']})"
        
        carA_status_surface = status_font.render(carA_status_str, True, COLOR_BLACK)
        carA_pos_surface = status_font.render(carA_pos_str, True, COLOR_BLACK)
        carA_edge_surface = status_font.render(carA_edge_str, True, COLOR_BLACK)
        screen.blit(carA_status_surface, (10, 40))
        screen.blit(carA_pos_surface, (10, 60))
        screen.blit(carA_edge_surface, (10, 80))

        # Car B
        carB_status_str = ""
        carB_pos_str = f"Car B Pos: {carB_state['pos']}"
        carB_edge_str = "Car B Edge: ---"
        if step_data['step'] < DELAY_B:
            carB_status_str = f"Car B: Waiting ({DELAY_B - step_data['step']})"
            carB_edge_str = "Car B Edge: Waiting"
        else:
            carB_status_str = "Car B: On Edge" if carB_in_transit else "Car B: At Node"
            if carB_in_transit:
                carB_edge_str = f"Car B Edge: ({carB_state['edge_from']} -> {carB_state['edge_to']})"

        carB_status_surface = status_font.render(carB_status_str, True, COLOR_BLACK)
        carB_pos_surface = status_font.render(carB_pos_str, True, COLOR_BLACK)
        carB_edge_surface = status_font.render(carB_edge_str, True, COLOR_BLACK)
        screen.blit(carB_status_surface, (10, 110))
        screen.blit(carB_pos_surface, (10, 130))
        screen.blit(carB_edge_surface, (10, 150))


        status_text = ""
        if step_data['caught']:
            status_text = "CAUGHT!"
            paused = True
        elif step_data['reached']:
            status_text = "ESCAPED!"
            paused = True
        if paused and not (step_data['caught'] or step_data['reached']):
            status_text = "PAUSED (Space to resume, R to restart)"

        status_surface = ui_font.render(status_text, True, COLOR_RED if step_data['caught'] else COLOR_EXIT)
        screen.blit(status_surface, (10, 180)) # Moved down

        pygame.display.flip()
        
        if not paused:
            current_step += 1
            
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()