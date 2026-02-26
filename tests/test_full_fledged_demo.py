import re
import os
import sys
import logging
import pathlib
import subprocess

def extract_code_from_doc(docfile, demofile, prefix):
    with open(docfile) as fd:
        text = fd.readlines()

    section = []
    i = 0
    while i < len(text):
        line = text[i]
        # print(line, end="")
        if not re.match(r"^\s{4}:caption:\s" + prefix + demofile + r"$", line):
            i += 1
            continue
        else:
            logging.debug(f"\tFound: {line.strip()}")
            line = "    "
            i += 1
            while line != "":
                has_code = re.search(r"^\s{4}(.+)$", line)
                if has_code:
                    code = has_code.group(1)
                    section.append(code)
                    line = text[i]
                    i += 1
                elif re.match(r"\s{4}$", line):
                    line = text[i]
                    i += 1
                    continue
                else:
                    break
            break

    return "\n".join(section)


def doc_to_file(docfile, demofile, dir, prefix):
    outfile = pathlib.Path(dir) / pathlib.Path(demofile)
    logging.debug(f"Parsing {docfile} for {prefix}{demofile}")
    content = extract_code_from_doc(docfile, demofile, prefix)
    assert content, "Unable to extract a file content."
    logging.debug(f"\tWriting extracted code to: {outfile}")
    with open(outfile, 'w') as fd:
        fd.write(content)


def test_full_fledged_demo():
    tutorials = "docs/sections/tutorials.rst"
    dir = "tests/full_fledge_demo"
    prefix = "demo_"
    logging.warning("This test extracts the code (mapping, ontology, etc.) from the documentation")
    logging.warning("If you want to fix some bug, DO NOT FIX THE FILES in test/, but instead, fix the documentation in `tutorial.rst`.")
    doc_to_file(tutorials, "data.csv"    , dir, prefix)
    doc_to_file(tutorials, "ontology.ttl", dir, prefix)
    doc_to_file(tutorials, "config.yaml" , dir, prefix)
    doc_to_file(tutorials, "mapping.yaml", dir, prefix)
    doc_to_file(tutorials, "schema.yaml" , dir, prefix)

    xs = f"{dir}/extended_schema.yaml"
    if os.path.isfile(xs):
        os.remove(xs)

    cmd = f"ontoweave --biocypher-config {dir}/config.yaml --auto-schema {xs} --biocypher-schema {dir}/schema.yaml {dir}/data.csv:{dir}/mapping.yaml --auto-schema-overwrite --debug"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


def test_simplest_example():
    tutorials = "docs/sections/tutorials.rst"
    dir = "tests/simplest_example"
    prefix = "simple_"
    doc_to_file(tutorials, "data.csv"    , dir, prefix)
    doc_to_file(tutorials, "ontology.ttl", dir, prefix)
    doc_to_file(tutorials, "config.yaml" , dir, prefix)
    doc_to_file(tutorials, "mapping.yaml", dir, prefix)

    xs = f"{dir}/extended_schema.yaml"
    if os.path.isfile(xs):
        os.remove(xs)

    cmd = f"ontoweave --biocypher-config {dir}/config.yaml --auto-schema {xs} {dir}/data.csv:{dir}/mapping.yaml --auto-schema-overwrite --debug"

    logging.debug(f"Run: {cmd}")
    subprocess.run(cmd.split(), capture_output=True, check=True)


if __name__ == "__main__":
    test_full_fledged_demo()
    test_simplest_example()
