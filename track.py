import pygame

class Node:
    def __init__(self, nid, x, y, station=False, platforms=0):
        self.id = nid
        self.x = x
        self.y = y
        self.station = station
        self.platforms = platforms

class Edge:
    def __init__(self, n1, n2):
        self.n1 = n1
        self.n2 = n2
        self.occupied = None
        self.blocked = False   # NEW

    def is_free(self):
        return self.occupied is None and not self.blocked


class TrackGraph:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def get_edge(self, n1, n2):
        for e in self.edges:
            if (e.n1 == n1 and e.n2 == n2) or (e.n1 == n2 and e.n2 == n1):
                return e
        return None

    def draw(self, surface):
        for e in self.edges:
            if e.blocked:
                color = (50, 50, 50)   # blocked = grey/black
            elif e.is_free():
                color = (0, 200, 0)   # free = green
            else:
                color = (200, 0, 0)   # occupied = red
            pygame.draw.line(surface, color,
                            (e.n1.x, e.n1.y), (e.n2.x, e.n2.y), 4)


