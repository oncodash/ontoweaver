import io
import yaml
import logging
import ontoweaver

def test_from_file():
    mapping = """
row:
   map:
       column: /table/tbody/tr/td[1]
       to_subject: variant
transformers:
    - map:
        column: /table/tbody/tr/td[2]
        to_object: patient
        via_relation: patient_has_variant
    - map:
        column: /table/tbody/tr/td[3]
        to_property: age
        for_object: patient
metadata:
    - origin: somewhere
    """
    config = yaml.full_load(mapping)

    parser = ontoweaver.mapping.YamlParser(config)
    mapper = parser()

    lxs = ontoweaver.loader.LoadXMLFile()
    local_nodes,local_edges = ontoweaver.load_extract("tests/xml/friends.xml", config, lxs, raise_errors = False)

    for n in local_nodes:
        logging.debug(repr(n))
    for e in local_edges:
        logging.debug(repr(e))

    assert len(local_nodes) == 6
    assert len(local_edges) == 3


def test_xpath():
    xml="""
<table>
    <caption>Friends</caption>
    <thead>
        <tr><th>variant_id</th><th>patient</th><th>age</th></tr>
    </thead>
    <tbody>
        <tr><td>1</td><td>B</td><td>12</td></tr>
        <tr><td>0</td><td>A</td><td>23</td></tr>
        <tr><td>2</td><td>C</td><td>34</td></tr>
    </tbody>
</table>
    """

    mapping = """
row:
   map:
       element: /table/tbody/tr/td[1]
       to_subject: variant
transformers:
    - map:
        element: /table/tbody/tr/td[2]
        to_object: patient
        via_relation: patient_has_variant
    - map:
        element: /table/tbody/tr/td[3]
        to_property: age
        for_object: patient
metadata:
    - origin: somewhere
    """
    config = yaml.full_load(mapping)

    parser = ontoweaver.mapping.YamlParser(config)
    mapper = parser()

    lxs = ontoweaver.loader.LoadXMLString()
    local_nodes,local_edges = ontoweaver.load_extract(xml, config, lxs, raise_errors = False)

    for n in local_nodes:
        logging.debug(repr(n))
    for e in local_edges:
        logging.debug(repr(e))

    assert len(local_nodes) == 6
    assert len(local_edges) == 3

if __name__ == "__main__":
    test_xpath()
