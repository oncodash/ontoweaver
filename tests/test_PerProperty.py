import pytest

import ontoweaver

def test_PerProperty_simple():

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


def test_PerProperty_error():

    lhs = {
        "A": "a1",
        "D": "d1",
    }

    rhs = {
        "A": "a2",
        "D": "d2",
    }

    sep = "|"
    merger = ontoweaver.merge.dictry.PerProperty({
        "A": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "*": ontoweaver.merge.ErrorIfCalled(),
    })

    with pytest.raises(Exception):
        merger.merge("Nope", lhs, rhs)


def test_PerProperty_default():

    lhs = {
        "A": "a1",
        "B": "b",
        "D": "d1",
        "E": "e",
    }

    rhs = {
        "A": "a2",
        "C": "c",
        "D": "d2",
        "F": "f",
    }

    sep = "|"
    merger = ontoweaver.merge.dictry.PerProperty({
        "A": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "B": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "C": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "*": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
    })

    merger.merge("Nope", lhs, rhs)
    res = merger.get()

    assert len(res["A"].split(sep)) == 2
    assert len(res["B"].split(sep)) == 1
    assert len(res["C"].split(sep)) == 1
    assert len(res["D"].split(sep)) == 2
    assert len(res["E"].split(sep)) == 1
    assert len(res["F"].split(sep)) == 1



def test_PerProperty_state():

    d1 = {
        "A": "a1",
        "B": "b1",
        "D": "d1",
        "E": "e1",
    }

    d2 = {
        "A": "a2",
        "C": "c2",
        "D": "d2",
        "F": "f2",
    }

    d3 = {
        "A": "a3",
        "B": "b3",
        "D": "d3",
        "E": "e3",
        "A": "a3",
        "C": "c3",
        "D": "d3",
        "F": "f3",
    }

    sep = "|"
    merger = ontoweaver.merge.dictry.PerProperty({
        "A": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "B": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "C": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
        "*": ontoweaver.merge.string.OrderedSet(reconciliate_sep = sep),
    })

    merger.merge("Nope", d1, d2)
    d = merger.get()
    merger.merge("Nope", d, d3)
    d = merger.get()

    assert len(d["A"].split(sep)) == 3
    assert len(d["B"].split(sep)) == 2
    assert len(d["C"].split(sep)) == 2
    assert len(d["D"].split(sep)) == 3
    assert len(d["E"].split(sep)) == 2
    assert len(d["F"].split(sep)) == 2


