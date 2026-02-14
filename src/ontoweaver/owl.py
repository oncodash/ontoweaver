import rdflib
import logging

from rdflib import RDF, RDFS, OWL

from collections.abc import Iterable
from typing import Optional

from . import base
from . import iterative
from . import validate
from . import transformer

logger = logging.getLogger("ontoweaver")


class OWLtools:
    def __init__(self, graph):
        self.graph = graph
        self.seen_labels = {}

    def iri(self, subj):
        if "#" in str(subj):
            obj = str(subj).split('#')[-1]
            return obj

        elif "/" in str(subj):
            obj = str(subj).split('/')[-1] # FIXME strong assumption
            return obj

        else:
            return subj


    def label_of(self, subj):
        # First, get the label, if any; else use the IRI end tag.
        triples = list(self.graph.triples((subj, RDFS.label, None)))
        # logger.debug(f"\tLabel triples: {triples}")
        if subj in self.seen_labels:
            logger.debug(f"Label of `{subj}` already seen: `{self.seen_labels[subj]}`")
            return self.seen_labels[subj]

        elif len(triples) == 0:
            obj = self.iri(subj)
            logger.warning(f"I can't find the label of the element `{subj}'. Label guessed from IRI: {obj}")
            self.seen_labels[subj] = obj

        else:
            if len(triples) > 1:
                logger.warning(f"There is {len(triples)} elements with label `{subj}`: {';'.join(triples)}, I'll take the first one: `{triples[0]}`.")
            assert(len(triples[0]) == 3)
            obj = str(triples[0][2])
            logger.debug(f"\t\tUse label: {obj}")
            self.seen_labels[subj] = obj
        # return biocypher._misc.pascalcase_to_sentencecase(str(obj))
        return obj[0].lower() + obj[1:]


    def node_class(self, subj):
        node_class = None
        for s,p,o in self.graph.triples((subj, RDF.type, None)):
            # logger.debug(f"({self.iri(s)})-[{self.iri(p)}]->({self.iri(o)})")
            # logger.debug(f"Individual type: {node_class}")

            if o == OWL.NamedIndividual:
                continue

            if node_class:
                raise RuntimeError(
                    f"Instantiating from multiple classes is not supported, "
                    f"fix individual `{subj}`, it should not instantiate both "
                    f"`{node_class}` and `{o}`")

            if rdflib.URIRef(o) != OWL.NamedIndividual:
                node_class = o

        return node_class


class OWLAutoAdapter(base.Adapter):
    def __init__(self,
                 graph: rdflib.Graph,
                 raise_errors = True,
                 **kwargs
                 ):

        super().__init__(
            raise_errors
        )
        self.graph = graph
        logger.debug(f"OWLAutoAdapter on {len(self.graph)} input RDF triples.")

        self.get = OWLtools(self.graph)

        if kwargs:
            logger.warning(f"OWLAutoAdapter does not support mappings, but you passed: {kwargs}, I'll ignore those arguments.")


    def run(self):
        # Iterate over individuals.
        for i,indi_triple in enumerate(self.graph.triples((None,RDF.type,OWL.NamedIndividual))):
            local_nodes = []
            local_edges = []

            subj = indi_triple[0]
            logger.debug(f"{i}:({self.get.iri(subj)})")
            subj_label = self.get.label_of(subj)

            node_class = self.get.node_class(subj)
            logger.debug(f"Individual class: {node_class}")
            if not node_class:
                logger.warning(f"Individual `{subj}` has no owl:Class, I'll ignore it.")
                continue

            properties = {}
            # Gather everything about the subject individual.
            for _,rel,obj in self.graph.triples((subj, None, None)):
                logger.debug(f"\t-[{self.get.iri(rel)}]->({self.get.iri(obj)})")

                if    obj == OWL.NamedIndividual \
                  or subj == OWL.NamedIndividual \
                  or subj_label == "NamedIndividual" \
                  or  rel == RDF.type \
                  or self.get.label_of(rel) == "type":
                    logger.debug("\t\t= pass")
                    # We don't need types, they will be set by BioCypher from labels.
                    pass

                elif type(obj) == rdflib.URIRef:
                    e = base.GenericEdge(None, self.get.iri(subj), self.get.iri(obj), {}, self.get.label_of(rel))
                    logger.debug(f"\t\t= {e}")
                    local_edges.append(e)

                else:
                    logger.debug(f"\t\t= prop[{self.get.iri(rel)}] = {self.get.iri(obj)}")
                    properties[str(rel)] = str(obj)

            assert(node_class)
            n = base.Node(self.get.iri(subj), properties, self.get.label_of(node_class))
            logger.debug(f"\tnode: {n}")
            local_nodes.append(n)

            self.edges_append(local_edges)
            self.nodes_append(local_nodes)

            yield local_nodes, local_edges


class OWLAdapter(iterative.IterativeAdapter):

    def __init__(self,
            graph: rdflib.Graph,
            subject_transformer: base.Transformer,
            transformers: Iterable[base.Transformer],
            metadata: Optional[dict] = None,
            validator: Optional[validate.InputValidator] = None,
            type_affix: Optional[base.TypeAffixes] = base.TypeAffixes.suffix,
            type_affix_sep: Optional[str] = ":",
            parallel_mapping: int = 0,
            raise_errors = True
        ):

        super().__init__(
           subject_transformer,
           transformers,
           metadata,
           validator,
           type_affix,
           type_affix_sep,
           parallel_mapping,
           raise_errors
        )
        self.graph = graph
        logger.debug(f"OWLAdapter on {len(self.graph)} input RDF triples.")

        self.get = OWLtools(self.graph)


    def iterate(self):
        for i,triple in enumerate(self.graph.triples((None,RDF.type,OWL.NamedIndividual))):
            subj,t,ni = triple
            logger.debug(f"({self.get.iri(subj)})-[{self.get.iri(t)}]->({self.get.iri(ni)})")
            node_class = self.get.node_class(subj)
            logger.debug(f"\tIndividual class: ({node_class})-")
            if not node_class:
                logger.warning(f"Individual `{subj}` has no owl:Class, I'll ignore it.")
                continue

            row = {}
            # Gather everything about the subject individual.
            for _,rel,obj in self.graph.triples((subj, None, None)):
                logger.debug(f"\t-[{self.get.iri(rel)}]->({self.get.iri(obj)})")

                if obj == OWL.NamedIndividual:
                    logger.debug("\t\t= pass")

                else:
                    t = self.get.label_of(rel)
                    o = self.get.label_of(obj)
                    logger.debug(f"\t\t=> {t} : {o}")
                    if t in row:
                        self.error(f"Multiple definitions for ({subj})--[{t}]->({o}), I don't know how to handle this.", section = "OWLAdapter", exception = exceptions.InputDataError)
                    else:
                        row[t] = o

            logger.debug(f"\t= {i}th individual:")
            for  k,v in row.items():
                logger.debug(f"\t\t{k}: {v}")

            yield i,row


