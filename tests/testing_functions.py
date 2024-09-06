import os
import glob
import pandas as pd
import time
def get_latest_directory(parent_dir):
    """Get the latest directory in the given parent directory."""
    all_dirs = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) if
                os.path.isdir(os.path.join(parent_dir, d))]
    latest_dir = max(all_dirs, key=os.path.getmtime)
    return latest_dir

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
