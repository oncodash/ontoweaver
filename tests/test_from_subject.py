import os
import sys
import logging
import subprocess

import ontoweaver


def test_from_subject():
    logging.debug(f"From: {os.getcwd()}")
    d = "./tests/from_subject"
    cmd=f"ontoweave {d}/path.csv:{d}/path.yaml --type-affix suffix --biocypher-schema {d}/schema.yaml --biocypher-config {d}/biocypher_config.yaml --register {d}/path.py --debug --log-level DEBUG"
    logging.debug(f"Run: {cmd}")

    proc = subprocess.run(cmd.split(), capture_output=True)
    logging.error(proc.stderr.decode())
    assert proc.returncode == 0

    import_file = proc.stdout.decode()
    logging.debug(import_file)

    # assert os.path.isfile(import_file)
    # with open(import_file) as fd:
    #     assert fd.readlines()

    # dir = os.path.dirname(import_file)

    # for f in [
    #     # f"{dir}/inhibition.csv",
    #     f"{dir}/stimulation.csv",
    #     f"{dir}/transcript_to_gene_relationship.csv",
    #     f"{dir}/undirected_molecular_interaction.csv"
    # ]:
    #     assert os.path.isfile(f)
    #     with open(f) as fd:
    #         assert fd.readlines()

