from ontoweaver import base


class Fuser:
    pass

class CompoundFuser(Fuser):

    def __init__(self,
                 MergeID,
                 MergeProperties,
                 MergeType,
                 ):
        self.MergeID = MergeID
        self.MergeProperties = MergeProperties
        self.MergeType = MergeType

    def __call__(self, lhs: base.Element, rhs: base.Element):
        self.MergeID(lhs, rhs)
        self.MergeProperties(lhs, rhs)
        self.MergeType(lhs, rhs)
