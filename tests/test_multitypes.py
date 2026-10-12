import ontoweaver
import pandas as pd

def test_MultiTypeLabelMaker():
    multi_type_dict = {
        "moderate": {
            "to_object": "fog",
            "via_relation": "reports",
            "final_type": "fog",
            "reverse_relation": None
            },
        "thick": {
            "to_object": "thickfog",
            "via_relation": "reports",
            "final_type": "thickfog",
            "reverse_relation": None
            }
        }

    validate = ontoweaver.validate.SkipValidator()

    m = ontoweaver.make_labels.MultiTypeLabelMaker()
    
    transformed_value = "moderate"
    branching_properties = {}
    row = None
    
    r = m(validate, transformed_value, multi_type_dict, branching_properties, row )
    assert r.extracted_cell_value == "moderate"
    assert r.edge_type == "reports"
    assert r.target_node_type == "fog"


def test_MultiTypeOnColumnLabelMaker():
    multi_type_dict = {
        "moderate": {
            "to_object": "fog",
            "via_relation": "reports",
            "final_type": "fog",
            "reverse_relation": None
            },
        "thick": {
            "to_object": "thickfog",
            "via_relation": "reports",
            "final_type": "thickfog",
            "reverse_relation": None
            }
        }

    validate = ontoweaver.validate.SkipValidator()

    m = ontoweaver.make_labels.MultiTypeOnColumnLabelMaker(match_type_from_column="fog_type")
    
    transformed_value = "moderate"
    branching_properties = {}
    row = pd.DataFrame({
        "fog_type": ["moderate"],
        "date": ["12/10/2026"]
                       })
    r = m(validate, transformed_value, multi_type_dict, branching_properties, row )
    assert r.extracted_cell_value == "moderate"
    assert r.edge_type == "reports"
    assert r.target_node_type == "fog"


def test_MultiTypeFromQueryLabelMaker():

    multi_type_dict = {
        "6 < wind_speed < 8": {
            "to_object": "level1",
            "via_relation": "reports",
            "final_type": "level1",
            "reverse_relation": None
            },
        "8 < wind_speed < 10": {
            "to_object": "level2",
            "via_relation": "reports",
            "final_type": "level2",
            "reverse_relation": None
            },
        "wind_speed >= 10": {
            "to_object": "level3",
            "via_relation": "reports",
            "final_type": "level3",
            "reverse_relation": None
            }
        }

    m = ontoweaver.make_labels.MultiTypeFromQueryLabelMaker()
    
    transformed_value = "9.1"
    branching_properties = {}
    validate = ontoweaver.validate.SkipValidator()
    df = pd.DataFrame({
        "wind_speed": [9.1, 5, 8, 11],
        "date": ["12/10/2026", "12/10/2026", "12/10/2026", "12/10/2026"]
         })
    r = m(validate, transformed_value, multi_type_dict, branching_properties, df.iloc[0]) 

    assert r.extracted_cell_value == "9.1"
    assert r.edge_type == "reports"
    assert r.target_node_type == "level2"
    
    transformed_value = "11"
    r = m(validate, transformed_value, multi_type_dict, branching_properties, df.iloc[3]) 

    assert r.extracted_cell_value == "11"
    assert r.edge_type == "reports"
    assert r.target_node_type == "level3"

if __name__ == "__main__":
    test_MultiTypeLabelMaker()
    test_MultiTypeOnColumnLabelMaker()
    test_MultiTypeFromQueryLabelMaker()
