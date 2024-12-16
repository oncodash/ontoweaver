import os
import subprocess
import logging

def test_ontoweave():
    logging.debug(f"From: {os.getcwd()}")
    cmd="./src/tools/ontoweave --config ./tests/simplest/biocypher_config.yaml --schema ./tests/simplest/schema_config.yaml --type-affix suffix --type-affix-sep : --prop-sep ';' --log-level DEBUG ./tests/simplest/data.csv:./tests/simplest/mapping.yaml --import-script-run"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)

if __name__ == "__main__":
    test_ontoweave()
