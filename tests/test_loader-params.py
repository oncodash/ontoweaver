import os
import logging
import subprocess

import ontoweaver

tests = [
    "",
    "{}",
    """{"na_filter":true}""",
    """{"sep":"\\\\t"}""",
    """{"sep":"\\\\s"}""",
    """{"quoting":3}""",
    """{"dtype":"string"}""",
    """{"dtype":{"A":"Int64"}}""",
    """{"sep":"\\\\t","dtype":{"A":"Int64"}}""",
    """{"sep" : "\\\\s",\t"dtype":{\t "A":"Int64"}}""",
    """{"dtype":{"A":"Int64","B":"string"}}""",
]
input_file = "./tests/loader_params/data.tsv"
map_file = "./tests/loader_params/mapping.yaml"


def test_loader_params():

    for k in tests:
        sin = input_file + k + ":" + map_file
        ontoweaver.logger.debug(sin)
        dmk = ontoweaver.ontoweave.parse_data_map(sin)
        ontoweaver.logger.debug(dmk)
        n,e = ontoweaver.extract([dmk])
        assert len(n) == 6
        assert len(e) == 3


def test_loader_params_ontoweave():

    logging.debug(f"From: {os.getcwd()}")
    for k in tests:
        sin = input_file + k + ":" + map_file
        cmd=f"ontoweave '{sin}' --biocypher-config ./tests/loader_params/biocypher_config.yaml --auto-schema ./tests/loader_params/autoschema.yaml --auto-schema-overwrite --log-level DEBUG --debug"
        logging.debug(f"uv run {cmd}")
        subprocess.run(cmd, capture_output=True, check=True, shell=True)

