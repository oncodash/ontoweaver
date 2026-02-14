import io
import yaml
import rdflib
import logging
import ontoweaver

def test_owladapter():
    ttl = """
@prefix : <http://fake.onto#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:thing a owl:Class ;
        rdfs:label "thing" .

:source a owl:Class ;
        rdfs:subClassOf :thing ;
        rdfs:label "source" .

:target a owl:Class ;
        rdfs:subClassOf :thing ;
        rdfs:label "target" .

owl:ObjectProperty rdfs:subClassOf owl:thing .

:link a owl:ObjectProperty ;
        rdfs:subClassOf :thing ;
        rdfs:label "link" .

:prop a owl:DataProperty ;
        rdfs:subClassOf :thing ;
        rdfs:label "prop" .

:S0 a :source ;
        a owl:NamedIndividual ;
        rdfs:label "S0" ;
        :link :T0 .

:T0 a :target ;
        a owl:NamedIndividual ;
        rdfs:label "T0" ;
        :prop "data property" .
    """

    rdf_io = io.StringIO(ttl)
    g = rdflib.Graph()
    g.parse(rdf_io, format = "turtle")

    mapping = """
subject:
    map:
        id_from_element: label
        match_type_from_element: type
        match:
            - source:
                to_subject: source
            - target:
                to_subject: target
transformers:
    - map:
        element: link
        to_object: target
        via_relation: link
    - map:
        element: prop
        to_property: prop
metadata:
    - source: "Test"
    """
    config = yaml.full_load(mapping)

    lrg = ontoweaver.loader.LoadOWLGraph()
    local_nodes,local_edges = ontoweaver.load_extract(g, config, lrg, raise_errors = False)

    logging.debug("Nodes:")
    for n in local_nodes:
        logging.debug(repr(n))

    logging.debug("Edges:")
    for e in local_edges:
        logging.debug(repr(e))

    bc_nodes = [n.as_tuple() for n in local_nodes]
    bc_edges = [e.as_tuple() for e in local_edges]

    fnodes, fedges = ontoweaver.fusion.reconciliate(bc_nodes, bc_edges, reconciliate_sep=";")

    logging.debug("Nodes:")
    for n in fnodes:
        logging.debug(repr(n))

    logging.debug("Edges:")
    for e in fedges:
        logging.debug(repr(e))

    assert len(fnodes) == 2
    assert len(fedges) == 1

if __name__ == "__main__":
    test_owladapter()
