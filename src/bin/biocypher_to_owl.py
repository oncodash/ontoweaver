import os
import sys
import rdflib
import logging
import argparse
import ontoweaver

def main():
    appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    do = argparse.ArgumentParser(
        description="Post-process an BioCypherized ontology to restore its original labels.",
        epilog=f"Example usage: {appname} my-biocypherized-onto.owl my-restoration.json > my-restored-onto.owl")

    do.add_argument("ontology")
    do.add_argument("restoration")

    rdflib_formats = ["xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext"]
    # owlready_formats = ["rdfxml","ntriples"]

    do.add_argument("-f", "--output-format", default="turtle",
        choices=rdflib_formats, metavar="OUT_FORMAT",
        help="the format in which to write the ontology (default: turtle)")

    do.add_argument("-F", "--input-format", default="turtle",
        choices=rdflib_formats, metavar="IN_FORMAT",
        help="the format from which to read the ontology (default: turtle)")

    do.add_argument("-l", "--log-level", default="WARNING",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Configure the log level. [default: WARNING]")

    do.add_argument("-a", "--type-affix", default=default.remove_affix,
        choices=["suffix","prefix","none"],
        help="Where to add the type string to the ID label.")

    do.add_argument("-A", "--type-affix-sep", default=default.affix_sep,
        metavar="CHARACTER",
        help="Character used to separate the label from the type affix.")

    asked = do.parse_args()

    logging.basicConfig(level = asked.log_level)

    logging.debug("Load JSON restoration...")
    with open(asked.restoration) as fd:
        restoration = json.load(fd)

    logging.debug("Load Ontology...")
    graph = rdflib.Graph()

    try:
        graph.parse(source = asked.ontology)
    except Exception as e:
        logging.warning("RDFlib failed to guess the ontology format:\n" \
                       f"`{e}`\n" \
                       f"I'm trying again with format set to: {asked.input_format}")
        graph.parse(source = asked.ontology, format = asked.input_format)

    logging.debug("Restore...")
    restored = ontoweaver.biocypher_to_owl.restore_owl(graph, restoration, asked.type_affix, asked.type_affix_sep)

    sys.stdout.write(restored.serialize(format = asked.output_format))


if __name__ == "__main__":
    main()

