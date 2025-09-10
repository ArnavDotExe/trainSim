import pygame, sys, json
from track import Node, Edge, TrackGraph
from train import Train
from timetable import Timetable

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 30

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("TrainLab Schematic Simulator")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)

# Load layout
with open("layouts/simple_station.json") as f:
    layout = json.load(f)

nodes = {nid: Node(nid, **data) for nid, data in layout["nodes"].items()}
edges = [Edge(nodes[a], nodes[b]) for a, b in layout["edges"]]
graph = TrackGraph(nodes, edges)

# timetable
timetable = Timetable([
    {"id": "WR1", "start_time": 1, "color": (0, 128, 255),
     "route": ["WL_A", "WL_B1", "WL_J", "WL_C"]},

    {"id": "CR1", "start_time": 2, "color": (255, 100, 100),
     "route": ["CL_A", "CL_B2", "CL_J", "CL_C"]},

    {"id": "Xover", "start_time": 4, "color": (100, 200, 100),
     "route": ["WL_A", "WL_B1", "X1", "CL_B1", "CL_J", "CL_C"]}
])

# --- Add Buttons ---
buttons = {
    "Send T1": pygame.Rect(650, 20, 120, 30),
    "Send T2": pygame.Rect(650, 60, 120, 30),
    "Toggle Block": pygame.Rect(650, 100, 120, 30)
}
block_mode = False

def draw_buttons():
    for label, rect in buttons.items():
        pygame.draw.rect(screen, (200, 200, 200), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
        txt = font.render(label, True, (0, 0, 0))
        screen.blit(txt, (rect.x + 5, rect.y + 5))


trains = []
time = 0
paused = False
running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    if not paused:
        time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Button clicks
            for label, rect in buttons.items():
                if rect.collidepoint(mx, my):
                    if label == "Send T1":
                        trains.append(Train("Manual1", (0,128,255),
                                            ["A", "B1", "J1", "C1", "J2", "D"]))
                    elif label == "Send T2":
                        trains.append(Train("Manual2", (255,100,100),
                                            ["A", "B2", "J1", "Branch1", "Branch2"]))
                    elif label == "Toggle Block":
                        block_mode = not block_mode

            # Block track with click
            if block_mode:
                for e in graph.edges:
                    x1, y1 = e.n1.x, e.n1.y
                    x2, y2 = e.n2.x, e.n2.y
                    # crude distance check (mouse near line)
                    dist = abs((y2-y1)*mx - (x2-x1)*my + x2*y1 - y2*x1) / (
                        ((x2-x1)**2 + (y2-y1)**2) ** 0.5
                    )
                    if dist < 10:
                        e.blocked = not e.blocked
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            paused = not paused

    for spec in timetable.check_spawns(time):
        trains.append(Train(spec["id"], spec["color"], spec["route"]))

    if not paused:
        for t in trains:
            t.update(graph, dt)

    screen.fill((240, 240, 240))
    graph.draw(screen)
    for t in trains:
        t.draw(screen, graph)

    
    txt = font.render(f"Time: {time:.1f}s (SPACE pause)", True, (0, 0, 0))
    screen.blit(txt, (10, 10))
    pygame.display.flip()
    
    
    
    

pygame.quit()
sys.exit()
