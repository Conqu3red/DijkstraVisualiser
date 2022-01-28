import dataclasses
from typing import *
from dataclasses import dataclass
import math
import heapq
from abc import abstractmethod

class BaseEdge:
    end: Hashable
    weight: Union[int, float]

    @abstractmethod
    def __hash__(self) -> int: ...

@dataclass
class MyEdge(BaseEdge):
    end: Hashable  # directional graph
    weight: Union[int, float]

    def __hash__(self) -> int:
        return hash((self.end,))

@dataclass
class Dist:
    dist: float
    shortest_parent: Optional[BaseEdge]

    def __lt__(self, o):
        if isinstance(o, Dist):
            return self.dist < o.dist



def dijkstra(graph: Dict[Hashable, Set[BaseEdge]], start: Hashable) -> Dict[Hashable, Dist]:
    visited: Set[Hashable] = set()
    tdists: Dict[Hashable, Dist] = {node: Dist(math.inf, None) for node in graph}
    # TODO: store metadata in tdists about where the previous edge came from!! To recreate the path

    current = start
    tdists[current].dist = 0

    unvisited = []
    heapq.heappush(unvisited, (tdists[current], current))

    while unvisited:
        tdist, node = heapq.heappop(unvisited)
        
        current = node
        if current in visited:
            continue

        for edge in graph[current]:
            if edge.end not in visited:
                new_dist = tdists[current].dist + edge.weight
                if new_dist < tdists[edge.end].dist:
                    tdists[edge.end].dist = new_dist
                    tdists[edge.end].shortest_parent = edge # BUG: not working?
                # TODO: store edge instead of node
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