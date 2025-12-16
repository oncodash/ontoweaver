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


class BaseOWLAdapter:

    def iri(self, subj):
        if "#" in str(subj):
            obj = str(subj).split('#')[-1]
            logger.debug(f"\t\tGuess label: {obj} from IRI {str(subj)}")
            return obj

        elif "/" in str(subj):
            obj = str(subj).split('/')[-1] # FIXME strong assumption
            logger.warning(f"I can't find the label of the element `{subj}'. Guess label: {obj}")
            return obj

        else:
            return subj


    def label_of(self, subj):
        # First, get the label, if any; else use the IRI end tag.
        triples = list(self.graph.triples((subj, RDFS.label, None)))
        # logger.debug(f"\tLabel triples: {triples}")
        if len(triples) == 0:
            obj = self.iri(subj)
        else:
            assert(len(triples[0]) == 3)
            obj = str(triples[0][2])
            logger.debug(f"\t\tUse label: {obj}")
        # return biocypher._misc.pascalcase_to_sentencecase(str(obj))
        return obj[0].lower() + obj[1:]
        # return obj


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



class BaseOWLAdapter:

    def iri(self, subj):
        if "#" in str(subj):
            obj = str(subj).split('#')[-1]
            logger.debug(f"\t\tGuess label: {obj} from IRI {str(subj)}")
            return obj

        elif "/" in str(subj):
            obj = str(subj).split('/')[-1] # FIXME strong assumption
            logger.warning(f"I can't find the label of the element `{subj}'. Guess label: {obj}")
            return obj

        else:
            return subj


    def label_of(self, subj):
        # First, get the label, if any; else use the IRI end tag.
        triples = list(self.graph.triples((subj, RDFS.label, None)))
        # logger.debug(f"\tLabel triples: {triples}")
        if len(triples) == 0:
            obj = self.iri(subj)
        else:
            assert(len(triples[0]) == 3)
            obj = str(triples[0][2])
            logger.debug(f"\t\tUse label: {obj}")
        # return biocypher._misc.pascalcase_to_sentencecase(str(obj))
        return obj[0].lower() + obj[1:]
        # return obj


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



class OWLAutoAdapter(BaseOWLAdapter, base.Adapter):
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

        if kwargs:
            logger.warning(f"OWLAutoAdapter does not support mappings, but you passed: {kwargs}, I'll ignore those arguments.")


    def run(self):
        def iri(subj):
            if "#" in str(subj):
                obj = str(subj).split('#')[-1] 
                logger.debug(f"\t\tGuess label: {obj} from IRI {str(subj)}")
                return obj

            elif "/" in str(subj):
                obj = str(subj).split('/')[-1] # FIXME strong assumption
                logger.warning(f"I can't find the label of the element `{subj}'. Guess label: {obj}")
                return obj

            else:
                return subj

        def label_of(subj):
            # First, get the label, if any; else use the IRI end tag.
            triples = list(self.graph.triples((subj, RDFS.label, None)))
            # logger.debug(f"\tLabel triples: {triples}")
            if len(triples) == 0:
                obj = iri(subj)
            else:
                assert(len(triples[0]) == 3)
                obj = str(triples[0][2])
                logger.debug(f"\t\tUse label: {obj}")
            # return biocypher._misc.pascalcase_to_sentencecase(str(obj))
            return obj[0].lower() + obj[1:]
            # return obj

        # Iterate over individuals.
        for i,indi_triple in enumerate(self.graph.triples((None,RDF.type,OWL.NamedIndividual))):
            local_nodes = []
            local_edges = []

            subj = indi_triple[0]
            logger.debug(f"{i}:({self.iri(subj)})")
            subj_label = self.label_of(subj)

            node_class = self.node_class(subj)
            logger.debug(f"Individual class: {node_class}")
            if not node_class:
                logger.warning(f"Individual `{subj}` has no owl:Class, I'll ignore it.")
                continue

            properties = {}
            # Gather everything about the subject individual.
            for _,rel,obj in self.graph.triples((subj, None, None)):
                logger.debug(f"\t-[{self.iri(rel)}]->({self.iri(obj)})")

                if obj == OWL.NamedIndividual:
                    logger.debug("\t\t= pass")
                    pass

                elif rel == RDF.type:
                    #e = base.GenericEdge(None, str(subj), str(obj), {}, str(rel))
                    e = base.GenericEdge(None, self.iri(subj), self.iri(obj), {}, self.label_of(rel))
                    logger.debug(f"\t\t= {e}")
                    local_edges.append(e)

                elif type(obj) == rdflib.URIRef:
                    e = base.GenericEdge(None, self.iri(subj), self.iri(obj), {}, self.label_of(rel))
                    logger.debug(f"\t\t= {e}")
                    local_edges.append(e)

                else:
                    logger.debug(f"\t\t= prop[{self.iri(rel)}] = {self.iri(obj)}")
                    properties[str(rel)] = str(obj)

            assert(node_class)
            n = base.Node(self.iri(subj), properties, self.label_of(node_class))
            logger.debug(f"\tnode: {n}")
            local_nodes.append(n)

            self.edges_append(local_edges)
            self.nodes_append(local_nodes)

            yield local_nodes, local_edges


class OWLAdapter(BaseOWLAdapter, iterative.IterativeAdapter):

    def __init__(self,
            graph: rdflib.Graph,
            subject_transformer: transformer.Transformer,
            transformers: Iterable[transformer.Transformer],
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


    def iterate(self):
        for i,triple in enumerate(self.graph.triples((None,RDF.type,OWL.NamedIndividual))):
            subj,t,ni = triple
            logger.debug(f"({self.iri(subj)})-[{self.iri(t)}]->({self.iri(ni)})")
            node_class = self.node_class(subj)
            logger.debug(f"\tIndividual class: ({node_class})-")
            if not node_class:
                logger.warning(f"Individual `{subj}` has no owl:Class, I'll ignore it.")
                continue

            row = {}
            # Gather everything about the subject individual.
            for _,rel,obj in self.graph.triples((subj, None, None)):
                logger.debug(f"\t-[{self.iri(rel)}]->({self.iri(obj)})")

                if obj == OWL.NamedIndividual:
                    logger.debug("\t\t= pass")
                    continue

                else:
                    t = self.label_of(rel)
                    o = self.label_of(obj)
                    logger.debug(f"\t\t=> {t} : {o}")
                    if t in row:
                        self.error(f"Multiple definitions for ({subj})--[{t}]->({o}), I don't know how to handle this.", section = "OWLAdapter", exception = exceptions.InputDataError)
                    else:
                        row[t] = o

            logger.debug(f"\t= {i}th individual:")
            for  k,v in row.items():
                logger.debug(f"\t\t{k}: {v}")

            yield i,row


