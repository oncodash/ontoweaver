#!/usr/bin/env python3

'''
Pre-processing of ontologies in order to be compatible with the requirements of Biocypher.

python3 -m preprocess_ontology <ontology_to_be_transformed>[.owl] > <new_ontology>
>> creates 
    - a new Biocypher compatible ontology, in <ontology_directory> named bc_<ontology_to_be_transformed>.owl
    - a 'bc_classes_mapping.json' file containing the mapping 
        between classes from <ontology_to_be_transformed>.owl and classes from bc_<ontology_to_be_transformed>.owl

Each element of bc_classes_mapping.json file is a json input with the folloging information:

<initial_classe_IRI in ontology>: {
    "labels": [
        <list of the labels in the initial ontology>
        ],
    "bc_label": "<label in bc_ontology>"
}


'''
import os
import re
import sys
import owlready2 as owl
import types
import json
import copy
import io
import rdflib
import logging

from itertools import chain

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL

logger = logging.getLogger("owl_to_biocypher")


chars_to_be_removed = [' ', "%", "-"]


def remove_characters(s, list_c):
    for c in list_c:
        s = s.replace(c, "")
    return s


def replace_underscore(s):
    p = s.find("_")
    while p>=0:
        c = s[p+1]
        s2 = s[:p]+c.upper()
        if len(s)>=p+1:
            s2=s2+s[p+2:]
        s = s2
        p = s.find("_")
    return s


def get_label_from_iri(iri):
    if iri.rfind("#")>0:
        return iri[iri.rfind("#")+1:]
    elif iri.rfind("/")>0:
        return iri[iri.rfind("/")+1:]
    else:
        return iri


def translate_labels(ontology_file, json_f=None, output_format="rdfxml"):
    ontology_path = os.path.abspath(ontology_file)
    iri_path = "".join(['file://', ontology_path])
    onto = owl.get_ontology(iri_path).load()

    translation_dict = {}

    with onto:
        thing_label = owl.Thing.label
        #print("\nThing label =", thing_label, type(thing_label))
        if not thing_label:
            thing_label = ["Thing"]
            owl.Thing.label = thing_label
        #print("Thing new label =", owl.Thing.label)

        for c in chain(onto.classes(), onto.object_properties()):
            # print(c, file=sys.stderr)
            # print(dir(c), file=sys.stderr)
            old_labels = c.label

            # labels = [l for l in c.label]
            # for l in labels:
            #     new_label = remove_characters(l, chars_to_be_removed)#.lower()
            #     new_label = replace_underscore(new_label)
            #     new_label = new_label.capitalize()
            #     c.label.append(new_label)

            # new_name = remove_characters(c.iri, chars_to_be_removed)
            # new_name = replace_underscore(new_name)
            # new_name = new_name.capitalize()
            if len(c.label)>0:
                new_label = c.label[0]
            else:
                new_label = get_label_from_iri(c.iri)#.lower()
            new_label = remove_characters(new_label, chars_to_be_removed)#.lower()
            new_label = replace_underscore(new_label)
            new_label = new_label[0].lower()+new_label[1:]
            c.label = []
            c.label.append(new_label)

            labels = c.label

            # If there is no obvious translation.
            if len(old_labels) == 0:
                logger.debug(f"There was no label for {new_label}, I will add it to the ontology, but not to the restoration for {c.iri}.")
            elif len(old_labels) == 1 and old_labels[0] == new_label:
                logger.debug(f"Label {new_label} is already compatible, I will not put it in the restoration for {c.iri}.")
            else:
                logger.info(f"Replace original {old_labels} by BioCypherized {new_label} for {c.iri}")
                # Save the translation.
                translation_dict[c.iri] = {
                    #"origin_class": c.iri,
                    "origin_labels": old_labels,
                    #"biocypher_class": new_name,
                    "biocypher_label": new_label
                }
            # parents = c.is_a
            # if parents == [owl.Thing]:
            #     with onto:
            #         bc_root_class = types.new_class("BcRootClass", (owl.Thing,))
            #         bc_root_class.label.append("BcRootClass")
            #         c.is_a = [bc_root_class]
            #print(c)

    if json_f:
        if len(translation_dict) == 0:
            logger.warning("There was no label translation to do on the input ontology, the restoration file will be a an empty mapping. But you still need to restore the ontology to remove the BioCypherRoot.")
        with open(json_f, 'w') as fp:
            json.dump(translation_dict, fp, indent=4)

    # Save ontology file in a buffer.
    by_io = io.BytesIO()
    onto.save(by_io, output_format)
    by_str = by_io.getvalue()
    text = by_str.decode("UTF-8")
    return text


def harden_labels(text):
    # Replace "<label…</label>" by "<rdfs:label</rdfs:label>"
    # Because Biocypher needs rdfs:label, or else it does not found any class.
    # Because OwlReady2 does not allow label with prefixes,
    # we rely on regexp substitution.
    text = re.sub(r"<label", "<rdfs:label", text)
    text = re.sub(r"</label>", "</rdfs:label>", text)

    return text


def add_root(owl_txt, input_format, root_name = "BioCypherRoot"):
    # Separated function, because it's using rdflib instead of owlredy2,
    # because it's actually easier to manipulate low-level stuff.

    if input_format == "rdfxml":
        input_format = "xml"

    rdf_io = io.StringIO(owl_txt)
    g = rdflib.Graph()
    g.parse(rdf_io, format = input_format)

    bcns = Namespace("https://biocypher.org/biocypher#")
    g.bind("biocypher", bcns)

    namespaces = {}
    for key,ns in g.namespaces():
        namespaces[key] = Namespace(ns)

    # Add a BioCypherRoot on top of owl:Thing and owl:topObjectProperty
    uri_root = URIRef(namespaces["biocypher"][root_name])
    g.add( (
            uri_root,
            RDFS.label,
            Literal(root_name)
        ) )

    g.add( (
            OWL.Thing,
            RDFS.subClassOf,
            uri_root,
        ) )

    g.add( (
            OWL.topObjectProperty,
            RDFS.subPropertyOf,
            uri_root,
        ) )

    # Add owl:topObjectProperty as an ancestor of all owl:ObjectProperty in the default namespace
    g.add( (
            OWL.topObjectProperty,
            RDFS.label,
            Literal("topObjectProperty")
        ) )

    # For all ObjectProperty
    for s,p,o in g.triples((None, RDF.type, OWL.ObjectProperty)):
        # If not already inheriting from something.
        if (s,RDFS.subPropertyOf,None) not in g:
            # Makes it inheriting from topObjectProperty
            g.add( (
                    s,
                    RDFS.subPropertyOf,
                    OWL.topObjectProperty,
                ) )

    # Make Entity a Thing
    g.add( (
            URIRef(namespaces[""]["Entity"]),
            RDFS.subClassOf,
            OWL.Thing
        ) )

    return g


def harden_owl(ontology_file, json_f, output_format = "rdfxml"):
    # rdfxml (owlready2) / xml (rdflib) is our pivot format
    # to pass from one lib to the other.
    owl_txt = translate_labels(ontology_file, json_f, output_format)
    owl_txt = harden_labels(owl_txt)
    graph = add_root(owl_txt, input_format = "xml")
    return graph


if __name__ == "__main__":
    import sys
    import argparse
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

    logging.basicConfig()
    logger.setLevel(asked.log_level)

    rdf_graph = harden_owl(asked.ontology_file, json_f = asked.json, output_format = "rdfxml")

    sys.stdout.write(rdf_graph.serialize(format = asked.output_format))
