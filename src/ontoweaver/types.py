import sys
from . import base

# Allow accessing all ontoweaver.Item classes defined in this module.
all = base.All(sys.modules[__name__])

