import logging

import ontoweaver

nodes = [
    ("1", "Source", {"p1":"z"}),
    ("1", "Source", {"p2":"y"}), # Simple duplicate.
    ("2", "Target", {}),
    ("2", "Target", {"p1":"x", "p2":"y"}),
    ("2", "Target", {"p2":"z"}),
]

edges = [
    ("A", "1", "2", "Edge", {"q1":"i"}),
    ("B", "1", "2", "Edge", {"q2":"j"}),
    ("C", "2", "1", "Edge", {"q1":"i", "q2": "j"}),
]

fnodes, fedges = ontoweaver.fusion.reconciliate(nodes, edges)

assert(len(fnodes) == 2)
assert(len(fedges) == 2)
