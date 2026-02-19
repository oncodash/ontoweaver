import logging
import abc
import re

from . import errormanager, exceptions

logger = logging.getLogger("ontoweaver")

class ReturnCreate:
    """Class for returning the extracted cell value of the transformer, along with the edge type, target node type,
    and properties of the target node type.
    """

    def __init__(self, extracted_cell_value = None, edge_type = None, target_node_type = None, properties_of = None, final_type = None, reverse_relation = None):
        """
        Initializes the ReturnCreate object.

        Args:
            extracted_cell_value: The extracted cell value of the transformer. Can serve as ID of the node, ID of the edge, or value of property.
            edge_type: The type of the edge.
            target_node_type: The type of the target node.
            properties_of: The properties of the returned target node type.
            final_type: The final type of the target node.
            reverse_relation: The reverse relation of the current edge.
        """

        self.extracted_cell_value = extracted_cell_value # Can serve as ID of the node, ID of the edge, or value of property.
        self.edge_type = edge_type
        self.target_node_type = target_node_type
        self.target_element_properties = properties_of
        self.final_type = final_type
        self.reverse_relation = reverse_relation


class LabelMaker(errormanager.ErrorManager, metaclass=abc.ABCMeta):
    """Interface for defining the correct labels (types) for each extracted value.
    The class is responsible for validating the extracted cell value and returning the appropriate label.
    """

    def __init__(self, raise_errors: bool = True):
        """
        Initializes the LabelMaker object.

        Args:
            raise_errors (bool): if True, will raise an exception when an error is encountered, else, will log the error and try to proceed.
        """
        super().__init__(raise_errors)

        self.local_errors = set()
        self.local_warnings = set()

    @abc.abstractmethod
    def __call__(self, validate, returned_value, multi_type_dict, branching_properties = None, row = None):
        """

        Args:
            validate: The validation function which uses the Pandera schema to validate the extracted value.
            returned_value: The extracted value of the cell.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            branching_properties: In case of branching on cell values, the dictionary holding the properties for each branch.
            row: The row of the dataframe that is being processed. Used in case of branching on column values.

        Returns:
            ReturnCreate: An object containing the defined values.
        """
        return NotImplementedError("The call method must be implemented in a subclass.")

    def __del__(self):
        if self.local_errors:
            logger.error("Got errors while making some labels:")
            for e in self.local_errors:
                logger.error(f"\t{e}")

        if self.local_warnings:
            logger.warning("Got warnings while making some labels:")
            for w in self.local_warnings:
                logger.error(f"\t{w}")


class SimpleLabelMaker(LabelMaker):
    """
    The class is used when the transformer does not have any kind of type branching logic.
    """

    def __init__(self, raise_errors: bool = True):
        super().__init__(raise_errors)

    def __call__(self, validate, returned_value, multi_type_dict, branching_properties = None, row = None):

        value = str(returned_value)
        if validate(value):
            if multi_type_dict:
                if "None" in multi_type_dict.keys():
                    # No branching needed. The transformer is not a branching transformer.
                    assert multi_type_dict["None"]["to_object"]
                    return ReturnCreate(
                        value,
                        multi_type_dict["None"]["via_relation"],
                        multi_type_dict["None"]["to_object"],
                        None,
                        multi_type_dict["None"]["final_type"], multi_type_dict["None"]["reverse_relation"] )
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(value)
        else:
            # Validation failed.
            return None


class MultiTypeLabelMaker(LabelMaker):
    """
    The class is used when the transformer has type branching logic based on the value that will become the ID of the element.
    """
    def __init__(self,raise_errors: bool = True):
        super().__init__(raise_errors)

    def __call__(self, validate, returned_value, multi_type_dict = None, branching_properties = None, row = None):
        label = str(returned_value)
        if validate(label):
            if multi_type_dict:
                has_match = False
                for pattern, types in multi_type_dict.items():
                    # Branching is performed on the regex patterns.
                    if re.search(pattern, label):
                        has_match = True
                        if branching_properties:
                            properties_of = branching_properties.get(types["to_object"].__name__, {})
                        else:
                            properties_of = {}
                        assert types["to_object"]
                        return ReturnCreate(
                            label,
                            types["via_relation"],
                            types["to_object"],
                            properties_of,
                            types["final_type"],
                            types["reverse_relation"]
                        )
                if not has_match:
                    self.local_warnings.add(f"No type pattern matching value: `{label}`.")
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(label)
        else:
            # Validation failed, return empty object with None values.
            return ReturnCreate()


class MultiTypeOnColumnLabelMaker(LabelMaker):
    """
    The class is used when the transformer has type branching logic based on the value of a column in the dataframe,
    not the value that will become the ID of the element.
    """
    def __init__(self, raise_errors: bool = True, match_type_from_column: str = None):
        self.match_type_from_column = match_type_from_column
        super().__init__(raise_errors)

    def __call__(self, validate, returned_value, multi_type_dict = None, branching_properties = None, row = None):
        label = str(returned_value)
        if validate(label):
            if multi_type_dict:
                has_match = False
                for pattern, types in multi_type_dict.items():
                    # Branching is performed on the regex patterns.
                    if re.search(pattern, row[self.match_type_from_column]):
                        has_match = True
                        if branching_properties:
                            properties_of = branching_properties.get(types["to_object"].__name__, {})
                        else:
                            properties_of = {}
                        assert types["to_object"]
                        return ReturnCreate(
                            label,
                            types["via_relation"],
                            types["to_object"],
                            properties_of,
                            types["final_type"],
                            types["reverse_relation"]
                        )
                if not has_match:
                    self.local_warnings.add(f"No type pattern matching value: `{row[self.match_type_from_column]}`.")
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(label)
        else:
            return ReturnCreate()

