from abc import ABCMeta, abstractmethod
import logging
import copy
from collections import OrderedDict

from . import base

class Merger(metaclass=ABCMeta):

    def __call__(self, key, lhs, rhs):
        # logging.debug(f"Call Merger `{type(self).__name__}`")
        self.precheck(key, lhs, rhs)
        self.merge(key, lhs, rhs)
        # logging.debug(f"Merger `{type(self).__name__}` called: {self.merged}")

    def precheck(self, key, lhs, rhs) -> None:
        pass

    def reset(self):
        # logging.debug(f"Init Merger `{type(self).__name__}`")
        self.merged = None

    def set(self, value) -> None:
        self.merged = value

    @abstractmethod
    def merge(self, key, lhs, rhs) -> None:
        raise NotImplementedError

    def get(self):
        # logging.debug(f"Get Merger `{type(self).__name__}`")
        return self.merged


class dictry:

    class DictryMerger(Merger):
        def precheck(self, key, lhs: dict[str,str], rhs: dict[str,str]) -> None:
            assert(issubclass(type(key), base.Element))
            assert(type(lhs) == dict)
            assert(type(rhs) == dict)

        def set(self, value: dict[str,str]) -> None:
            assert(type(value) == dict)
            self.merged = value

        @abstractmethod
        def merge(self, key, lhs: dict[str,str], rhs: dict[str,str]) -> dict[str,str]:
            raise NotImplementedError

        def get(self) -> dict[str,str]:
            return self.merged


    class Append(DictryMerger):
        def __init__(self, sep = None):
            self.sep = sep

        def reset(self):
            self.merged = {}

        def set(self, merged) -> None:
            assert(type(merged) == dict)
            for k,v in merged.items():
                e = self.merged.get(k, set())
                if type(v) == set:
                    e.union(v)
                else:
                    self.merged[k] = set(v).union(e)

        def merge(self, key, lhs: dict[str,str], rhs: dict[str,str]):
            self.set(lhs)
            self.set(rhs)

        def get(self) -> str:
            merged = {}
            for k,v in self.merged.items():
                assert(type(v) == set)
                # Convert sets as str.
                if self.sep:
                    merged[k] = self.sep.join(v)
                else:
                    merged[k] = str(list(v))
            return merged


class string:

    class StringMerger(Merger):
        def precheck(self, key, lhs: str, rhs: str):
            assert(issubclass(type(key), base.Element))
            assert(type(lhs) == str)
            assert(type(rhs) == str)

        @abstractmethod
        def merge(self, key, lhs: str, rhs: str) -> str:
            raise NotImplementedError

        def get(self) -> str:
            return str(self.merged)


    class UseKey(StringMerger):
        def merge(self, key, lhs: str, rhs: str) -> str:
            self.set(key)


    class UseFirst(StringMerger):
        def merge(self, key, lhs: str, rhs: str) -> str:
            self.set(lhs)


    class UseLast(StringMerger):
        def merge(self, key, lhs: str, rhs: str) -> str:
            self.set(rhs)


    class OrderedSet(StringMerger):
        def __init__(self, sep = None):
            self.sep = sep

        def reset(self):
            self.merged = OrderedDict()

        def set(self, value) -> None:
            if type(value) == OrderedDict:
                for k in value.keys():
                    self.merged[k] = None
            else:
                self.merged[value] = None

        def merge(self, key, lhs: str, rhs: str):
            self.set(lhs)
            self.set(rhs)

        def get(self) -> str:
            if self.sep:
                return self.sep.join(self.merged.keys())
            else:
                return str(list(self.merged.keys()))

