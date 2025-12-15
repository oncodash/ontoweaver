import logging
import subprocess
import os

def test_validate_input():
    logging.basicConfig(level=logging.DEBUG)

    logging.debug(f"From: {os.getcwd()}")
    cmd = "poetry run ontoweave ./tests/validate_input/data.csv:./tests/validate_input/mapping.yaml --validate-only"

    logging.debug(f"Run: {cmd}")

    result = subprocess.run(cmd.split(), capture_output=True, text=True, check=False)

    # Check if the return code is 76 - indicating the validation has detected an error. This is the expected behavior,
    # so test passes in this case.
    if result.returncode == 76:
        logging.info("Test passed: Command returned the expected exit code 76.")
    else:
        raise Exception(f"Test failed: Expected exit code 76 but got {result.returncode}.")

if __name__ == "__main__":
    test_validate_input()
