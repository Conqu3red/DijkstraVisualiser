import dataclasses
from typing import *
from dataclasses import dataclass
import math
import heapq
from abc import abstractmethod

class BaseEdge:
    @property
    @abstractmethod
    def end(self) -> Hashable: ...

    @property
    @abstractmethod
    def weight(self) -> Union[float, int]: ...

    @abstractmethod
    def __hash__(self) -> int: ...

class MyEdge(BaseEdge, NamedTuple):
    end: Hashable  # directional graph
    weight: int

@dataclass
class Dist:
    dist: float
    shortest_parent: Optional[Hashable]


def dijkstra(graph: Dict[Hashable, Set[BaseEdge]], start: Hashable) -> Dict[Hashable, Dist]:
    visited: Set[Hashable] = set()
    tdists: Dict[Hashable, Dist] = {node: Dist(math.inf, None) for node in graph}
    # TODO: store metadata in tdists about where the previous edge came from!! To recreate the path

    current = start
    tdists[current] = 0

    unvisited = []
    heapq.heappush(unvisited, (tdists[current], current))

    while unvisited:
        tdist, node = heapq.heappop(unvisited)
        
        current = node
        if current in visited:
            continue

        for edge in graph[current]:
            if edge.end not in visited:
                new_dist = tdists[current] + edge.weight
                tdists[edge.end].dist = min(tdists[edge.end], new_dist)
                tdists[edge.end].shortest_parent = current
                heapq.heappush(unvisited, (tdists[edge.end], edge.end))

        visited.add(current)

    return tdists

class SNode(NamedTuple):
    name: str

n1 = SNode("A")
n2 = SNode("B")
n3 = SNode("C")
g = {n1: {MyEdge(n2, 5)}, n2: {MyEdge(n3, 7)}, n3: set()}
print(dijkstra(g, n1))