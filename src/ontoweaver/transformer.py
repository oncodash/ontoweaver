import logging

from . import base

# Return dictionary of mappings for both property and node ids
class split(base.Transformer):
    """Transformer subclass used to split cell values at defined separator and create nodes with
    their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, source_id = None):

        elements = []

        if source_id is None:
            for key in self.columns:
                if self.valid(row[key]):
                    source_id = self.make_id(row[key])
                    elements.append(self.make_node( id=source_id, properties = self.properties(row)))
            return source_id
        else:
            for key in self.columns:
                if self.valid(row[key]):
                    # TODO if make id is called within node split_transformer is redundant
                    # TODO just return list of IDs
                    target_id = self.split_transformer(row[key])
                    for i in target_id.split(self.separator):
                        logging.debug(f"\t\t\t\t\tMake node `{i}` in {target_id.split(self.separator)}.")
                        elements.append(self.make_node(id = i, properties = self.properties(row)))
                        logging.debug(f"\t\t\t\t\tMake edge toward `{i}` in {target_id.split(self.separator)}.")
                        elements.append(self.make_edge(id_target = i, id_source = source_id, properties = self.properties(row)))

        return elements



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

        elements = []

        # TODO if there is from_subject, change soruce_Id in edge to that id

        if source_id is None:
            for key in self.columns:
                if self.valid(row[key]):
                    source_id = self.make_id(row[key])
                    logging.debug(f"\t\t\t\t\tDeclared source id: `{source_id}")
                    elements.append(self.make_node(id=source_id, properties = self.properties(row)))
            return source_id
        else:
            for key in self.columns:
                if self.valid(row[key]):
                    target_id = self.make_id(row[key])
                    # TODO combine make_id within make_node
                    elements.append(self.make_node(id=target_id, properties = self.properties(row)))
                    if target_id:
                        elements.append(self.make_edge(id_source=source_id, id_target=target_id, properties = self.properties(row)))

            return elements
