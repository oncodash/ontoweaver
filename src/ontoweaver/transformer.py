import logging

from . import base

# Return dictionary of mappings for both property and node ids
class split(base.Transformer):
    """Transformer subclass used to split cell values at defined separator and create nodes with
    their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row):

        for key in self.columns:
            if self.valid(row[key]):
                items = row[key].split(self.separator)

                for item in items:
                    yield item
            else:
                logging.error(
                     f"Error while mapping column: `{key}`. Invalid cell content: `{row[key]}`")
class cat(base.Transformer):
    """Transformer subclass used to concatenate cell values of defined columns and create nodes with
    their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row):

        formatted_items = ""

        if hasattr(self, "format_string"):

            parts = self.format_string.split('{')

            for part in parts[1:]:
                column_name, rest_of_string = part.split('}', 1)

                column_value = row.get(column_name, '')

                if self.valid(column_value):
                    formatted_items += f"{column_value}{rest_of_string}"
                else:
                    logging.error(
                         f"Error while mapping column: `{key}`. Invalid cell content: `{row[key]}`")

            yield formatted_items

        else:

            for key in self.columns:
                if self.valid(row[key]):
                    formatted_items += str(row[key])
                else:
                    logging.error(
                        f"Error while mapping column: `{key}`. Invalid cell content: `{row[key]}`")

            yield formatted_items


class rowIndex(base.Transformer):

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, index):
        if self.valid(index):
            yield index
        else:
            logging.error(
                f"Error while mapping by row index. Invalid cell content: `{index}`")


class map(base.Transformer):
    """Transformer subclass used for the simple mapping of cell values of defined columns and creating
    nodes with their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row):

        # TODO if there is from_subject, change soruce_Id in edge to that id

        for key in self.columns:
            if self.valid(row[key]):
                yield row[key]
            else:
                logging.error(
                    f"Error while mapping column: `{key}`. Invalid cell content: `{row[key]}`")

