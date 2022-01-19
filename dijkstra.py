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


def get_distance(graph: Dict[Hashable, Set[BaseEdge]], start: Hashable, dest: Hashable):
    visited: Set[Hashable] = set()
    tdists: Dict[Hashable, Union[float, int]] = {node: math.inf for node in graph}

    current = start
    tdists[current] = 0

    unvisited = []
    heapq.heappush(unvisited, (tdists[current], current))

    while dest not in visited:
        if len(unvisited):
            tdist, node = heapq.heappop(unvisited)
        else:
            return math.inf
        current = node
        if current in visited:
            continue

        for edge in graph[current]:
            if edge.end not in visited:
                new_dist = tdists[current] + edge.weight
                tdists[edge.end] = min(tdists[edge.end], new_dist)
                heapq.heappush(unvisited, (tdists[edge.end], edge.end))

        visited.add(current)

    return tdists[dest]

class SNode(NamedTuple):
    name: str

n1 = SNode("A")
n2 = SNode("B")
n3 = SNode("C")
g = {n1: {MyEdge(n2, 5)}, n2: {MyEdge(n3, 7)}, n3: set()}
print(get_distance(g, n1, n3))