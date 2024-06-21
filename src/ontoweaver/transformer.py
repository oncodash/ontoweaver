import logging

from . import base

# Return dictionary of mappings for both property and node ids
class split(base.Transformer):
    """Transformer subclass used to split cell values at defined separator and create nodes with
    their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, source_id = None):

        for key in self.columns:
            if self.valid(row[key]):
                logging.debug(f"AAAAAAA {row[key]}")
                # TODO if make id is called within node split_transformer is redundant
                # TODO just return list of IDs
                return row[key]
class cat(base.Transformer):
    """Transformer subclass used to concatenate cell values of defined columns and create nodes with
    their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    pass

class rowIndex(base.Transformer):

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    pass

class map(base.Transformer):
    """Transformer subclass used for the simple mapping of cell values of defined columns and creating
    nodes with their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, source_id=None):

        # TODO if there is from_subject, change soruce_Id in edge to that id

        if source_id is None:
            for key in self.columns:
                if self.valid(row[key]):
                    return row[key]
        else:
            for key in self.columns:
                if self.valid(row[key]):
                    return row[key]
                    # TODO combine make_id within make_node

