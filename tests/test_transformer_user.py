import io
import json
import yaml
import logging
import pandas as pd
import ontoweaver
from ontoweaver import exceptions

class user_transformer(ontoweaver.base.Transformer):

    class ValueMaker(ontoweaver.make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                if key not in row:
                    self.error(f"Column '{key}' not found in data", section="map.call",
                               exception=exceptions.TransformerDataError)
                yield row[key]

    def __init__(self, properties_of, value_maker = ValueMaker(), label_maker = None, branching_properties=None, columns=None, **kwargs):
        super().__init__(properties_of, value_maker, label_maker, branching_properties, columns, **kwargs)

    def __call__(self, row, i):

        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)


def test_transformer_user():
    # Add the passed transformer to the list available to OntoWeaver.
    ontoweaver.transformer.register(user_transformer)

    directory_name = "simplest"

    logging.debug("Load mapping...")
    yaml_mapping = """
    row:
        rowIndex:
            to_subject: variant
    transformers:
        - user_transformer:
            columns:
                - patient
            to_object: patient
            via_relation: patient_has_variant
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, mapping, affix="none")


class jsonmap(ontoweaver.base.Transformer):
    def __call__(self, row, i):
        c = row[self.columns[0]]
        l = json.loads(c)
        for e in l:
            if "lastname" in e:
                v = e["lastname"]
                if v:
                    yield self.create(v, row)

def test_transformer_user_json():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = '''Name,Data
Bob,[{"lastname":"Sponge"}]
Claire,[]
Matthieu,"[]"
Marko,[{}]
Johann,"[{""lastname"":""Dreo""},{""lastname"":""Dréo""}]"'''

    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = r"""
row:
    map:
        column: Name
        to_subject: person
transformers:
    - jsonmap:
        column: Data
        to_property: lastname
        for_object: person
"""

    ontoweaver.transformer.register(jsonmap)

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for n in nodes:
        logging.debug(n)
        assert "lastname" in n.properties
        assert isinstance(n.properties["lastname"], str) or isinstance(n.properties["lastname"], list)
        if isinstance(n.properties["lastname"], list):
            assert len(n.properties["lastname"]) == 2


if __name__ == "__main__":
    logging.getLogger().setLevel("DEBUG")
    test_transformer_user_json()

