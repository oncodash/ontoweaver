import logging
from abc import abstractmethod, ABCMeta
from typing import Optional

from . import base
from . import fuse
from . import congregate

class Fusioner(metaclass=ABCMeta):
    def __init__(self, fuser: fuse.Fuser):
        self.fuser = fuser

    def __call__(self, congregater: congregate.Congregater):
        fusioned = set()
        for key, elem_list in congregater.duplicates.items():
            self.fuser.reset()
            logging.debug(f"Fusion of {type(congregater).__name__} with {type(congregater.serializer).__name__} for key: `{key}`")
            assert(elem_list)
            assert(len(elem_list) > 0)

            # Manual functools.reduce without initial state.
            it = iter(elem_list)
            lhs = next(it)
            logging.debug(f"  Fuse `{lhs}`...")
            logging.debug(f"    with itself: {repr(lhs)}")
            self.fuser(key, lhs, lhs)
            logging.debug(f"      = {repr(self.fuser.get())}")
            for rhs in it:
                logging.debug(f"    with `{rhs}`: {repr(rhs)}")
                self.fuser(key, lhs, rhs)
                logging.debug(f"      = {repr(self.fuser.get())}")

            # Convert to final string.
            f = self.fuser.get()
            assert(issubclass(type(f), base.Element))
            fusioned.add(f)
        return fusioned

