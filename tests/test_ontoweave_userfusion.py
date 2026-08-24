import os
import logging
import subprocess

def test_userfusion():
    logging.debug(f"From: {os.getcwd()}")
    cmd="tests/userfusion.py --biocypher-config ./tests/simplest/biocypher_config.yaml --biocypher-schema ./tests/simplest/schema_config.yaml --type-affix suffix --type-affix-sep : --prop-sep ';' --debug ./tests/simplest/data.csv:./tests/simplest/mapping.yaml"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)

