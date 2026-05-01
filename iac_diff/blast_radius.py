from dataclasses import dataclass
import networkx as nx
from .differ import ResourceChange

@dataclass
class BlastRadiusResult:
    change: ResourceChange
    directly_affected: list[str]
    transitively_affected: list[str]
    severity: str

    def affected_count(self):
        return len(set(self.directly_affected + self.transitively_affected))


def compute_blast_radius(
    changes: list[ResourceChange],
    graph_before: nx.DiGraph,
    graph_after: nx.DiGraph
) -> list[BlastRadiusResult]:
    results = []

    for change in changes:
        rid = change.resource_id
        G = graph_after if change.change_type != "removed" else graph_before

        if rid in G:
            direct = list(G.successors(rid))
            transitive = [n for n in nx.descendants(G, rid) if n not in direct]
        else:
            direct, transitive = [], []

        total = len(set(direct + transitive))
        severity = (
            "critical" if total > 10 else
            "high"     if total > 5  else
            "medium"   if total > 1  else
            "low"
        )

        results.append(BlastRadiusResult(
            change=change,
            directly_affected=direct,
            transitively_affected=transitive,
            severity=severity
        ))

    return results