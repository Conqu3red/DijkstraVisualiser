import dataclasses
from pygame.math import Vector2 as _Vector2
import pygame.display
import pygame
from typing import *
from dataclasses import dataclass
from dijkstra import *
from uuid import UUID, uuid4

from enum import Enum

pygame.init()
pygame.display.init()
pygame.display.set_caption("Dijkstra Visualiser by Conqu3red")

pointerNormal = pygame.Cursor((1, 1), pygame.image.load("assets/pointerNormal.png"))
pointerMove = pygame.Cursor((16, 16), pygame.image.load("assets/pointerMove.png"))

pygame.mouse.set_cursor(pointerNormal)

class Vector2(_Vector2):
    def __hash__(self):
        return hash((self.x, self.y))
    
    Zero: "Vector2"

Vector2.Zero = Vector2(0, 0)

@dataclass
class Node:
    pos: Vector2
    id: UUID = dataclasses.field(default_factory=uuid4)

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass
class Edge(BaseEdge):
    start: Node
    end: Node  # directional graph
    
    @property
    def weight(self) -> float:
        return self.start.pos.distance_to(self.end.pos)
    
    def __hash__(self) -> int:
        return hash((self.start, self.end))


class Engine:
    def __init__(self):
        self.graph: Dict[Node, Set[Edge]] = {}
        self.computed: Dict[Hashable, Dist] = None
    
    def remove_node(self, node: Node):
        del self.graph[node]
        for edges in self.graph.values():
            for edge in [e for e in edges]:
                if edge.end is node or edge.start is node:
                    edges.remove(edge)


class Mode(Enum):
    NORMAL = 0

def rotate_point(point: Vector2, origin: Vector2, angle: float):
    return origin + (point - origin).rotate(angle)


class Renderer:
    FPS = 60
    SELECT_RANGE = 25
    EDGE_THICKNESS = 3

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.SIZE = (600, 600)
        self.screen = pygame.display.set_mode(self.SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.screen.fill((0, 0, 0))

        self.camera_dragging = False
        self.node_dragging: Optional[Node] = None
        self.selecting = False
        self.selected_node: Optional[Node] = None
        self.nearby_node: Optional[Node] = None

        self.start: Optional[Node] = None
        self.end: Optional[Node] = None
        self.path: Set[Edge] = set()

        self.mode = Mode.NORMAL
        self.camera = Vector2()
        self.zoom = 1

    def to_camera(self, point: Vector2):
        return (point + self.camera) * self.zoom

    def to_world(self, point: Vector2):
        return (point / self.zoom) - self.camera

    def draw_line(self, color, p1: Vector2, p2: Vector2, width: float = 1):
        pygame.draw.line(self.screen, color, self.to_camera(p1), self.to_camera(p2), int(width * self.zoom))

    def draw_circle(self, color, center: Vector2, radius: float, width: int = 0):
        pos = self.to_camera(center)
        pygame.draw.circle(self.screen, color, (int(pos.x), int(pos.y)), int(radius * self.zoom), width=width)
    
    def draw_polygon(self, color, points: Sequence[Vector2], width: int = 0):
        pygame.draw.polygon(self.screen, color, [self.to_camera(p) for p in points], width)

    def draw_dashed_line(self, color, p1: Vector2, p2: Vector2, width: float = 1, dash_length: int = 10):
        origin = p1
        target = p2
        displacement = target - origin
        length = displacement.length()
        if length == 0: return
        slope = displacement / length

        for index in range(0, int(length // dash_length), 2):
            start = origin + (slope *    index    * dash_length)
            end   = origin + (slope * (index + 1) * dash_length)
            self.draw_line(color, start, end, width)
    
    def draw_directional_head(self, color, p1: Vector2, p2: Vector2, width: float = 1, end_length: float = 10):
        length = p1.distance_to(p2)
        if length == 0: return

        start = p1 + (p2 - p1) * ((length - end_length) / length)
        angle = Vector2(0, 0).angle_to(p2 - p1)
        points = [
            rotate_point(Vector2(start.x, start.y + width / 2), start, angle),
            rotate_point(Vector2(start.x, start.y - width / 2), start, angle),
            rotate_point(Vector2(p2.x, p2.y - width / 2), p2, angle),
            rotate_point(Vector2(p2.x, p2.y + width / 2), p2, angle),
        ]
        self.draw_polygon(color, points) # TODO
    

    def update_hovering_node(self):
        m = self.to_world(Vector2(pygame.mouse.get_pos()))

        cur_dist = self.nearby_node.pos.distance_to(m) if self.nearby_node else math.inf
        if cur_dist > self.SELECT_RANGE:
            self.nearby_node = None
        for node in self.engine.graph:
            new_dist = node.pos.distance_to(m)
            if self.SELECT_RANGE >= new_dist < cur_dist:
                cur_dist = new_dist
                self.nearby_node = node

    def create_node(self) -> Node:
        pos = self.to_world(Vector2(pygame.mouse.get_pos()))
        node = Node(Vector2(pos.x, pos.y))
        self.engine.graph[node] = set()
        self.selected_node = node
        self.calculate_paths()

        return node

    def place_edge(self, n1: Node, n2: Node):
        if n2 is not n1:
            self.engine.graph[n1].add(Edge(n1, n2))
            self.calculate_paths()
        self.selected_node = n2

    def process_left_click(self):
        if self.selected_node is not None:
            self.place_edge(self.selected_node, self.create_node() if self.nearby_node is None else self.nearby_node)
        else:
            self.selected_node = self.nearby_node if self.nearby_node is not None else self.create_node()

    def delete_selected(self):
        if self.nearby_node is not None:
            self.engine.remove_node(self.nearby_node)
            if self.nearby_node == self.start: self.start = None
            if self.nearby_node == self.end: self.end = None
            self.calculate_paths()
            self.selected_node = None
            self.nearby_node = None
            self.node_dragging = None
    
    def calculate_paths(self):
        if self.start:
            print("recalculating paths.")
            self.engine.computed = dijkstra(self.engine.graph, self.start)
            self.maybe_update_path()
    
    def maybe_update_path(self):
        self.path.clear()
        if self.start and self.end:
            edge = self.engine.computed[self.end].shortest_parent
            while edge:
                self.path.add(edge)
                edge = self.engine.computed[edge.start].shortest_parent

    def render(self):
        event = pygame.event.poll()
        # if self.mode == Mode.BUILD:
        #    self.process_build_mode(event)
        # if self.mode == Mode.SIM:
        #    self.process_sim_mode(event)

        keys = pygame.key.get_pressed()
        pygame.mouse.get_pressed()

        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                if keys[pygame.K_LSHIFT] and self.selected_node is None and self.nearby_node is not None:
                    self.node_dragging = self.nearby_node
                elif not self.node_dragging and not keys[pygame.K_LSHIFT]:
                    self.process_left_click()
                    self.update_hovering_node()
            
            if event.button == 3:
                self.delete_selected()

            if event.button == 2:
                self.camera_dragging = True

            if event.button == 4:
                self.zoom += self.zoom * 0.1
            if event.button == 5:
                self.zoom += -(self.zoom * 0.1)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.camera_dragging = False
            self.node_dragging = None
            if not keys[pygame.K_LSHIFT]:
                pygame.mouse.set_cursor(pointerNormal)

        elif event.type == pygame.MOUSEMOTION:
            movement = pygame.mouse.get_rel()
            world_movement = Vector2(*movement) / self.zoom

            self.update_hovering_node()

            if self.camera_dragging:
                self.camera += Vector2(*movement) / self.zoom
            
            if self.node_dragging is not None:
                self.node_dragging.pos += world_movement
                self.calculate_paths()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.selected_node = None
            elif event.key == pygame.K_d:
                for node, edges in self.engine.graph.items():
                    print(node)
                    for edge in edges:
                        print(f"    {edge}")
            if self.nearby_node is not None and self.selected_node is None and self.node_dragging is None:
                # nearby and not drawing and not dragging
                if event.key == pygame.K_s:
                    self.start = self.nearby_node
                    if self.end == self.nearby_node: self.end = None
                    self.calculate_paths()
                elif event.key == pygame.K_e:
                    self.end = self.nearby_node
                    if self.start == self.nearby_node: self.start = None
                    self.maybe_update_path()
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LSHIFT and not self.node_dragging:
                pygame.mouse.set_cursor(pointerNormal)
        
        if keys[pygame.K_LSHIFT] and self.selected_node is None and pygame.mouse.get_cursor() != pointerMove:
            pygame.mouse.set_cursor(pointerMove)

        self.screen.fill((0, 0, 0))

        # preview placement
        if self.selected_node is not None:
            pos = self.nearby_node.pos if self.nearby_node is not None else self.to_world(Vector2(pygame.mouse.get_pos()))
            self.draw_dashed_line(
                (255, 255, 255),
                self.selected_node.pos,
                pos,
                width = self.EDGE_THICKNESS
            )

            if self.nearby_node is None:
                self.draw_circle((0, 0, 0), pos, self.SELECT_RANGE)
                self.draw_circle((255, 255, 255), pos, self.SELECT_RANGE, width=2)


        # rendering graph
        for node, edges in self.engine.graph.items():
            for edge in edges:
                color = (255, 255, 255)
                if edge in self.path or Edge(edge.end, edge.start) in self.path:
                    color = (255, 0, 0)

                # TODO: signify edge direction
                self.draw_line(
                    color,
                    node.pos,
                    edge.end.pos,
                    self.EDGE_THICKNESS
                )
                # BUG: fix identical edges going in opposite directions
        
        for node, edges in self.engine.graph.items():
            for edge in edges:
                self.draw_directional_head(
                    (232, 222, 130),
                    node.pos,
                    edge.end.pos,
                    self.EDGE_THICKNESS * 3,
                    min(self.SELECT_RANGE * 2, node.pos.distance_to(edge.end.pos))
                )
        
        for node, edges in self.engine.graph.items():
            color = (230, 201, 18)
            if self.start == node: color = (117, 245, 66)
            elif self.end == node: color = (245, 93, 66)
            elif self.selected_node == node: color = (194, 255, 148)
            elif self.nearby_node == node: color = (255, 240, 148)
            self.draw_circle(
                color,
                node.pos,
                self.SELECT_RANGE
            )
            
            

        pygame.display.flip()

engine = Engine()
renderer = Renderer(engine)
while renderer.running:
    #engine.simulate()
    renderer.render()
    renderer.clock.tick(renderer.FPS)