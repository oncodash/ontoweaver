import sys
from typing import TypeAlias
from typing import Optional
from enum import Enum
from enum import auto

import ontoweaver

class sample(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class patient(ontoweaver.Node):
    @staticmethod
    def fields():
        return ["cohort_code", "survival"]

class sample_to_patient(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return sample

    @staticmethod
    def target_type():
        return patient

    @staticmethod
    def fields():
        return []

# The `variant` class is declared through the config file, along with its properties.
class variant(ontoweaver.Node):
    @staticmethod
    def fields():
        return ["timestamp", "version", "mutation_effect_description", "variant_summary"]

class amplification(variant):
    pass
    # Fields would be gathered from parent class.

class deletion(variant):
    pass

class gain(variant):
    pass

class loss(variant):
    pass


# Allow accessing all ontoweaver.Item classes defined in this module.
all = ontoweaver.All(sys.modules[__name__])
