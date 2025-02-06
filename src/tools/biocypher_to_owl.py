#!/usr/bin/env python3

import re
import json

import rdflib
from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL

import logging
logger = logging.getLogger("biocypher_to_owl")

def restore_owl(graph, restoration, remove_affix = "none", affix_sep = ":"):
    logger.debug("Restore labels...")
    for uri,p,label in graph.triples((None, RDFS.label, None)):

        if remove_affix != "none":
            if remove_affix == "prefix":
                matched = re.search(r"\w+:(.*)", str(label))
                if matched:
                    assert len(matched.groups()) == 1
                    clean_label = matched.groups()[0]
            elif remove_affix == "suffix":
                matched = re.search(r"(.*):\w+", str(label))
                if matched:
                    assert len(matched.groups()) == 1
                    clean_label = matched.groups()[0]

            if matched:
                logger.debug(f"Remove {remove_affix} from: {label} to {clean_label}")

                graph.remove((
                    uri,
                    p,
                    label
                ))

                graph.add((
                    uri,
                    p,
                    Literal(clean_label)
                ))

        iri = str(uri)
        if iri in restoration:
            logger.info(f"Remove {restoration[iri]['biocypher_label']} label from {iri}")
            graph.remove((
                uri,
                RDFS.label,
                rdflib.Literal(restoration[iri]["biocypher_label"])
            ))
            for label in restoration[iri]["origin_labels"]:
                logger.info(f"Add {label} label to {iri}")
                graph.add((
                    uri,
                    rdflib.namespaces.RDFS.label,
                    rdflib.Literal(label)
                ))

    logger.debug("Remove the BioCypherRoot...")
    bcns = Namespace("https://biocypher.org/biocypher#")
    graph.bind("biocypher", bcns)
    namespaces = {}
    for key,ns in graph.namespaces():
        namespaces[key] = Namespace(ns)

    root_name = "BioCypherRoot"
    uri_root = URIRef(namespaces["biocypher"][root_name])
    logger.info(f"Remove {root_name} label from {uri_root}")
    graph.remove( (
            uri_root,
            RDFS.label,
            Literal(root_name)
        ) )

    logger.info(f"Remove {uri_root} as a superclass of Thing")
    graph.remove( (
            OWL.Thing,
            RDFS.subClassOf,
            uri_root,
        ) )

    logger.info(f"Remove {uri_root} as a superproperty of topObjectProperty")
    graph.remove( (
            OWL.topObjectProperty,
            RDFS.subPropertyOf,
            uri_root,
        ) )

    return graph

if __name__ == "__main__":
    import os
    import sys
    import argparse
    appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    do = argparse.ArgumentParser(
        description="Post-process an BioCypherized ontology to restore its original labels.",
        epilog=f"Example usage: {appname} my-biocypherized-onto.owl my-restoration.json > my-restored-onto.owl")

    do.add_argument("ontology")
    do.add_argument("restoration")

    rdflib_formats = ["xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext"]
    owlready_formats = ["rdfxml","ntriples"]
    do.add_argument("-f", "--output-format",
        help="the format in which to write the ontology (default: turtle)",
        choices=rdflib_formats, default="turtle", metavar="OUT_FORMAT")

    do.add_argument("-F", "--input-format",
        help="the format from which to read the ontology (default: turtle)",
        choices=rdflib_formats, default="turtle", metavar="IN_FORMAT")

    do.add_argument("-l", "--log-level", default="WARNING",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Configure the log level. [default: WARNING]")

    do.add_argument("-a", "--type-affix", choices=["suffix","prefix","none"], default="none",
        help="Where to add the type string to the ID label.")

    do.add_argument("-A", "--type-affix-sep", metavar="CHARACTER", default=":",
        help="Character used to separate the label from the type affix.")

    asked = do.parse_args()

    logging.basicConfig()
    logger.setLevel(asked.log_level)

    logger.debug("Load JSON restoration...")
    with open(asked.restoration) as fd:
        restoration = json.load(fd)

    logger.debug("Load Ontology...")
    graph = rdflib.Graph()

    try:
        graph.parse(source = asked.ontology)
    except:
        graph.parse(source = asked.ontology, format = asked.input_format)

    logger.debug("Restore...")
    restored = restore_owl(graph, restoration, asked.type_affix, asked.type_affix_sep)

    sys.stdout.write(restored.serialize(format = asked.output_format))
