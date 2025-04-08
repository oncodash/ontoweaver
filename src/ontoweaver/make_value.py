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

    @abc.abstractmethod
    def __call__(self, columns, row, i):
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