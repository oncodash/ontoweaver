import math
import yaml
import logging
import threading

import types as pytypes
import pandas as pd
import pandera as pa

from itertools import chain
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from collections.abc import Iterable
from enum import Enum, EnumMeta

from . import errormanager
from . import base
from . import types
from . import transformer
from . import exceptions
from . import validate
from . import make_labels

logger = logging.getLogger("ontoweaver")

class MetaEnum(EnumMeta):
    """
    Metaclass for Enum to allow checking if an item is in the Enum.
    """

    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class Enumerable(Enum, metaclass=MetaEnum):
    """
    Base class for Enums with MetaEnum metaclass.
    """
    pass


class TypeAffixes(str, Enumerable):
    """
    Enum for type affixes used in ID creation.
    """
    suffix = "suffix"
    prefix = "prefix"
    none = "none"


class PandasAdapter(base.Adapter):
    """Interface for extracting data from a Pandas DataFrame with a simple mapping configuration based on declared types.

    The general idea is that each row of the table is mapped to a source node,
    and some column values are mapped to an edge leading to another node.
    Some other columns may also be mapped to properties of either a node or an edge.

    The class expect a configuration formed by three objects:
        - the type of the source node mapped for each row.
        - a dictionary mapping each column name to the type of the edge (which contains the type of both the source and target node),
        - a dictionary mapping each (node or edge) type to another dictionary listing which column is extracted to which property.

    Note that, when using the `configure` mapping,
    types are created by default in the `ontoweaver.types` module,
    so that you may access the list of all declared types by using:
        - `ontoweaver.types.all.nodes()`,
        - `ontoweaver.types.all.node_fields()`,
        - `ontoweaver.types.all.edges()`,
        - `ontoweaver.types.all.edge_fields()`.
    """

    def __init__(self,
                 df: pd.DataFrame,
                 subject_transformer: base.Transformer,
                 transformers: Iterable[base.Transformer],
                 metadata: Optional[dict] = None,
                 validator: Optional[validate.InputValidator] = None,
                 type_affix: Optional[TypeAffixes] = TypeAffixes.suffix,
                 type_affix_sep: Optional[str] = ":",
                 parallel_mapping: int = 0,
                 raise_errors = True,
                 ):
        """
        Instantiate the adapter.

        Args:
            df (pd.DataFrame): The table containing the input data.
            subject_transformer (base.Transformer): The transformer that maps the subject node.
            transformers (Iterable[base.Transformer]): List of transformer instances that map the data frame to nodes and edges.
            metadata (Optional[dict]): Metadata to be added to all the nodes and edges.
            type_affix (Optional[TypeAffixes]): Where to add a type annotation to the labels (either TypeAffixes.prefix, TypeAffixes.suffix or TypeAffixes.none).
            type_affix_sep (Optional[str]): String used to separate a label from the type annotation (WARNING: double-check that your BioCypher config does not use the same character as a separator).
            parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
            raise_errors (bool): if True, will raise an exception when an error is encountered, else, will log the error and try to proceed.
        """
        super().__init__(raise_errors)

        logger.info("DataFrame info:")
        # logger.info(df.info())
        logger.debug("Columns:")
        for c in df.columns:
            logger.debug(f"\t`{c}`")
        pd.set_option('display.max_rows', 30)
        pd.set_option('display.max_columns', 30)
        pd.set_option('display.width', 150)
        logger.info("\n" + str(df))
        self.df = df

        self.validator = validator

        if not type_affix in TypeAffixes:
            self.error(f"`type_affix`={type_affix} is not one of the allowed values ({[t for t in TypeAffixes]})", exception = exceptions.ConfigError)
        else:
            self.type_affix = type_affix

        self.type_affix_sep = type_affix_sep

        self.subject_transformer = subject_transformer
        self.transformers = transformers
        self.property_transformers = [] # populated at parsing in self.properties.
        self.metadata = metadata
        # logger.debug(self.target_element_properties)
        self.parallel_mapping = parallel_mapping

    # FIXME not used, maybe will come in handy?
    def source_type(self, row):
        """
        Accessor to the row type actually used by `run`.

        You may overload this function if you want
        to make the row type dependent on some column value.

        By default, just return the default row type defined in the constructor,
        without taking the row values into account.

        Args:
            row: The current row of the DataFrame.

        Returns:
            The row type.
        """
        return self.row_type


    def make_id(self, entry_type, entry_name):
        """
        LabelMaker a unique id for the given cell consisting of the entry name and type,
        taking into account affix and separator configuration.

        Args:
            entry_type: The type of the entry.
            entry_name: The name of the entry.

        Returns:
            str: The created ID.

        Raises:
            ValueError: If the ID creation fails.
        """
        assert(type(entry_type) == str)
        if type(entry_name) != str:
            logger.warning(f"Identifier '{entry_name}' (of type '{entry_type}') is not a string, I had to convert it explicitely, check that the related transformer yields a string.")
            entry_name = str(entry_name)

        if self.type_affix == TypeAffixes.prefix:
            id = f'{entry_type}{self.type_affix_sep}{entry_name}'
        elif self.type_affix == TypeAffixes.suffix:
            id = f'{entry_name}{self.type_affix_sep}{entry_type}'
        elif self.type_affix == TypeAffixes.none:
            id = f'{entry_name}'

        if id:
            logger.debug(f"\t\tFormatted ID `{id}` for cell value `{entry_name}` of type: `{entry_type}`")
            return id
        else:
            self.error(f"Failed to format ID for cell value: `{entry_name}` of type: `{entry_type}`", exception = exceptions.DeclarationError)


    def valid(self, val):
        """
        Checks if cell value is valid - not a `nan`.

        Args:
            val: The value to check.

        Returns:
            bool: True if the value is valid, False otherwise.
        """
        if pd.api.types.is_numeric_dtype(type(val)):
            if (math.isnan(val) or val == float("nan")):
                return False
        elif str(val) == "nan":  # Conversion from Pandas' `object` needs to be explicit.
            return False
        return True


    def properties(self, property_dict, row, i, edge_t, node_t, node = False):

        """
        Extract properties of each property category for the given node type.
        If no properties are found, return an empty dictionary.

        Args:
            property_dict: Dictionary of property mappings.
            row: The current row of the DataFrame.
            i: The index of the current row.
            edge_t: The type of the edge of the current transformer.
            node_t: The type of the node of the current transformer.
            node: True if the object created is a node, False otherwise.

        Returns:
            dict: Extracted properties.
        """
        properties = {}

        for prop_transformer, property_name in property_dict.items():
            for property, none_node, none_edge in prop_transformer(row, i):
                if property:
                    properties[property_name] = str(property).replace("'", "`")
                    logger.info(f"                 {prop_transformer} to property `{property_name}` with value `{properties[property_name]}`.")
                else:
                    self.error(f"Failed to extract valid property with {prop_transformer.__repr__()} for {i}th row.", indent=2, exception = exceptions.TransformerDataError)
                    continue

        # If the metadata dictionary is not empty, add the metadata to the property dictionary.
        if self.metadata:
            if node:
                elem = node_t
            else:
                elem = edge_t
            if elem.__name__ in self.metadata:
                for key, value in self.metadata[elem.__name__].items():
                    properties[key] = value

        return properties


    def make_node(self, node_t, id, properties):
        """
        LabelMaker nodes of a certain type.

        Args:
            node_t: The type of the node.
            id: The ID of the node.
            properties: The properties of the node.

        Returns:
            The created node.
        """
        return node_t(id=id, properties=properties)


    def make_edge(self, edge_t, id_target, id_source, properties):
        """
        LabelMaker edges of a certain type.

        Args:
            edge_t: The type of the edge.
            id_target: The ID of the target node.
            id_source: The ID of the source node.
            properties: The properties of the edge.

        Returns:
            The created edge.
        """
        return edge_t(id_source=id_source, id_target=id_target, properties=properties)

    def run(self):
        """Iterate through dataframe in parallel and map cell values according to YAML file, using a list of transformers."""

        # Thread-safe containers with their respective locks
        self._nodes = []
        self._edges = []
        self._errors = []
        self._nodes_lock = threading.Lock()
        self._edges_lock = threading.Lock()
        self._errors_lock = threading.Lock()
        self._row_lock = threading.Lock()
        self._transformations_lock = threading.Lock()
        self._local_nb_nodes_lock = threading.Lock()

        # Function to process a single row and collect operations
        def process_row(row_data):
            i, row = row_data
            local_nodes = []
            local_edges = []
            local_errors = []
            local_rows = 0
            local_transformations = 0
            local_nb_nodes = 0

            logger.debug(f"Process row {i}...")
            local_rows += 1
            # There can be only one subject, so transformers yielding multiple IDs cannot be used.
            logger.debug("\tLabelMaker subject node:")
            subject_generator_list = list(self.subject_transformer(row, i))
            if (len(subject_generator_list) > 1):
                local_errors.append(self.error(f"You cannot use a transformer yielding multiple IDs as a subject. "
                                               f"Subject Transformer `{self.subject_transformer}` produced multiple IDs: "
                                               f"{subject_generator_list}", indent=2, exception = exceptions.TransformerInterfaceError))

            source_id, subject_edge, subject_node = subject_generator_list[0]

            if self.subject_transformer.final_type:
                # If a final_type attribute is present in the transformer, use it as the source node type, instead
                # of the default type.
                subject_node = self.subject_transformer.final_type

            if source_id:
                source_node_id = self.make_id(subject_node.__name__, source_id)

                if source_node_id:
                    logger.debug(f"\t\tDeclared subject ID: {source_node_id}")
                    local_nodes.append(self.make_node(node_t=subject_node, id=source_node_id,
                                                      # FIXME: Should we use the meta-way of accessing node properties as well?
                                                      # FIXME: This would require a refactoring of the transformer interfaces and tabular.run.
                                                      properties=self.properties(self.subject_transformer.properties_of,
                                                                                 row, i, subject_edge, subject_node,
                                                                                 node=True)))
                else:
                    local_errors.append(self.error(f"Failed to declare subject ID for row #{i}: `{row}`.",
                                                   indent=2, exception = exceptions.DeclarationError))

                # Loop over list of transformer instances and label_maker corresponding nodes and edges.
                # FIXME the transformer variable here shadows the transformer module.
                for j,transformer in enumerate(self.transformers):
                    local_transformations += 1
                    logger.debug(f"\tCalling transformer: {transformer}...")
                    for target_id, target_edge, target_node in transformer(row, i):
                        local_nb_nodes += 1
                        if target_id and target_edge and target_node:

                            if transformer.final_type:
                                # If a final_type attribute is present in the transformer, use it as the target node type, instead
                                # of the default type.
                                target_node = transformer.final_type

                            target_node_id = self.make_id(target_node.__name__, target_id)
                            logger.debug(f"\t\tMake node {target_node_id}")
                            local_nodes.append(self.make_node(node_t=target_node, id=target_node_id,
                                                              # FIXME: Should we use the meta-way of accessing node properties as well?
                                                              # FIXME: This would require a refactoring of the transformer interfaces and tabular.run.
                                                              properties=self.properties(transformer.properties_of, row,
                                                                                         i, target_edge, target_node, node=True)))

                            # If a `from_subject` attribute is present in the transformer, loop over the transformer
                            # list to find the transformer instance mapping to the correct type, and then label_maker new
                            # subject id.

                            # FIXME add hook functions to be overloaded.

                            # FIXME: Make from_subject reference a list of subjects instead of using the add_edge function.

                            if hasattr(transformer, "from_subject"):

                                found_valid_subject = False

                                for t in self.transformers:
                                    if transformer.from_subject == t.target_type:
                                        found_valid_subject = True
                                        for s_id, s_edge, s_node in t(row, i):
                                            if s_id and s_edge and s_node:
                                                if t.final_type:
                                                    s_node = t.final_type
                                                subject_id = s_id
                                                subject_node_id = self.make_id(t.target_type, subject_id)
                                                logger.debug(
                                                    f"\t\tMake edge from {subject_node_id} toward {target_node_id}")
                                                local_edges.append(
                                                    self.make_edge(edge_t=target_edge, id_source=subject_node_id,
                                                                   id_target=target_node_id,
                                                                   properties=self.properties(target_edge.fields(),
                                                                                              row, i, s_edge, s_node)))

                                            else:
                                                local_errors.append(self.error(
                                                    f"No valid identifiers from {t} for {i}th row, when trying to change default subject type",
                                                    f"by {transformer} with `from_subject` attribute.",
                                                    indent=7, section="transformers", index=j,
                                                    exception=exceptions.TransformerDataError))
                                                continue

                                    else:
                                        # The transformer instance type does not match the type in the `from_subject` attribute.
                                        continue

                                if not found_valid_subject:
                                    local_errors.append(self.error(f"\t\t\tInvalid subject declared from {transformer}."
                                                                   f" The subject you declared in the `from_subject` directive: `"
                                                                   f"{transformer.from_subject}` must not be the same as the default subject type.",
                                                                   exception=exceptions.ConfigError))


                            else: # no attribute `from_subject` in `transformer`
                                logger.debug(f"\t\tMake edge {target_edge.__name__} from {source_node_id} toward {target_node_id}")
                                local_edges.append(self.make_edge(edge_t=target_edge, id_target=target_node_id,
                                                                  id_source=source_node_id,
                                                                  properties=self.properties(target_edge.fields(),
                                                                                             row, i, target_edge, target_node)))
                        else:
                            local_errors.append(self.error(f"No valid target node identifier from {transformer}"
                                                           f" for {i}th row.", indent=2, section="transformers",
                                                           index=j, exception = exceptions.TransformerDataError))
                            continue
            else:
                local_errors.append(self.error(f"No valid source node identifier from {self.subject_transformer} for {i}th row."
                                               f" This row will be skipped.", indent=2, exception = exceptions.TransformerDataError))
                return local_nodes, local_edges, local_errors, local_rows, local_transformations, local_nb_nodes

            return local_nodes, local_edges, local_errors, local_rows, local_transformations, local_nb_nodes
        # End of process_row local function

        nb_rows = 0
        nb_transformations = 0
        nb_nodes = 0

        if self.parallel_mapping > 0:
            logger.info(f"Processing dataframe in parallel. Number of workers set to: {self.parallel_mapping} ...")
            # Process the dataset in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor() as executor:
                # Map the process_row function across the dataframe
                results = list(executor.map(process_row, self.df.iterrows()))

            # Append the results in a thread-safe manner after all rows have been processed
            for local_nodes, local_edges, local_errors, local_rows, local_transformations, local_nb_nodes in results:
                with self._nodes_lock:
                    self.nodes_append(local_nodes)
                with self._edges_lock:
                    self.edges_append(local_edges)
                with self._errors_lock:
                    self.errors += local_errors
                with self._row_lock:
                    nb_rows += local_rows
                with self._transformations_lock:
                    nb_transformations += local_transformations
                with self._local_nb_nodes_lock:
                    nb_nodes += local_nb_nodes

        elif self.parallel_mapping == 0:
            logger.info(f"Processing dataframe sequentially...")
            for i, row in self.df.iterrows():
                local_nodes, local_edges, local_errors, local_rows, local_transformations, local_nb_nodes = process_row((i, row))
                self.nodes_append(local_nodes)
                self.edges_append(local_edges)
                self.errors += local_errors
                nb_rows += local_rows
                nb_transformations += local_transformations
                nb_nodes += local_nb_nodes

        else:
            self.error(f"Invalid value for `parallel_mapping` ({self.parallel_mapping})."
                       f" Pass 0 for sequential processing, or the number of workers for parallel processing.", exception = exceptions.ConfigError)

        # Final logger
        error_count = {}
        for transformer in chain([self.subject_transformer], self.transformers, self.property_transformers):
            if transformer.output_validator:
                for msg,err in transformer.output_validator.messages.items():
                    desc = f"in {err['section']} with {transformer}: {msg}"
                    # FIXME do we want the number of validation errors or the number of bad cell values?
                    # error_count[desc] = error_count.get(desc, 0) + err['count']
                    error_count[desc] = error_count.get(desc, err['count'])
        for desc,count in error_count.items():
            logger.error(f"Recorded {count} times a validation error {desc}")

        if self.errors:
            logger.error(
                f"Recorded {len(self.errors)} errors while processing {nb_transformations} transformations with {1+len(self.transformers)} node transformers, producing {nb_nodes} nodes for {nb_rows} rows.")
            # logger.debug("\n".join(self.errors))
        else:
            logger.info(
                f"Performed {nb_transformations} transformations with {1+len(self.transformers)} node transformers, producing {nb_nodes} nodes for {nb_rows} rows.")


def extract_table(df: pd.DataFrame, config: dict, parallel_mapping = 0, module = types, affix = "suffix", separator = ":", validate_output = False, raise_errors = True):
    """
    Proxy function for extracting from a table all nodes, edges and properties
    that are defined in a PandasAdapter configuration.

    Args:
        df (pd.DataFrame): The DataFrame containing the input data.
        config (dict): The configuration dictionary.
        parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
        module: The module in which to insert the types declared by the configuration.
        affix (str): The type affix to use (default is "suffix").
        separator (str): The separator to use between labels and type annotations (default is ":").
        validate_output: Whether to validate the output of the transformers. Defaults to False.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        PandasAdapter: The configured adapter.
    """
    parser = YamlParser(config, module, validate_output = validate_output, raise_errors = raise_errors)
    mapping = parser()

    adapter = PandasAdapter(
        df,
        *mapping,
        type_affix=affix,
        type_affix_sep=separator,
        parallel_mapping=parallel_mapping,
        raise_errors = raise_errors,
    )

    adapter.run()

    return adapter



class Declare(errormanager.ErrorManager):
    """
    Declarations of functions used to declare and instantiate object classes used by the Adapter for the mapping
    of the data frame.

    Args:
        module: The module in which to insert the types declared by the configuration.
    """

    def __init__(self,
                 module=types,
                 raise_errors = True,
                 ):
        super().__init__(raise_errors)
        self.module = module

    def make_node_class(self, name, properties={}, base=base.Node):
        """
        LabelMaker a node class with the given name and properties.

        Args:
            name: The name of the node class.
            properties (dict): The properties of the node class.
            base: The base class for the node class.

        Returns:
            The created node class.
        """
        # If type already exists, return it.
        if hasattr(self.module, name):
            cls = getattr(self.module, name)
            logger.debug(
                f"\t\tNode class `{name}` (prop: `{cls.fields()}`) already exists, I will not create another one.")
            for p in properties.values():
                if p not in cls.fields():
                    logger.warning(f"\t\t\tProperty `{p}` not found in declared fields for node class `{cls.__name__}`.")
            return cls

        def fields():
            return list(properties.values())

        attrs = {
            "__module__": self.module.__name__,
            "fields": staticmethod(fields),
        }
        t = pytypes.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
        logger.debug(f"\t\tDeclare Node class `{t.__name__}` (prop: `{properties}`).")
        setattr(self.module, t.__name__, t)
        return t

    def make_edge_class(self, name, source_t, target_t, properties={}, base=base.Edge):
        """
        LabelMaker an edge class with the given name, source type, target type, and properties.

        Args:
            name: The name of the edge class.
            source_t: The source type of the edge.
            target_t: The target type of the edge.
            properties (dict): The properties of the edge class.
            base: The base class for the edge class.

        Returns:
            The created edge class.
        """
        # If type already exists, check if the fields are the same.
        if hasattr(self.module, name):
            cls = getattr(self.module, name)
            cls_fields = cls.fields()

            # Compare the properties with the existing class fields
            if properties == cls_fields:
                logger.info(
                    f"\t\tEdge class `{name}` (prop: `{cls_fields}`) already exists with the same properties, I will not create another one.")
                return cls

            logger.warning(f"\t\tEdge class `{name}` already exists, but properties do not match.")
            # If properties do not match, we proceed to create a new class with the new properties.

        def fields():
            return properties

        def st():
            return source_t

        def tt():
            return [target_t]

        attrs = {
            "__module__": self.module.__name__,
            "fields": staticmethod(fields),
            "source_type": staticmethod(st),
            "target_type": staticmethod(tt),
        }
        t = pytypes.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
        logger.debug(f"\t\tDeclare Edge class `{t.__name__}` (prop: `{properties}`).")
        setattr(self.module, t.__name__, t)
        return t

    def make_transformer_class(self, transformer_type, multi_type_dictionary = None, branching_properties = None,
                               properties=None, columns=None, output_validator=None, label_maker = None, raise_errors = True, **kwargs):
        """
        LabelMaker a transformer class with the given parameters.

        Args:
            multi_type_dictionary: Dictionary of regex rules and corresponding types in case of cell value match.
            transformer_type: The class of the transformer.
            properties: The properties of the transformer.
            columns: The columns to be processed by the transformer.
            output_validator: validate.OutputValidator instance for transformer output validation.
            raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.
            **kwargs: Additional keyword arguments.

        Returns:
            The created transformer class.

        Raises:
            TypeError: If the transformer type is not an existing transformer.
        """
        if hasattr(transformer, transformer_type):
            parent_t = getattr(transformer, transformer_type)
            kwargs.setdefault("subclass", parent_t)
            if not issubclass(parent_t, base.Transformer):
                self.error(f"Object `{transformer_type}` is not an existing transformer.", exception = exceptions.DeclarationError)
                logger.debug(f"\t\tDeclare Transformer class '{transformer_type}' for node type '{nt}'")
            return parent_t(properties_of=properties,
                            columns=columns,
                            output_validator=output_validator,
                            multi_type_dict = multi_type_dictionary,
                            branching_properties = branching_properties,
                            label_maker = label_maker,
                            raise_errors = raise_errors,
                            **kwargs)
        else:
            # logger.debug(dir(generators))
            self.error(f"Cannot find a transformer class with name `{transformer_type}`.", exception = exceptions.DeclarationError)

class YamlParser(Declare):
    """
    Parse a table extraction configuration and return the three objects needed to configure an Adapter.

    The config is a dictionary containing only strings, as converted from the following YAML description:

    .. code-block:: yaml

            row:
               map:
                  columns:
                    - <MY_COLUMN_NAME>
                  to_subject: <MY_SUBJECT_TYPE>
            transformers:
                - map:
                    columns:
                        - <MY_COLUMN_NAME>
                    to_object: <MY_OBJECT_TYPE>
                    via_relation: <MY_RELATION_TYPE>
                - map:
                    columns:
                        - <MY_OTHER_COLUMN>
                    to_property:
                        - <MY_PROPERTY>
                    for_objects:
                        - <MY_OBJECT_TYPE>

    This maps the table row to a MY_SUBJECT_TYPE node type, adding an edge of type MY_RELATION_TYPE,
    between the MY_SUBJECT_TYPE node and another MY_OBJECT_TYPE node. The data in MY_OTHER_COLUMN is mapped
    to the MY_PROPERTY property of the MY_OBJECT_TYPE node. Note that `to_properties` may effectively map to
    an edge type or several types.

    In order to allow the user to write mappings configurations using their preferred vocabulary, the following
    keywords are interchangeable:
        - subject = row = entry = line,
        - columns = fields,
        - to_target = to_object = to_node
        - via_edge = via_relation = via_predicate.

    :param dict config: A configuration dictionary.
    :param module: The module in which to insert the types declared by the configuration.
    :return tuple: subject_transformer, transformers, metadata as needed by the Adapter.
    """

    def __init__(self, config: dict, module=types, validate_output = False, raise_errors = True):
        """
        Initialize the YamlParser.

        Args:
            config (dict): The configuration dictionary.
            validate_output (bool): Whether to validate the output of the transformers. Defaults to False.
            module: The module in which to insert the types declared by the configuration.
        """
        super().__init__(module, raise_errors = raise_errors)
        self.config = config
        self.validate_output = validate_output


        logger.debug(f"Classes will be created in module '{self.module}'")

    def get_not(self, keys, pconfig=None):
        """
        Get the first dictionary (key, item) not matching any of the passed keys.

        Args:
            keys: The keys to exclude.
            pconfig: The configuration dictionary to search in (default is self.config).

        Returns:
            dict: The first dictionary not matching any of the passed keys.
        """
        res = {}
        if not pconfig:
            pconfig = self.config
        for k in pconfig:
            if k not in keys:
                res[k] = pconfig[k]
        return res

    def get(self, keys, pconfig=None):
        """
        Get a dictionary item matching any of the passed keys.

        Args:
            keys: The keys to search for.
            pconfig: The configuration dictionary to search in (default is self.config).

        Returns:
            The first item matching any of the passed keys, or None if no match is found.
        """
        if not pconfig:
            pconfig = self.config
        for k in keys:
            if k in pconfig:
                return pconfig[k]
        return None

    def _extract_metadata(self, k_metadata_column, metadata_list, metadata, types, columns):
        """
        Extract metadata and update the metadata dictionary.

        Args:
            k_metadata_column (list): List of keys to be used for adding source column names.
            metadata_list (list): List of metadata items to be added.
            metadata (dict): The metadata dictionary to be updated.
            types (str): The type of the node or edge.
            columns (list): List of columns to be added to the metadata.

        Returns:
            dict: The updated metadata dictionary.
        """
        # TODO: Redundant code with the _extract_metadata function.
        if metadata_list and types:
            if type(types) != set:
                t = types
                metadata.setdefault(t, {})
                for item in metadata_list:
                    metadata[t].update(item)
                for key in k_metadata_column:
                    if key in metadata[t]:
                        # Use the value of k_metadata_column as the key.
                        key_name = metadata[t][key]
                        # Remove the k_metadata_column key from the metadata dictionary.
                        if key_name in metadata[t]:
                            msg = f"The key you used for adding source column names: `{key_name}` to node: `{t}` already exists in the metadata dictionary."
                            # FIXME is it an error or a warning?
                            # self.error(msg)
                            logger.warning(msg)
                        del metadata[t][key]
                        if columns:
                            # TODO make the separator a parameter.
                            metadata[t][key_name] = ", ".join(columns)
            else:
                for t in types:
                    metadata.setdefault(t, {})
                    for item in metadata_list:
                        metadata[t].update(item)
                    for key in k_metadata_column:
                        if key in metadata[t]:
                            # Use the value of k_metadata_column as the key.
                            key_name = metadata[t][key]
                            # Remove the k_metadata_column key from the metadata dictionary.
                            if key_name in metadata[t]:
                                msg = f"The key you used for adding source column names: `{key_name}` to node: `{t}` already exists in the metadata dictionary."
                                # FIXME is it an error or a warning?
                                # self.error(msg)
                                logger.warning(msg)
                            del metadata[t][key]
                            if columns:
                                # TODO make the separator a parameter.
                                metadata[t][key_name] = ", ".join(columns)

            return metadata
        else:
            return None


    def _get_input_validation_rules(self,):
        """
        Extract input data validation schema from yaml file and instantiate a Pandera DataFrameSchema object and validator.
        """
        k_validate = ["validate"]
        validation_rules = self.get(k_validate)
        yaml_validation_rules = yaml.dump(validation_rules, default_flow_style=False)
        validator = None

        try:
            validation_schema = pa.DataFrameSchema.from_yaml(yaml_validation_rules)
            validator = validate.InputValidator(validation_schema, raise_errors=self.raise_errors)
        except Exception as e:
            self.error(f"Failed to parse the input validation schema: {e}", exception=exceptions.ConfigError)

        return validator

    def _make_output_validator(self, output_validation_rules = None):
        """
        LabelMaker a validator for the output of a transformer.

        Args:
            output_validation_rules: The output validation rules for the transformer extracted from yaml file.

        Returns:
            validate.OutputValidator: The created validator.
        """

        if self.validate_output:
            if output_validation_rules:
                output_validator = validate.OutputValidator(raise_errors=self.raise_errors)
                # Adjust the formatting for output validation rules to match the expected format. This is so the
                # user would not have to type `columns` and `cell_value` in the configuration file each time.
                dict_output_validation_rules = {"columns": {"cell_value": output_validation_rules}}
                yaml_output_validation_rules = yaml.dump(dict_output_validation_rules, default_flow_style=False)
                output_validator.update_rules(pa.DataFrameSchema.from_yaml(yaml_output_validation_rules))
            else:
                output_validator = validate.SimpleOutputValidator(raise_errors=self.raise_errors)
        else:
            output_validator = validate.SkipValidator(raise_errors=self.raise_errors)

        return output_validator

    def _extract_final_type_class(self, final_type, possible_types, metadata, metadata_list, columns, properties_of):
        """
        Extract metadata and class for the final type and update the metadata dictionary.
        """

        if final_type:
            final_type_class = self.make_node_class(final_type, properties_of.get(final_type, {}))
            possible_types.add(final_type_class.__name__)
            extracted_s_final_type_metadata = self._extract_metadata(self.k_metadata_column,
                                                                     metadata_list, metadata,
                                                                     final_type,
                                                                     columns)
            if extracted_s_final_type_metadata:
                metadata.update(extracted_s_final_type_metadata)

            return final_type_class

        return None


    def _make_branching_dict(self, subject: bool, match_parser, properties_of, metadata_list, metadata, columns, final_type_class,
                             multi_type_dictionary, possible_node_types, possible_edge_types):
        """
        Helper function to parse the `match` clause of the YAML configuration file for subject and target transformers.
        """

        k_extract  = self.k_subject if subject else self.k_target

        for entry in match_parser:
            for k, v in entry.items():
                if isinstance(v, dict):
                    key = k
                    multi_type_dictionary[key] = {k1: v1 for k1, v1 in v.items()}
                    alt_type = self.get(k_extract, v)
                    alt_type_class = self.make_node_class(alt_type, properties_of.get(alt_type, {}))

                    possible_node_types.add(alt_type)

                    alt_final_type = self.get(self.k_final_type, v)

                    alt_final_type_class = self._extract_final_type_class(alt_final_type, possible_node_types, metadata,
                                                                          metadata_list, columns, properties_of)

                    if not subject:
                        alt_edge = self.get(self.k_edge, v)
                        alt_edge_class = self.make_edge_class(alt_edge, None, alt_type_class,
                                                              properties_of.get(alt_edge, {}))

                        possible_edge_types.add(alt_edge)

                        extracted_alt_edge_metadata = self._extract_metadata(self.k_metadata_column,
                                                                             metadata_list, metadata, alt_edge,
                                                                             None)

                        if extracted_alt_edge_metadata:
                            metadata.update(extracted_alt_edge_metadata)

                    extracted_alt_type_metadata = self._extract_metadata(self.k_metadata_column,
                                                                           metadata_list, metadata, alt_type,
                                                                           columns)
                    if extracted_alt_type_metadata:
                        metadata.update(extracted_alt_type_metadata)

                    if extracted_alt_type_metadata:
                        metadata.update(extracted_alt_type_metadata)

                    multi_type_dictionary[key] = {
                        'to_object': alt_type_class,
                        # Via relation is always None for subject, since there is never an edge declared for the subject type.
                        'via_relation': None if subject is True else alt_edge_class,
                        # We first try and declare the final type passed to the whole class of the
                        # transformer, and if it is not defined, we use the final type of the
                        # alternative node type, under the `match` clause.
                        'final_type': final_type_class if final_type_class else alt_final_type_class
                    }

    def parse_properties(self, properties_of, possible_subject_types, transformers_list):
        """
        Parse the properties of the transformers defined in the YAML mapping, and update the properties_of dictionary.
        """
        logger.debug(f"Parse properties...")
        for n_transformer, transformer_types in enumerate(transformers_list):
            for transformer_type, field_dict in transformer_types.items():
                if not field_dict:
                    self.error(f"There is no field for the {n_transformer}th transformer: '{transformer_type}',"
                               f" did you forget an indentation?", "transformers",
                               n_transformer, exception=exceptions.MissingFieldError)

                if any(field in field_dict for field in self.k_properties):
                    object_types = self.get(self.k_prop_to_object, pconfig=field_dict)
                    property_names = self.get(self.k_properties, pconfig=field_dict)
                    if type(property_names) != list:
                        logger.debug(f"\tDeclared singular property")
                        assert (type(property_names) == str)
                        property_names = [property_names]
                    if not object_types:  # FIXME: Creates errors with branching subject types and subject final type features.
                        logger.info(
                            f"No `for_objects` defined for properties {property_names}, I will attach those properties to the row subject(s) `{possible_subject_types}`")
                        if type(possible_subject_types) == set and len(possible_subject_types) == 1:
                            object_types = list(possible_subject_types)[0]
                        if type(possible_subject_types) == set and len(possible_subject_types) > 1:
                            object_types = list(possible_subject_types)
                    if type(object_types) != list:
                        logger.debug(f"\tDeclared singular for_object: `{object_types}`")
                        assert (type(object_types) == str)
                        object_types = [object_types]

                    column_names = self.get(self.k_columns, pconfig=field_dict)
                    if column_names != None and type(column_names) != list:
                        logger.debug(f"\tDeclared singular column `{column_names}`")
                        assert (type(column_names) == str)
                        column_names = [column_names]
                    gen_data = self.get_not(self.k_target + self.k_edge + self.k_columns, pconfig=field_dict)

                    # Parse the validation rules for the output of the property transformer.
                    p_output_validation_rules = self.get(self.k_validate_output, pconfig=field_dict)
                    p_output_validator = self._make_output_validator(p_output_validation_rules)

                    prop_transformer = self.make_transformer_class(transformer_type, columns=column_names,
                                                                   output_validator=p_output_validator,
                                                                   label_maker=make_labels.SimpleLabelMaker(
                                                                       raise_errors=self.raise_errors), **gen_data)

                    for object_type in object_types:
                        properties_of.setdefault(object_type, {})
                        for property_name in property_names:
                            properties_of[object_type].setdefault(prop_transformer, property_name)
                        logger.debug(f"\t\tDeclared property mapping for `{object_type}`: {properties_of[object_type]}")

        return properties_of

    def parse_subject(self, properties_of, transformers_list, metadata_list, metadata):
        """
        Parse the subject transformer and its properties from the YAML mapping.
        """

        logger.debug(f"Declare subject type...")
        subject_transformer_dict = self.get(self.k_row)
        subject_transformer_class = list(subject_transformer_dict.keys())[0]
        subject_kwargs = self.get_not(self.k_subject_type + self.k_columns, subject_transformer_dict[
            subject_transformer_class])  # FIXME shows redundant information filter out the keys that are not needed.
        subject_columns = self.get(self.k_columns, subject_transformer_dict[subject_transformer_class])
        subject_final_type = self.get(self.k_final_type, subject_transformer_dict[subject_transformer_class])
        if subject_columns != None and type(subject_columns) != list:
            logger.debug(f"\tDeclared singular subject’s column `{subject_columns}`")
            assert (type(subject_columns) == str)
            subject_columns = [subject_columns]

        # Parse the validation rules for the output of the subject transformer.
        subject_output_validation_rules = self.get(self.k_validate_output,
                                                   subject_transformer_dict[subject_transformer_class])
        subject_output_validator = self._make_output_validator(subject_output_validation_rules)

        subject_multi_type_dict = {}
        # TODO: assert subject_transformer_dict contains only ONE transformer.

        subject_transformer_params = subject_transformer_dict[subject_transformer_class]

        possible_subject_types = set()
        subject_branching = False

        s_final_type_class = self._extract_final_type_class(subject_final_type, possible_subject_types, metadata,
                                                            metadata_list, subject_columns, properties_of)

        if "match" in subject_transformer_params:

            subject_branching = True

            self._make_branching_dict(subject = True, match_parser = subject_transformer_params["match"],
                                      properties_of = properties_of, metadata_list = metadata_list, metadata = metadata,
                                      columns = subject_columns, final_type_class = s_final_type_class,
                                      multi_type_dictionary = subject_multi_type_dict, possible_node_types = possible_subject_types,
                                      possible_edge_types = set())

            source_t = None # Subject_type declared None because the subject transformer is a branching transformer.
            subject_type = None
            logger.debug(f"Parse subject transformer...")

            if "match_type_from_column" in subject_kwargs: #FIXME should be a k_variable just like the others.
                s_label_maker = make_labels.MultiTypeOnColumnLabelMaker(raise_errors=self.raise_errors,
                                                                        match_type_from_column=subject_kwargs['match_type_from_column'])
            else:
                s_label_maker = make_labels.MultiTypeLabelMaker(raise_errors=self.raise_errors)

        # "None" key is used to return any type of string, in case no branching is needed.
        else:
            subject_type = self.get(self.k_subject_type, subject_transformer_dict[subject_transformer_class])
            source_t = self.make_node_class(subject_type, properties_of.get(subject_type, {}))

            subject_multi_type_dict = {'None': {
                'to_object': source_t,
                'via_relation': None,
                'final_type': s_final_type_class
            }}

            possible_subject_types.add(source_t.__name__)

            s_label_maker = make_labels.SimpleLabelMaker(raise_errors=self.raise_errors)

        properties_of = self.parse_properties(properties_of, possible_subject_types, transformers_list)

        subject_transformer = self.make_transformer_class(transformer_type=subject_transformer_class,
                                                          multi_type_dictionary=subject_multi_type_dict,
                                                          branching_properties=properties_of if subject_branching else None,
                                                          properties=properties_of.get(subject_type,
                                                                                       {}) if not subject_branching else None,
                                                          columns=subject_columns,
                                                          output_validator=subject_output_validator,
                                                          label_maker=s_label_maker, raise_errors=self.raise_errors,
                                                          **subject_kwargs)

        logger.debug(f"\tDeclared subject transformer: {subject_transformer}")

        logger.debug(
            f"\tDeclare subject of possible types: '{possible_subject_types}', subject transformer: '{subject_transformer_class}', "
            f"subject kwargs: '{subject_kwargs}', subject columns: '{subject_columns}'")

        extracted_metadata = self._extract_metadata(self.k_metadata_column, metadata_list, metadata, possible_subject_types, subject_columns)
        if extracted_metadata:
            metadata.update(extracted_metadata)

        return possible_subject_types, subject_transformer, source_t, subject_columns


    def parse_targets(self, transformers_list, properties_of, source_t, metadata_list, metadata):
        """
        Parse the target transformers and their properties from the YAML mapping.
        """

        transformers = []
        possible_target_types = set()
        possible_edge_types = set()

        logger.debug(f"Declare types...")
        for n_transformer,transformer_types in enumerate(transformers_list):
            for transformer_type, field_dict in transformer_types.items():
                if not field_dict:
                    continue
                elif any(field in field_dict for field in self.k_properties):
                    if any(field in field_dict for field in self.k_target):
                        prop = self.get(self.k_properties, field_dict)
                        target = self.get(self.k_target, field_dict)
                        self.error(f"ERROR in transformer '{transformer_type}': one cannot "
                                      f"declare a mapping to both properties '{prop}' and object type '{target}'.", "transformers",
                                   n_transformer, exception = exceptions.CardinalityError)
                    continue
                else:
                    if type(field_dict) != dict:
                        self.error(str(field_dict)+" is not a dictionary", exception = exceptions.ParsingDeclarationsError)

                    columns = self.get(self.k_columns, pconfig=field_dict)
                    if type(columns) != list:
                        logger.debug(f"\tDeclared singular column")
                        # The rowIndex transformer is a special case, where the column does not need to be defined in the mapping.
                        # FIXME: In next refactoring do not assert `rowIndex` transformer name, in order to have a generic implementation. (ref: https://github.com/oncodash/ontoweaver/pull/153)
                        if transformer_type != "rowIndex":
                            assert(type(columns) == str)
                            columns = [columns]

                    target = self.get(self.k_target, pconfig=field_dict)
                    if type(target) == list:
                        self.error(f"You cannot declare multiple objects in transformers. For transformer `{transformer_type}`.",
                                   section="transformers", index=n_transformer, indent=1, exception = exceptions.CardinalityError)

                    subject = self.get(self.k_subject, pconfig=field_dict)
                    if type(subject) == list:
                        self.error(f"You cannot declare multiple subjects in transformers. For transformer `{transformer_type}`.",
                                   section="transformers", index=n_transformer, indent=1, exception = exceptions.CardinalityError)

                    edge = self.get(self.k_edge, pconfig=field_dict)
                    if type(edge) == list:
                        self.error(f"You cannot declare multiple relations in transformers. For transformer `{transformer_type}`.",
                                   section="transformers", index=n_transformer, indent=1, exception = exceptions.CardinalityError)

                    gen_data = self.get_not(self.k_target + self.k_edge + self.k_columns + self.k_final_type, pconfig=field_dict)

                    # Extract the final type if defined in the mapping.
                    final_type = self.get(self.k_final_type, pconfig=field_dict)

                    final_type_class = self._extract_final_type_class(final_type, possible_target_types, metadata,
                                                                      metadata_list, columns, properties_of)

                    # Harmonize the use of the `from_subject` and `from_source` synonyms in the configuration, because
                    # from_subject` is used in the transformer class to refer to the source node type.
                    if 'from_source' in gen_data:
                        gen_data['from_subject'] = gen_data['from_source']
                        del gen_data['from_source']

                    multi_type_dictionary = {}

                    if "match" in gen_data:

                        self._make_branching_dict(subject=False, match_parser=gen_data["match"],
                                                  properties_of=properties_of, metadata_list=metadata_list,
                                                  metadata=metadata,
                                                  columns=columns, final_type_class=final_type_class,
                                                  multi_type_dictionary=multi_type_dictionary,
                                                  possible_node_types=possible_target_types,
                                                  possible_edge_types=possible_edge_types)

                    # Parse the validation rules for the output of the transformer. Each transformer gets its own
                    # instance of the OutputValidator with (at least) the default output validation rules.
                    output_validation_rules = self.get(self.k_validate_output, pconfig=field_dict)
                    output_validator = self._make_output_validator(output_validation_rules)

                    if target and edge:
                        logger.debug(f"\tDeclare node .target for `{target}`...")
                        target_t = self.make_node_class(target, properties_of.get(target, {}))
                        possible_target_types.add(target)
                        logger.debug(f"\t\tDeclared target for `{target}`: {target_t.__name__}")
                        if subject:
                            logger.debug(f"\tDeclare subject for `{subject}`...")
                            subject_t = self.make_node_class(subject, properties_of.get(subject, {}))
                            possible_target_types.add(subject_t.__name__)
                            edge_t = self.make_edge_class(edge, subject_t, target_t, properties_of.get(edge, {}))
                            possible_edge_types.add(edge_t.__name__)
                        else:
                            logger.debug(f"\tDeclare edge for `{edge}`...")
                            edge_t = self.make_edge_class(edge, source_t, target_t, properties_of.get(edge, {}))
                            possible_edge_types.add(edge_t.__name__)

                        # "None" key is used to return any type of string, in case no branching is needed.
                        multi_type_dictionary['None'] = {
                            'to_object': target_t,
                            'via_relation': edge_t,
                            'final_type': final_type_class
                        }

                        # Parse the validation rules for the output of the transformer. Each transformer gets its own
                        # instance of the OutputValidator with (at least) the default output validation rules.
                        output_validation_rules = self.get(self.k_validate_output, pconfig=field_dict)
                        output_validator = self._make_output_validator(output_validation_rules)

                        logger.debug(f"\tDeclare transformer `{transformer_type}`...")
                        target_transformer = self.make_transformer_class(transformer_type=transformer_type,
                                                                         multi_type_dictionary=multi_type_dictionary,
                                                                         properties=properties_of.get(target, {}),
                                                                         columns=columns,
                                                                         output_validator=output_validator,
                                                                         label_maker=make_labels.SimpleLabelMaker(
                                                                             raise_errors=self.raise_errors),
                                                                         raise_errors=self.raise_errors, **gen_data)
                        transformers.append(target_transformer)
                        logger.debug(f"\t\tDeclared mapping `{columns}` => `{edge_t.__name__}`")
                    elif (target and not edge) or (edge and not target):
                        self.error(f"Cannot declare the mapping  `{columns}` => `{edge}` (target: `{target}`), "
                                   f"missing either an object or a relation.", "transformers", n_transformer,
                                   indent=2, exception = exceptions.MissingDataError)


                    elif multi_type_dictionary and "match_type_from_column" in gen_data and not target and not edge:
                        target_transformer = self.make_transformer_class(transformer_type=transformer_type,
                                                                         multi_type_dictionary=multi_type_dictionary,
                                                                         branching_properties=properties_of,
                                                                         columns=columns,
                                                                         output_validator=output_validator,
                                                                         label_maker=make_labels.MultiTypeOnColumnLabelMaker(
                                                                             raise_errors=self.raise_errors, match_type_from_column=gen_data["match_type_from_column"]),
                                                                         raise_errors=self.raise_errors, **gen_data)

                        transformers.append(target_transformer)

                    elif multi_type_dictionary and not target and not edge and "match_type_from_column" not in gen_data:
                        target_transformer = self.make_transformer_class(transformer_type=transformer_type,
                                                                         multi_type_dictionary=multi_type_dictionary,
                                                                         branching_properties=properties_of,
                                                                         columns=columns,
                                                                         output_validator=output_validator,
                                                                         label_maker=make_labels.MultiTypeLabelMaker(
                                                                             raise_errors=self.raise_errors),
                                                                         raise_errors=self.raise_errors, **gen_data)

                        transformers.append(target_transformer)

                    # Declare the metadata for the target and edge types.

                    extracted_metadata = self._extract_metadata(self.k_metadata_column, metadata_list, metadata, target, columns)
                    if extracted_metadata:
                        metadata.update(extracted_metadata)

                    if edge:
                        extracted_metadata = self._extract_metadata(self.k_metadata_column, metadata_list, metadata, edge, None)
                        if extracted_metadata:
                            metadata.update(extracted_metadata)

        return transformers, possible_target_types, possible_edge_types


    def __call__(self):
        """
        Parse the configuration and return the subject transformer and transformers.

        Returns:
            tuple: The subject transformer and a list of transformers.
        """
        logger.debug(f"Parse mapping:")

        properties_of = {}
        metadata = {}

        # Various keys are allowed in the config to allow the user to use their favorite ontology vocabulary.
        self.k_row = ["row", "entry", "line", "subject", "source"]
        self.k_subject_type = ["to_subject", "to_object', 'to_node", "to_label", "to_type", "id_from_column"]
        self.k_columns = ["columns", "fields", "column", "match_column", "id_from_column"]
        self.k_target = ["to_target", "to_object", "to_node", "to_label", "to_type"]
        self.k_subject = ["from_subject", "from_source", "to_subject", "to_source", "to_node", "to_label", "to_type"]
        self.k_edge = ["via_edge", "via_relation", "via_predicate"]
        self.k_properties = ["to_properties", "to_property"]
        self.k_prop_to_object = ["for_objects", "for_object"]
        self.k_transformer = ["transformers"]
        self.k_metadata = ["metadata"]
        self.k_metadata_column = ["add_source_column_names_as"]
        self.k_validate_output = ["validate_output"]
        self.k_final_type = ["final_type", "final_object", "final_node", "final_subject", "final_label", "final_target"]

        #TODO create make node class for nested final_type instantiation

        # Extract transformer list and metadata list from the config.
        transformers_list = self.get(self.k_transformer)
        metadata_list = self.get(self.k_metadata)

        # Parse subject type, metadata for subject, and properties for both subject and target types (parse_subject calls parse_properties).
        possible_subject_types, subject_transformer, source_t, subject_columns = self.parse_subject(properties_of, transformers_list, metadata_list, metadata)

        # Parse the target types and target metadata.
        transformers, possible_target_types, possible_edge_types = self.parse_targets(transformers_list, properties_of, source_t, metadata_list, metadata)

        validator = self._get_input_validation_rules()

        if source_t:
            logger.debug(f"source class: {source_t}")
        elif possible_edge_types:
            logger.debug(f"possible_source_types: {possible_subject_types}")
        logger.debug(f"properties_of: {properties_of}")
        logger.debug(f"transformers: {transformers}")
        logger.debug(f"metadata: {metadata}")
        return subject_transformer, transformers, metadata, validator

