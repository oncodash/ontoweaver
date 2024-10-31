from abc import ABCMeta
from . import fusion
import logging

class Merge:
    pass


class Append(Merge):
    def __init__(self):
        super().__init__()

    def __call__(self, accumulator, element):
        for key, value in element.properties.items():
            if key not in accumulator:
                accumulator[key] = [value]
            elif value not in accumulator[key]:
                accumulator[key].append(value)
            logging.debug(f"Accumulated properties: {accumulator}")
        return accumulator