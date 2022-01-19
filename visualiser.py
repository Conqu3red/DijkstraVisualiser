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

@dataclass
class Node:
    pos: Vector2
    id: UUID = dataclasses.field(default_factory=uuid4)

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass
class Edge:
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
    
    def remove_node(self, node: Node):
        del self.graph[node]
        for edges in self.graph.values():
            for edge in [e for e in edges]:
                if edge.end is node or edge.start is node:
                    edges.remove(edge)


class Mode(Enum):
    NORMAL = 0


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

        return node

    def place_edge(self, n1: Node, n2: Node):
        if n2 is not n1:
            self.engine.graph[n1].add(Edge(n1, n2))
        self.selected_node = n2

    def process_left_click(self):
        if self.selected_node is not None:
            self.place_edge(self.selected_node, self.create_node() if self.nearby_node is None else self.nearby_node)
        else:
            self.selected_node = self.nearby_node if self.nearby_node is not None else self.create_node()

    def delete_selected(self):
        if self.nearby_node is not None:
            self.engine.remove_node(self.nearby_node)
            self.selected_node = None
            self.nearby_node = None
            self.node_dragging = None

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
            world_movement = self.to_world(Vector2(*movement))

            self.update_hovering_node()

            if self.camera_dragging:
                self.camera += Vector2(*movement) / self.zoom
            
            if self.node_dragging is not None:
                self.node_dragging.pos += world_movement

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.selected_node = None
            elif event.key == pygame.K_r and self.start and self.end:
                print("Running.")
                
            if self.nearby_node is not None and self.selected_node is None and self.node_dragging is None:
                # nearby and not drawing and not dragging
                if event.key == pygame.K_s:
                    self.start = self.nearby_node
                    if self.end == self.nearby_node: self.end = None
                elif event.key == pygame.K_e:
                    self.end = self.nearby_node
                    if self.start == self.nearby_node: self.start = None
        
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
            color = (255, 255, 255)
            for edge in edges:
                self.draw_line(
                    color,
                    node.pos,
                    edge.end.pos,
                    self.EDGE_THICKNESS
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