import yaml
import logging

import pandera.pandas as pa

from . import base
from . import types
from . import transformer
from . import exceptions
from . import validate
from . import make_labels

logger = logging.getLogger("ontoweaver")

class YamlParser(base.Declare):
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

    def __init__(self, config: dict, module = None, validate_output = False, raise_errors = True):
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
        if not module:
            self.module = types
        else:
            self.module = module

        if not self.validate_output:
            logger.info(
                f"Transformer output validation will be skipped. This could result in some empty or `nan` nodes in your knowledge graph."
                f" To enable output validation set `validate_output` to `True`.")

        logger.debug(f"Classes will be created in module '{self.module}'")


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


    # ====================================================================
    # Getter functions for retrieval of dictionary items from YAML config
    # ====================================================================

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


    # ================================================================
    # Helper Functions for both Target, Subject and Property parsing
    # ================================================================

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

                        # Extract reverse edge, if specified in config.
                        alt_reverse_edge = self.get(self.k_reverse_edge, v)
                        if alt_reverse_edge:
                            alt_reverse_edge_class = self.make_edge_class(alt_reverse_edge, None, alt_type_class,
                                                                          properties_of.get(alt_reverse_edge, {}))

                            possible_edge_types.add(alt_reverse_edge)
                            extracted_alt_reverse_edge_metadata = self._extract_metadata(self.k_metadata_column,
                                                                                 metadata_list, metadata, alt_reverse_edge,
                                                                                 None)

                            if extracted_alt_reverse_edge_metadata:
                                metadata.update(extracted_alt_reverse_edge_metadata)

                        #TODO: Create new function or add this to make edge class?

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
                        'final_type': final_type_class if final_type_class else alt_final_type_class,
                        # None if subject because subject does not come with edge, and None if alt reverse edge class is not
                        # declared in mapping file.
                        'reverse_relation': None if subject is True else alt_reverse_edge_class if alt_reverse_edge else None,
                    }


    # ============================================================
    # Property parsing
    # ============================================================

    def parse_properties(self, properties_of, possible_subject_types, transformers_list):
        """
        Parse the properties of the transformers defined in the YAML mapping, and update the properties_of dictionary.
        """
        logger.debug(f"Parse properties...")

        for n_transformer, transformer_types in enumerate(transformers_list):
            if not hasattr(transformer_types, "items"):
                transformer_types = {transformer_types: []}

            for transformer_type, field_dict in transformer_types.items():
                if not field_dict:
                    logger.warning(f"There is no field for the {n_transformer}th transformer: '{transformer_type}',"
                               f" did you forget an indentation?")

                    continue

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

                    prop_transformer = self.make_transformer_class(
                        transformer_type, columns=column_names,
                        output_validator=p_output_validator,
                        label_maker=make_labels.SimpleLabelMaker(
                            raise_errors=self.raise_errors),
                        **gen_data)

                    for object_type in object_types:
                        properties_of.setdefault(object_type, {})
                        for property_name in property_names:
                            properties_of[object_type].setdefault(prop_transformer, property_name)
                        logger.debug(f"\t\tDeclared property mapping for `{object_type}`: {properties_of[object_type]}")

        return properties_of

    # ============================================================
    # Subject parsing
    # ============================================================

    def parse_subject(self, properties_of, transformers_list, metadata_list, metadata):
        """
        Parse the subject transformer and its properties from the YAML mapping.
        """

        logger.debug(f"Declare subject type...")
        subject_transformer_dict = self.get(self.k_row)
        if not subject_transformer_dict:
            msg = f"There is no `{'`, `'.join(self.k_row)}` key in your mapping."
            logging.error(msg)
            raise RuntimeError(msg)

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
        subject_output_validation_rules = self.get(
            self.k_validate_output,
            subject_transformer_dict[subject_transformer_class])

        subject_output_validator = self._make_output_validator(subject_output_validation_rules)

        subject_multi_type_dict = {}
        # TODO: assert subject_transformer_dict contains only ONE transformer.

        subject_transformer_params = subject_transformer_dict[subject_transformer_class]

        possible_subject_types = set()
        subject_branching = False

        s_final_type_class = self._extract_final_type_class(
            subject_final_type, possible_subject_types, metadata,
            metadata_list, subject_columns, properties_of)

        if subject_transformer_params:

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
                    'final_type': s_final_type_class,
                    'reverse_relation': None
                }}

                possible_subject_types.add(source_t.__name__)

                s_label_maker = make_labels.SimpleLabelMaker(raise_errors=self.raise_errors)

            # Append properties to subject type(s). In case other types are not declared.
            properties_of = self.parse_properties(properties_of, possible_subject_types, transformers_list)

            subject_transformer = self.make_transformer_class(transformer_type=subject_transformer_class,
                                                              multi_type_dictionary=subject_multi_type_dict,
                                                              branching_properties=properties_of if subject_branching else None,
                                                              properties=properties_of.get(subject_type,
                                                                                           {}) if not subject_branching else None,
                                                              columns=subject_columns,
                                                              output_validator=subject_output_validator,
                                                              label_maker=s_label_maker,
                                                              **subject_kwargs)

            logger.debug(f"\tDeclared subject transformer: {subject_transformer}")

            logger.debug(
                f"\tDeclare subject of possible types: '{possible_subject_types}', subject transformer: '{subject_transformer_class}', "
                f"subject kwargs: '{subject_kwargs}', subject columns: '{subject_columns}'")

        else:

            # Still parse properties even if no subject transformer parameters are declared.
            properties_of = self.parse_properties(properties_of, possible_subject_types, transformers_list)

            logger.warning(f"No keywords declared for subject transformer `{subject_transformer_class}`"
                       f" Creating transformer with no parameters.")

            subject_transformer = self.make_transformer_class(transformer_type=subject_transformer_class,
                                                             branching_properties=properties_of)

            # Declare source type as None because no parameters were declared for the subject transformer.
            source_t = None

        extracted_metadata = self._extract_metadata(self.k_metadata_column, metadata_list, metadata, possible_subject_types, subject_columns)
        if extracted_metadata:
            metadata.update(extracted_metadata)

        return possible_subject_types, subject_transformer, source_t, subject_columns

    # ============================================================
    # Target Transformer Parsing and Helper Functions
    # ============================================================

    def _make_target_label_maker(self, target, edge, gen_data, columns, transformer_index, multi_type_dictionary):

        label_maker = None

        if (target and not edge) or (edge and not target):
            self.error(f"Cannot declare the mapping  `{columns}` => `{edge}` (target: `{target}`), "
                       f"missing either an object or a relation.", "transformers", transformer_index,
                       indent=2, exception=exceptions.MissingDataError)
        elif multi_type_dictionary and "match_type_from_column" in gen_data and not target and not edge:
            label_maker = make_labels.MultiTypeOnColumnLabelMaker(raise_errors=self.raise_errors,
                                                                match_type_from_column=gen_data["match_type_from_column"])

        elif multi_type_dictionary and not target and not edge and "match_type_from_column" not in gen_data:
            label_maker = make_labels.MultiTypeLabelMaker(raise_errors=self.raise_errors)
        else:
            label_maker = make_labels.SimpleLabelMaker(raise_errors = self.raise_errors)

        return label_maker

    def _check_target_sanity(self, transformer_keyword_dict, transformer_type, transformer_index, transformers, properties_of):
        """
        Preforms sanity checks on target transformer before assigning the target, edge and subject variables, and connected
        columns.
        """

        if not transformer_keyword_dict:
            logger.warning(f"No keywords declared for target transformer `{transformer_type}` at index"
                       f" `{transformer_index}`. Creating transformer with no parameters.")
            target_transformer = self.make_transformer_class(transformer_type=transformer_type,
                                                             branching_properties=properties_of)
            transformers.append(target_transformer)

        elif any(field in transformer_keyword_dict for field in self.k_properties):
            if any(field in transformer_keyword_dict for field in self.k_target):
                prop = self.get(self.k_properties, transformer_keyword_dict)
                target = self.get(self.k_target, transformer_keyword_dict)
                self.error(f"ERROR in transformer '{transformer_type}', at index `{transformer_index}`: one cannot "
                           f"declare a mapping to both properties '{prop}' and object type '{target}'.", "transformers",
                           transformer_index, exception=exceptions.CardinalityError)

        elif type(transformer_keyword_dict) != dict:
            self.error(str(transformer_keyword_dict) + " is not a dictionary",
                       exception=exceptions.ParsingDeclarationsError)

        else:
            columns = self.get(self.k_columns, pconfig=transformer_keyword_dict)
            if type(columns) != list:
                logger.debug(f"\tDeclared singular column")
                # The rowIndex transformer is a special case, where the column does not need to be defined in the mapping.
                # FIXME: In next refactoring do not assert `rowIndex` transformer name, in order to have a generic implementation. (ref: https://github.com/oncodash/ontoweaver/pull/153)
                if transformer_type != "rowIndex":
                    assert (type(columns) == str)
                    columns = [columns]

            target = self.get(self.k_target, pconfig=transformer_keyword_dict)
            if type(target) == list:
                self.error(
                    f"You cannot declare multiple objects in transformers. For transformer `{transformer_type}`.",
                    section="transformers", index=transformer_index, indent=1, exception=exceptions.CardinalityError)

            subject = self.get(self.k_subject, pconfig=transformer_keyword_dict)
            if type(subject) == list:
                self.error(
                    f"You cannot declare multiple subjects in transformers. For transformer `{transformer_type}`.",
                    section="transformers", index=transformer_index, indent=1, exception=exceptions.CardinalityError)

            edge = self.get(self.k_edge, pconfig=transformer_keyword_dict)
            if type(edge) == list:
                self.error(
                    f"You cannot declare multiple relations in transformers. For transformer `{transformer_type}`.",
                    section="transformers", index=transformer_index, indent=1, exception=exceptions.CardinalityError)

            reverse_relation = self.get(self.k_reverse_edge, pconfig=transformer_keyword_dict)
            if type(reverse_relation) == list:
                self.error(
                    f"You cannot declare multiple reverse relations in transformers. For transformer `{transformer_type}`.",
                    section="transformers", index=transformer_index, indent=1, exception=exceptions.CardinalityError)

            return columns, target, edge, subject, reverse_relation


    def _make_target_classes(self, target, properties_of, edge, source_t, final_type_class, reverse_relation, possible_target_types, possible_edge_types, multi_type_dictionary):
        """
        Helper function to create the target and edge classes for a target transformer, and store them in the multi_type_dictionary.
        """

        logger.debug(f"\tDeclare node target `{target}`...")
        target_t = self.make_node_class(target, properties_of.get(target, {}))
        possible_target_types.add(target)
        logger.debug(f"\t\tDeclared target`{target}`: {target_t.__name__}")

        edge_t = self.make_edge_class(edge, source_t, target_t, properties_of.get(edge, {}))
        logger.debug(f"\tDeclare edge `{edge}: {edge_t.__name__}")
        possible_edge_types.add(edge_t.__name__)

        if reverse_relation is not None:
            reverse_relation_t = self.make_edge_class(reverse_relation, target_t, source_t, properties_of.get(reverse_relation, {}))
            logger.debug(f"\tDeclare reverse relation `{reverse_relation}: {reverse_relation_t.__name__}")
            possible_edge_types.add(reverse_relation_t)



        # "None" key is used to return any type of string, in case no branching is needed.
        multi_type_dictionary['None'] = {
            'to_object': target_t,
            'via_relation': edge_t,
            'final_type': final_type_class,
            'reverse_relation': reverse_relation_t if reverse_relation is not None else None,
        }

        # FIXME: Edge may not be needed as return here.
        return edge_t, target_t

    # ============================================================
    # Target parsing
    # ============================================================

    def parse_targets(self, transformers_list, properties_of, source_t, metadata_list, metadata):
        """
        Parse the target transformers and their properties from the YAML mapping.
        """

        transformers = []
        possible_target_types = set()
        possible_edge_types = set()

        logger.debug(f"Declare types...")
        # Iterate through the list of target transformers and extract the information needed to create the
        # corresponding classes.
        for transformer_index, target_transformer_yaml_dict in enumerate(transformers_list):
            if not hasattr(target_transformer_yaml_dict, "items"):
                target_transformer_yaml_dict = {target_transformer_yaml_dict: []}

            for transformer_type, transformer_keyword_dict in target_transformer_yaml_dict.items():

                target_branching = False
                elements = self._check_target_sanity(transformer_keyword_dict, transformer_type, transformer_index, transformers, properties_of)
                if elements is None:
                    continue
                # Transformer passed sanity check, unpack the returned elements.
                else:
                    columns, target, edge, subject, reverse_relation = elements

                gen_data = self.get_not(self.k_target + self.k_edge + self.k_columns + self.k_final_type + self.k_reverse_edge, pconfig=transformer_keyword_dict)

                # Extract the final type if defined in the mapping.
                final_type = self.get(self.k_final_type, pconfig=transformer_keyword_dict)
                final_type_class = self._extract_final_type_class(final_type, possible_target_types, metadata,
                                                                  metadata_list, columns, properties_of)

                # Harmonize the use of the `from_subject` and `from_source` synonyms in the configuration, because
                # from_subject` is used in the transformer class to refer to the source node type.
                if 'from_source' in gen_data:
                    gen_data['from_subject'] = gen_data['from_source']
                    del gen_data['from_source']

                multi_type_dictionary = {}

                #The target transformer is a simple transformer if it does not have a `match` clause. We create a simple multi_type_dictionary,
                #with a "None" key, to indicate that no branching is needed.
                if target and edge:
                    edge_t, target_t = self._make_target_classes(target, properties_of, edge, source_t, final_type_class, reverse_relation, possible_target_types, possible_edge_types, multi_type_dictionary)
                    # Parse the validation rules for the output of the transformer. Each transformer gets its own
                    # instance of the OutputValidator with (at least) the default output validation rules.
                    output_validation_rules = self.get(self.k_validate_output, pconfig=transformer_keyword_dict)
                    output_validator = self._make_output_validator(output_validation_rules)
                    logger.debug(f"\tDeclare transformer `{transformer_type}`...")

                #The target transformer is a branching transformer if it has a `match` clause. We create a branching dictionary.
                #The keys of the dictionary are the regex patterns to be matched against the extracted value of the column.

                if "match" in gen_data:

                    target_branching = True
                    self._make_branching_dict(subject=False, match_parser=gen_data["match"],
                                              properties_of=properties_of, metadata_list=metadata_list,
                                              metadata=metadata,
                                              columns=columns, final_type_class=final_type_class,
                                              multi_type_dictionary=multi_type_dictionary,
                                              possible_node_types=possible_target_types,
                                              possible_edge_types=possible_edge_types)
                # Parse the validation rules for the output of the transformer. Each transformer gets its own
                # instance of the OutputValidator with (at least) the default output validation rules.
                output_validation_rules = self.get(self.k_validate_output, pconfig=transformer_keyword_dict)
                output_validator = self._make_output_validator(output_validation_rules)

                label_maker = self._make_target_label_maker(target, edge, gen_data, columns, transformer_index, multi_type_dictionary)
                target_transformer = self.make_transformer_class(transformer_type=transformer_type,
                                                                 multi_type_dictionary=multi_type_dictionary,
                                                                 branching_properties=properties_of if target_branching else None,
                                                                 properties=properties_of.get(target_t.__name__,
                                                                                              {}) if not target_branching else None,
                                                                 columns=columns,
                                                                 output_validator=output_validator,
                                                                 label_maker=label_maker, **gen_data)
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
        logger.debug(f"Parse mapping...")

        properties_of = {}
        metadata = {}

        # Various keys are allowed in the config to allow the user to use their favorite ontology vocabulary.
        self.k_row = ["row", "entry", "line", "subject", "source"]
        self.k_subject_type = ["to_subject", "to_object', 'to_node", "to_label", "to_type", "id_from_column"]
        self.k_columns = ["columns", "fields", "column", "field", "match_column", "id_from_column", "label"]
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
        self.k_reverse_edge = ["reverse_relation", "reverse_edge", "reverse_predicate", "reverse_link"]

        #TODO create make node class for nested final_type instantiation

        # Extract transformer list and metadata list from the config.
        transformers_list = self.get(self.k_transformer)
        if not transformers_list:
            self.error(f"I cannot find the `transformers' section or it is empty,"
            f"check syntax for a typo (forgotten `s'?) or declare at leaset one transformer.`",
            exception = exceptions.ParsingDeclarationsError)

        metadata_list = self.get(self.k_metadata)

        # Parse subject type, metadata for subject, and properties for both subject and target types (parse_subject calls parse_properties).
        possible_subject_types, subject_transformer, source_t, subject_columns = self.parse_subject(properties_of, transformers_list, metadata_list, metadata)

        # Parse the target types and target metadata.
        transformers, possible_target_types, possible_edge_types = self.parse_targets(transformers_list, properties_of, source_t, metadata_list, metadata)

        validator = self._get_input_validation_rules()

        if not validator or type(validator) == validate.SkipValidator:
            logger.warning(f"Input validation will be skipped.")

        skipped_columns = []
        for t in transformers:
            if type(t.output_validator) == validate.SkipValidator:
                skipped_columns += t.columns

        if skipped_columns:
            logger.warning(f"Skip output validation for columns: `{'`, `'.join(skipped_columns)}`. This could result in some empty or `nan` nodes."
                           f" To enable output validation set `validate_output` to `True`.")

        if source_t:
            logger.debug(f"source class: {source_t}")
        elif possible_edge_types:
            logger.debug(f"possible_source_types: {possible_subject_types}")

        logger.debug(f"properties_of:")
        for kind in properties_of:
            for k in properties_of[kind]:
                logger.debug(f"\t{kind}: {k} {properties_of[kind][k]}>")

        logger.debug(f"transformers:")
        for t in transformers:
            logger.debug(f"\t{t}")

        if len(metadata) > 0:
            logger.debug(f"metadata:")
            for k in metadata:
                logger.debug(f"\t{metadata[k]}")
        else:
            logging.debug("No metadata")

        return subject_transformer, transformers, metadata, validator


