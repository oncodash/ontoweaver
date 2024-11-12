import yaml
import logging
import shutil
import pandas as pd
import biocypher

import ontoweaver
from . import testing_functions

def test_extract_reconciliate_write():

    dir = "tests/simplest/"

    import_file = ontoweaver.extract_reconciliate_write(
        dir+"/biocypher_config.yaml",
        dir+"/schema_config.yaml",
        {
            dir+"data.csv": dir+"mapping.yaml"
        }
    )

    assert(import_file)

    # output_dir = testing_functions.get_latest_directory("biocypher-out")
    # assert_output_path = dir + "/assert_output"
    # testing_functions.compare_csv_files(assert_output_path, output_dir)
    # shutil.rmtree(output_dir)

if __name__ == "__main__":
    test_extract_reconciliate_write()

