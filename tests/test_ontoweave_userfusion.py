import os
import logging
import subprocess

def test_userfusion():
    logging.debug(f"From: {os.getcwd()}")
    cmd="uv run tests/userfusion.py --biocypher-config ./tests/simplest/biocypher_config.yaml --biocypher-schema ./tests/simplest/schema_config.yaml --type-affix suffix --type-affix-sep : --prop-sep ';' --debug ./tests/simplest/data.csv:./tests/simplest/mapping.yaml"

    logging.info(f"Run: {' '.join(cmd)}")
    try:
        subprocess.run(cmd.split(), capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        for k,v in e.__dict__.items():
            logging.error(k)
            if isinstance(v, bytes):
                logging.error(v.decode("utf-8"))
            else:
                logging.error(v)
        raise e
