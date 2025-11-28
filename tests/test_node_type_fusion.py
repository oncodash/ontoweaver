import logging

import yaml

import pandas as pd

import biocypher
import ontoweaver

logger =logging.getLogger("ontoweaver")

def test_node_type_fusion():

    data_file = "tests/test_node_type_fusion/test.csv"
    
    filename_to_mapping = {data_file : "tests/test_node_type_fusion/mapping.yaml"}
    logger.debug("Load data...")
        
    nodes, edges = ontoweaver.extract(filename_to_mapping)

    bc_nodes, bc_edges = ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges)

    on_ID = ontoweaver.serialize.ID()
    congregater = ontoweaver.congregate.Nodes(on_ID)
    for n in congregater(bc_nodes):
        pass

    logger.debug('Initialize Biocypher instance...')

    bc = biocypher.BioCypher(
        biocypher_config_path = "tests/test_node_type_fusion/biocypher_config.yaml",
        schema_config_path = "tests/test_node_type_fusion/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    as_keys  = ontoweaver.merge.string.UseKey()
    as_sub_type = ontoweaver.merge.string.CommonSubType(bc._get_ontology())
    in_lists = ontoweaver.merge.dictry.Append()
    fuser = ontoweaver.fuse.Members(ontoweaver.base.Node,
            merge_ID    = as_keys,
            merge_label = as_sub_type,
            merge_prop  = in_lists,
        )

    fusioner = ontoweaver.fusion.Reduce(fuser)
    fusioned = fusioner(congregater)

    logger.debug("Fusioned items:")
    fused = []
    f_str = []
    for f in fusioned:
        logger.debug("  "+repr(f))
        fused.append(f)
        f_str.append(f._label)

    nb_persons = 0
    with open(data_file) as f:
        nb_persons = sum(1 for line in f) - 1
    assert nb_persons == len(fused)
    
    data_df = pd.read_csv(data_file)
    nb_male = len(data_df[data_df['genre'] == 'male'])
    nb_female = len(data_df[data_df['genre'] == 'female'])

    nb_fused_male = f_str.count("male")
    nb_fused_female = f_str.count("female")

    assert nb_male == nb_fused_male
    assert nb_female == nb_fused_female

if __name__ == "__main__":
    test_node_type_fusion()

    
