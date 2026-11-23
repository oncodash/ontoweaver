import yaml
import logging

import ontoweaver

logger = logging.getLogger("ontoweaver")

def test_submap_properties():

    row = {  # JSON payload.
        "target": '''{
            "concepts": [
                {"id": "a", "group": "A"},
                {"id": "b", "group": "B"}
            ],
            "date": "now",
            "extraction": {"ref": "X"}
        }'''
    }

    map = '''
columns:
    - target
submapping:
  row:
      map:
          element: concepts[*].id
          to_subject: node
  transformers:
      - map:
          element: concepts[*].group
          to_property: group
          for_object: node
    '''

    yamap = yaml.safe_load(map)

    t = ontoweaver.transformer.submap({}, **yamap)

    result = t(row, 0)
    assert not result

    nodes,edges = t.get()

    for node in nodes:
        n = node.as_tuple()
        logging.debug(n)
        assert "group" in n[2]
        assert n[2]["group"] == n[0].upper()

    # 2 subjects
    assert len(nodes) == 2
    assert len(edges) == 0


def test_submap_edge():

    row = {  # JSON payload.
        "target": '''{
            "concepts": [
                {"id": "a", "group": "A"},
                {"id": "b", "group": "B"}
            ],
            "date": "now",
            "extraction": {"ref": "X"}
        }'''
    }

    map = '''
columns:
    - target
submapping:
  row:
      map:
          element: concepts[*].id
          to_subject: node
  transformers:
      - map:
          element: concepts[*].group
          to_object: group
          via_relation: related
    '''

    yamap = yaml.safe_load(map)

    t = ontoweaver.transformer.submap({}, **yamap)

    result = t(row, 0)
    assert not result

    nodes,edges = t.get()

    for node in nodes:
        n = node.as_tuple()
        assert not n[2]
        logging.debug(n)

    for edge in edges:
        e = edge.as_tuple()
        logging.debug(e)

    # 2 subjects, 2 objects
    assert len(nodes) == 4
    assert len(edges) == 2

