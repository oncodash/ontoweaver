import logging
import ontoweaver

def test_merger_Function():

    key = ontoweaver.base.Node()

    merge = ontoweaver.merge.string.Function(max)
    merge(key, "a", "b")
    assert merge.get() == "b"

    merge = ontoweaver.merge.string.Function(min)
    merge(key, "a", "b")
    assert merge.get() == "a"

    merge = ontoweaver.merge.string.Function(max, int)
    merge(key, "1", "2")
    assert merge.get() == "2"

    merge = ontoweaver.merge.string.Function(max, float)
    merge(key, "1", "2")
    assert merge.get() == "2.0"

    merge = ontoweaver.merge.string.Function(min, int)
    merge(key, "1", "2")
    assert merge.get() == "1"

    merge = ontoweaver.merge.string.Function(lambda x,y: ",".join([x,y]), str)
    merge(key, "oh", "ha")
    assert merge.get() == "oh,ha"

