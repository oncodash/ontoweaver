import logging
import math
from abc import ABCMeta

import pandas as pd
import pandera as pa
from pandera import Column, Check


class Validator(metaclass=ABCMeta):
    """Class used for data validation against a schema. The class uses the Pandera package to validate the data frame."""

    def __init__(self, validation_rules: pa.DataFrameSchema = None):
        """Constructor for the Validator class.

        Args:
            validation_rules: The schema used for validation.
        """

        self.validation_rules: pa.DataFrameSchema = validation_rules

    def __call__(self, df):
        """
        Validate the data frame against the schema.

        Args:
            df: The data frame to validate.

        Returns:
            bool: True if the data frame is valid, False otherwise.
        """
        if self.validation_rules:
            try:
                self.validation_rules.validate(df)
                return True
            except pa.errors.SchemaErrors as exc:
                print(exc.failure_cases)
        else:
            raise ValueError("No schema provided for validation.")

class InputValidator(Validator):
    """Class used for input data validation against a schema. The class uses the Pandera package to validate the data frame."""

    def __init__(self, validation_rules: pa.DataFrameSchema = None):
        """Constructor for the InputValidator class.

        Args:
            validation_rules: The schema used for validation.
        """

        super().__init__(validation_rules)

    def __call__(self, df):
        """
        Validate the data frame against the schema.

        Args:
            df: The data frame to validate.

        Returns:
            bool: True if the data frame is valid, False otherwise.
        """
        super().__call__(df)


def valid(val):
    """Check if a value is valid.
    Args:
        val: The value to check.
    """
    
    if pd.api.types.is_numeric_dtype(type(val)):
        if (math.isnan(val) or val == float("nan")):
            return False

    elif str(val).lower() == "nan" or val == "":
        return False

    return True


class OutputValidator(Validator):
    """Class used for transformer output data validation against a schema.
    The schema contains some general rules for the output data frame expected by default. The user can add additional rules
    to the schema for each transformer type used on each column. The class uses the Pandera package to validate the data frame."""

    def __init__(self,
                validation_rules: pa.DataFrameSchema = pa.DataFrameSchema({
                "cell_value": Column(
                    object,  # Use object to allow multiple types
                    checks=Check(valid, element_wise=True, error="Invalid value found.")
                )
            })):
        """Constructor for the OutputValidator class.

        Args:
            validation_rules: The schema used for validation.
        """
        super().__init__(validation_rules)


    def __call__(self, df):
        """
        Validate the data frame against the schema.

        Args:
            df: The data frame to validate.

        Returns:
            bool: True if the data frame is valid, False otherwise.
        """
        if self.validation_rules:
            try:
                self.validation_rules.validate(df)
                return True
            except:
                return False

        else:
            raise ValueError("No schema provided for validation.")

    def update_rules(self, new_rules):
        """Update the validation schema with additional rules.

        Args:
            new_rules: The additional rules to be added to the schema.
        """
        if not isinstance(new_rules, pa.DataFrameSchema):
            raise ValueError("new_rules must be a Pandera DataFrameSchema instance.")

        # Merge the existing rules with the new ones
        merged_rules = self.validation_rules.columns.copy() if self.validation_rules else {}
        merged_rules.update(new_rules.columns)

        # Update the validation rules
        self.validation_rules = pa.DataFrameSchema(merged_rules)
