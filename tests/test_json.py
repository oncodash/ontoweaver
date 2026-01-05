import io
import yaml
import logging
import ontoweaver

def test_from_file():
    mapping = """
row:
   map:
       column: data[*].variant
       to_subject: variant
transformers:
    - map:
        column: data[*].patient
        to_object: patient
        via_relation: patient_has_variant
    - map:
        column: data[*].age
        to_property: age
        for_object: patient
metadata:
    - origin: somewhere
    """
    config = yaml.full_load(mapping)

    parser = ontoweaver.mapping.YamlParser(config)
    mapper = parser()

    ljs = ontoweaver.loader.LoadJSONFile()
    local_nodes,local_edges = ontoweaver.load_extract("tests/json/friends.json", config, ljs, raise_errors = False)

    for n in local_nodes:
        logging.debug(repr(n))
    for e in local_edges:
        logging.debug(repr(e))

    assert len(local_nodes) == 6
    assert len(local_edges) == 3


def test_jmespath():
    json="""
{
    "data": [
        {"variant": 0, "patient": "A", "age": 12 },
        {"variant": 1, "patient": "B", "age": 23 },
        {"variant": 2, "patient": "C", "age": 34 }
    ]
}
    """

    mapping = """
row:
   map:
       element: data[*].variant
       to_subject: variant
transformers:
    - map:
        element: data[*].patient
        to_object: patient
        via_relation: patient_has_variant
    - map:
        element: data[*].age
        to_property: age
        for_object: patient
metadata:
    - origin: somewhere
    """
    config = yaml.full_load(mapping)

    parser = ontoweaver.mapping.YamlParser(config)
    mapper = parser()

    ljs = ontoweaver.loader.LoadJSONString()
    local_nodes,local_edges = ontoweaver.load_extract(json, config, ljs, raise_errors = False)

    for n in local_nodes:
        logging.debug(repr(n))
    for e in local_edges:
        logging.debug(repr(e))

    assert len(local_nodes) == 6
    assert len(local_edges) == 3

if __name__ == "__main__":
    test_xpath()

