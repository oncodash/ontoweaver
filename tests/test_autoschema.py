import yaml
import logging
import ontoweaver

def test_autoschema_edge_property():

    logging.debug("Load mapping...")

    mapping = r"""
row:
    rowIndex:
        to_subject: people
transformers:
    - map:
        column: Team
        to_object: team
        via_relation: in_team
    - map:
        column: Role
        to_property: role
        for_object: people  # node
    - map:
        column: Since
        to_property: since
        for_object: in_team  # edge
"""

    map = yaml.safe_load(mapping)

    logging.debug("Make an autoschema...")
    auto_schema = ontoweaver.make_autoschema([map], {})
    print(yaml.dump(auto_schema))

    assert "properties" in auto_schema["people"]
    assert "role" in auto_schema["people"]["properties"]
    assert "properties" in auto_schema["in_team"]
    assert "since" in auto_schema["in_team"]["properties"]

