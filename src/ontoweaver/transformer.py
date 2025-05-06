import re
import sys
import logging
import pandas as pd

from . import base
from. import exceptions
from . import validate
from . import make_value

logger = logging.getLogger("ontoweaver")


def register(transformer_class):
    """Adds the given transformer class to those available to OntoWeaver.

    The given class should inherit from ontoweaver.base.Transformer

    Example::

        import ontoweaver

        class user_transformer(ontoweaver.base.Transformer):
            def __init__(self, target, target_element_properties, edge=None, columns=None, **kwargs):
                super().__init__(target, target_element_properties, edge, columns, **kwargs)

            def __call__(self, row, i):
                for key in self.columns:
                    yield str(row[key])

        ontoweaver.transformer.register( user_transformer )

        # The mapping can now use "user_transformer" in the transformers list.

    Args:
        transformer_class: The class to add to the ontoweaver.transformer module.
    """

    if not issubclass(transformer_class, base.Transformer):
        logging.error(f"{transformer_class.__name__} should inherit from ontoweaver.base.Transformer.", section="transformer.register", exception = exceptions.InterfaceInheritanceError)
    current = sys.modules[__name__]
    setattr(current, transformer_class.__name__, transformer_class)


# NOTE: transformers pass all kwargs to superclass to allow it to show
#       the (additional) user-defined arguments when calling __repr__.


class split(base.Transformer):
    """Transformer subclass used to split cell values at defined separator and label_maker nodes with
    their respective values as id."""

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, separator: str = None):
            self.separator = separator
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            for key in columns:
                items = str(row[key]).split(self.separator)
                for item in items:
                    yield item

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, raise_errors = True, separator = None, **kwargs):
        """
        Initialize the split transformer.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            sep: Character(s) to use for splitting.
            output_validator: the OutputValidator object used for validating transformer output.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
            separator: The character(s) to use for splitting the cell values. Defaults to ",".
        """

        self.separator = separator

        self.value_maker = self.ValueMaker(raise_errors=raise_errors, separator=self.separator)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         raise_errors=raise_errors, **kwargs)


    def __call__(self, row, i):
        """
        Process a row and yield split items as node IDs.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: Each split item from the cell value.
        """
        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)


class cat(base.Transformer):
    """Transformer subclass used to concatenate cell values of defined columns and label_maker nodes with
    their respective values as id."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            formatted_items = ""

            for key in columns:
                formatted_items += str(row[key])
                yield formatted_items

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Initialize the cat transformer.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            output_validator: the OutputValidator object used for validating transformer output.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
        """

        self.value_maker = self.ValueMaker(raise_errors=raise_errors)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)

    def __call__(self, row, i):
        """
        Process a row and yield concatenated items as node IDs.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The concatenated string from the cell values.
        """
        if not self.columns:
            self.error(f"No column declared for the {type(self).__name__} transformer, did you forgot to add a `columns` keyword?", section="cat.call", exception = exceptions.TransformerInputError)

        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)




class cat_format(base.Transformer):
    """Transformer subclass used to concatenate cell values of defined columns and label_maker nodes with
    their respective values as id."""

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, format_string: str = None):
            self.format_string = format_string
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            formatted_string = self.format_string.format_map(row)
            yield formatted_string

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, format_string = None,  **kwargs):
        """
        Initialize the cat_format transformer.

        Args:.
            target_element_properties: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            format_string: A format string containing the column names to assemble.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
        """

        if not format_string:  # Neither empty string nor None.
            self.error(f"The `format_string` parameter of the `{self.__name__}` transformer cannot be an empty string.")
        self.format_string = format_string
        self.value_maker = self.ValueMaker(raise_errors=raise_errors, format_string=self.format_string)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator, multi_type_dict,
                         raise_errors=raise_errors, **kwargs)

    def __call__(self, row, i):
        """
        Process a row and yield a formatted string as node ID.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The formatted string from the cell values.

        Raises:
            Exception: If the format string is not defined or if invalid content is encountered.
        """

        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)

class rowIndex(base.Transformer):
    """Transformer subclass used for the simple mapping of nodes with row index values as id."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            yield i

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Initialize the rowIndex transformer.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
        """

        self.value_maker = self.ValueMaker(raise_errors=raise_errors)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)

    def __call__(self, row, i, result_object=None):
        """
        Process a row and yield the row index as node ID.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Returns:
            int: The row index if valid.

        Raises:
            Warning: If the row index is invalid.
        """
        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)

class map(base.Transformer):
    """Transformer subclass used for the simple mapping of cell values of defined columns and creating
    nodes with their respective values as id."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                if key not in row:
                    self.error(f"Column '{key}' not found in data", section="map.call",
                               exception=exceptions.TransformerDataError)
                yield row[key]

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Initialize the map transformer.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
        """

        self.value_maker = self.ValueMaker(raise_errors=raise_errors)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)

    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The cell value if valid.

        Raises:
            Warning: If the cell value is invalid.
        """
        if not self.columns:
            self.error(f"No column declared for the {type(self).__name__} transformer, did you forgot to add a `columns` keyword?", section="map.call", exception = exceptions.TransformerInputError)

        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)


class translate(base.Transformer):
    """Translate the targeted cell value using a tabular mapping and yield a node with using the translated ID."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                if key not in row:
                    self.error(f"Column '{key}' not found in data", section="map.call",
                               exception=exceptions.TransformerDataError)
                yield row[key]

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Constructor.

        NOTE: The user should provide at least either `translations` or `translations_file`, but not both.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            translations: A dictionary figuring what to replace (keys) with which string (values).
            translations_file: A filename pointing to a tabular file readable by Pandas' csv_read.
            translate_from: The column in the file containing what to replace.
            translate_to: The column in the file containing the replacement string.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
            kwargs: Additional arguments to pass to Pandas' read_csv (if "sep=TAB", reads the translations_file as tab-separated).
        """

        self.value_maker = self.ValueMaker(raise_errors=raise_errors)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)
        self.map = map(properties_of, label_maker, branching_properties, columns, output_validator, multi_type_dict, **kwargs)

        # Since we cannot expand kwargs, let's recover what we have inside.
        translations = kwargs.get("translations", None)
        translations_file = kwargs.get("translations_file", None)
        translate_from = kwargs.get("translate_from", None)
        translate_to = kwargs.get("translate_to", None)

        if translations and translations_file:
            self.error(f"Cannot have both `translations` (=`{translations}`) and `translations_file` (=`{translations_file}`) defined in a {type(self).__name__} transformer.", secton="translate", exception = exceptions.TransformerInterfaceError)

        if translations:
            self.translate = translations
            logger.debug(f"\t\t\tManual translations: `{self.translate}`")
        elif translations_file:
            logger.debug(f"\t\t\tGet translations from file: `{translations_file}`")
            if not translate_from:
                self.error(f"No translation source column declared for the `{type(self).__name__}` transformer using translations_file=`{translations_file}`, did you forget to add a `translate_from` keyword?", section="translate.init", exception = exceptions.TransformerInterfaceError)
            if not translate_to:
                self.error(f"No translation target column declared for the `{type(self).__name__}` transformer using translations_file=`{translations_file}`, did you forget to add a `translate_to` keyword?", section="translate.init", exception = exceptions.TransformerInterfaceError)
            else:
                self.translations_file = translations_file
                self.translate_from = translate_from
                self.translate_to = translate_to

                # Extract available arguments from Pandas' read_csv docstring:
                pd_read_csv_args = []
                for line in pd.read_csv.__doc__.split("\n"):
                    if re.match(r"^[a-z_]+ :", line):
                        pd_read_csv_args.append(line.split(":")[0].strip())

                # Keep only the user-passed arguments that are in Pandas' read_csv list.
                pd_args = {k:v for k,v in kwargs.items() if k in pd_read_csv_args}

                if "sep" in pd_args and pd_args["sep"] == "TAB":
                    logger.debug(f"\t\t\tMapping asked for sep:TAB, enable Pandas' read_csv engine:python to avoid a warning.")
                    pd_args["sep"] = '\t'
                    pd_args["engine"] = "python"

                logger.debug(f"\t\t\tArguments passed to pandas.read_csv: `{pd_args}`")

                self.df = pd.read_csv(self.translations_file, **pd_args)

                if self.translate_from not in self.df.columns:
                    self.error(f"Source column `{self.translate_from}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = exceptions.TransformerDataError)

                if self.translate_to not in self.df.columns:
                    self.error(f"Target column `{self.translate_to}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = exceptions.TransformerDataError)

                self.translate = {}
                for i,row in self.df.iterrows():
                    if row[self.translate_from] and row[self.translate_to]:
                        self.translate[row[self.translate_from]] = row[self.translate_to]
                    else:
                        logger.warning(f"Cannot translate from `{self.translate_from}` to `{self.translate_to}`, invalid translations values at row {i} of file `{self.translations_file}`: `{row[self.translate_from]}` => `{row[self.translate_to]}`. I will ignore this translation.")

        else:
            self.error(f"When using a {type(self).__name__} transformer, you must define either `translations` or `translations_file`.", section="translate.init", exception = exceptions.TransformerInterfaceError)


        if not self.translate:
            self.error(f"No translation found, did you forget the `translations` keyword?", section="translate.init", exception = exceptions.TransformerInterfaceError)

    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The cell value if valid.

        Raises:
            Warning: If the cell value or the translation is invalid.
        """
        if not self.columns:
            self.error(f"No column declared for the {type(self).__name__} transformer, did you forgot to add a `columns` keyword?", section="translate", exception = exceptions.TransformerDataError)

        for key in self.columns:
            if key not in row:
                self.error(f"Column '{key}' not found in data", section="translate", exception = exceptions.TransformerDataError)
            cell = row[key]
            if cell in self.translate:
                row[key] = self.translate[cell]
            else:
                logger.warning(f"Row {i} does not contain something to be translated from `{self.translate_from}` to `{self.translate_to}` at column `{key}`.")

        for e, edge, node in self.map(row, i):
            yield e, edge, node

class string(base.Transformer):
    """A transformer that makes up the given static string instead of extractsing something from the table."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True, string: str = None):
            self.string = string
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            yield self.string

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Constructor.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            value: The string to use.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
        """

        self.value = kwargs.get("value", None)
        self.value_maker = self.ValueMaker(raise_errors=raise_errors, string=self.value)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)

    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The cell value if valid.

        Raises:
            Warning: If the cell value is invalid.
        """
        if not self.value:
            self.error(f"No value passed to the {type(self).__name__} transformer, did you forgot to add a `value` keyword?", section="string.call", exception = exceptions.TransformerInterfaceError)

        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)

class replace(base.Transformer):
    """Transformer subclass used to remove characters that are not allowed from cell values of defined columns.
     The forbidden characters are defined by a regular expression pattern, and are substituted with a user-defined
     character or removed entirely. In case the cell value is made up of only forbidden characters, the node is not
     created and a warning is logged."""

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, forbidden = None, substitute = None):

            self.forbidden = forbidden
            self.substitute = substitute
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                logger.info(
                    f"Setting forbidden characters: {self.forbidden} for `replace` transformer, with substitute character: `{self.substitute}`.")
                formatted = re.sub(self.forbidden, self.substitute, row[key])
                strip_formatted = formatted.strip(self.substitute)
                logger.debug(f"Formatted value: {strip_formatted}")
                yield strip_formatted

    def __init__(self, properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Constructor.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            forbidden: The regular expression pattern to match forbidden characters.
            substitute: The string to replace forbidden characters with.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
        """
        self.forbidden = kwargs.get("forbidden", r'[^a-zA-Z0-9_`.()]') # By default, allow alphanumeric characters (A-Z, a-z, 0-9),
        # underscore (_), backtick (`), dot (.), and parentheses (). TODO: Add or remove rules as needed based on errors in Neo4j import.
        self.substitute = kwargs.get("substitute", "")

        self.value_maker = self.ValueMaker(raise_errors=raise_errors, forbidden=self.forbidden, substitute=self.substitute)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)

    def __call__(self, row, i):
        """
        Process a row and yield cell values with forbidden characters removed or replaced.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The processed cell value with forbidden characters removed or replaced.

        Raises:
            Warning: If the processed cell value is invalid.
        """
        for value in self.value_maker(self.columns, row, i):
            yield self.create(value, row)