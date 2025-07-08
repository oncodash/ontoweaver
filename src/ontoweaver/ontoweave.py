#!/usr/bin/env python3

import os
import sys
import logging
import pathlib
import platform
import xdg_base_dirs as xdg
import importlib

error_codes = {
    "ParsingError"    :  65, # "data format"
    "RunError"        :  70, # "internal"
    "DataValidationError": 76,  # "protocol"
    "ConfigError"     :  78, # "bad config"
    "CannotAccessFile": 126, # "no perm"
    "FileError"       : 127, # "not found"
    "SubprocessError" : 128, # "bad exit"
    "OntoWeaverError" : 254,
    "Exception"       : 255,
}

def check_file(filename):
    """Exit if the given filename does not exists or is not readable."""
    if not os.path.isfile(filename):
        logging.error(f"File `{filename}` not found.")
        sys.exit(error_codes["FileError"])

    if not os.access(filename, os.R_OK):
        logging.error(f"Cannot access file `{filename}`.")
        sys.exit(error_codes["CannotAccessFile"])


def config_directories(appname = "ontoweave"):
    """Yield standard configuration directories (as defined by XDG under MocOS/Unix)."""
    os = platform.system()
    logging.debug(f"Detected OS: {os}")

    #NOTE: All matched config files will be parsed and applied in the given order.
    if os == "Windows":
        if "APPDATA" in os.environ:
            yield pathlib.Path(os.environ["APPDATA"])
        yield pathlib.Path("~")/pathlib.Path("AppData")/pathlib.Path("Roaming")/pathlib.Path(appname)

    elif os == "Java" or os == "":
        logging.warning(f"I don't know where to search for configuration files on platform `{os}`, I'll only search in current directory")

    else: # Probably an Unix flavor (Darwin, Linux, Solaris, IRIX, etc.)
        # XDG will return the default defined in the specification
        # if the env variables are not set, so hardcoded defaults
        # like "~/.config/" should not be necessary.
        for p in xdg.xdg_config_dirs():
            yield p/appname
        yield xdg.xdg_config_home()/appname

    yield pathlib.Path("../ontoweaver")


def config_paths(appname = "ontoweave"):
    """Yield any path named <appname>.yaml in standard configuration directories."""
    dirs = config_directories()
    for p in dirs:
        yield str(p / (appname+".yaml"))


def import_from_path(file_path):
    """Import the given Python file path as a module."""
    # See https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    module_name = pathlib.Path(file_path).stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main():
    import jsonargparse
    import argparse
    import subprocess
    import inspect

    appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    logging.basicConfig()
    logger = logging.getLogger(appname)

    config_files = list(config_paths(appname))

    do = jsonargparse.ArgumentParser(
        description = "A command line tool to run OntoWeaver mapping adapters on a set of tabular data, and call the created BioCypher export scripts.",
        epilog = f"Example usage:\n  {appname} table.csv:mapping.yaml\n  {appname} --biocypher-config biocypher_config.yaml --biocypher-schema schema.yaml table1.csv:mapping1.yaml table2.tsv:mapping1.yaml table3.parquet:mapping2.yaml --import-script-run",
        default_config_files = config_files,
        env_prefix="ONTOWEAVE",
        default_env = True, # By default jsonargparse does not check environment, so one enables it explicitly.
        formatter_class = argparse.RawTextHelpFormatter,
        logger = logger, # FIXME jsonargparse seems to override any later config of logging, this seems like a bug.
    )

    do.add_argument("mapping", metavar="FILE:MAPPING", nargs="+",
        help=f"Run the given YAML MAPPING to extract data from the tabular FILE (usually a CSV). Several mappings can be passed to {appname}. You may also use the same mapping on different data files. If set to `STDIN`, will read the list of mappings from standard input.")

    do.add_argument("-c", "--config", metavar="FILE", action=jsonargparse.ActionConfigFile,
        help=f"The {appname} configuration file, which can host the same arguments than the command line tool. [default: {' or '.join(config_files)}]")

    do.add_argument("-C", "--biocypher-config", metavar="FILE", default="biocypher_config.yaml",
        help="The BioCypher config file (the one managing ontologies and the output backend). [default: %(default)s]")

    do.add_argument("-s", "--biocypher-schema", metavar="FILE", default="schema.yaml",
        help="The BioCypher schema file (the one managing node and edge types). [default: %(default)s]")

    do.add_argument("-p", "--parallel", metavar="NB_CORES", default="0",
        help=f"Number of processor cores to use when processing with multi-threading. `0` means a sequential processing (no parallelization, the default). Use 'auto' to let {appname} do its best to use a good number. [default: %(default)s]")

    do.add_argument("-i", "--import-script-run", action="store_true",
        help=f"If passed {appname} will call the import scripts created by Biocypher for you.")

    do.add_argument("-r", "--register", metavar="PYTHON_MODULE", nargs="*", default=[],
        help="Register all transformers available in the given module.")

    do.add_argument("-S", "--prop-sep", metavar="CHARACTER", default = ";",
        help="The character used to separate property values fused in the same property at the reconciliation step. [default: %(default)s]")

    do.add_argument("-a", "--type-affix", choices=["suffix","prefix","none"], default="none",
        help="Where to add the type string to the ID label. [default: %(default)s]")

    do.add_argument("-A", "--type-affix-sep", metavar="CHARACTER", default=":",
        help="Character used to separate the label from the type affix. [default: %(default)s]")

    do.add_argument("-E", "--pass-errors", action="store_true",
        help=f"When an error occurs, log is, and then try to continue processing. If not passed, the default behavior is to raise errors immediatly and stop execution.")

    do.add_argument("-l", "--log-level", default="WARNING",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Configure the log level. [default: %(default)s]")

    do.add_argument("-v", "--validate-only", action="store_true",
                    help="Only validate the given input data, do not apply the mapping.")

    do.add_argument("-V", "--validate-output", action="store_true",
                    help="Validate the output data against the mapping rules.")

    do.add_argument("-Ds", "--database-sep", metavar="CHARACTER",
        help="Character used to separate values in the database.")

    do.add_argument("-D", "--debug", action="store_true",
        help=f"Run in debug mode. implies `--log-level DEBUG`, disables `--pass-errors`. NOTE: this will disable explicit return codes and show the call stack.")

    asked = do.parse_args()

    if asked.debug:
        if asked.log_level != "DEBUG":
            logger.setLevel("DEBUG")
            logger.warning(f"You asked for --debug but set --log-level={asked.log_level}, I will ignore that and set --log-level=DEBUG")
        if asked.pass_errors:
            logger.warning(f"You asked for --debug but passed --pass-errors, I will ignore that.")
        asked.log_level = "DEBUG"
        asked.pass_errors = False

    logger.setLevel(asked.log_level)
    logging.getLogger("ontoweaver").setLevel(asked.log_level)

    logger.info("OntoWeave parameters:")

    logger.info(f"    config files: {config_files}")
    logger.info(f"    config: `{asked.biocypher_config}`")
    logger.info(f"    schema: `{asked.biocypher_schema}`")
    logger.info(f"    prop-sep: `{asked.prop_sep}`")
    logger.info(f"    type-affix: `{asked.type_affix}`")
    logger.info(f"    type-affix-sep: `{asked.type_affix_sep}`")
    logger.info(f"    import-script-run: `{asked.import_script_run}`")
    logger.info(f"    debug: `{asked.debug}`")
    logger.info(f"    log-level: `{asked.log_level}`")
    logger.info(f"    pass-errors: `{asked.pass_errors}`")
    logger.info(f"    validate-only: `{asked.validate_only}`")
    logger.info(f"    validate-output: `{asked.validate_output}`")

    logger.info(f"    asked mappings: `{asked.mapping}`")
    asked_mapping = []

    if asked.mapping == ["STDIN"]:
        while True:
            try:
                item = sys.stdin.readline()
            except UnicodeDecodeError:
                continue
            except KeyboardInterrupt:
                break
            if not item:
                break
            asked_mapping.append(item)
    else:
        asked_mapping = asked.mapping

    logger.info(f"    parsed mappings:")
    mappings = {}
    for data_map in asked_mapping:
        if ":" not in data_map:
            msg = f"Cannot parse the DATA:MAPPING `{data_map}`, I cannot find the colon character."
            logger.error(msg)
            sys.exit(error_codes["ConfigError"])
        data,map = data_map.split(":")
        mappings[data] = map
        logger.info(f"    `{data}` => `{map}`")

    if asked.parallel == "auto":
        parallel = min(32, (os.process_cpu_count() or 1) + 4)
    else:
        parallel = int(asked.parallel)
    logger.info(f"    parallel: `{asked.parallel}`")

    # Late import to avoid useless Biocypher's logs when asking for --help.
    import ontoweaver
    from biocypher._logger import get_logger as biocypher_logger
    biocypher_logger("biocypher").setLevel(asked.log_level)

    # Validate the input data if asked.
    if asked.validate_only:
        logger.info(f"Validating input data frame...")
        if ontoweaver.validate_input_data(filename_to_mapping=mappings, sep=asked.database_sep):
            logger.info(f"  Input data is valid according to provided rules.")
            sys.exit(0)
        else:
            logger.error(f"  Input data is invalid according to provided rules.")
            sys.exit(error_codes["DataValidationError"])

    # Register all transformers existing in the given modules.
    for mpath in asked.register:
        check_file(mpath)
        logger.info(f"Look for transformers in `{mpath}`")
        mod = import_from_path(mpath)
        for name,cls in mod.__dict__.items():
            if inspect.isclass(cls):
                logger.debug(f"{cls}")
                if issubclass(cls, ontoweaver.base.Transformer):
                    logger.info(f"    Register transformer: `{cls}`")
                    ontoweaver.transformer.register(cls)

    # Double check file inputs and exit on according errors.
    check_file(asked.biocypher_config)
    check_file(asked.biocypher_schema)
    for file_map in asked.mapping:
        data_file, map_file = file_map.split(":")
        check_file(data_file)
        check_file(map_file)

    if asked.validate_output:
        validate_output = True
    else:
        validate_output = False

    logger.info(f"Running OntoWeaver...")
    if asked.debug:
        import_file = ontoweaver.extract_reconciliate_write(
            asked.biocypher_config,
            asked.biocypher_schema,
            mappings,
            parallel_mapping=parallel,
            separator=asked.prop_sep,
            affix=asked.type_affix,
            affix_separator = asked.type_affix_sep,
            validate_output = validate_output,
            raise_errors = not asked.pass_errors)
    else:
        try:
            import_file = ontoweaver.extract_reconciliate_write(
                asked.biocypher_config,
                asked.biocypher_schema,
                mappings,
                parallel_mapping=parallel,
                separator=asked.prop_sep,
                affix=asked.type_affix,
                affix_separator = asked.type_affix_sep,
                validate_output = validate_output,
                raise_errors = not asked.pass_errors)
        # Manage exceptions wih specific error codes:
        except ontoweaver.exceptions.ConfigError as e:
            logger.error(f"ERROR in configuration: "+str(e))
            sys.exit(error_codes["ConfigError"])
        except ontoweaver.exceptions.RunError as e:
            logger.error(f"ERROR in content: "+str(e))
            sys.exit(error_codes["RunError"])
        except ontoweaver.exceptions.ParsingError as e:
            logger.error(f"ERROR during parsing of the YAML mapping: "+str(e))
            sys.exit(error_codes["ParsingError"])
        except ontoweaver.exceptions.DataValidationError as e:
            logger.error(f"ERROR during data validation: "+str(e))
            sys.exit(error_codes["DataValidationError"])
        except ontoweaver.exceptions.OntoWeaverError as e:
            logger.error(f"ERROR: "+str(e))
            sys.exit(error_codes["OntoWeaverError"])
        except Exception as e:
            logger.error(f"UNKNOWN ERROR: "+str(e))
            sys.exit(error_codes["Exception"])

    # Output import file on stdout, in case the user would want to capture it.
    print(import_file)
    check_file(import_file)

    if asked.import_script_run:
        shell = os.environ["SHELL"]
        logger.info(f"Run import scripts with {shell}...")
        if asked.debug:
            subprocess.run([shell, import_file])

        else:
            try:
                subprocess.run([shell, import_file])
            except Exception as e:
                logger.error(e)
                sys.exit(error_codes["SubprocessError"])


    logger.info("Done")

if __name__ == "__main__":
    main()
