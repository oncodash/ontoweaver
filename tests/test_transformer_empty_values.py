import logging
import yaml
import io
import pandas as pd

import ontoweaver

def test_transformer_empty_values():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """,name,genre,is_child_of
0,father_1,Male,
1,child _nb_1_of_0,Female,father_1
2,child _nb_2_of_0,Female,father_1
3,child _nb_3_of_0,Male,father_1
4,father_2,Male,
5,father_3,Male,
6,child _nb_1_of_2,Male,father_3
7,child _nb_2_of_2,Male,father_3"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = """
row:
    map:
        id_from_column: name
        match_type_from_column: genre
        match:
            - Male:
                to_subject: Male
            - Female:
                to_subject: Female
transformers:
    - map:
        column: is_child_of
        to_object: Male
        via_relation: is_child_of
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    adapter = ontoweaver.tabular.extract_table(table, map, affix="none")

    nodes = list(adapter.nodes)
    edges = list(adapter.edges)

    print("***nodes:")
    print(nodes)
    print("---edges:")
    print(edges)

    assert(len(nodes)==13)
    assert(len(edges)==5)


if __name__ == "__main__":
    test_transformer_empty_values()


