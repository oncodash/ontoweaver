""" The module that stores all the default transformers and the register functions.
"""
from __future__ import division

import re
import sys
import math
import json
import copy
import inspect
import logging
import pathlib
import operator
import importlib
import collections
from abc import abstractmethod

from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)

import numpy as np
import pandas as pd
import pandera.pandas as pa


from . import errormanager
from. import exceptions
from . import validate
from . import make_value
from . import make_labels
from . import base
from . import loader

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
    logging.debug(f"Adding transformer {transformer_class.__name__}")
    setattr(current, transformer_class.__name__, transformer_class)


# NOTE: transformers pass all kwargs to superclass to allow it to show
#       the (additional) user-defined arguments when calling __repr__.


def import_from_path(file_path):
    """Import the given Python file path as a module."""
    # See https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    module_name = pathlib.Path(file_path).stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def register_all(module_path):
    for mpath in module_path:
        logger.info(f"Look for transformers in `{mpath}`")
        mod = import_from_path(mpath)
        for name,cls in mod.__dict__.items():
            if inspect.isclass(cls):
                logger.debug(f"{cls}")
                if issubclass(cls, base.Transformer):
                    logger.info(f"    Register transformer: `{cls}`")
                    register(cls)


class map(base.Transformer):
    """Transformer subclass used for the simple mapping of cell values of defined columns and creating
    nodes with their respective values as id."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                if key not in row:
                    self.log_missing_key(key, row)
                else:
                    yield row[key]

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
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

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

        if not self.columns:
            self.error(f"No column declared for the `{type(self).__name__}` transformer, did you forgot to add a `columns` keyword?", section="map.call", exception = exceptions.TransformerInputError)


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
        for item in super().__call__(row, i):
            yield item


class split(base.Transformer):
    """Transformer subclass used to split cell values at defined separator and label_maker nodes with
    their respective values as id."""

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, separator: str = None):
            if not separator:
                separator = r'\s'
            self.separator = re.compile(separator)
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                if key not in row:
                    self.log_missing_key(key, row)
                    continue

                val = row[key]
                if isinstance(val, str):
                    items = re.split(
                        pattern = self.separator,
                        string = val
                    )
                    logger.debug(f"re.split('{self.separator}', '{val}') == {items}")
                    assert type(items) is list
                    for item in items:
                        yield item.strip() # Remove leading and trailing whitespace

                elif not base.is_not_null(val):
                    logger.debug(f"Value is null, I'll let my caller skip it.")
                    yield val  # Will be passed by super.__call__

                else:
                    try:  # Try generic access.
                        logger.debug(f"Tries to iterate on: {val}")
                        for item in val:
                            yield item
                    except Exception as e:
                        self.error(f"Cannot skip or iterate over {type(val)}: `{val}`. {e}",
                            "transformer.split",
                            exception = exceptions.TransformerDataError)

    def __init__(self,
        properties_of,
        label_maker = None,
        branching_properties = None,
        columns=None,
        output_validator: validate.OutputValidator = None,
        multi_type_dict = None,
        raise_errors = True,
        separator = None,
        **kwargs
    ):
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

        assert columns, "I need at least 1 column to operate."
        assert isinstance(columns, list), "I need at least 1 column to operate."
        assert len(columns) >= 1, "I need at least 1 column to operate."

        self.separator = separator

        self.value_maker = self.ValueMaker(raise_errors=raise_errors, separator=self.separator)

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict = multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )


class cat(base.Transformer):
    """Transformer subclass used to concatenate cell values of defined columns and label_maker nodes with
    their respective values as id."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            formatted_items = ""
            for key in columns:
                if key not in row:
                    self.log_missing_key(key, row)
                    continue
                formatted_items += str(row[key])

            yield formatted_items

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
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

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

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
            self.error(f"No column declared for the {type(self).__name__} transformer, did you forgot to add a `columns` keyword?", section=f"{type(self).__name__}.call", exception = exceptions.TransformerInputError)

        for item in super().__call__(row, i):
            yield item


class cat_format(base.Transformer):
    """Transformer subclass used to concatenate cell values of defined columns and label_maker nodes with
    their respective values as id."""

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, format_string: str = None):
            self.format_string = format_string
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            try:
                formatted_string = self.format_string.format_map(row)
            except KeyError as err:
                self.error(f"{err}, available keys:\n{row}",
                    exception = exceptions.TransformerConfigError,
                    index = i,
                    section = "cat_format"
                )

            yield formatted_string

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            format_string = None,
             **kwargs
         ):
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

        self.value_maker = self.ValueMaker(
            raise_errors=raise_errors,
            format_string=format_string
        )

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

        if not format_string:  # Neither empty string nor None.
            self.error(f"The `format_string` parameter of the `{type(self).__name__}` transformer cannot be an empty string.")



class rowIndex(base.Transformer):
    """Transformer subclass used for the simple mapping of nodes with row index values as id."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            yield i

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
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

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )


class nested(base.Transformer):
    """Transformer subclass used for accessing a value within
       nested dictionaries or dataframes."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, keys, dic, i):
            value = self.nested(keys, dic, i)
            if value:
                return [value]
            else:
                return []

        def nested(self, keys, dic, i, depth = " "):
            depth += "| "
            logger.debug(f"{depth}Received: {type(dic)}{keys}:\n{dic}")

            if dic is None:
                return None

            if isinstance(dic, str) and not keys:
                # Break recursivity.
                logger.debug(f"{depth}Ended with: `{dic}`")
                return dic

            if not isinstance(keys, str):
                logger.debug(f"{depth}I can iterate over keys")
                if isinstance(dic, str):
                    if ':' in dic and '{' in dic and '}' in dic:
                        # Probably a Python/JSON dictionary.
                        logger.debug(f"{depth}I'm parsing a JSON dictionary string.")
                        dic = json.loads(dic)
                        logger.debug(f"{depth}{dic}")
                    assert not isinstance(dic, str)

                # Consider it an object with bracket access, we just pass it.
                if isinstance(dic, np.ndarray):
                    if dic.shape == (0,):
                        return None
                    else:
                        return self.nested( keys[1:], dic[keys[0]], i, depth )

                elif keys[0] not in dic:
                    if isinstance(dic, dict):
                        available_keys = ', '.join(dic.keys())
                    elif isinstance(dic, pd.DataFrame):
                        available_keys = ', '.join(dic.columns)
                    else:
                        available_keys = f"[unknown object type `{type(dic)}`, I cannot read its keys or it does not have ones]"

                    msg = f"Key '{keys[0]}' not found in data, I can only see keys: {available_keys}."
                    msg += f" Object repr: {dic}."
                    self.error(msg, section="nested.call",
                               exception=exceptions.TransformerDataError)
                else:
                    # Recursive call until exhaustion.
                    logger.debug(f"{depth}Get: {type(dic)}[{keys[0]}]")
                    return self.nested( keys[1:], dic[keys[0]], i, depth )

    def __init__(self,
        properties_of,
        label_maker = None,
        branching_properties = None,
        columns=None,
        output_validator: validate.OutputValidator = None,
        multi_type_dict = None,
        raise_errors = True,
        **kwargs
    ):

        assert columns, "I need at least 1 key to operate."
        assert isinstance(columns, list), "I need at least 1 key to operate."
        assert len(columns) >= 1, "I need at least 1 key to operate."

        self.value_maker = self.ValueMaker(raise_errors=raise_errors)
        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

        self.keys = columns
        logger.debug(f"keys: {self.keys}")
        if not self.keys:
            self.error(f"No key declared for the `{type(self).__name__}` transformer, did you forgot to add a `keys` keyword?", section="nested.call", exception = exceptions.TransformerInputError)

    def __call__(self, row, i):
        for item in super().__call__(row, i):
            yield item


class split_nested(base.Transformer):

    def __init__(self,
        properties_of,
        label_maker = None,
        branching_properties = None,
        columns=None,
        output_validator: validate.OutputValidator = None,
        multi_type_dict = None,
        raise_errors = True,
        separator = None,
        **kwargs
    ):
        """
        FIXME doc
        """

        logger.debug(f"COLUMNS: {type(columns)}\n{columns}")
        assert columns, "I need 2 keys to operate."
        assert isinstance(columns, list), "I need several keys."
        assert len(columns) >= 2, "I need 2 keys, or you should use either split or nested."

        self.split = split(
            properties_of,
            label_maker,
            branching_properties,
            [columns[0]],
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            separator = separator,
            **kwargs,
        )

        keys = columns[1:]
        if not isinstance(keys, list):
            keys = [keys]

        self.nested = nested(
            properties_of,
            label_maker,
            branching_properties,
            keys,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs,
        )

        super().__init__(properties_of,
            self.split.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

    def __call__(self, row, i):
        for rowval in self.split.value_maker(self.split.columns, row, i):
            val = self.nested.value_maker(self.nested.keys, rowval, i)

            value, edge_type, node_type, reverse_edge = self.create(val, row)
            if base.is_not_null(value):
                yield value, edge_type, node_type, reverse_edge


class capitalize(map):
    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs,
        with first letter in uppercase.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The capitalized cell value if valid.

        Raises:
            Warning: If the cell value is invalid.
        """
        for item in super().__call__(row, i):
            value, edge_type, node_type, reverse_edge = item
            val = " ".join(w.capitalize() for w in value.split(" "))
            yield val, edge_type, node_type, reverse_edge


class lower(map):
    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs,
        with all letters in lowercase.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The capitalized cell value if valid.

        Raises:
            Warning: If the cell value is invalid.
        """
        for item in super().__call__(row, i):
            value, edge_type, node_type, reverse_edge = item
            val = " ".join(w.lower() for w in value.split(" "))
            yield val, edge_type, node_type, reverse_edge


class upper(map):
    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs,
        with all letters in uppercase.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The capitalized cell value if valid.

        Raises:
            Warning: If the cell value is invalid.
        """
        for item in super().__call__(row, i):
            value, edge_type, node_type, reverse_edge = item
            val = " ".join(w.upper() for w in value.split(" "))
            yield val, edge_type, node_type, reverse_edge


class lower_capitalize(map):
    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs,
        with first letter in uppercase, and all others in lowercase.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The capitalized cell value if valid.

        Raises:
            Warning: If the cell value is invalid.
        """
        for item in super().__call__(row, i):
            value, edge_type, node_type, reverse_edge = item
            val = " ".join(w.lower().capitalize() for w in value.split(" "))
            yield val, edge_type, node_type, reverse_edge


class translate(base.Transformer):
    """Translate the targeted cell value using a tabular mapping and yield a node with using the translated ID."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, translate, translate_from, translate_to, on_unknown_value, raise_errors: bool = True):
            self.translate = translate
            self.translate_from = translate_from
            self.translate_to = translate_to
            self.on_unknown_value = on_unknown_value
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            for key in columns:
                if key not in row:
                    self.log_missing_key(key, row)
                    continue
                cell = row[key]
                if cell in self.translate:
                    yield self.translate[cell]
                else:
                    if self.on_unknown_value == "skip":
                        continue
                    elif self.on_unknown_value == "keep":
                        yield cell
                    else:
                        assert self.on_unknown_value == "error"
                        self.error(f"The cell value `{cell}` at column `{key}`" \
                            f" is not found in the translation table" \
                            f" (`{self.translate_from}` => `{self.translate_to}`)" \
                            f" I'll skip this value.",
                            exception = exceptions.TransformerDataError
                        )


    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
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
            kwargs: Additional arguments to pass to a Loader function (e.g. if you want to load TSVs, "sep=TAB", reads the translations_file as tab-separated).
        """

        self.map = map(properties_of, label_maker, branching_properties, columns, output_validator, multi_type_dict, **kwargs)

        lpf = loader.LoadPandasFile()
        lpd = loader.LoadPandasDataframe()
        lrf = loader.LoadOWLFile()
        lrg = loader.LoadOWLGraph()

        # Since we cannot expand kwargs, let's recover what we have inside.
        self.translations = kwargs.get("translations", None)
        self.translations_file = kwargs.get("translations_file", None)
        self.translate_from = kwargs.get("translate_from", None)
        self.translate_to = kwargs.get("translate_to", None)

        if "on_unknown_value" not in kwargs:
            if self.translations_file:
                msg = "You did not specify how a translate transformer" \
                    f" (`{self.translate_from}` => `{self.translate_to}`) should" \
                    " handle values that are not in translate tables." \
                    " The default is to `on_unknown_value: skip` them."
            else:
                msg = "You did not specify how a manual translate transformer should" \
                    " handle values that are not in translate tables." \
                    " The default is to `on_unknown_value: skip` them."
            logger.warning(msg)

        self.on_unknown_value = kwargs.get("on_unknown_value", "skip")
        behaviors = ["skip", "keep", "error"]
        if self.on_unknown_value not in behaviors:
            self.error(
                f"Option `on_unknown_value` cannot be `{self.on_unknown_value}`," \
                f" possible values are: {', '.join(behaviors)}",
                exception = exceptions.TransformerConfigError
            )

        if self.translations and self.translations_file:
            self.error(f"Cannot have both `translations` (=`{self.translations}`) and `translations_file` (=`{self.translations_file}`) defined in a {type(self).__name__} transformer.", section="translate", exception = exceptions.TransformerInterfaceError)

        if self.translations:
            self.translate = self.translations
            logger.debug(f"\t\t\tManual translations: `{self.translate}`")
        elif self.translations_file:
            logger.debug(f"\t\t\tGet translations from file: `{self.translations_file}`")
            if not self.translate_from:
                self.error(f"No translation source column declared for the `{type(self).__name__}` transformer using translations_file=`{self.translations_file}`, did you forget to add a `translate_from` keyword?", section="translate.init", exception = exceptions.TransformerInterfaceError)
            if not self.translate_to:
                self.error(f"No translation target column declared for the `{type(self).__name__}` transformer using translations_file=`{self.translations_file}`, did you forget to add a `translate_to` keyword?", section="translate.init", exception = exceptions.TransformerInterfaceError)
            else:
                # self.translations_file = translations_file
                # self.translate_from = translate_from
                # self.translate_to = translate_to

                # Possible arguments from the `translate` section.
                mapping_args = ["translations", "translations_file", "translate_from", "translate_to", "on_unknown_value"]
                # Possible Python attributes.
                mapping_args += ["subclass"]
                # Discard match
                mapping_args += ["match"]
                # All possible arguments found in a YAML mapping.
                for attr in dir(base.MappingParser):
                    if re.match("^k_", attr):
                        mapping_args += getattr(base.MappingParser, attr)

                # Keep only the user-passed arguments that are not in possible YAML keywords.
                more_args = {k:v for k,v in kwargs.items() if k not in mapping_args}
                if "sep" in more_args:
                    if more_args['sep'] == 'TAB': # FIXME why the fuck is this changed somehow?
                        more_args['sep'] = '\t'

                logger.debug(f"\t\t\tAdditional user-passed arguments for the load function: {more_args}")

                self.df = pd.DataFrame()
                for with_loader in [lpf, lpd, lrf, lrg]:
                    if with_loader.allows([self.translations_file]):
                        logger.debug(f"\t\t\tUsing loader: {type(with_loader).__name__}")
                        try:
                            self.df = with_loader.load([self.translations_file], **more_args)
                        except exceptions.InputDataError as err:
                            logging.error(f"I cannot load the translations_file `{self.translations_file}`. Maybe you forgot that the path is the one from the working directory?")
                            raise err
                        break

                if self.df.empty:
                    self.error(f"I was not able to load a valid translations_file from: `{self.translations_file}`")

                logger.debug(f"Loaded a DataFrame: {self.df}")

                if self.translate_from not in self.df.columns:
                    self.error(f"Source column `{self.translate_from}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = exceptions.TransformerDataError)

                if self.translate_to not in self.df.columns:
                    self.error(f"Target column `{self.translate_to}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = exceptions.TransformerDataError)

                self.translate = {}
                for i,row in self.df.iterrows():
                    frm = row[self.translate_from]
                    to = row[self.translate_to]
                    if frm in self.translate and self.translate[frm] != to:
                        logger.warning(f"The key `{frm}` already exists in the translation table, and translated to `{self.translate[frm]}`. It now translates to `{to}`. You may want to avoid such duplicates in translation tables.")
                    if frm and to:
                        self.translate[frm] = to
                    else:
                        logger.warning(f"Cannot translate frm `{self.translate_from}` to `{self.translate_to}`, invalid translations values at row {i} of file `{self.translations_file}`: `{frm}` => `{to}`. I will ignore this translation.")

        else:
            self.error(f"When using a {type(self).__name__} transformer, you must define either `translations` or `translations_file`.", section="translate.init", exception = exceptions.TransformerInterfaceError)


        if not self.translate:
            self.error("No translation found, did you forget the `translations` keyword?", section="translate.init", exception = exceptions.TransformerInterfaceError)

        self.value_maker = self.ValueMaker(
            self.translate,
            self.translate_from,
            self.translate_to,
            self.on_unknown_value,
            raise_errors=raise_errors
        )

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

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

        for item in super().__call__(row, i):
            yield item


class string(base.Transformer):
    """A transformer that makes up the given static string instead of extractsing something from the table."""

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True, string: str = None):
            self.string = string
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            yield self.string

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
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

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

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


class replace(base.Transformer):
    """Transformer subclass used to remove characters that are not allowed from cell values of defined columns.
     The forbidden characters are defined by a regular expression pattern, and are substituted with a user-defined
     character or removed entirely. In case the cell value is made up of only forbidden characters, the node is not
     created and a warning is logged."""

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, forbidden, substitute, raise_errors: bool = True):

            assert type(forbidden) is str
            logger.debug(f"forbidden: {forbidden}")
            self.forbidden = re.compile(forbidden)

            assert type(substitute) is str
            logger.debug(f"substitute: {substitute}")
            self.substitute = substitute

            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                if key not in row:
                    self.log_missing_key(key, row)
                    continue

                if not base.is_not_null(row[key]):
                    yield row[key]
                else:
                    logger.debug(
                        f"re.sub('{self.forbidden}', '{self.substitute}', '{row[key]}')")
                    formatted = re.sub(self.forbidden, self.substitute, row[key])

                    strip_formatted = formatted.strip()
                    logger.debug(f"Replaced result: `{strip_formatted}`")
                    yield strip_formatted

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
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
        # By default, allow alphanumeric characters (A-Z, a-z, 0-9),
        # underscore (_), backtick (`), dot (.), and parentheses ().
        self.forbidden = kwargs.get("forbidden", r'[^a-zA-Z0-9_`.()]') # i.e. replace anything that's not those...
        self.substitute = kwargs.get("substitute", "") # by nothing.

        self.value_maker = self.ValueMaker(forbidden=self.forbidden, substitute=self.substitute, raise_errors=raise_errors)

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )


class boolean(base.Transformer):
    """A transformer that can map any set of values onto a boolean pair.

    It considers a set of truth values, along with a set of falsehood values,
    and then set the node ID to the user's true or false value.

    If no configuration is given for ``consider_true`` and ``consider_false``,
    OntoWeaver will use Python's `bool(value)`` to assert the truth of the value
    passed from the cell.

    If ``output_true`` or ``output_false`` are omitted, they will default to "True"
    and "False".

    For instance:

    .. code:: yaml

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

    .. code:: python

        if value in ["Y", "Yes", "yes"]:
            yield "my_truth"
        if value in ["N", "No", no"]:
            yield "my_falsehood"

    """

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, output_true = "true", output_false = "false", consider_true = None, consider_false = None):
            if (not consider_true and consider_false) or (consider_true and not consider_false):
                msg = "I can only handle both `consider_true` and `consider_false` being `None` at the same time. But here, one of them is `None` and the other is not."
                logger.error(msg)
                raise exceptions.TransformerConfigError(msg)

            elif consider_true and consider_false:
                if not isinstance(consider_true, list) or not isinstance(consider_false, list):
                    msg = "I can only consider both `consider_true` and `consider_false` being lists."
                    logger.error(msg)
                    raise exceptions.TransformerConfigError(msg)

                if len(consider_true) == 0 or len(consider_false) == 0:
                    msg = "I need both `consider_true` and `consider_false` to contain at least one value."
                    logger.error(msg)
                    raise exceptions.TransformerConfigError(msg)

                common = set(consider_true) & set(consider_false)
                if common:
                   msg = f"There are values that are common to both `consider_true` and `consider_false`: {common}, this makes no sense."
                   logger.error(msg)
                   raise exceptions.TransformerConfigError(msg)

            if output_true == output_false:
                msg = "Both `output_true` and `output_false` are the same value, this makes no sense."
                logger.error(msg)
                raise exceptions.TransformerConfigError(msg)

            if output_true is None or output_false is None:
                msg = "I need both `output_true` and `output_false` to have some value."
                logger.error(msg)
                raise exceptions.TransformerConfigError(msg)

            self.output_true = output_true
            self.output_false = output_false
            self.consider_false = consider_false
            self.consider_true = consider_true

            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                if key not in row:
                    self.log_missing_key(key, row)
                    continue
                value = row[key]
                if value is None:
                    continue
                if pd.isnull(value):
                    continue
                value = str(value)

                if value in self.consider_true:
                    boo = True
                elif value in self.consider_false:
                    boo = False
                else:
                    logger.error(f"Value `{value}` is not found in either `consider_true` (`{'`, `'.join(self.consider_true)}`) or `consider_false` (`{'`, `'.join(self.consider_false)}`). I will bypass columns {columns} at row {i}.")
                    continue

                if boo:
                    out = self.output_true
                else:
                    out = self.output_false

                logger.debug(f"Made a boolean from `{value}` to `{out}`.")
                yield out

    def __init__(self,
             properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            output_true = "true",
            output_false = "false",
            consider_true = None,
            consider_false = None,
            **kwargs
        ):

        self.value_maker = self.ValueMaker(
            raise_errors=raise_errors,
            output_true    = output_true,
            output_false   = output_false,
            consider_true  = [str(i) for i in consider_true],
            consider_false = [str(i) for i in consider_false],
        )

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )


class split_translate(base.Transformer):

    def __init__(self,
        properties_of,
        label_maker = None,
        branching_properties = None,
        columns=None,
        output_validator: validate.OutputValidator = None,
        multi_type_dict = None,
        raise_errors = True,
        separator = None,
        **kwargs
    ):
        """
        FIXME doc
        """

        self.split = split(
            properties_of,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            separator = separator,
            **kwargs,
        )

        self.translate = translate(
            properties_of,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs,
        )

        super().__init__(properties_of,
            self.split.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

    def __call__(self, row, i):

        for value in self.split.value_maker(self.split.columns, row, i):
            if base.is_not_null(value):
                logging.debug(f"VALUE {value}")
                pseudorow = {"translate_column": value}
                for val in self.translate.value_maker(["translate_column"], pseudorow, i):
                    logging.debug(f"VAL {val}")
                    value, edge_type, node_type, reverse_edge = self.create(val, row)
                    yield value, edge_type, node_type, reverse_edge


class split_replace(base.Transformer):

    def __init__(self,
        properties_of,
        label_maker = None,
        branching_properties = None,
        columns=None,
        output_validator: validate.OutputValidator = None,
        multi_type_dict = None,
        raise_errors = True,
        separator = None,
        **kwargs
    ):
        """
        FIXME doc
        """

        self.split = split(
            properties_of,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            separator = separator,
            **kwargs,
        )

        self.replace = replace(
            properties_of,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs,
        )

        super().__init__(properties_of,
            self.split.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

    def __call__(self, row, i):

        for value in self.split.value_maker(self.split.columns, row, i):
            if base.is_not_null(value):
                pseudorow = {"replace_column": value}
                for val in self.replace.value_maker(["replace_column"], pseudorow, i):
                    value, edge_type, node_type, reverse_edge = self.create(val, row)
                    yield value, edge_type, node_type, reverse_edge


class NumericStringParser(object):
    '''
    Most of this code comes from the fourFn.py pyparsing example

    '''

    def pushFirst(self, strg, loc, toks):
        self.exprStack.append(toks[0])

    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(e + Word("+-" + nums, nums)))
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                 (ident + lpar + expr + rpar | pi | e | fnumber).setParseAction(self.pushFirst))
                | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
                ).setParseAction(self.pushUMinus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + \
            ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + \
            ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + \
            ZeroOrMore((addop + term).setParseAction(self.pushFirst))
        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {"+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.truediv,
                    "^": operator.pow}
        self.fn = {"sin": math.sin,
                   "cos": math.cos,
                   "tan": math.tan,
                   "exp": math.exp,
                   "abs": abs,
                   "trunc": lambda a: int(a),
                   "round": round,
                   "sgn": lambda a: abs(a) > epsilon and cmp(a, 0) or 0}

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack(s)
        if op in "+-*/^":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluateStack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parseAll=True):
        self.exprStack = []
        results = self.bnf.parseString(num_string, parseAll)
        val = self.evaluateStack(self.exprStack[:])
        return val


class maths(base.Transformer):

    class ValueMaker(make_value.ValueMaker):

        def __init__(self,
            raise_errors: bool = True,
            operation: str = None,
            nsp = NumericStringParser()
        ):
            self.operation = operation
            self.nsp = nsp
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            try:
                eq = self.operation.format_map(row)
                result = self.nsp.eval(eq)
            except KeyError as err:
                self.error(f"{err}, available keys:\n{row}",
                    exception = exceptions.TransformerConfigError,
                    index = i,
                    section = "maths"
                )
            except Exception as err:
                self.error(f"{err}, while evaluating operation: {eq}",
                    exception = exceptions.TransformerDataError,
                    index = i,
                    section = "maths"
                )

            yield result

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            operation = None,
             **kwargs
         ):
        """
        Initialize the math transformer.

        Args:.
            target_element_properties: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            operation: A format string assembling the column names in an arithmetic operation.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
        """

        self.value_maker = self.ValueMaker(
            raise_errors=raise_errors,
            operation=operation
        )

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

        if not operation:  # Neither empty string nor None.
            self.error(f"The `operation` parameter of the `{type(self).__name__}` transformer cannot be an empty string.")



class western_name(base.Transformer):
    """Transformer """

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

            # Known naming schemes:
            NAME = r"([A-ZÀ-ÖØ-Ÿ][A-ZÀ-ÖØ-Ÿʼ']*(?=[\-ʼ'][A-ZÀ-ÖØ-Ÿ])(?:[\-ʼ'][A-ZÀ-ÖØ-Ÿ]*)*)"
            Name = r"([A-ZÀ-ÖØ-Ÿ][a-zØ-öø-ÿʼ']*(?=[\-ʼ'][A-ZÀ-ÖØ-Ÿ])*(?:[\-ʼ'][A-ZÀ-ÖØ][a-zØ-öø-ÿ]*)*)"
            # NAME  = r"([A-ZÀ-ÖØ-Ÿ][A-ZÀ-ÖØ-Ÿʼ']+(?=-[A-ZÀ-ÖØ-Ÿ])(?:-[A-ZÀ-ÖØ-Ÿ]*)*)"
            # Name  = r"([A-ZÀ-ÖØ-Ÿ][a-zØ-öø-ÿʼ']+(?=-[A-ZÀ-ÖØ-Ÿ])*(?:-[A-ZÀ-ÖØ][a-zØ-öø-ÿ]*)*)"

            NAMES = r"([A-ZÀ-ÖØ-Ÿ][A-ZÀ-ÖØ-Ÿʼ']*(?=[\s\-ʼ'][A-ZÀ-ÖØ-Ÿ])*(?:[\s\-ʼ'][A-ZÀ-ÖØ-Ÿ]*)*)"
            Names = r"([A-ZÀ-ÖØ-Ÿ][a-zØ-öø-ÿʼ']*(?=[\s\-ʼ'][A-ZÀ-ÖØ-Ÿ])*(?:[\s\-ʼ'][A-ZÀ-ÖØ-Ÿ][a-zØ-öø-ÿ\-ʼ']*)*)"

            whatev = r"([A-ZÀ-ÖØ-Ÿa-zØ-öø-ÿʼ'\-\s\.]+)"
            I = r"([A-ZÀ-ÖØ-Ÿ]\.)"
            Is = r"([A-ZÀ-ÖØ-Ÿ]\.(?=\s[A-ZÀ-ÖØ-Ÿ]\.)(?:\s[A-ZÀ-ÖØ-Ÿ]\.)+)"
            particle = r"([a-zØ-öø-ÿʼ']+)"
            s = r"\s+"

            # The order with which we search matters.
            self.patterns = collections.OrderedDict()

            # Canonical forms.
            self.patterns["lasts_comma_firsts"] = (whatev + r",\s*" + whatev, [0], [1])

            # With onomastic particle
            self.patterns["Firsts_particle_LASTs"] = (Names+s + particle+s + NAMES, [1,2], [0])
            self.patterns["Firsts_particle_Lasts"] = (Names+s + particle+s + Names, [1,2], [0])
            self.patterns["particle_Lasts_comma_Firsts"] = (particle+s + Names + r',\s*' + Names, [0,1], [2])
            self.patterns["particle_LASTs_comma_Firsts"] = (particle+s + NAMES + r',\s*' + Names, [0,1], [2])

            # With 1 initials
            self.patterns["Firsts_I_LASTs"] = (Names + s + I+s + NAMES, [2], [0,1])
            self.patterns["Firsts_I_Lasts"] = (Names + s + I+s + Names, [2], [0,1])
            self.patterns["LASTs_Firsts_I"] = (NAMES + s + Names + s + I, [0], [1,2])
            self.patterns["Lasts_Firsts_I"] = (Names + s + Names + s + I, [0], [1,2])

            # With 2 initials
            self.patterns["Firsts_II_LASTS"] = (Names + s + I+s + I+s + NAMES, [3], [0,1,2])
            self.patterns["Firsts_II_Lasts"] = (Names + s + I+s + I+s + Names, [3], [0,1,2,])
            self.patterns["LASTs_Firsts_II"] = (NAMES + s + Names + s + I+s + I, [0], [1,2,3])
            self.patterns["Last_First_II"] = (Name + s + Name + s + I+s + I, [0], [1,2,3])

            # With 3 initials
            self.patterns["Firsts_III_LASTS"] = (Names + s + I+s + I+s + I+s + NAMES, [4], [0,1,2,3])
            self.patterns["Firsts_III_Lasts"] = (Names + s + I+s + I+s + I+s + Names, [4], [0,1,2,3])
            self.patterns["LASTS_Firsts_III"] = (NAMES + s + Names + s + I+s + I+s + I, [0], [1,2,3,4])
            self.patterns["Last_First_III"] = (Name + s + Name + s + I+s + I+s + I, [0], [1,2,3,4])

            # Only 1 initials
            self.patterns["I_First_Last"] = (I+s + Name+s + Name, [2], [0,1])

            self.patterns["I_LASTS"] = (I+s + NAMES, [1], [0])
            self.patterns["I_Lasts"] = (I+s + Names, [1], [0])
            self.patterns["LASTS_I"] = (NAMES + s + I, [0], [1])
            self.patterns["Lasts_I"] = (Names + s + I, [0], [1])

            # 2 initials around
            self.patterns["I_Firsts_I_Lasts"] = (I+s + Names+s +I+s + Names, [3], [0,1,2])
            self.patterns["I_Firsts_I_LASTS"] = (I+s + Names+s +I+s + NAMES, [3], [0,1,2])
            self.patterns["Lasts_I_Firsts_I"] = (Names+s + I+s + Names+s +I, [0], [1,2,3])
            self.patterns["LASTS_I_Firsts_I"] = (NAMES+s + I+s + Names+s +I, [0], [1,2,3])

            # Only 2 initials
            self.patterns["II_LASTS"] = (I+s + I+s + NAMES,   [2], [0,1])
            self.patterns["II_Lasts"] = (I+s + I+s + Names,   [2], [0,1])
            self.patterns["LASTS_II"] = (NAMES + s + I+s + I, [0], [1,2])
            self.patterns["Lasts_II"] = (Names + s + I+s + I, [0], [1,2])

            # Only 3 initials
            self.patterns["III_LASTS"] = (I+s + I+s + I+s + NAMES, [3], [0,1,2])
            self.patterns["III_Lasts"] = (I+s + I+s + I+s + Names, [3], [0,1,2])
            self.patterns["LASTS_III"] = (NAMES + s + I+s + I+s + I, [0], [1,2,3])
            self.patterns["Lasts_III"] = (Names + s + I+s + I+s + I, [0], [1,2,3])

            # With 1 other name
            self.patterns["First_Name_LAST"] = (Name + s + Name+s + NAME, [2], [0,1])
            self.patterns["LAST_First_Name"] = (NAME + s + Name+s + Name, [0], [1,2])

            # With 2 other names
            self.patterns["First_Name_Name_LASTS"] = (Name + s + Name+s + Name+s + NAMES, [3], [0,1,2])
            self.patterns["LASTS_First_Name_Name"] = (NAMES + s + Name+s + Name+s + Name, [0], [1,2,3])

            # With 3 other names
            self.patterns["First_Name_Name_Name_LASTS"] = (Name + s + Name+s + Name+s + Name+s + NAMES, [4], [0,1,2,3])
            self.patterns["LASTS_First_Names"] = (NAMES + s + Name+s + Names, [0], [1,2])

            # Heuristics, but common enough
            self.patterns["First_Name_Last"] = (Name + s + Name+s + Name, [2], [0,1])
            self.patterns["First_Name_Name_Last"] = (Name + s + Name+s + Name+s + Name, [3], [0,1,2])
            self.patterns["First_Name_Name_Name_Last"] = (Name + s + Name+s + Name+s + Name+s + Name, [4], [0,1,2,3])

            # Without initials or other names
            self.patterns["LASTS_Firsts"] = (NAMES + s + Names, [0], [1])
            self.patterns["Firsts_LASTS"] = (Names + s + NAMES, [1], [0])
            self.patterns["First_Last"] = (Name + s + Name, [1], [0])

            self.patterns["Firsts_particle_whatever"] = (Names+s + particle + whatev, [1,2], [0])

            self.retronyms = [
                r"Junior",
                r"Jr\.",
                r"Jr",  # After the form with the dot.
                r"JR\.",
                r"JR",
                r"Jnr\.",
                r"Jnr",
                r"Senior",
                r"Sr\.",
                r"Sr",
                r"SR\.",
                r"SR",
                r"père",
                r"fils",
                r"I",
                r"II",
                r"III",
                r"Major",
                r"Maior",
                r"Minor",
                r"Primo",
                r"Segundo",
            ]
            self.retronym_tag = r'\b(' + r"|".join(self.retronyms) + r')(\s|,|$)'

            if logger.getEffectiveLevel() <= logging.DEBUG:
                logger.debug("Patterns:")
                for k,p in self.patterns.items():
                    logger.debug(f"├ {k}: '^{p[0]}$'  @ {p[1]}")


        def capitalize(self, sentence):
            # Capitalize uppercase words.
            capitalized = re.sub(
                r"([A-ZÀ-ÖØ]+)",
                lambda m:
                    m.group(0).capitalize(),
                sentence
            )
            # Remove non-canonical space characters and double spaces.
            return " ".join(capitalized.split()).strip()


        def extract(self, pattern, i_last, i_first, value):
            logger.debug(f'''│ echo "{value}" | colout "{pattern}"''')
            m = re.match(pattern, value)
            if m:
                logger.debug(f"│ Matches with {len(m.groups())} groups")
                assert len(m.groups()) == len(i_last)+len(i_first)
                last = " ".join([m.groups()[i] for i in i_last]).strip()
                first = " ".join([m.groups()[i] for i in i_first]).strip()
                assert last
                assert first
                res = f"{last}, {first}"
                res = re.sub(r"' ", "'", res)
                res = re.sub(r"ʼ ", "ʼ", res)
                res = self.capitalize(res)
                logger.debug(f"│ Result: {res}")
                return res
            else:
                return None


        def __call__(self, columns, row, i):
            # First, concatenate columns:
            value = ""
            for key in columns:
                if key not in row:
                    self.log_missing_key(key, row)
                    continue
                else:
                    value += f" {row[key]}"
            value = value.strip()
            logger.debug(f"Call western_name( `{value}` )")

            # Remove the retronym tag.
            # Most of the times, the Jr. tag is put after last names,
            # but we want it as part of the first name, were it belongs,
            # so here we remove it, and will add it back later.
            logger.debug(f"├ Retronym search with: `{self.retronym_tag}`")
            retronym = re.search(self.retronym_tag, value)
            logger.debug(f"│ │ Found: {retronym}")
            if retronym:
                value = re.sub(self.retronym_tag, '', value).strip()
                logger.debug(f"│ ┕ With retronym removed: `{value}`")
                assert not re.search(self.retronym_tag, value)
            else:
                logger.debug(f"│ ┕ No retronym found")

            # logger.debug(f"├ Searching...")
            found = False
            for p in self.patterns:
                logger.debug(f"├ Matching against: {p}")
                pattern, i_last, i_first = self.patterns[p]
                formatted = self.extract(r'^'+pattern+'$', i_last, i_first, value)
                if formatted:
                    logger.debug(f"│ I found a name matching: {p}")
                    logger.debug(f"│ Which is: '^{self.patterns[p]}$'")
                    logger.debug(f"┕ Formatted as: `{formatted}`")
                    found = True
                    if retronym:
                        logger.debug(f"├ Add back the retronym")
                        formatted += f" {retronym.group(0).strip()}"
                        # formatted += f" {' '.join([jr.capitalize() for jr in retronym.groups()])}"
                    yield formatted
                    break
                else:
                    logger.debug(f"│ ┕ Pattern does not match.")
                    continue

            if not found:
                logger.error(f"┕ I could not find a name in the value: `{value}`")


    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
        """
        Constructor.

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

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

class compose(base.Transformer):

    class ValueMaker(make_value.ValueMaker):
        def __init__(self, raise_errors: bool = True):
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            raise NotImplementedError()


    def init_checks(self):
        if not hasattr(self, "call") or type(self.call) is not list or len(self.call) == 0:
            self.error("You must pass a list of transformers in a `call` argument to the `compose` transformer.")

        MP = base.MappingParser
        current = sys.modules[__name__]

        for section in self.call:
            if type(section) is str:
                continue
            if len(section.keys()) > 1:
                self.error(f"There is several transformer names: {' & '.join(section.keys())}, but there should be only one.")

            t_name = list(section.keys())[0]
            if not hasattr(current, t_name):
                self.error(f"I cannot find a transformer named `{t}`, check for spelling error or register this transformer class.")

            # Check that arguments in each transformer's section are not reserved.
            for arg,val in section[t_name].items():
                for attr in dir(MP):
                    if re.match(r"^\s*k_([a-z_]+)", attr):
                        keywords = getattr(MP, attr)
                        for k in keywords:
                            if arg == k:
                                self.error(f"You should not pass the `{k}` argument to transformers within a `compose` transformer. Try passing this in the `compose` section transformer instead.")
                                break


    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
        """
        Constructor.

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

        super().__init__(
            properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )
        self.init_checks()
        self.tag = "ONTOWEAVER"

        def make_transformer(t_section, columns = None):
            if type(t_section) is str:
                t_name = t_section
                t_args = {}
            else:
                t_name = list(t_section.keys())[0]
                t_args = t_section[t_name]

            if not columns:
                columns = [self.tag]

            current = sys.modules[__name__]
            t_class = getattr(current, t_name)
            return t_class(
                    properties_of,
                    label_maker,
                    branching_properties,
                    columns,
                    output_validator,
                    multi_type_dict,
                    raise_errors,
                    **(t_args)
                )

        # Instantiate the list of configured transformers.
        # First transformer gets any columns passed to compose.
        self.transformers = [make_transformer(self.call[0], self.columns)]

        # Others will get a special column name.
        for t in self.call[1:]:
            self.transformers.append(make_transformer(t))

        logger.debug(self.transformers)


    def recursive_call(self, row, i, t_indexes):
        logger.debug("#############################################")
        logger.debug(f"recursive_call({dict(row)}, {i}, {t_indexes})")
        assert len(t_indexes) > 0

        # Since we're altering indices, we need to copy it,
        # or else the reference will affect recursive calls in the stack.
        t_indices = copy.copy(t_indexes)

        transformer = self.transformers[t_indices.pop(0)]

        logger.debug(f"Apply transformer: {transformer} on {dict(row)}")
        for value, edge_type, node_type, reverse_edge in transformer(row, i):
            logger.debug(f"Transformer output value: `{value}`")

            if len(t_indices) == 0:
                logger.debug(f"No more tranformer to apply, yield result: `{value}`")
                yield value, edge_type, node_type, reverse_edge
            else:
                internal_row = {self.tag: value}
                logger.debug(f"Call remaining {len(t_indices)} transformers on : {internal_row}")
                for venr in self.recursive_call(internal_row, i, t_indices):
                    yield venr


    def __call__(self, row, i):
        t_indices = list(range(len(self.transformers)))
        for venr in self.recursive_call(row, i, t_indices):
            yield venr

