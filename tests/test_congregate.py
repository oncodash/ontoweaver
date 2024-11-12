import ontoweaver

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

    on_ID = ontoweaver.serialize.ID()

    congregate_nodes = ontoweaver.congregate.Nodes(on_ID)
    congregate_nodes(nodes)
    assert(len(congregate_nodes.duplicates) == 2)

    congregate_edges = ontoweaver.congregate.Edges(on_ID)
    congregate_edges(edges)
    assert(len(congregate_edges.duplicates) == 1)


    on_Everything = ontoweaver.serialize.All()

    congregate_nodes = ontoweaver.congregate.Nodes(on_Everything)
    congregate_nodes(nodes)
    assert(len(congregate_nodes.duplicates) == 3)

    congregate_edges = ontoweaver.congregate.Edges(on_Everything)
    congregate_edges(edges)
    assert(len(congregate_edges.duplicates) == 1)


if __name__ == "__main__":
    test_congregate()
