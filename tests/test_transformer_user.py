import logging
import yaml
import pandas as pd
import ontoweaver
from ontoweaver import exceptions

class user_transformer(ontoweaver.base.Transformer):

    class ValueMaker(ontoweaver.make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def call(self, columns, row, i, **kwargs):
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
    adapter = ontoweaver.tabular.extract_table(table, mapping, affix="none")


if __name__ == "__main__":
    test_transformer_user()
