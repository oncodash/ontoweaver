import os
import sys
import logging
import ontoweaver

def main():
    # CLI args management
    appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    config_files = list(ontoweaver.ontoweave.config_paths(appname))
    logging.debug(f"config files: {config_files}")
    do = ontoweaver.ontoweave.make_cli_parser(appname, config_files)
    asked = do.parse_args()

    # Call mappings
    bc_nodes, bc_edges = ontoweaver.ontoweave.extract(asked)

    # Basic fusion
    fnodes,fedges = ontoweaver.ontoweave.reconciliate(bc_nodes, bc_edges, asked)

    # Sort, write, call import script
    import_file = ontoweaver.ontoweave.write(fnodes, fedges, asked)

    # Output import file on stdout, in case the user would want to capture it.
    print(import_file)

    logging.info("Done ontoweave")


if __name__ == "__main__":
    main()

