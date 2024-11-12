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


if __name__ == "__main__":
    test_append()
