""" Base class for errors management.
"""
import logging

logger = logging.getLogger("ontoweaver")

class ErrorManager:
    def __init__(self, raise_errors = True, delayed_print_limit = 20):
        self.raise_errors = raise_errors
        self.delayed_errors = []
        self.delayed_warnings = []
        self.delayed_infos = []
        self.delayed_print_limit = delayed_print_limit


    def format_msg(self, msg, section = None, index = None, exception = RuntimeError, indent = 0):
        location = ""
        if section:
            location = f" [for {section}"
            if index:
                location += f" #{index}"
            location += "]"

        err = "\t"*indent
        if exception:
            err += f"{exception.__name__}: "
        err += msg
        err += location

        return err


    def error(self, msg, section = None, index = None, exception = RuntimeError, indent = 0):
        err = self.format_msg(msg, section, index, exception, indent)
        logger.error(err)

        if self.raise_errors:
            raise exception(err)

        return err


    def delay_error(self, msg, section = None, index = None, indent = 0):
        err = self.format_msg(msg, section = section, index = index, indent = indent)
        self.delayed_errors.append(err)

    def delay_warning(self, msg, section = None, index = None, indent = 0):
        warn = self.format_msg(msg, section = section, index = index, indent = indent)
        self.delayed_warnings.append(warn)

    def delay_info(self, msg, section = None, indent = 0):
        info = self.format_msg(msg, section = section, indent = indent, exception = None)
        self.delayed_infos.append(info)


    def log_missing_key(self, key, row):
        """Helper function for logging a common problem in a standardized way."""
        available = "`, `".join(row.keys())
        self.delay_warning(f"Column `{key}` not found in data. Available columns: `{available}`")

    def log_all(self):
        msg = "There's more than " + str(self.delayed_print_limit) + " delayed {}, I will stop printing them here. Run in DEBUG mode to see them all, or increase `delayed_print_limit` to see more."

        if self.delayed_infos:
            logger.debug(f"{type(self).__name__} issued {len(self.delayed_infos)} infos:")
            delayed = set(self.delayed_infos)
            for info in delayed:
                # No print limit for infos
                logger.info(f"> {info}")

        if self.delayed_warnings:
            logger.warning(f"Delayed {len(self.delayed_warnings)} warnings from {type(self).__name__}:")
            delayed = set(self.delayed_warnings)
            for i,warn in enumerate(delayed):
                if i <= self.delayed_print_limit or logger.isEnabledFor(logging.DEBUG):
                    logger.warning(f"> {warn}")
                else:
                    logger.warning("[...]")
                    logger.warning(msg.format("warnings"))
                    break

        if self.delayed_errors:
            logger.error(f"Delayed {len(self.delayed_errors)} errors from {type(self).__name__}:")
            delayed = set(self.delayed_errors)
            for i,err in enumerate(delayed):
                if i <= self.delayed_print_limit or logger.isEnabledFor(logging.DEBUG):
                    logger.error(f"> {err}")
                else:
                    logger.warning("[...]")
                    logger.warning(msg.format("errors"))
                    break

    def __del__(self):
        self.log_all()
