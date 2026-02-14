import os
import logging
import subprocess

import ontoweaver

class user_transformer(ontoweaver.base.Transformer):
    def __init__(self, target, properties_of, edge=None, columns=None, **kwargs):
        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, i):
        for key in self.columns:
            yield str(row[key])


def test_ontoweave():
    logging.debug(f"From: {os.getcwd()}")
    cmd="ontoweave --biocypher-config ./tests/simplest/biocypher_config.yaml --biocypher-schema ./tests/simplest/schema_config.yaml --type-affix suffix --type-affix-sep : --prop-sep ';' --debug ./tests/simplest/data.csv:./tests/simplest/mapping.yaml"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


def test_ontoweave_register():
    logging.debug(f"From: {os.getcwd()}")
    cmd="ontoweave --biocypher-config ./tests/simplest/biocypher_config.yaml --biocypher-schema ./tests/simplest/schema_config.yaml --type-affix suffix --type-affix-sep : --prop-sep ';' --debug ./tests/simplest/data.csv:./tests/simplest/mapping.yaml --register ./tests/test_ontoweave.py"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


def test_ontoweave_automap():
    logging.debug(f"From: {os.getcwd()}")
    cmd="ontoweave --biocypher-config ./tests/family_automap/biocypher_config_2_bioPathNet.yaml --biocypher-schema ./tests/family_automap/schema_config.yaml ./tests/family_automap/reasoned.ttl:automap --debug"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


def test_ontoweave_autoschema_min():
    logging.debug(f"From: {os.getcwd()}")
    d = "./tests/autoschema"
    xs = f"{d}/extended_schema.yaml"
    if os.path.isfile(xs):
        os.remove(xs)
    cmd = f"ontoweave --biocypher-config {d}/biocypher_config.yaml --auto-schema {xs} --biocypher-schema {d}/schema_min.yaml {d}/example.csv:{d}/mapping.yaml {d}/example.csv:{d}/mapping_with_props.yaml --debug"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


def test_ontoweave_autoschema_complete():
    logging.debug(f"From: {os.getcwd()}")
    d = "./tests/autoschema"
    xs = f"{d}/extended_schema.yaml"
    if os.path.isfile(xs):
        os.remove(xs)
    cmd = f"ontoweave --biocypher-config {d}/biocypher_config.yaml --auto-schema {xs} --biocypher-schema {d}/schema_complete.yaml {d}/example.csv:{d}/mapping.yaml {d}/example.csv:{d}/mapping_with_props.yaml --debug"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


def test_ontoweave_autoschema_half():
    logging.debug(f"From: {os.getcwd()}")
    d = "./tests/autoschema"
    xs = f"{d}/extended_schema.yaml"
    if os.path.isfile(xs):
        os.remove(xs)
    cmd = f"ontoweave --biocypher-config {d}/biocypher_config.yaml --auto-schema {xs} --biocypher-schema {d}/schema_half.yaml {d}/example.csv:{d}/mapping.yaml {d}/example.csv:{d}/mapping_with_props.yaml --debug"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


if __name__ == "__main__":
    test_ontoweave()
