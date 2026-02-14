import ontoweaver
print("Module imported from:",ontoweaver.__file__)

import logging
logger = logging.getLogger("ontoweaver")

def test_congregate():
    nodes = [
        ("Source:1", "Source", {"p1":"z"}),
        ("Source:1", "Source", {"p2":"y"}), # Simple duplicate.
        ("Target:2", "Target", {"p1":"x", "p2":"y"}),
    ]

    edges = [
        ("Link:0", "Source:1", "Target:2", "Link", {}),
        ("Link:0", "Source:1", "Target:2", "Link", {}) # Complete duplicate
    ]
    logger.debug(nodes)

    on_ID = ontoweaver.serialize.ID()

    congregate_nodes = ontoweaver.congregate.Nodes(on_ID)
    print("nodes:",nodes)
    for n in congregate_nodes(nodes):
        pass

    assert nodes, "There is no node"
    logger.debug(congregate_nodes.duplicates)
    print("duplicates:",congregate_nodes.duplicates)
    assert len(congregate_nodes.duplicates) > 0, "There is no fused node"
    assert len(congregate_nodes.duplicates) == 2, "Not the correct number of duplicated nodes"

    congregate_edges = ontoweaver.congregate.Edges(on_ID)
    for n in congregate_edges(edges):
        pass

    assert edges, "There is no edge"
    assert len(congregate_edges.duplicates) == 1, "Not the correct number of duplicated nodes"


    on_Everything = ontoweaver.serialize.All()

    congregate_nodes = ontoweaver.congregate.Nodes(on_Everything)
    for n in congregate_nodes(nodes):
        pass
    assert nodes, "There is no node"
    assert len(congregate_nodes.duplicates) > 0, "There is no fused node"
    assert len(congregate_nodes.duplicates) == 3, "Not the correct number of duplicated nodes"

    congregate_edges = ontoweaver.congregate.Edges(on_Everything)
    for n in congregate_edges(edges):
        pass
    assert edges, "There is no edge"
    assert len(congregate_edges.duplicates) == 1, "Not the correct number of duplicated nodes"


if __name__ == "__main__":
    logger.setLevel("DEBUG")
    # logger.info("START")
    logging.getLogger("ontoweaver").setLevel("DEBUG")
    print("START")
    from biocypher._logger import get_logger as biocypher_logger
    biocypher_logger("biocypher").setLevel("DEBUG")
    test_congregate()
