import logging
import yaml
import io
import pandas as pd

import ontoweaver


def test_transformer_split_string_properties_2():

    data="""source	target	source_genesymbol	target_genesymbol	is_directed	is_stimulation	is_inhibition	consensus_direction	consensus_stimulation	consensus_inhibition	sources	references	omnipath	kinaseextra	ligrecextra	pathwayextra	mirnatarget	dorothea	collectri	tf_target	lncrna_mrna	tf_mirna	small_molecule	dorothea_curated	dorothea_chipseq	dorothea_tfbs	dorothea_coexp	dorothea_level	type	curation_effort	extra_attrs	evidences	ncbi_tax_id_source	entity_type_source	ncbi_tax_id_target	entity_type_target
htr2a-as1	P12004	htr2a-as1	PCNA	True	False	False	False	False	False	ncRDeathDB	ncRDeathDB:17932748	False	False	False	False	False	False	False	False	True	False	False						lncrna_post_transcriptional	1	"blabla"	9606	lncrna	9606	protein
P48281	Q9JMA7	Vdr	Cyp3a41a; Cyp3a41b	True	True	False	True	True	False	ExTRI_CollecTRI;HTRI_CollecTRI;HTRIdb;HTRIdb_DoRothEA;NTNU.Curated_CollecTRI;SIGNOR_CollecTRI;TRRUST;TRRUST_CollecTRI;TRRUST_DoRothEA	CollecTRI:11723248;CollecTRI:11991950;CollecTRI:12147248;	False	False	False	False	False	True	True	True	False	False	False	True	False	False	False	A;D	transcriptional	21	"blabla"	"blabli"	10090	protein	10090	protein"""

    csv = io.StringIO(data)
    table = pd.read_csv(csv, sep = '\t')

    logging.debug("Load mappings...")

    mapping = """
    row:
        map:
            column: source
            to_subject: source
    transformers:
        - map:
            column: target
            to_object: target
            via_relation: source_has_target
        - split:
            column: target_genesymbol
            separator: "; "
            to_property: genesymbol
            for_object: target
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")
    fnodes, fedges = ontoweaver.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    for n in fnodes:
        logging.debug(n)

    for n in fnodes:
        if n[0] == 'Q9JMA7':
            assert 'genesymbol' in n[2]
            assert n[2]['genesymbol'] != ''
            assert '|' in n[2]['genesymbol']


def test_transformer_split_string_properties():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Patient,Variant,Source
P1,V1-1,"S0; S1"
P1,V1-2,S1
P2,V2-1,"S2; S4"
P2,V2-2,S3"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = """
    row:
        map:
            column: Variant
            to_subject: variant
    transformers:
        - map:
            column: Patient
            to_object: patient
            via_relation: patient_has_variant
        - split:
            column: Source
            separator: "; "
            to_property: source
            for_object: variant
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")
    fnodes, fedges = ontoweaver.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    for n in fnodes:
        logging.debug(n)

    for n in fnodes:
        logging.debug(n)
        if n[1] == 'variant':
            assert "source" in n[2]


def test_transformer_split_string():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Patient,Variant,Source
P1,V1-1,"S0,S1"
P1,V1-2,S1
P2,V2-1,"S2,S4"
P2,V2-2,S3"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = """
    row:
        map:
            column: Variant
            to_subject: variant
    transformers:
        - map:
            column: Patient
            to_object: patient
            via_relation: patient_has_variant
        - split:
            column: Source
            separator: ","
            to_object: source
            via_relation: has_source
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")
    fnodes, fedges = ontoweaver.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    for n in fnodes:
        logging.debug(n)
    assert len(fnodes) == 11


def test_transformer_split_list():

    logging.debug("Load data...")

    table = pd.DataFrame({
        'Patient': ['P1', 'P1', 'P2', 'P2'],
        'Variant': ['V1-1', 'V1-2', 'V2-1', 'V2-2'],
        'Source' : [['S0', 'S1'], 'S1', ['S2', 'S4'], 'S3']
    })

    logging.debug("Load mappings...")

    mapping = """
    row:
        map:
            column: Variant
            to_subject: variant
    transformers:
        - map:
            column: Patient
            to_object: patient
            via_relation: patient_has_variant
        - split:
            column: Source
            separator: ","
            to_object: source
            via_relation: has_source
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")
    fnodes, fedges = ontoweaver.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    for n in fnodes:
        logging.debug(n)
    assert len(fnodes) == 11


if __name__ == "__main__":
    test_transformer_split_string()



