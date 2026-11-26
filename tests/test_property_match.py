import pandas as pd
import pytest

import ontoweaver
from ontoweaver import exceptions


@pytest.mark.parametrize("property_key", ["to_property", "to_properties"])
def test_match_on_property_mapping_is_rejected(property_key):
    table = pd.DataFrame({"value": ["yes", "no"]})
    mapping = {
        "row": {"rowIndex": {"to_subject": "sample"}},
        "transformers": [
            {
                "map": {
                    "column": "value",
                    property_key: "status"
                    if property_key == "to_property"
                    else ["status"],
                    "for_object": "sample",
                    "match": [{"yes": {"to_property": "status"}}],
                }
            },
        ],
    }

    with pytest.raises(exceptions.TransformerConfigError, match="match.*propert"):
        ontoweaver.extract_table(table, mapping, affix="none")


def test_invalid_property_match_is_skipped_when_errors_are_disabled(caplog):
    table = pd.DataFrame({"value": ["no"]})
    mapping = {
        "row": {"rowIndex": {"to_subject": "sample"}},
        "transformers": [
            {
                "map": {
                    "column": "value",
                    "to_property": "invalid_status",
                    "for_object": "sample",
                    "match": [{"yes": {"to_property": "invalid_status"}}],
                }
            },
            {
                "map": {
                    "column": "value",
                    "to_property": "valid_status",
                    "for_object": "sample",
                }
            },
        ],
    }

    nodes, edges = ontoweaver.extract_table(
        table, mapping, affix="none", raise_errors=False
    )

    assert len(nodes) == 1
    assert nodes[0].properties == {"valid_status": "no"}
    assert edges == []
    assert "match" in caplog.text
