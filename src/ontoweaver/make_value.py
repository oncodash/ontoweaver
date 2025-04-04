import logging
import abc

from . import errormanager
from . import exceptions

logger = logging.getLogger("ontoweaver")
class ValueMaker(errormanager.ErrorManager, metaclass=abc.ABCMeta):
    def __init__(self, raise_errors: bool = True):

        super().__init__(raise_errors)

    def check_attributes(self, **kwargs):
        expected_att = self.__dict__
        self.__dict__.update(**kwargs)

        expected_keys = {k: v for k, v in expected_att.items() if not k.startswith('__')}
        for k, v in expected_keys.items():
            if v is None:
                self.error(f"Attribute {k} not set.", section=f"{self.__class__.__name__}.check", exception=exceptions.TransformerDataError)

    @abc.abstractmethod
    def select(self, columns, row, i):
        raise NotImplementedError("The call method must be implemented in a subclass.")

    def __call__(self, columns, row, i, **kwargs):

        self.check_attributes(**kwargs)
        return self.select(columns, row, i)