import os
import logging
import subprocess

import ontoweaver

class user_transformer(ontoweaver.transformer.Transformer):
    def __init__(self, target, properties_of, edge=None, columns=None, **kwargs):
        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, i):
        for key in self.columns:
            yield str(row[key])


def test_ontoweave():
    logging.debug(f"From: {os.getcwd()}")
    cmd="./bin/ontoweave --biocypher-config ./tests/simplest/biocypher_config.yaml --biocypher-schema ./tests/simplest/schema_config.yaml --type-affix suffix --type-affix-sep : --prop-sep ';' --log-level DEBUG ./tests/simplest/data.csv:./tests/simplest/mapping.yaml"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


def test_ontoweave_register():
    logging.debug(f"From: {os.getcwd()}")
    cmd="./bin/ontoweave --biocypher-config ./tests/simplest/biocypher_config.yaml --biocypher-schema ./tests/simplest/schema_config.yaml --type-affix suffix --type-affix-sep : --prop-sep ';' --log-level DEBUG ./tests/simplest/data.csv:./tests/simplest/mapping.yaml --register ./tests/test_ontoweave.py"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


if __name__ == "__main__":
    test_ontoweave()
