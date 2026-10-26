import ontoweaver

def test_PerProperty():

    lhs = {
        "A": "a1",
        "B": "b1",
    }

    rhs = {
        "A": "a2",
        "B": "b2",
        "C": "c",
    }

    sep = "|"
    merger = ontoweaver.merge.dictry.PerProperty({
        "A": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "B": ontoweaver.merge.string.UseFirst(),
        "C": ontoweaver.merge.string.UseLast(),
        "*": ontoweaver.merge.ErrorIfCalled(),
    })

    merger.merge("Nope", lhs, rhs)
    res = merger.get()

    assert len(res["A"].split(sep)) == 2
    assert res["B"] == "b1"
    assert res["C"] == "c"


def test_PerProperty_default():

    lhs = {
        "A": "a1",
        "B": "b1",
    }

    rhs = {
        "A": "a2",
        "B": "b2",
        "C": "c",
    }

    sep = "|"
    merger = ontoweaver.merge.dictry.PerProperty({
        "A": ontoweaver.merge.string.UseFirst(),
        "*": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
    })

    merger.merge("Nope", lhs, rhs)
    res = merger.get()

    assert res["A"] == "a1"
    assert len(res["B"].split(sep)) == 2
    assert res["C"] == "c"


