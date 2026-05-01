import networkx as nx
from .parser import Resource

def build_graph(resources: dict[str, Resource]) -> nx.DiGraph:
    """Build a directed dependency graph from parsed resources"""
    G = nx.DiGraph()
    
    for rid, resource in resources.items():
        G.add_node(rid, resource=resource, type=resource.type)
    
    for rid, resource in resources.items():
        for ref in resource.references:
            if ref in resources:
                # rid depends on ref
                G.add_edge(ref, rid, label="depends_on")
    
    return G


def get_dependents(G: nx.DiGraph, node: str) -> list[str]:
    """All nodes downstream of this node (things that depend on it)"""
    if node not in G:
        return []
    return list(nx.descendants(G, node))


def get_dependencies(G: nx.DiGraph, node: str) -> list[str]:
    """All nodes upstream of this node (things this node needs)"""
    if node not in G:
        return []
    return list(nx.ancestors(G, node))