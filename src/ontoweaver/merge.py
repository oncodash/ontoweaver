from abc import ABCMeta, abstractmethod
import logging
import copy
from collections import OrderedDict

import networkx as nx;
import rdflib
from rdflib.extras.external_graph_libs import rdflib_to_networkx_digraph

from . import base

logger = logging.getLogger("ontoweaver")

class Merger(metaclass=ABCMeta):
    """Interface for classes merging two member variable of Elements.

    The contract is to take two variables of the same type,
    taken from duplicated base.Elements,
    along with the serialized key used to detect that they are duplicated,
    and decide how to merge them in a single variable.

    This interface fits the requirements of a functor used in a "reduce" functions,
    that will process a list of duplicates by iterating over pairs of candidate elements.
    It is nonetheless compatible with use-casess where a Merger would need to know
    the whole list of duplicates before deciding how to merge them,
    hence the slightly complicated interface.

    The main rationale is that at least the `merge` function is implemented by the inheriting class,
    and decide what parts of the given key, left-hand-side or right-hand-side object is taken into account.
    Indicating what is taken into account is done through the `set` function,
    which stores whatever is of interest in the `self.merged` member variable.

    Passed objects can be of any type in this interface (usually either base.Element subclass
    or regular member variable types, usually a string).

    The merging step actually take place when the `get` function is called,
    after having processed all the duplicates list.

    Since this type of functors may be called at each step of a loop iterating
    over the keys of a duplicates dictionary (see `congregater.Congregater`),
    they need to be reseted after having processed a duplicates list.
    This is done by calling the `reset` function, which should reset the `self.merged` member.

    The default implementation provided by the interface is that `set` stores whatever is passed to it,
    and `get` returns it (hence returning the value stored at the last call of `set`).

    See the `string.UseKey` class for an example of minimal implementation.
    """

    def __call__(self, key, lhs, rhs):
        """The actuall call interface, this only calls `precheck`, then `merge`.

        Args:
            key: the key that has been used to decide that lhs and rhs were duplicates
            lhs: variable of interest
            rhs: variable of interest 
        """

        # logger.debug(f"Call Merger `{type(self).__name__}`")
        self.precheck(key, lhs, rhs)
        self.merge(key, lhs, rhs)
        # logger.debug(f"Merger `{type(self).__name__}` called: {self.merged}")

    def precheck(self, key, lhs, rhs) -> None:
        """A function where a subclass may check pre-conditions at each call.

        Args:
            key: the key that has been used to decide that lhs and rhs were duplicates
            lhs: variable of interest
            rhs: variable of interest
        """
        pass

    def reset(self) -> None:
        """Reset the `self.merged` member, to erase whatever state was seen
        while processing the last list of duplicates."""
        # logger.debug(f"Init Merger `{type(self).__name__}`")
        self.merged = None

    def set(self, value) -> None:
        """Save whatever state is of interest in what is passed to `merge`.

        Args:
            value: a state of interest
        """
        self.merged = value

    @abstractmethod
    def merge(self, key, lhs, rhs) -> None:
        """Get whatever state is of interest in the given key or pair of elements.

        Args:
            key: the key that has been used to decide that lhs and rhs were duplicates
            lhs: variable of interest
            rhs: variable of interest
        """
        raise NotImplementedError

    def get(self):
        """Return the actually merged variable, representing de-duplicated data."""
        # logger.debug(f"Get Merger `{type(self).__name__}`")
        return self.merged

class dictry:
    """Mergers operating on dictionaries."""

    class DictryMerger(Merger):
        """Interface for Mergers operating on dictionaries.

        Basically implements `precheck` with asserting that key is a base.Element
        and lhs & rhs are dict.
        """
        def precheck(self, key, lhs: dict[str,str], rhs: dict[str,str]) -> None:
            assert(issubclass(type(key), base.Element))
            assert(type(lhs) == dict)
            assert(type(rhs) == dict)

        def set(self, value: dict[str,str]) -> None:
            assert(type(value) == dict)
            self.merged = value

        @abstractmethod
        def merge(self, key, lhs: dict[str,str], rhs: dict[str,str]) -> dict[str,str]:
            raise NotImplementedError

        def get(self) -> dict[str,str]:
            return self.merged

    class Append(DictryMerger):
        """Merge dictionaries by removing duplicated values
        and aggregating values that are different in a list.

        returns a string, where all values are joined.
        """

        def __init__(self, reconciliate_sep = "|"):
            self.reconciliate_sep = reconciliate_sep
            self.merged = {}

        def reset(self):
            self.merged = {}

        def set(self, merged) -> None:
            assert(type(merged) == dict)
            for k,v in merged.items():
                e = self.merged.get(k, set())
                if type(v) == set:
                    e.union(v)
                    self.merged[k] = e
                else:
                    self.merged[k] = set((v,)).union(e)

        def merge(self, key, lhs: dict[str,str], rhs: dict[str,str]):
            self.set(lhs)
            self.set(rhs)

        def get(self) -> str:
            merged = {}
            for k,v in self.merged.items():
                assert(type(v) == set)
                # Convert sets as str.
                merged[k] = self.reconciliate_sep.join(v)
            return merged

class string:
    """Mergers operating on strings."""

    class StringMerger(Merger):
        """Interface for Mergers operating on dictionaries.

        Basically implements `precheck` with asserting that key is a base.Element
        and lhs & rhs are str.
        """
        def precheck(self, key, lhs: str, rhs: str):
            assert(issubclass(type(key), base.Element))
            assert(type(lhs) == str)
            assert(type(rhs) == str)

        @abstractmethod
        def merge(self, key, lhs: str, rhs: str) -> str:
            raise NotImplementedError

        def get(self) -> str:
            return str(self.merged)

    class UseKey(StringMerger):
        """Use the key when merging"""
        def merge(self, key, lhs: str, rhs: str) -> str:
            self.set(key)

    class UseFirst(StringMerger):
        """Use the first (leftmost) seen object when merging"""
        def merge(self, key, lhs: str, rhs: str) -> str:
            self.set(lhs)

    class UseLast(StringMerger):
        """Use the last (rightmost) seen object when merging"""
        def merge(self, key, lhs: str, rhs: str) -> str:
            self.set(rhs)

    class EnsureIdentical(StringMerger):
        """If the merged values are not all identical, raise a ValueError.
        If no error is raised, the last seen value is returned."""

        def merge(self, key, lhs: str, rhs: str) -> str:
            if self.merged:
                if self.merged != lhs or self.merged != rhs:
                    raise ValueError(f"Merged value `{lhs}`/`{rhs}` not identical to previously seen one: `{self.merged}`.")
            else:
                if lhs != rhs:
                    raise ValueError(f"Merged value `{lhs}`/`{rhs}` not identical.`")
            self.set(lhs) # Should be equal to rhs.


    class CommonSubType(StringMerger):
        """If the merged values are not all identical, sets the most generic common subtype
        in the ontology hierarchy as the value."""

        def __init__(self, ontology):
            self.ontology = ontology

        def merge(self, key, lhs: str, rhs: str) -> str:
            logger.debug(f"Merge of `{lhs}` and` `{rhs}`")

            graph_hierarchy = copy.copy(self.ontology._head_ontology.get_nx_graph())
            if self.ontology._tail_ontologies:
                for onto in self.ontology._tail_ontologies.values():
                    tail_graph = copy.copy(onto.get_nx_graph())
                    graph_hierarchy = nx.compose(tail_graph, graph_hierarchy)

            if self.merged:
                merge = nx.lowest_common_ancestor(graph_hierarchy, self.merged, lhs)
                if merge is None:
                    raise ValueError(f" Value `{lhs}` has no common subtype with previously seen one: `{self.merged}`.`")
                self.set(merge)
                self.merged = merge
                logger.debug(f"`{merge}`")

                merge = nx.lowest_common_ancestor(graph_hierarchy, self.merged, rhs)
                if merge is None:
                    raise ValueError(f"Value `{rhs}` has no common subtype with previously seen one: `{self.merged}`.`")
                self.set(merge)
                self.merged = merge
                logger.debug(f"`{merge}`")

            else :
                merge = nx.lowest_common_ancestor(graph_hierarchy, lhs, rhs)
                if merge is None:
                    raise ValueError(f"Merged value `{lhs}`/`{rhs}` has no common subtype.`")
                self.merged = merge
                self.set(merge)
                logger.debug(f"`{merge}`")


    class CommonSuperType(StringMerger):
        """If the merged values are not all identical, sets the most specific common supertype
        in the ontology hierarchy as the value."""

        def __init__(self, ontology):
            self.ontology = ontology

        def merge(self, key, lhs: str, rhs: str) -> str:
            logger.debug(f"Merge of `{lhs}` and` `{rhs}`")

            graph_hierarchy = copy.copy(self.ontology._head_ontology.get_nx_graph())
            if self.ontology._tail_ontologies:
                for onto in self.ontology._tail_ontologies.values():
                    tail_graph = copy.copy(onto.get_nx_graph())
                    graph_hierarchy = nx.compose(tail_graph, graph_hierarchy)

            if self.merged:
                merge = nx.lowest_common_ancestor(nx.reverse(graph_hierarchy), self.merged, lhs)
                if merge is None:
                    raise ValueError(f" Value `{lhs}` has no common subtype with previously seen one: `{self.merged}`.`")
                self.set(merge)
                self.merged = merge
                logger.debug(f"`{merge}`")

                merge = nx.lowest_common_ancestor(nx.reverse(graph_hierarchy), self.merged, rhs)
                if merge is None:
                    raise ValueError(f"Value `{rhs}` has no common subtype with previously seen one: `{self.merged}`.`")
                self.set(merge)
                self.merged = merge
                logger.debug(f"`{merge}`")

            else :
                merge = nx.lowest_common_ancestor(graph_hierarchy, lhs, rhs)
                if merge is None:
                    raise ValueError(f"Merged value `{lhs}`/`{rhs}` has no common subtype.`")
                self.merged = merge
                self.set(merge)
                logger.debug(f"`{merge}`")


    class OrderedSet(StringMerger):
        """Aggregate all seen values, ordered lexicographically.

        returns a string, where all values are joined.
        """
        def __init__(self, reconciliate_sep = "|"):
            self.reconciliate_sep = reconciliate_sep

        def reset(self):
            self.merged = OrderedDict()

        def set(self, value) -> None:
            if type(value) == OrderedDict:
                for k in value.keys():
                    self.merged[k] = None
            else:
                self.merged[value] = None

        def merge(self, key, lhs: str, rhs: str):
            self.set(lhs)
            self.set(rhs)

        def get(self) -> str:
            return self.reconciliate_sep.join(self.merged.keys())
