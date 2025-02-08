import logging

logger = logging.getLogger("ontoweaver")

class ErrorManager:
    def __init__(self, raise_errors = True):
        self.raise_errors = raise_errors

    def error(self, msg, section = None, index = None, exception = RuntimeError, indent = 0):
        location = ""
        if section:
            location = f" [for {section}"
            if index:
                location += f" #{index}"
            location += "]"

        err = "\t"*indent
        err += f"{exception.__name__}: "
        err += msg
        err += location

        logger.error(err)

        if self.raise_errors:
            raise exception(err)

        return err

