import logging

import ontoweaver

def test_reconciliate():
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

    for n in fnodes:
        assert("p1" in n[2]) # properties
        assert("p2" in n[2]) # properties
        assert(n[0] in "12") # id
        assert(n[1] in ["Source", "Target"]) # Label/type
        logging.info(n)

    for e in fedges:
        assert("q1" in e[4])
        assert("q2" in e[4])
        assert(e[3] == "Edge")
        for l in e[0].split(";"):
            assert(l in "ABC")
        assert(e[1] in "12")
        assert(e[2] in "12")
        logging.info(e)


if __name__ == "__main__":
    test_reconciliate()
