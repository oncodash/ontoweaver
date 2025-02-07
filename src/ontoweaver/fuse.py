import logging
from abc import ABCMeta, abstractmethod

from . import base
from . import merge

logger = logging.getLogger("ontoweaver")

class Fuser(merge.Merger):
    """Interface for Merger classes merging elements of a given type
    (usually a base.Element subclass).

    A subclass implementing this interface should keep trace of
    which ID was replaced by which one, in the `ID_mapping` dictionary.
    This dictionary may be used to remap the id_source and id_target of
    the related edges, processed later by another Fuser.
    """

    def __init__(self, cls):
        logger.debug(f"Instantiante {type(self).__name__} for class {cls.__name__}:")
        self.cls = cls
        self.ID_mapping = {}


class Members(Fuser):
    """A Fuser that merges base.Element objects, members by members,
    by calling the given sub-Mergers for each members.

    By definition, a merge performed with this class cannot implement
    a processing that depends on the values of other member variables.
    Each merging of member variables is independant.

    For instance, if the fusion that you want to implement decides
    how to merge types based on properties, you will need to implement
    your own subclass of Fuser.
    """

    # FIXME avoid calling methods on all 5 sub mergers each time.

    class Mergers:
        def __init__(self,
             merge_ID    : merge.string.StringMerger = merge.string.UseKey(),
             merge_label : merge.string.StringMerger = merge.string.UseKey(),
             merge_prop  : merge.dictry.DictryMerger = merge.dictry.Append(),
             merge_source: merge.string.StringMerger = merge.string.OrderedSet(),
             merge_target: merge.string.StringMerger = merge.string.OrderedSet()
        ):
            self.ID = merge_ID
            self.label = merge_label
            self.prop = merge_prop
            self.source = merge_source
            self.target = merge_target

    def __init__(self,
                 cls,
                 merge_ID    : merge.string.StringMerger = merge.string.UseKey(),
                 merge_label : merge.string.StringMerger = merge.string.UseKey(),
                 merge_prop  : merge.dictry.DictryMerger = merge.dictry.Append(),
                 merge_source: merge.string.StringMerger = merge.string.OrderedSet(),
                 merge_target: merge.string.StringMerger = merge.string.OrderedSet()
                 ):
        """Constructor.

        Takes the class to merge and a merger for each member variable
        of either a Node or an Edge.

         Args:
             cls: either a base.Node or a base.Edge subclass
             merge_ID: the merger used to merge `id`(s)
             merge_label: the merger used to merge `label`(s)
             merge_prop: the merger used to merge `property`(s)
             merge_source: the merger used to merge `id_source`(s)
             merge_target: the merger used to merge `id_target`(s)
        """

        super().__init__(cls)

        self.merged = Members.Mergers(merge_ID, merge_label, merge_prop, merge_source, merge_target)
        logger.debug(f"  ID    : {type(self.merged.ID).__name__}")
        logger.debug(f"  label : {type(self.merged.label).__name__}")
        logger.debug(f"  prop  : {type(self.merged.prop).__name__}")

        self.members = {
            "id": None,
            "label": None,
            "properties": {},
        }
        if issubclass(self.cls, base.Edge):
            self.members.update({
                "id_source": None,
                "id_target": None,
            })
            logger.debug(f"  source: {type(self.merged.source).__name__}")
            logger.debug(f"  target: {type(self.merged.target).__name__}")

        self._ID_seen = set()


    def precheck(self, key, lhs, rhs):
        assert(issubclass(type(key), base.Element))
        assert(issubclass(type(lhs), base.Element))
        assert(issubclass(type(rhs), base.Element))

    def reset(self):
        self.merged.ID.reset()
        self._ID_seen = set()
        self.merged.label.reset()
        self.merged.prop.reset()
        self.merged.source.reset()
        self.merged.target.reset()

    def set(self, mergers) -> None:
        self.merged.ID.set(mergers.ID.merged)
        self.merged.label.set(mergers.label.merged)
        self.merged.prop.set(mergers.prop.merged)

        if issubclass(self.cls, base.Edge):
            self.merged.source.set(mergers.source.merged)
            self.merged.target.set(mergers.target.merged)

    def merge(self, key, lhs: base.Element, rhs: base.Element):
        assert(issubclass(type(lhs), base.Node) and issubclass(type(rhs), base.Node)
               or
               issubclass(type(lhs), base.Edge) and issubclass(type(rhs), base.Edge) )

        self._ID_seen.add(lhs.id)
        self._ID_seen.add(rhs.id)
        self.merged.ID(key, lhs.id, rhs.id)
        self.merged.label(key, lhs.label, rhs.label)
        self.merged.prop(key, lhs.properties, rhs.properties)

        if issubclass(self.cls, base.Edge):
            self.merged.source(key, lhs.id_source, rhs.id_source)
            self.merged.target(key, lhs.id_target, rhs.id_target)

        self.set(self.merged)

    def get(self) -> base.Element:
        self.members["id"] = self.merged.ID.get()
        # Save the ID mappings we've seen so far.
        for id in self._ID_seen:
            # We do not need to save self-mappings.
            if id != self.members["id"]:
                self.ID_mapping[id] = self.members["id"]

        self.members["label"] = self.merged.label.get()
        self.members["properties"] = self.merged.prop.get()

        if issubclass(self.cls, base.Edge):
            self.members["id_source"] = self.merged.source.get()
            self.members["id_target"] = self.merged.target.get()

        return self.cls(**(self.members))

