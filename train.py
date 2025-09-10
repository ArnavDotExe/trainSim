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

    def update(self, graph, dt):
        if self.finished:
            return

        if self.current_index >= len(self.route) - 1:
            self.finished = True
            return

        n1 = graph.nodes[self.route[self.current_index]]
        n2 = graph.nodes[self.route[self.current_index + 1]]
        edge = graph.get_edge(n1, n2)

        if not edge.is_free() and edge.occupied != self:
            return  # wait for free block

        edge.occupied = self
        dx, dy = n2.x - n1.x, n2.y - n1.y
        length = (dx**2 + dy**2) ** 0.5
        self.progress += self.speed * dt / length

        if self.progress >= 1.0:
            edge.occupied = None
            self.current_index += 1
            self.progress = 0.0

    def draw(self, surface, graph):
        if self.finished:
            return

        n1 = graph.nodes[self.route[self.current_index]]

        if self.current_index + 1 < len(self.route):
            n2 = graph.nodes[self.route[self.current_index + 1]]
            x = n1.x + (n2.x - n1.x) * self.progress
            y = n1.y + (n2.y - n1.y) * self.progress

            pygame.draw.rect(surface, self.color, (x - 10, y - 10, 20, 10))
            font = pygame.font.SysFont("Arial", 12)
            txt = font.render(self.tid, True, (0, 0, 0))
            surface.blit(txt, (x - 15, y - 25))
    def reroute(self, new_route):
        """Force a new route for the train"""
        self.route = new_route
        self.current_index = 0
        self.progress = 0.0
        self.finished = False