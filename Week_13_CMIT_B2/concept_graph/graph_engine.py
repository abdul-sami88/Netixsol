"""
Concept Graph Engine
Constructs prerequisite Directed Acyclic Graph (DAG), performs cycle detection
(Kahn's and DFS 3-color), validates acyclicity, computes topological depth,
and maps lessons and questions to knowledge nodes.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict, deque
import json
import os
from concept_graph.concepts_def import CONCEPTS

class ConceptGraph:
    """
    Knowledge graph engine representing prerequisite relationships across Python learning concepts.
    """

    def __init__(self, concepts_data: Optional[List[Dict[str, Any]]] = None):
        self.concepts: Dict[str, Dict[str, Any]] = {}
        self.adj_list: Dict[str, List[str]] = defaultdict(list)        # u -> [v] (u is prereq for v)
        self.reverse_adj: Dict[str, List[str]] = defaultdict(list)    # v -> [u] (v requires u)
        self.in_degree: Dict[str, int] = defaultdict(int)
        self.lesson_mapping: Dict[str, List[str]] = {}
        self.question_mapping: Dict[str, str] = {}

        data = concepts_data if concepts_data is not None else CONCEPTS
        self._load_concepts(data)

    def _load_concepts(self, data: List[Dict[str, Any]]) -> None:
        """Loads concepts and constructs adjacency representations."""
        for c in data:
            c_id = c["id"]
            self.concepts[c_id] = c
            if c_id not in self.adj_list:
                self.adj_list[c_id] = []
            if c_id not in self.reverse_adj:
                self.reverse_adj[c_id] = []
            if c_id not in self.in_degree:
                self.in_degree[c_id] = 0

        # Build edges: prerequisite -> dependent
        for c in data:
            c_id = c["id"]
            for prereq in c.get("prerequisites", []):
                if prereq in self.concepts:
                    self.adj_list[prereq].append(c_id)
                    self.reverse_adj[c_id].append(prereq)
                    self.in_degree[c_id] += 1
                else:
                    raise ValueError(f"Prerequisite '{prereq}' for concept '{c_id}' not found in concept taxonomy.")

    def check_cycles_kahns(self) -> Tuple[bool, List[str]]:
        """
        Kahn's algorithm: Returns (is_acyclic, topological_order).
        If acyclic is False, topological_order contains only the nodes resolved before cycle deadlock.
        """
        in_deg = dict(self.in_degree)
        queue = deque([node for node, deg in in_deg.items() if deg == 0])
        topo_order = []

        while queue:
            curr = queue.popleft()
            topo_order.append(curr)

            for neighbor in self.adj_list[curr]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)

        is_dag = len(topo_order) == len(self.concepts)
        return is_dag, topo_order

    def find_cycles_dfs(self) -> List[List[str]]:
        """
        DFS 3-color algorithm (0=White, 1=Gray, 2=Black).
        Returns list of cycle paths found, if any.
        """
        color = {node: 0 for node in self.concepts}
        parent = {node: None for node in self.concepts}
        cycles = []

        def dfs(node: str, path: List[str]):
            color[node] = 1 # Gray
            for neighbor in self.adj_list[node]:
                if color[neighbor] == 1: # Found back edge -> cycle!
                    cycle_start_idx = path.index(neighbor) if neighbor in path else 0
                    cycle_path = path[cycle_start_idx:] + [neighbor]
                    cycles.append(cycle_path)
                elif color[neighbor] == 0:
                    parent[neighbor] = node
                    dfs(neighbor, path + [neighbor])
            color[node] = 2 # Black

        for node in self.concepts:
            if color[node] == 0:
                dfs(node, [node])

        return cycles

    def compute_concept_depths(self) -> Dict[str, int]:
        """
        Calculates topological tier/depth for each concept (longest distance from any root).
        Roots have depth 0.
        """
        is_dag, topo_order = self.check_cycles_kahns()
        if not is_dag:
            raise ValueError("Cannot compute depths: graph contains cycles!")

        depths = {node: 0 for node in self.concepts}
        for node in topo_order:
            for neighbor in self.adj_list[node]:
                if depths[node] + 1 > depths[neighbor]:
                    depths[neighbor] = depths[node] + 1

        return depths

    def get_prerequisites(self, concept_id: str, recursive: bool = True) -> Set[str]:
        """Returns direct or transitive prerequisites for a given concept."""
        if concept_id not in self.concepts:
            return set()

        if not recursive:
            return set(self.reverse_adj[concept_id])

        visited = set()
        stack = list(self.reverse_adj[concept_id])
        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.add(curr)
                stack.extend(self.reverse_adj[curr])
        return visited

    def get_dependents(self, concept_id: str, recursive: bool = True) -> Set[str]:
        """Returns direct or transitive dependent concepts that require this concept."""
        if concept_id not in self.concepts:
            return set()

        if not recursive:
            return set(self.adj_list[concept_id])

        visited = set()
        stack = list(self.adj_list[concept_id])
        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.add(curr)
                stack.extend(self.adj_list[curr])
        return visited

    def map_lessons(self, lesson_mappings: Dict[str, List[str]]) -> None:
        """Associates lesson IDs with their taught concepts."""
        for l_id, concept_ids in lesson_mappings.items():
            for c_id in concept_ids:
                if c_id not in self.concepts:
                    raise ValueError(f"Concept '{c_id}' in lesson {l_id} not in graph.")
            self.lesson_mapping[l_id] = concept_ids

    def map_questions(self, questions_data: List[Dict[str, Any]]) -> None:
        """Associates question IDs with their assessed concept."""
        for q in questions_data:
            q_id = q["id"]
            c_id = q["concept_id"]
            if c_id not in self.concepts:
                raise ValueError(f"Concept '{c_id}' for question {q_id} not in graph.")
            self.question_mapping[q_id] = c_id

    def export_graph(self, filepath: str = "concept_graph/concept_graph.json") -> Dict[str, Any]:
        """
        Exports graph nodes, edges, validation status, and mappings to JSON.
        """
        is_dag, topo_order = self.check_cycles_kahns()
        cycles = self.find_cycles_dfs()
        depths = self.compute_concept_depths() if is_dag else {}

        nodes = []
        for c_id, c_data in self.concepts.items():
            node_dict = dict(c_data)
            node_dict["depth"] = depths.get(c_id, 0)
            node_dict["in_degree"] = self.in_degree[c_id]
            node_dict["out_degree"] = len(self.adj_list[c_id])
            nodes.append(node_dict)

        edges = []
        for u in self.adj_list:
            for v in self.adj_list[u]:
                edges.append({"source": u, "target": v, "type": "prerequisite_of"})

        graph_payload = {
            "metadata": {
                "total_concepts": len(self.concepts),
                "total_prerequisite_edges": len(edges),
                "is_dag": is_dag,
                "cycles_detected": len(cycles),
                "max_depth": max(depths.values()) if depths else 0,
                "topological_sort": topo_order
            },
            "nodes": nodes,
            "edges": edges,
            "lesson_mapping": self.lesson_mapping,
            "question_mapping": self.question_mapping
        }

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(graph_payload, f, indent=2)

        return graph_payload

