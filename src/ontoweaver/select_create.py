import re
import logging
from . import errormanager
from . import exceptions

logger = logging.getLogger("ontoweaver")
class Select(errormanager.ErrorManager):
    def __init__(self, raise_errors: bool = True):

        super().__init__(raise_errors)
    def check(self, **kwargs):
        self.__dict__.update(**kwargs)
        expected_att = self.__dict__

        expected_keys = {k: v for k, v in expected_att.items() if not k.startswith('__')}
        for k, v in expected_keys.items():
            if v is None:
                self.error(f"Attribute {k} not set.", section=f"{self.__class__.__name__}.check", exception=exceptions.TransformerDataError)

    def call(self, columns, row, i, **kwargs):
        pass

    def __call__(self, columns, row, i, **kwargs):

        self.check(**kwargs)
        return self.call(columns, row, i, **kwargs)
 

class MapSelect(Select):
    def __init__(self, raise_errors: bool = True):
        super().__init__(raise_errors)

    def call(self, columns, row, i, **kwargs):
        for key in columns:
            if key not in row:
                self.error(f"Column '{key}' not found in data", section="map.call", exception = exceptions.TransformerDataError)
            yield row[key]

class CatSelect(Select):
    def __init__(self, raise_errors: bool = True):
        super().__init__(raise_errors)

    def call(self, columns, row, i, **kwargs):
        formatted_items = ""

        for key in columns:
            formatted_items += str(row[key])
            yield formatted_items

class RowIndexSelect(Select):
    def __init__(self, raise_errors: bool = True):
        super().__init__(raise_errors)

    def call(self, columns, row, i, **kwargs):
        yield i

class ReplaceSelect(Select):

    def __init__(self,raise_errors: bool = True):
        self.forbidden = None
        self.substitute = None
        super().__init__(raise_errors)

    def call(self, columns, row, i, **kwargs):

        for key in columns:
            logger.info(f"Setting forbidden characters: {self.forbidden} for `replace` transformer, with substitute character: `{self.substitute}`.")
            formatted = re.sub(self.forbidden, self.substitute, row[key])
            strip_formatted = formatted.strip(self.substitute)
            logger.debug(f"Formatted value: {strip_formatted}")
            yield strip_formatted

class SplitSelect(Select):

    def __init__(self, raise_errors: bool = True):
        self.separator = None
        super().__init__(raise_errors)

    def call(self, columns, row, i, **kwargs):

        for key in columns:
            items = str(row[key]).split(self.separator)
            for item in items:
                yield item

class ReturnCreate:
    """Class for returning the result of the transformer.

        Args:
            result (str): The result of the transformer - ID of node.
            edge_type (str): The class of the edge.
            target_node_type (str): The class of the target node.
            properties_of (dict): The properties of the target node.

    """

    def __init__(self, result = None, edge_type = None, target_node_type = None, properties_of = None):
        self.result = result
        self.edge_type = edge_type
        self.target_node_type = target_node_type
        self.properties_of = properties_of

class Create(errormanager.ErrorManager):
    def __init__(self, output_validator = None, raise_errors: bool = True):
        self.output_validator = output_validator
        super().__init__(raise_errors)

    def check(self, **kwargs):
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

    def call(self, validate, returned_value, multi_type_dict, branching_properties = None, **kwargs):
        pass

    def __call__(self, validate, returned_value, multi_type_dict, branching_properties = None, **kwargs):
        self.check(**kwargs)
        return self.call(validate, returned_value, multi_type_dict, branching_properties, **kwargs)


class SimpleCreate(Create):
    def __init__(self, raise_errors: bool = True):
        super().__init__(raise_errors)

    def call(self, validate, returned_value, multi_type_dict, branching_properties = None, **kwargs):

        res = str(returned_value)
        if validate(res):
            if multi_type_dict:
                if "None" in multi_type_dict.keys():
                    # No branching needed. The transformer is not a branching transformer.
                    return ReturnCreate(res, multi_type_dict["None"]["via_relation"], multi_type_dict["None"]["to_object"])
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(res)
        else:
            # Validation failed, return empty object with None values.
            return ReturnCreate()

class MultiTypeCreate(Create):
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

class MultiTypeOnColumnCreate(Create):
    def __init__(self, raise_errors: bool = True):
        self.columns = None
        self.type_branch_from_column = None
        super().__init__(raise_errors)

    def call(self, validate, returned_value, multi_type_dict = None, branching_properties = None, **kwargs):
        row = kwargs.get("row")
        res = str(returned_value)
        if validate(res):
            if multi_type_dict:
                for key, types in multi_type_dict.items():
                    # Branching is performed on the regex patterns.
                    if re.search(key, row[self.type_branch_from_column]):
                        if branching_properties:
                            properties_of = branching_properties.get(types["to_object"].__name__, {})
                        else:
                            properties_of = {}
                        return ReturnCreate(res, types["via_relation"], types["to_object"], properties_of)
                    else:
                        logger.info(f"          Branching key `{key}` does not match extracted value `{row[self.type_branch_from_column]}`.")
                        continue
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(res)
        else:
            return ReturnCreate()



