#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#    "biocypher<1.0.0,>=0.11.0",
#    "pooch<2.0.0,>=1.7.0",
#    "pandas<3.0.0,>=2.3.1",
#    "numpy<3.0.0,>=2.2.4",
#    "owlready2<1.0,>=0.49",
#    "jsonargparse<5.0,>=4.39",
#    "xdg-base-dirs<7.0.0,>=6.0.2",
#    "pandera[io]<1.0.0,>=0.27.0",
#    "alive-progress<4.0,>=3.2",
#    "fsspec<2026.0.0,>=2025.10.0",
#    "natsort>5.0.0",
#    "lxml>6.0.0",
#    "jmespath>=1.0.1",
# ]
# ///

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
    logger.debug(f"Remove {remove_affix} from IRIs in subjects")
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
    logger.debug(f"Remove {remove_affix} from IRIs in objects")
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
    logger.debug("Translate biocypherized labels back")
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

