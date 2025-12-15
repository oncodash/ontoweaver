import math
import re
import sys
import logging
from abc import abstractmethod

import pandas as pd


from . import errormanager
from. import exceptions
from . import validate
from . import make_value
from . import base

logger = logging.getLogger("ontoweaver")


class Transformer(errormanager.ErrorManager):
    """"Class used to manipulate cell values and return them in the correct format."""""

    def __init__(self, properties_of, value_maker = None, label_maker = None, branching_properties = None, columns = None,
                 output_validator: validate.OutputValidator() = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Instantiate transformers.

        :param properties_of: the properties of each node type.
        :param value_maker: the ValueMaker object used for the logic of cell value selection for each transformer. Default is None.
        :param label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
        :param branching_properties: in case of branching on cell values, the dictionary holds the properties for each branch.
        :param columns: the columns to use in the mapping.
        :param output_validator: the OutputValidator object used for validating transformer output. Default is None.
        :param multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
        :param raise_errors: whether to raise errors or not. Default is True.
            each transformer is instantiated with a default OutputValidator object, and additional user-defined rules if needed in
            the tabular module.


        """
        super().__init__(raise_errors)

        self.properties_of = properties_of
        self.value_maker = value_maker
        self.label_maker = label_maker
        self.branching_properties = branching_properties
        self.columns = columns
        self.output_validator = output_validator
        if not self.output_validator:
            self.output_validator = validate.OutputValidator(validate.default_validation_rules, raise_errors = raise_errors)
        self.parameters = kwargs
        self.multi_type_dict = multi_type_dict
        self.final_type = None # The final type is to be passed by the label maker class based on the YAML mapping. That
                               # is why here it is None by default
        self.kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.declare_types = base.Declare()

    def get_transformer(self):
        return self

    def __call__(self, row, i):
        """
        Process a row. If not empty/null, yields concatenated items as node IDs.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The concatenated string from the cell values.
       """
        for value in self.value_maker(self.columns, row, i):
            value, edge_type, node_type, reverse_edge = self.create(value, row)
            if self.is_not_null(value):
                yield value, edge_type, node_type, reverse_edge


    def is_not_null(self, val):
        """
        Checks if cell value is not empty nor 'null', 'nan'...

        Args:
            val: The value to check.

        Returns:
            bool: True if the value is valid, False otherwise.
        """
        if pd.api.types.is_numeric_dtype(type(val)):
            if (math.isnan(val) or val == float("nan")):
                return False
        elif str(val).lower() == "nan":  # Conversion from Pandas' `object` needs to be explicit.
            return False
        elif str(val) == "":
            return False
        return True

    #FIXME: The functions below are never implemented.
    @abstractmethod
    def nodes(self):
        raise NotImplementedError

    @abstractmethod
    def edges(self):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def edge_type():
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def target_type():
       raise NotImplementedError

    @classmethod
    def source_type(cls):
       return cls.edge_type().source_type()

    def __repr__(self):

        representation = ""

        if hasattr(self, "from_subject"):
            from_subject = self.from_subject
        else:
            from_subject = "."

        target_name = ""
        edge_name = ""

        if hasattr(self, "multi_type_dict") and self.multi_type_dict is not None:
            for key, value in self.multi_type_dict.items():
                if value['to_object'] and value['via_relation']:
                    target_name = value['to_object']
                    edge_name = value['via_relation']
                elif value['to_object'] and not value['via_relation']:
                    target_name = value['to_object']
                    edge_name = "."


                if self.properties_of:
                    # The transformer is not a branching transformer, and has only one set of properties.
                    props = "{"
                    trans = []
                    for kind in self.properties_of:
                        trans.append(f"{kind} {self.properties_of[kind]}>")
                    props += ", ".join(trans)
                    props+="}"
                elif self.branching_properties and self.branching_properties.get(value['to_object'], None):
                    # The transformer is a branching transformer, and has multiple sets of properties. We extract the ones for the current type.
                    props = self.branching_properties.get(value['to_object'])
                else:
                    # The transformer has no properties for the type.
                    props = "{}"


                params = ""
                parameters = {k:v for k,v in self.parameters.items() if k not in ['subclass', 'from_subject', "match"]}
                if parameters:
                    p = []
                    for k,v in parameters.items():
                        p.append(f"{k}={v}")
                    params = ','.join(p)

                if from_subject == "." and edge_name == "." and target_name == "." and props == "{}":
                    # If this is a property transformer
                    link = ""

                elif from_subject == "." and edge_name == "." and (target_name != "." or props != "{}"):
                    # This a subject transformer.
                    link = f" => ({target_name}/{props})"

                else:
                    # This is a regular transformer.
                    link = f" => ({from_subject})--[{edge_name.__name__}]->({target_name.__name__}/{props})"

                if self.columns:
                    columns = self.columns
                else:
                    columns = []

                for c in columns:
                    if type(c) != str:
                        self.error(f"Column `{c}` is not a string, did you mistype a leading colon?", exception=exceptions.ParsingError)

                representation += (f"<{type(self).__name__}({params}) {','.join(columns)}{link}>")

        else:
            #The transformer is a property transformer. We add the property name and value in the tabular.properties() function.
            representation += (f"<{type(self).__name__}() {','.join(self.columns) if self.columns else ''} =>")

        return representation


    def validate(self, res):
        """
        Validate the output of the transformer, using the output_validator. of the transformer instance.
        """
        try:
            if isinstance(self.output_validator, validate.SimpleOutputValidator) or isinstance(self.output_validator, validate.SkipValidator):
                # The SimpleOutputValidator and SkipValidator do not use the Pandera package, and the value is therefore not
                # required to be in a DataFrame format. Voiding the creation of a DataFrame here saves computational time for
                # large datasets.
                if self.output_validator(res):
                    return True
                else:
                    return False
            else:
                if self.output_validator(pd.DataFrame([res], columns=["cell_value"])):
                    return True
                else:
                    return False
        except pa.errors.SchemaErrors as error:
            msg = f"Transformer {self.__repr__()} did not produce valid data {error}."
            self.error(msg, exception = exceptions.DataValidationError)

    def create(self, returned_value, row):
        """
        Create the output of the transformer, using the label_maker of the transformer instance.

        Returns:
            Extracted cell value (can be node ID, property value, edge ID), edge type, target node type, and
            reverse relation in case declared in the mapping.
        """
        result_object = self.label_maker(self.validate, returned_value, self.multi_type_dict, self.branching_properties, row)
        if result_object.target_node_type:
            self.target_type = result_object.target_node_type.__name__
        if result_object.target_element_properties is not None:
            self.properties_of = result_object.target_element_properties
        self.final_type = result_object.final_type
        return result_object.extracted_cell_value, result_object.edge_type, result_object.target_node_type, result_object.reverse_relation





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

    if not issubclass(transformer_class, Transformer):
        logging.error(f"{transformer_class.__name__} should inherit from ontoweaver.base.Transformer.", section="transformer.register", exception = exceptions.InterfaceInheritanceError)
    current = sys.modules[__name__]
    logging.debug(f"Adding transformer {transformer_class.__name__}")
    setattr(current, transformer_class.__name__, transformer_class)


# NOTE: transformers pass all kwargs to superclass to allow it to show
#       the (additional) user-defined arguments when calling __repr__.


class split(Transformer):
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




class cat(Transformer):
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

        for item in super().__call__(row, i):
            yield item




class cat_format(Transformer):
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


class rowIndex(Transformer):
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



class map(Transformer):
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

        for item in super().__call__(row, i):
            yield item


class translate(Transformer):
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

        for e, edge, node, rev_rel in self.map(row, i):
            yield e, edge, node, rev_rel

class string(Transformer):
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

        for item in super().__call__(row, i):
            yield item

class replace(Transformer):
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
                logger.debug(
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


class boolean(Transformer):
    """A transformer that can map any set of values onto a boolean pair.

    It considers a set of truth values, along with a set of falsehood values,
    and then set the node ID to the user's true or false value.

    If no configuration is given for ``consider_true`` and ``consider_false``,
    OntoWeaver will use Python's `bool(value)`` to assert the truth of the value
    passed from the cell.

    If ``output_true`` or ``output_false`` are omitted, they will default to "True"
    and "False".

    For instance:

        - boolean:
            column: my_column
            via_relation: my_relation
            consider_true:
                - Y
                - Yes
                - yes
            output_true: my_truth
            consider_false:
                - N
                - No
                - no
            output_false: my_falsehood

    Is equivalent to:
        if value in ["Y", "Yes", "yes"]:
            yield "my_truth"
        if value in ["N", "No", no"]:
            yield "my_falsehood"
    """

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, output_true = "True", output_false = "False", consider_true = None, consider_false = None):
            if (not consider_true and consider_false) or (consider_true and not consider_false):
                msg = f"I can only handle both `consider_true` and `consider_false` being `None` at the same time. But here, one of them is `None` and the other is not."
                logger.error(msg)
                raise exceptions.TransformerConfigError(msg)

            elif consider_true and consider_false:
                if type(consider_true) != list or type(consider_false) != list:
                    msg = "I can only consider both `consider_true` and `consider_false` being lists."
                    logger.error(msg)
                    raise exceptions.TransformerConfigError(msg)

                if len(consider_true) == 0 or len(consider_false) == 0:
                    msg = "I need both `consider_true` and `consider_false` to contain at least one value."
                    logger.error(msg)
                    raise TransformerConfigError(msg)

                common = set(consider_true) & set(consider_false)
                if common:
                   msg = f"There are values that are common to both `consider_true` and `consider_false`: {common}, this makes no sense."
                   logger.error(msg)
                   raise exceptions.TransformerConfigError(msg)

            if output_true == output_false:
                msg = "Both `output_true` and `output_false` are the same value, this makes no sense."
                logger.error(msg)
                raise excceptions.TransformerConfigError(msg)

            if not output_true or not output_false:
                msg = "I need both `output_true` and `ooutput_false` to have some value."
                logger.error(msg)
                raise exceptions.TransformerConfigError(msg)

            self.output_true = output_true
            self.output_false = output_false
            self.consider_false = consider_false
            self.consider_true = consider_true

            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                value = row[key]
                if not self.consider_true and not self.consider_false:
                    # Let Python do it.
                    boo = bool(value)
                else:
                    if value in self.consider_true:
                        boo = True
                    elif value in self.consider_false:
                        boo = False
                    else:
                        logger.error(f"Value `{value}` is not found in either `consider_true` or `consider_false`. I will bypass columns {columns} at row {i}.")
                        continue

                if boo:
                    out = self.output_true
                else:
                    out = self.output_false

                logger.debug(f"Made a boolean from `{value}` to `{out}`.")
                yield out

    def __init__(self,  properties_of, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, output_true = "True", output_false = "False", consider_true = None, consider_false = None, **kwargs):

        self.value_maker = self.ValueMaker(raise_errors=raise_errors, output_true = output_true, output_false = output_false, consider_true = consider_true, consider_false = consider_false)

        super().__init__(properties_of, self.value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)

