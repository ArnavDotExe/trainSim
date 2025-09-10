import pygame, sys, json
from track import Node, Edge, TrackGraph
from train import Train
from timetable import Timetable
from collections import deque

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
# Use valid node ids from simple_station.json (A, B1, B2, J1, C1, C2, J2, D, Branch1, Branch2)
timetable = Timetable([
    {"id": "WR1", "start_time": 1, "color": (0, 128, 255),
     "route": ["A", "B1", "J1", "C1", "J2", "D"]},

    {"id": "CR1", "start_time": 2, "color": (255, 100, 100),
     "route": ["A", "B2", "J1", "C2", "J2", "D"]},

    {"id": "Xover", "start_time": 4, "color": (100, 200, 100),
     "route": ["A", "B1", "J1", "C2", "J2", "D"]}
])

# --- Buttons ---
buttons = {
    "Send Train 1": pygame.Rect(650, 20, 120, 30),
    "Send Train 2": pygame.Rect(650, 60, 120, 30),
    "Block Mode": pygame.Rect(650, 100, 120, 30)
}
block_mode = False


def draw_buttons():
    for label, rect in buttons.items():
        pygame.draw.rect(screen, (200, 200, 200), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
        txt = font.render(label, True, (0, 0, 0))
        screen.blit(txt, (rect.x + 5, rect.y + 5))


def pick_edge_from_point(mx, my, graph, threshold=10):
    # crude distance check to find nearest edge
    for e in graph.edges:
        x1, y1 = e.n1.x, e.n1.y
        x2, y2 = e.n2.x, e.n2.y
        num = abs((y2 - y1) * mx - (x2 - x1) * my + x2 * y1 - y2 * x1)
        den = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if den == 0:
            continue
        dist = num / den
        if dist < threshold:
            return e
    return None


def find_node_near(mx, my, graph, threshold=12):
    for n in graph.nodes.values():
        dx, dy = mx - n.x, my - n.y
        if (dx * dx + dy * dy) ** 0.5 < threshold:
            return n
    return None


def route_ok(route, graph):
    missing = [nid for nid in route if nid not in graph.nodes]
    if missing:
        print(f"[Route ERROR] Missing node ids: {missing}")
        return False
    for a, b in zip(route, route[1:]):
        if graph.get_edge(graph.nodes[a], graph.nodes[b]) is None:
            print(f"[Route ERROR] No edge between {a} and {b}")
            return False
    return True


# Auto-routing helpers
def leftmost_node_id(graph):
    return min(graph.nodes.values(), key=lambda n: n.x).id if graph.nodes else None


def rightmost_node_id(graph):
    return max(graph.nodes.values(), key=lambda n: n.x).id if graph.nodes else None


def bfs_route(graph, start_id, end_id):
    if start_id not in graph.nodes or end_id not in graph.nodes:
        return None
    adj = {nid: [] for nid in graph.nodes.keys()}
    for e in graph.edges:
        adj[e.n1.id].append(e.n2.id)
        adj[e.n2.id].append(e.n1.id)
    prev = {start_id: None}
    q = deque([start_id])
    while q:
        v = q.popleft()
        if v == end_id:
            break
        for w in adj.get(v, []):
            if w not in prev:
                prev[w] = v
                q.append(w)
    if end_id not in prev:
        return None
    path = []
    cur = end_id
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


trains = []
time = 0
paused = False
running = True

dragging = None  # (train, offset_x, offset_y)

while running:
    dt = clock.tick(FPS) / 1000.0
    if not paused:
        time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Button clicks (left click only). If a button is clicked, skip other mouse handlers.
            if event.button == 1:
                for label, rect in buttons.items():
                    if rect.collidepoint(mx, my):
                        if label == "Send Train 1":
                            print("[UI] Button: Send Train 1")
                            start, end = leftmost_node_id(graph), rightmost_node_id(graph)
                            route = bfs_route(graph, start, end)
                            if route and route_ok(route, graph):
                                trains.append(Train("Manual1", (0, 128, 255), route))
                                print(f"[Spawn] Manual1 (buttons) {start}->{end} via {len(route)} nodes. Trains={len(trains)}")
                            else:
                                print("[Spawn ERROR] No path for Manual1")
                        elif label == "Send Train 2":
                            print("[UI] Button: Send Train 2")
                            start = leftmost_node_id(graph)
                            target = 'Branch2' if 'Branch2' in graph.nodes else rightmost_node_id(graph)
                            route = bfs_route(graph, start, target)
                            if route and route_ok(route, graph):
                                trains.append(Train("Manual2", (255, 100, 100), route))
                                print(f"[Spawn] Manual2 (buttons) {start}->{target} via {len(route)} nodes. Trains={len(trains)}")
                            else:
                                print("[Spawn ERROR] No path for Manual2")
                        elif label == "Block Mode":
                            block_mode = not block_mode
                            print(f"[UI] Button: Block Mode -> {'ON' if block_mode else 'OFF'}")
                        break
                else:
                    # Try to start dragging a train first
                    started_drag = False
                    for t in reversed(trains):  # topmost first
                        pos = t.get_draw_position(graph)
                        if pos:
                            tx, ty = pos
                            rect = pygame.Rect(tx - 10, ty - 10, 20, 10)
                            if rect.collidepoint(mx, my) and not t.finished:
                                dragging = (t, mx - tx, my - ty)
                                print(f"[Drag] Start {t.tid}")
                                started_drag = True
                                break
                    # If not dragging, allow block toggle when in block_mode (not on a button)
                    if not started_drag and block_mode:
                        e = pick_edge_from_point(mx, my, graph)
                        if e:
                            e.blocked = not e.blocked
                            print(f"[Block] Edge {e.n1.id}-{e.n2.id} -> {'BLOCKED' if e.blocked else 'FREE'}")

            # Right click to reroute a waiting train at a junction
            if event.button == 3:
                node = find_node_near(mx, my, graph)
                if node:
                    for t in trains:
                        if not t.finished and t.is_waiting() and t.current_node_id() == node.id:
                            e = pick_edge_from_point(mx, my, graph)
                            if e:
                                next_node = e.n2 if e.n1.id == node.id else (e.n1 if e.n2.id == node.id else None)
                                if next_node and t.set_next_hop(next_node.id, graph):
                                    print(f"[Reroute] {t.tid}: next -> {next_node.id}")
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            mx, my = event.pos
            if event.button == 1 and dragging:
                t, ox, oy = dragging
                dragging = None
                node_id = t.current_node_id()
                curr_node = graph.nodes.get(node_id)
                if curr_node:
                    e = pick_edge_from_point(mx, my, graph)
                    cand = None
                    if e:
                        if e.n1.id == node_id:
                            cand = e.n2
                        elif e.n2.id == node_id:
                            cand = e.n1
                    if cand and t.set_next_hop(cand.id, graph):
                        print(f"[Drag-Reroute] {t.tid}: next -> {cand.id}")

        elif event.type == pygame.MOUSEMOTION:
            # visual only; handled in draw section
            pass

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
                print(f"[Key] Pause -> {'ON' if paused else 'OFF'}")
            elif event.key in (pygame.K_KP1, pygame.K_1):
                print("[Hotkey] Send Train 1")
                start, end = leftmost_node_id(graph), rightmost_node_id(graph)
                route = bfs_route(graph, start, end)
                if route and route_ok(route, graph):
                    trains.append(Train("Manual1", (0, 128, 255), route))
                    print(f"[Spawn] Manual1 (hotkey) {start}->{end} via {len(route)} nodes. Trains={len(trains)}")
                else:
                    print("[Spawn ERROR] No path for Manual1")
            elif event.key in (pygame.K_KP2, pygame.K_2):
                print("[Hotkey] Send Train 2")
                start = leftmost_node_id(graph)
                target = 'Branch2' if 'Branch2' in graph.nodes else rightmost_node_id(graph)
                route = bfs_route(graph, start, target)
                if route and route_ok(route, graph):
                    trains.append(Train("Manual2", (255, 100, 100), route))
                    print(f"[Spawn] Manual2 (hotkey) {start}->{target} via {len(route)} nodes. Trains={len(trains)}")
                else:
                    print("[Spawn ERROR] No path for Manual2")
            elif event.key in (pygame.K_KP0, pygame.K_0, pygame.K_b):
                block_mode = not block_mode
                print(f"[Hotkey] Block Mode -> {'ON' if block_mode else 'OFF'}")

    for spec in timetable.check_spawns(time):
        route = spec["route"]
        if route_ok(route, graph):
            trains.append(Train(spec["id"], spec["color"], route))
            print(f"[Timetable] Spawn {spec['id']}. Trains={len(trains)}")

    if not paused:
        for t in trains:
            t.update(graph, dt)

    # Draw phase
    screen.fill((240, 240, 240))
    graph.draw(screen)
    for t in trains:
        t.draw(screen, graph)

    # If dragging, draw a helper line from the train to mouse
    if dragging:
        t, ox, oy = dragging
        pos = t.get_draw_position(graph)
        if pos:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.line(screen, (50, 50, 200), pos, (mx, my), 2)

    draw_buttons()
    txt = font.render(f"Time: {time:.1f}s (SPACE pause)  BlockMode: {'ON' if block_mode else 'OFF'}", True, (0, 0, 0))
    screen.blit(txt, (10, 10))
    pygame.display.flip()

pygame.quit()
sys.exit()
