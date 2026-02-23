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

    out = set()
    for elem in tuple_output:
        id = elem[0]
        type = elem[1]
        if len(elem) == 3: # Nodes
            sp = {}
            for k,v in elem[2].items():
                if isinstance(v, list):
                    sp[k] = ",".join(v)
                else:
                    sp[k] = v
            props = tuple(sorted(sp.items()))
            out.add(tuple([id, type, props]))

        elif len(elem) == 4: # Edges
            source = elem[2]
            target = elem[3]
            props = tuple(sorted(elem[4].items()))
            out.add(tuple([id, type, source, target, props]))

    return out


def assert_equals(given, expected):
    given_set = convert_to_set(given)
    expected_set = convert_to_set(expected)
    assert len(expected_set) == len(given_set)
    for elem in given_set:
        assert elem in expected_set, f"Element {elem} should exists."

