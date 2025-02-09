
class OntoWeaverError(Exception):
    pass

class FeatureError(OntoWeaverError):
    pass

class ConfigError(OntoWeaverError):
    pass

class RunError(OntoWeaverError):
    pass

class DeclarationError(RunError):
    pass

class TransformerError(RunError):
    pass

class TransformerInterfaceError(TransformerError):
    pass

class TransformerDataError(TransformerError):
    pass

class DataValidationError(TransformerError):
    pass

class ParsingError(OntoWeaverError):
    pass

class ParsingPropertiesError(ParsingError):
    pass

class MissingFieldError(ParsingPropertiesError):
    pass

class ParsingDeclarationsError(ParsingError):
    pass

class CardinalityError(ParsingDeclarationsError):
    pass

class MissingDataError(ParsingDeclarationsError):
    pass


class InterfaceInheritanceError(TransformerError):
    pass

class TransformerConfigError(TransformerError):
    pass

class TransformerInputError(TransformerError):
    pass

