import logging

import ontoweaver

def test_reconciliate():

    dir = "tests/simplest/"

    fnodes, fedges = ontoweaver.fusion.reconciliate(
        dir+"/biocypher_config.yaml",
        dir+"/schema_config.yaml",
        {
            dir+"data.csv": dir+"mapping.yaml"
        }
    )

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
