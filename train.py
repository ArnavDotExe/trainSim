import pygame

class Train:
    def __init__(self, tid, color, route, speed=80):
        self.tid = tid
        self.color = color
        self.route = route  # list of node ids
        self.current_index = 0
        self.progress = 0.0
        self.speed = speed  # pixels per second
        self.finished = False
        self.waiting = False  # waiting due to blocked/occupied/unreachable next edge

    def update(self, graph, dt):
        if self.finished:
            return

        # reset waiting state each tick
        self.waiting = False

        if self.current_index >= len(self.route) - 1:
            self.finished = True
            return

        curr_id = self.route[self.current_index]
        next_id = self.route[self.current_index + 1]

        # Guard against missing nodes in graph
        if curr_id not in graph.nodes:
            # terminate gracefully if current node no longer exists
            # print(f"[WARN] Train {self.tid}: missing node '{curr_id}' in graph; terminating")
            self.finished = True
            return
        if next_id not in graph.nodes:
            # wait for user reroute if next node id is invalid
            self.waiting = True
            return

        n1 = graph.nodes[curr_id]
        n2 = graph.nodes[next_id]
        edge = graph.get_edge(n1, n2)

        # If no edge or not free, wait
        if edge is None or (not edge.is_free() and edge.occupied != self):
            self.waiting = True
            return  # wait for free/unblocked block

        edge.occupied = self
        dx, dy = n2.x - n1.x, n2.y - n1.y
        length = (dx**2 + dy**2) ** 0.5
        # avoid div-by-zero on coincident nodes
        if length == 0:
            # treat as instantly arrived at next node
            edge.occupied = None
            self.current_index += 1
            self.progress = 0.0
            return
        self.progress += self.speed * dt / length

        if self.progress >= 1.0:
            edge.occupied = None
            self.current_index += 1
            self.progress = 0.0

    def draw(self, surface, graph):
        if self.finished:
            return

        # Guard against invalid current index or missing nodes
        if self.current_index >= len(self.route):
            return
        curr_id = self.route[self.current_index]
        if curr_id not in graph.nodes:
            return
        n1 = graph.nodes[curr_id]

        if self.current_index + 1 < len(self.route):
            next_id = self.route[self.current_index + 1]
            if next_id not in graph.nodes:
                # cannot compute position without next node
                return
            n2 = graph.nodes[next_id]
            x = n1.x + (n2.x - n1.x) * self.progress
            y = n1.y + (n2.y - n1.y) * self.progress

            pygame.draw.rect(surface, self.color, (x - 10, y - 10, 20, 10))
            font = pygame.font.SysFont("Arial", 12)
            txt = font.render(self.tid, True, (0, 0, 0))
            surface.blit(txt, (x - 15, y - 25))

    def get_draw_position(self, graph):
        """Return (x, y) where this train is drawn."""
        if self.finished or self.current_index >= len(self.route):
            return None
        curr_id = self.route[self.current_index]
        if curr_id not in graph.nodes:
            return None
        n1 = graph.nodes[curr_id]
        x, y = n1.x, n1.y
        if self.current_index + 1 < len(self.route):
            next_id = self.route[self.current_index + 1]
            if next_id in graph.nodes:
                n2 = graph.nodes[next_id]
                x = n1.x + (n2.x - n1.x) * self.progress
                y = n1.y + (n2.y - n1.y) * self.progress
        return (x, y)

    def reroute(self, new_route):
        """Force a new route for the train"""
        self.route = new_route
        self.current_index = 0
        self.progress = 0.0
        self.finished = False
        self.waiting = False

    # New helpers for interactive rerouting
    def is_waiting(self):
        return self.waiting

    def current_node_id(self):
        return self.route[self.current_index]

    def set_next_hop(self, next_node_id, graph):
        """Replace the immediate next node if reachable from current node."""
        if self.current_index >= len(self.route) - 1:
            return False
        curr_id = self.route[self.current_index]
        if next_node_id == curr_id:
            return False
        if curr_id not in graph.nodes or next_node_id not in graph.nodes:
            return False
        curr_node = graph.nodes[curr_id]
        next_node = graph.nodes[next_node_id]
        edge = graph.get_edge(curr_node, next_node)
        if edge is None or edge.blocked:
            return False
        # Apply change
        self.route[self.current_index + 1] = next_node_id
        self.waiting = False
        return True