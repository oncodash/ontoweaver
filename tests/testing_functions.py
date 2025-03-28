import os
import glob
import pandas as pd

def get_csv_files(directory):
    """Get all CSV files in the directory."""
    return glob.glob(os.path.join(directory, "*.csv"))

def compare_csv_files(expected_dir, output_dir):
    """Compare all CSV files between two directories."""
    expected_files = get_csv_files(expected_dir)
    output_files = get_csv_files(output_dir)

    assert len(expected_files) == len(output_files), "The number of CSV files does not match."

    for expected_file in expected_files:
        filename = os.path.basename(expected_file)
        output_file = os.path.join(output_dir, filename)
        assert os.path.exists(output_file), f"Output file {filename} does not exist."

        expected_df = pd.read_csv(expected_file, on_bad_lines='skip')
        output_df = pd.read_csv(output_file, on_bad_lines='skip')

        pd.testing.assert_frame_equal(output_df, expected_df)

def convert_to_set(tuple_output):
    """Convert the OntoWeaver tuple output to a set."""

    return set([
    tuple([
        node[0],
        node[1],
        tuple(sorted(node[2].items()))
    ]) if len(node) == 3 else tuple([
        node[0],
        node[1],
        node[2],
        node[3],
        tuple(sorted(node[4].items()))
    ]) for node in tuple_output
    ])
