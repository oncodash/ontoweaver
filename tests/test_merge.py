import logging

import ontoweaver

def test_append():

    sep = ";"
    merge = ontoweaver.merge.dictry.Append(sep)

    k = ontoweaver.base.Node()

    merge(k, {"p1":"x"},{"p2":"y"} )
    assert( merge.get() == {"p1":"x", "p2":"y"} )

    merge.reset()
    merge(k, {"p1":"x"},{} )
    assert( merge.get() == {"p1":"x"} )

    merge.reset()
    merge(k, {"p1":"x", "p2":"y"},{} )
    assert( merge.get() == {"p1":"x", "p2":"y"} )

    merge.reset()
    merge(k, {"p1":"x"},{"p1":"y"} )
    assert( "y" in merge.get()["p1"].split(sep) )
    assert( "x" in merge.get()["p1"].split(sep) )

    merge.reset()
    merge(k, {"p1":"abcd"},{"p1":"efgh"} )
    m = merge.get()
    assert( "abcd" in m["p1"].split(sep) )
    assert( "efgh" in m["p1"].split(sep) )

    merge.reset()
    merge(k, {"p1":"[abcd]"},{"p1":"[efgh]"} )
    m = merge.get()
    assert( "[abcd]" in m["p1"].split(sep) )
    assert( "[efgh]" in m["p1"].split(sep) )


def test_uselonger_useshorter():
    longer  = ontoweaver.merge.string.UseLonger()
    shorter = ontoweaver.merge.string.UseShorter()

    k = ontoweaver.base.Node()

    longer.reset()
    longer(k, "short", "but longer")
    assert longer.get() == "but longer"

    shorter.reset()
    shorter(k, "short", "but longer")
    assert shorter.get() == "short"


if __name__ == "__main__":
    test_append()
