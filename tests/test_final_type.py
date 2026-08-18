import io
import yaml
import logging
import ontoweaver
import pandas as pd

def test_final_type():
    from . import testing_functions

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "final_type"

    expected_nodes = [
        ('chair:aaaaaa', 'aaaaaa', {'localisation': 'Peterkitchen', 'blabla': 'blabla', 'source_columns': 'furniture'}),
        ('kitchen:eeeeee', 'eeeeee', {'blabla': 'blabla', 'source_columns': 'localisation'}),
        ('Paul:cccccc', 'cccccc', {'blabla': 'blabla', 'source_columns': 'name'}),
        ('bathroom:eeeeee', 'eeeeee', {'blabla': 'blabla', 'source_columns': 'localisation'}),
        ('Mary:dddddd', 'dddddd', {'blabla': 'blabla', 'source_columns': 'name'}),
        ('sofa:aaaaaa', 'aaaaaa', {'localisation': 'Paulbathroom', 'blabla': 'blabla', 'source_columns': 'furniture'}),
        ('fridge:aaaaaa', 'aaaaaa', {'localisation': 'Marykitchen', 'blabla': 'blabla', 'source_columns': 'furniture'}),
        ('Peter:dddddd', 'dddddd', {'blabla': 'blabla', 'source_columns': 'name'})
    ]

    expected_edges = [
        ('(chair:aaaaaa)--[has_localisation]->(kitchen:eeeeee)', 'chair:aaaaaa', 'kitchen:eeeeee', 'has_localisation', {'blabla': 'blabla'}),
        ('(chair:aaaaaa)--[will_not_sit]->(Peter:dddddd)', 'chair:aaaaaa', 'Peter:dddddd', 'will_not_sit', {'blabla': 'blabla'}),
        ('(fridge:aaaaaa)--[will_not_sit]->(Mary:dddddd)', 'fridge:aaaaaa', 'Mary:dddddd', 'will_not_sit', {'blabla': 'blabla'}),
        ('(sofa:aaaaaa)--[will_sit]->(Paul:cccccc)', 'sofa:aaaaaa', 'Paul:cccccc', 'will_sit', {'blabla': 'blabla'}),
        ('(sofa:aaaaaa)--[has_localisation]->(bathroom:eeeeee)', 'sofa:aaaaaa', 'bathroom:eeeeee', 'has_localisation', {'blabla': 'blabla'}),
        ('(fridge:aaaaaa)--[has_localisation]->(kitchen:eeeeee)', 'fridge:aaaaaa', 'kitchen:eeeeee', 'has_localisation', {'blabla': 'blabla'})
    ]

    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    logging.debug(fnodes)
    logging.debug(fedges)
    testing_functions.assert_equals(fnodes, expected_nodes)
    testing_functions.assert_equals(fedges, expected_edges)


def test_final_type_2():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Managed,Manager,Team
Johann,Benno,CSB
Matthieu,Benno,CSB
"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = r"""
row:
    map:
        column: Managed
        to_subject: people_managed
        final_type: people
transformers:
    - map:
        column: Manager
        to_object: people_manager
        via_relation: managed
        final_type: people
    - map:
        column: Team
        to_property: team
        for_objects:
            - people_managed
            - people_manager
"""

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for node in nodes:
        n = node.as_tuple()
        logging.debug(n)
        assert n[1] == "people"
        assert n[2] == {"team": "CSB"}

    for edge in edges:
        logging.debug(edge.as_tuple())

    assert len(nodes) == 4
    assert len(edges) == 2


def test_final_type_compose():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Managed_FirstName,Managed_LastName,Manager_FirstName,Manager_LastName,Team
Dreo,Johann,Schwikowski,Benno,CSB
Najm,Matthieu,Schwikowski,Benno,CSB
"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = r"""
row:
    compose:
        columns:
            - Managed_FirstName
            - Managed_LastName
        call:
            - cat_format:
                format_string: "{Managed_LastName}, {Managed_FirstName}"
            - western_name
        to_subject: people_managed
        final_type: people
transformers:
    - compose:
        columns:
            - Manager_FirstName
            - Manager_LastName
        call:
            - cat_format:
                format_string: "{Manager_LastName}, {Manager_FirstName}"
            - western_name
        to_object: people_manager
        final_type: people
        via_relation: managed by
    - map:
        column: Team
        to_property: team
        for_objects:
            - people_managed
            - people_manager
"""

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for node in nodes:
        n = node.as_tuple()
        logging.debug(n)
        assert n[1] == "people"
        assert n[2] == {"team": "CSB"}

    for edge in edges:
        logging.debug(edge.as_tuple())

    assert len(nodes) == 4
    assert len(edges) == 2


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    test_final_type_compose()
