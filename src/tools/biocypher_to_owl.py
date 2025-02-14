#!/usr/bin/env python3

import re
import json

import rdflib
from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL
from urllib.parse import quote_plus as url_quote

import logging
logger = logging.getLogger("biocypher_to_owl")


class default:
    root_name = "BioCypherRoot"
    remove_affix = "none"
    affix_sep = ":"


def clean_affix_uri(name, remove_affix = default.remove_affix, affix_sep = default.affix_sep):
    affix_sep = url_quote(affix_sep)

    if remove_affix != default.remove_affix:
        if remove_affix == "prefix":
            matched = re.search(r"(.+)#\w+" +affix_sep+ r"([\w%]*)$", name)
            if matched:
                assert len(matched.groups()) == 2
                clean = matched.groups()[0] + matched.groups()[1]
        elif remove_affix == "suffix":
            matched = re.search(r"(.+#[\w%]*)" +affix_sep+ r"\w+$", name)
            if matched:
                assert len(matched.groups()) == 1
                clean = matched.groups()[0]
    if matched:
        return clean
    else:
        return None


def clean_affix_literal(name, remove_affix = default.remove_affix, affix_sep = default.affix_sep):
    if remove_affix != default.remove_affix:
        if remove_affix == "prefix":
            matched = re.search(r"^\w+" +affix_sep+ r"([\w%]*)$", name)
            if matched:
                assert len(matched.groups()) == 1
                clean = matched.groups()[0]
        elif remove_affix == "suffix":
            matched = re.search(r"^([\w%]*)" +affix_sep+ r"\w+$", name)
            if matched:
                assert len(matched.groups()) == 1
                clean = matched.groups()[0]
    if matched:
        return clean
    else:
        return None


def remove_labels_affixes(graph, remove_affix, affix_sep = default.affix_sep):
    logger.debug(f"Remove {remove_affix} in labels")
    for uri,p,label in graph.triples((None, RDFS.label, None)):

        if remove_affix != default.remove_affix:
            clean_label = clean_affix_literal(label, remove_affix, affix_sep)

            if clean_label:
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
            else:
                logger.debug(f"Label {label} does not need cleaning.")


def remove_affixes_subjects(graph, remove_affix, affix_sep = default.affix_sep):
    logging.debug(f"Remove {remove_affix} from IRIs in subjects")
    if remove_affix != default.remove_affix:
        for uri,p,obj in graph.triples((None, None, None)):
            clean_uri = clean_affix_uri(uri, remove_affix, affix_sep)
            if clean_uri:
                logger.debug(f"Remove subject {remove_affix} from: {uri} to {clean_uri}")

                graph.remove((
                    uri,
                    p,
                    obj
                ))

                graph.add((
                    URIRef(clean_uri),
                    p,
                    obj
                ))
            else:
                logger.debug(f"Subject {uri} does not need cleaning.")


def remove_affixes_objects(graph, remove_affix, affix_sep = default.affix_sep):
    logging.debug(f"Remove {remove_affix} from IRIs in objects")
    if remove_affix != default.remove_affix:
        for uri,p,obj in graph.triples((None, None, None)):
            clean_obj = clean_affix_uri(obj, remove_affix, affix_sep)
            if clean_obj:
                logger.debug(f"Remove object {remove_affix} from: {obj} to {clean_obj}")

                graph.remove((
                    uri,
                    p,
                    obj
                ))

                graph.add((
                    uri,
                    p,
                    URIRef(clean_obj)
                ))
            else:
                logger.debug(f"Object {obj} does not need cleaning.")


def restore_labels(graph, restoration):
    logging.debug(f"Translate biocypherized labels back")
    for uri,p,label in graph.triples((None, RDFS.label, None)):
        iri = str(uri)
        if iri in restoration:
            logger.info(f"\tRemove {restoration[iri]['biocypher_label']} label from {iri}")
            graph.remove((
                uri,
                RDFS.label,
                rdflib.Literal(restoration[iri]["biocypher_label"])
            ))
            for label in restoration[iri]["origin_labels"]:
                logger.info(f"\tAdd {label} label to {iri}")
                graph.add((
                    uri,
                    rdflib.namespaces.RDFS.label,
                    rdflib.Literal(label)
                ))


def remove_root(graph, root_name = default.root_name):
    logger.debug("Remove the BioCypher root...")
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



def restore_owl(graph, restoration, remove_affix = default.remove_affix, affix_sep = default.affix_sep, root_name = default.root_name):
    remove_labels_affixes(graph, remove_affix, affix_sep)
    remove_affixes_subjects(graph, remove_affix, affix_sep)
    remove_affixes_objects(graph, remove_affix, affix_sep)
    restore_labels(graph, restoration)
    remove_root(graph, root_name)
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
