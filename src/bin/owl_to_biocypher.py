import os
import sys
import logging
import argparse
import ontoweaver

def main():
    appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    p = argparse.ArgumentParser(
        description="Pre-process (i.e. downgrade) an OWL ontology to make it compatible with the (harsh) requirements of BioCypher.",
        epilog=f"Example usage: {appname} my-onto.owl --json my-restoration-.json > my-biocypherized-onto.owl")

    p.add_argument("ontology_file")

    p.add_argument("-j", "--json",
        help="a JSON file in which to save the computed mapping, for further reference or reconstruction (default: None)",
        metavar="JSON_FILE", default=None)

    rdflib_formats = ["xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext"]
    owlready_formats = ["rdfxml","ntriples"]
    p.add_argument("-f", "--output-format",
        help="the format in which to write the ontology (default: turtle)",
        choices=rdflib_formats, default="turtle", metavar="FORMAT")

    p.add_argument("-l", "--log-level", default="WARNING",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Configure the log level. [default: WARNING]")

    asked = p.parse_args()

    logging.basicConfig(level = asked.log_level)

    rdf_graph = ontoweaver.owl_to_biocypher.harden_owl(asked.ontology_file, json_f = asked.json, output_format = "rdfxml")

    sys.stdout.write(rdf_graph.serialize(format = asked.output_format))


if __name__ == "__main__":
    main()


