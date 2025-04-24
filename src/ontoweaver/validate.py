import logging
import math
from abc import ABCMeta

import pandas as pd
import pandera as pa
from pandera import Column, Check

from . import errormanager
from . import base
from . import exceptions

logger = logging.getLogger("ontoweaver")


class Validator(errormanager.ErrorManager):
    """Class used for data validation against a schema. The class uses the Pandera package to validate the data frame."""

    def __init__(self, validation_rules: pa.DataFrameSchema = None, raise_errors = True):
        """Constructor for the Validator class.

        Args:
            validation_rules: The schema used for validation.
        """
        super().__init__(raise_errors)

        self.validation_rules: pa.DataFrameSchema = validation_rules

        # Repeated validation error messages.
        self.messages = {}

    def error(self, msg, section = None):
        super().error(msg, section = section, exception = exceptions.DataValidationError)
        err = self.messages.get(msg, {"count": 0, "section": section})
        err["count"] += 1
        self.messages[msg] = err

    def __call__(self, df, section = None):
        """
        Validate the data frame against the schema.

        Args:
            df: The data frame to validate.

        Returns:
            bool: True if the data frame is valid, Otherwise raise an pa.errors.SchemaError.
        """
        if self.validation_rules:
            # May raise a pa.errors.SchemaError which will be catched in caller.
            # Generally base.Transformer.label_maker(...), so that
            # we know which transformer deals the issue.
            try:
                self.validation_rules.validate(df)
                return True
            except pa.errors.SchemaError as e:
                self.error(str(e), section = section)
                return False

        else:
            logger.warning("No schema provided for data validation.")
            return True

class InputValidator(Validator):
    """Class used for input data validation against a schema. The class uses the Pandera package to validate the data frame."""

    def __init__(self, validation_rules: pa.DataFrameSchema = None, raise_errors = True):
        """Constructor for the InputValidator class.

        Args:
            validation_rules: The schema used for validation.
        """

        super().__init__(validation_rules, raise_errors)

    def __call__(self, df):
        """
        Validate the data frame against the schema.

        Args:
            df: The data frame to validate.

        Returns:
            bool: True if the data frame is valid, False otherwise.
        """
        return super().__call__(df, section = self.__class__.__name__)


no_validation_rules: pa.DataFrameSchema = pa.DataFrameSchema({})

default_validation_rules: pa.DataFrameSchema = pa.DataFrameSchema({
            "cell_value": Column(
                pa.Object,
                checks=[
                    Check(
                        # We pass a lambda function which checks if the value is numeric or non-numeric NaN,
                        # or an empty string. This is meant to be the default behavior of an instance of the
                        # OutputValidator class.
                        lambda s: (
                              s.apply(lambda x: pd.api.types.is_numeric_dtype(type(x))
                                                and not pd.isna(x))
                            | s.apply(lambda x: not pd.api.types.is_numeric_dtype(type(x))
                                                and str(x).lower() != "nan"
                                                and x != "")
                        ),
                        error="Invalid value detected"
                    )
                ],

                # We additionally set that a cell value cannot be null.
                nullable=False
            )
    })

class OutputValidator(Validator):
    """Class used for transformer output data validation against a schema.
    The schema contains some general rules for the output data frame expected by default. The user can add additional rules
    to the schema for each transformer type used on each column. The class uses the Pandera package to validate the data frame."""

    def __init__(self,
                validation_rules = default_validation_rules,
            raise_errors = True):
        """Constructor for the OutputValidator class. By default, the output validator is instantiated with a schema that
        checks for numeric and non - numeric NaN values, and empty strings.

        Args:
            validation_rules: The schema used for validation.
        """
        super().__init__(validation_rules, raise_errors)



    def __call__(self, df):
        """
        Validate the data frame against the schema.

        Args:
            df: The data frame to validate.

        Returns:
            bool: True if the data frame is valid, False otherwise.
        """
        return super().__call__(df, section = self.__class__.__name__)


    def update_rules(self, new_rules):
        """Update the validation schema with additional rules.

        Args:
            new_rules: The additional rules to be added to the schema.
        """
        if not isinstance(new_rules, pa.DataFrameSchema):
            self.error("new_rules must be a Pandera DataFrameSchema instance.", section = self.__class__.__name__)

        # Merge the existing rules with the new ones
        merged_rules = self.validation_rules.columns.copy() if self.validation_rules else {}
        merged_rules.update(new_rules.columns)

        # Update the validation rules
        self.validation_rules = pa.DataFrameSchema(merged_rules)

class SimpleOutputValidator(Validator):

    def __init__(self, validation_rules = None, raise_errors = True):
        """Constructor for the SimpleValidator class. This class is used in case of absence of any validation rules outside
        of checking for none-types and empty strings. The class is used to bypass the use of the Pandera package for validation,
        which saves a lot of computational time when big datasets are used.

        Args:
            validation_rules: The schema used for validation.
        """
        super().__init__(validation_rules, raise_errors)

    def __call__(self, val):
        if pd.api.types.is_numeric_dtype(type(val)):
            if math.isnan(val) or val == float("nan"):
                return False

        elif str(val).lower() == "nan" or val == "":
            return False

        return True

class SkipValidator(Validator):
    """Class used for skipping validation. This class is used to skip validation for specific transformers.
    We implement the SkipValidator class in order to keep the validation logic in the same place as the other validators,
    and keep the code in base.py uniform for all validation options."""

    def __init__(self, validation_rules = None, raise_errors = True):
        """Constructor for the SkipValidator class.

        Args:
            validation_rules: The schema used for validation.
        """
        super().__init__(validation_rules, raise_errors)

    def __call__(self, val):

        logger.info(f"Transformer output validation skipped. This could result in some empty or `nan` nodes in your knowledge graph."
                    f" To enable output validation set validate_output to True.")

        return True

