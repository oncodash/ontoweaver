import logging
import abc

from . import errormanager
from . import exceptions

logger = logging.getLogger("ontoweaver")
class ValueMaker(errormanager.ErrorManager, metaclass=abc.ABCMeta):
    """
    Interface for value makers that are used to define the extraction logic for each of the transformer classes.
    """
    def __init__(self, raise_errors: bool = True):
        """
        Initialize the ValueMaker with the option to raise errors.

        Args:
            raise_errors (bool): if True, will raise an exception when an error is encountered, else, will log the error and try to proceed.
        """

        super().__init__(raise_errors)

    def check_attributes(self, **kwargs):
        """
        Check if all attributes expected in the __init__ are set. If not, raise an error.
        """

        expected_att = self.__dict__
        self.__dict__.update(**kwargs)

        expected_keys = {k: v for k, v in expected_att.items() if not k.startswith('__')}
        for k, v in expected_keys.items():
            if v is None:
                self.error(f"Attribute {k} not set.", section=f"{self.__class__.__name__}.check", exception=exceptions.TransformerDataError)

    @abc.abstractmethod
    def call(self, columns, row, i):
        """
        Select the value from the columns and row based on the logic defined in the subclass.
        Args:
            columns: The columns of the transformer instance.
            row: The current row of the dataframe.
            i: The current index of the row.

        Returns:
            The selected value.
        """
        raise NotImplementedError("The call method must be implemented in a subclass.")

    def __call__(self, columns, row, i, **kwargs):

        self.check_attributes(**kwargs)
        return self.call(columns, row, i)