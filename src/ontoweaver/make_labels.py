import logging
import abc
import re

from . import errormanager, exceptions

logger = logging.getLogger("ontoweaver")

class ReturnCreate:
    """Class for returning the extracted_cell_value of the transformer.

        Args:
            extracted_cell_value (str): The extracted_cell_value of the transformer - ID of node.
            edge_type (str): The class of the edge.
            target_node_type (str): The class of the target node.
            properties_of (dict): The properties of the target node.

    """

    def __init__(self, extracted_cell_value = None, edge_type = None, target_node_type = None, properties_of = None):
        self.extracted_cell_value = extracted_cell_value # Can serve as ID of the node, ID of the edge, or value of property.
        self.edge_type = edge_type
        self.target_node_type = target_node_type
        self.target_element_properties = properties_of

class LabelMaker(errormanager.ErrorManager, metaclass=abc.ABCMeta):
    def __init__(self, output_validator = None, raise_errors: bool = True):
        self.output_validator = output_validator
        super().__init__(raise_errors)

    def check_attributes(self, **kwargs):
        # Get attributes that are already in self.__dict__ and are None
        expected_keys = {k for k, v in self.__dict__.items() if not k.startswith('__') and v is None}

        # Update only expected keys if they are present in kwargs
        for k in expected_keys:
            if k in kwargs:
                setattr(self, k, kwargs[k])

        # Find attributes that are still None because they were expected but not provided in kwargs
        missing_keys = [k for k in expected_keys if getattr(self, k) is None]

        # Raise an error for any missing expected attributes
        if missing_keys:
            for k in missing_keys:
                self.error(
                    f"Attribute {k} not set.",
                    section=f"{self.__class__.__name__}.check",
                    exception=exceptions.TransformerDataError
                )

    @abc.abstractmethod
    def call(self, validate, returned_value, multi_type_dict, branching_properties = None, **kwargs):
        raise NotImplementedError("The call method must be implemented in a subclass.")

    def __call__(self, validate, returned_value, multi_type_dict, branching_properties = None, **kwargs):
        self.check_attributes(**kwargs)
        return self.call(validate, returned_value, multi_type_dict, branching_properties, **kwargs)


class SimpleLabelMaker(LabelMaker):

    def __init__(self, raise_errors: bool = True):
        super().__init__(raise_errors)

    def call(self, validate, returned_value, multi_type_dict, branching_properties = None, **kwargs):

        res = str(returned_value)
        if validate(res):
            if multi_type_dict:
                if "None" in multi_type_dict.keys():
                    # No branching needed. The transformer is not a branching transformer.
                    return ReturnCreate(res, multi_type_dict["None"]["via_relation"],
                                        multi_type_dict["None"]["to_object"])
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(res)
        else:
            # Validation failed, return empty object with None values.
            return ReturnCreate()

class MultiTypeLabelMaker(LabelMaker):
    def __init__(self,raise_errors: bool = True):
        super().__init__(raise_errors)

    def call(self, validate, returned_value, multi_type_dict = None, branching_properties = None, **kwargs):
        res = str(returned_value)
        if validate(res):
            if multi_type_dict:
                for key, types in multi_type_dict.items():
                    # Branching is performed on the regex patterns.
                    if re.search(key, res):
                        if branching_properties:
                            properties_of = branching_properties.get(types["to_object"].__name__, {})
                        else:
                            properties_of = {}
                        return ReturnCreate(res, types["via_relation"], types["to_object"], properties_of)
                    else:
                        logger.info(f"          Branching key `{key}` does not match extracted value `{res}`.")
                        continue
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(res)
        else:
            # Validation failed, return empty object with None values.
            return ReturnCreate()

class MultiTypeOnColumnLabelMaker(LabelMaker):
    def __init__(self, raise_errors: bool = True):
        self.match_type_from_column = None
        super().__init__(raise_errors)

    def call(self, validate, returned_value, multi_type_dict = None, branching_properties = None, **kwargs):
        row = kwargs.get("row")
        res = str(returned_value)
        if validate(res):
            if multi_type_dict:
                for key, types in multi_type_dict.items():
                    # Branching is performed on the regex patterns.
                    if re.search(key, row[self.match_type_from_column]):
                        if branching_properties:
                            properties_of = branching_properties.get(types["to_object"].__name__, {})
                        else:
                            properties_of = {}
                        return ReturnCreate(res, types["via_relation"], types["to_object"], properties_of)
                    else:
                        logger.info(f"          Branching key `{key}` does not match extracted value `{row[self.match_type_from_column]}`.")
                        continue
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(res)
        else:
            return ReturnCreate()



