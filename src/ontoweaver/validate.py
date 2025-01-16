from abc import ABCMeta
import pandera as pa
import yaml
from pandera import Column, Check


class Validator(metaclass=ABCMeta):
    """Class used for data validation against a schema. The class uses the Pandera package to validate the data frame."""

    def __init__(self, validation_rules: pa.DataFrameSchema = None):
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
        super().__init__(validation_rules)

    def __call__(self, df):
        super().__call__(df)

class OutputValidator(Validator):
    """Class used for transformer output data validation against a schema.
    The schema contains some general rules for the output data frame expected by default. The user can add additional rules
    to the schema for each transformer type used on each column. The class uses the Pandera package to validate the data frame."""

    def __init__(self,
                 validation_rules: pa.DataFrameSchema = pa.DataFrameSchema({ "column2": Column(float, Check(lambda s: s < -1.2))})):
        super().__init__(validation_rules)



        super().__init__(validation_rules)

    def __call__(self, df):
        super().__call__(df)
