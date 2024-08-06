import logging

from . import base
class split(base.Transformer):
    """Transformer subclass used to split cell values at defined separator and create nodes with
    their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, i):

        for key in self.columns:
            if self.valid(row[key]):
                items = row[key].split(self.separator)

                for item in items:
                    yield item
            else:
                logging.warning(
                     f"Encountered invalid content when mapping column: `{key}`. Skipping cell value: `{row[key]}`")
class cat(base.Transformer):
    """Transformer subclass used to concatenate cell values of defined columns and create nodes with
    their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, i):

        formatted_items = ""

        if hasattr(self, "format_string"):

            parts = self.format_string.split('{')

            for part in parts[1:]:
                column_name, rest_of_string = part.split('}', 1)

                column_value = row.get(column_name, '')

                if self.valid(column_value):
                    formatted_items += f"{column_value}{rest_of_string}"
                else:
                    logging.warning(
                        f"Encountered invalid content when mapping column: `{column_name}`. Skipping cell value: `{row[column_name]}`")

            yield formatted_items

        else:

            for key in self.columns:
                if self.valid(row[key]):
                    formatted_items += str(row[key])
                else:
                    logging.warning(
                        f"Encountered invalid content when mapping column: `{key}`. Skipping cell value: `{row[key]}`")

            yield formatted_items


class rowIndex(base.Transformer):
    """Transformer subclass used for the simple mapping of nodes with row index values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, i):
        if self.valid(i):
            yield i
        else:
            logging.warning(
                f"Error while mapping by row index. Invalid cell content: `{i}`")


class map(base.Transformer):
    """Transformer subclass used for the simple mapping of cell values of defined columns and creating
    nodes with their respective values as id."""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):

        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, i):

        # TODO if there is from_subject, change soruce_Id in edge to that id

        for key in self.columns:
            if self.valid(row[key]):
                yield row[key]
            else:
                logging.warning(
                     f"Encountered invalid content when mapping column: `{key}`. Skipping cell value: `{row[key]}`")

