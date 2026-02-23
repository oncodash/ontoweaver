def test_oncokb():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "oncokb"

    expected_nodes = [
        ('0:variant', 'variant', {'timestamp': '91', 'mutation_effect_description': 'MET amplification results from the gain of the MET gene on chromosome 7 (PMID: 17463250).'}),
        ('33:patient', 'patient', {}),
        ('MET:gene_hugo', 'gene_hugo', {'entrez_gene_id': '4233', 'gene_summary': 'MET, a receptor tyrosine kinase.'}),
        ('HGSOC:disease', 'disease', {}),
        ('Oncogenic:oncogenicity', 'oncogenicity', {}),
        ('30073261:publication', 'publication', {}),
        ('16461907:publication', 'publication', {}),
        ('19117057:publication', 'publication', {}),
        ('17667909:publication', 'publication', {}),
        ('22869872:publication', 'publication', {}),
        ('18077425:publication', 'publication', {}),
        ('18093943:publication', 'publication', {}),
        ('28481359:publication', 'publication', {}),
        ('17463250:publication', 'publication', {}),
        ('2023-02-26:drug', 'drug', {}),
        ('Gain-of-function:functional_effect', 'functional_effect', {}),
        ('Amplification:alteration', 'alteration', {}),
        ('33:patient', 'patient', {}),
        ('LEVEL_Fda3:fda_evidence_level', 'fda_evidence_level', {}),
        ('LEVEL_3B:oncokb_evidence_level', 'oncokb_evidence_level', {}),
        ('1:variant', 'variant', {'timestamp': '92', 'mutation_effect_description': 'MET amplification results from the gain of the MET gene on chromosome 7 (PMID: 17463250).'}),
        ('34:patient', 'patient', {}),
        ('MET2:gene_hugo', 'gene_hugo', {'entrez_gene_id': '4234', 'gene_summary': 'MET, a receptor tyrosine kinase.'}),
        ('HGSOC:disease', 'disease', {}),
        ('Oncogenic:oncogenicity', 'oncogenicity', {}),
        ('30073261:publication', 'publication', {}),
        ('16461907:publication', 'publication', {}),
        ('2023-02-26:drug', 'drug', {}),
        ('Gain-of-function:functional_effect', 'functional_effect', {}),
        ('Amplification:alteration', 'alteration', {}),
        ('34:patient', 'patient', {}),
        ('LEVEL_Fda3:fda_evidence_level', 'fda_evidence_level', {}),
        ('LEVEL_3B:oncokb_evidence_level', 'oncokb_evidence_level', {})
    ]

    expected_edges = [
        ('(0:variant)--[patient_has_variant]->(33:patient)', '0:variant', '33:patient', 'patient_has_variant', {}),
        ('(0:variant)--[variant_in_gene]->(MET:gene_hugo)', '0:variant', 'MET:gene_hugo', 'variant_in_gene', {}),
        ('(0:variant)--[variant_to_disease]->(HGSOC:disease)', '0:variant', 'HGSOC:disease', 'variant_to_disease', {}),
        ('(0:variant)--[variant_to_oncogenicity]->(Oncogenic:oncogenicity)', '0:variant', 'Oncogenic:oncogenicity', 'variant_to_oncogenicity', {}),
        ('(0:variant)--[published]->(30073261:publication)', '0:variant', '30073261:publication', 'published', {}),
        ('(0:variant)--[published]->(16461907:publication)', '0:variant', '16461907:publication', 'published', {}),
        ('(0:variant)--[published]->(19117057:publication)', '0:variant', '19117057:publication', 'published', {}),
        ('(0:variant)--[published]->(17667909:publication)', '0:variant', '17667909:publication', 'published', {}),
        ('(0:variant)--[published]->(22869872:publication)', '0:variant', '22869872:publication', 'published', {}),
        ('(0:variant)--[published]->(18077425:publication)', '0:variant', '18077425:publication', 'published', {}),
        ('(0:variant)--[published]->(18093943:publication)', '0:variant', '18093943:publication', 'published', {}),
        ('(0:variant)--[published]->(28481359:publication)', '0:variant', '28481359:publication', 'published', {}),
        ('(0:variant)--[published]->(17463250:publication)', '0:variant', '17463250:publication', 'published', {}),
        ('(0:variant)--[variant_affected_by_drug]->(2023-02-26:drug)', '0:variant', '2023-02-26:drug', 'variant_affected_by_drug', {}),
        ('(0:variant)--[variant_has_effect]->(Gain-of-function:functional_effect)', '0:variant', 'Gain-of-function:functional_effect', 'variant_has_effect', {}),
        ('(0:variant)--[variant_to_alteration]->(Amplification:alteration)', '0:variant', 'Amplification:alteration', 'variant_to_alteration', {}),
        ('(0:variant)--[variant_to_fda_evidence]->(LEVEL_Fda3:fda_evidence_level)', '0:variant', 'LEVEL_Fda3:fda_evidence_level', 'variant_to_fda_evidence', {}),
        ('(0:variant)--[variant_to_oncokb_evidence]->(LEVEL_3B:oncokb_evidence_level)', '0:variant', 'LEVEL_3B:oncokb_evidence_level', 'variant_to_oncokb_evidence', {}),
        ('(1:variant)--[patient_has_variant]->(34:patient)', '1:variant', '34:patient', 'patient_has_variant', {}),
        ('(1:variant)--[variant_in_gene]->(MET2:gene_hugo)', '1:variant', 'MET2:gene_hugo', 'variant_in_gene', {}),
        ('(1:variant)--[variant_to_disease]->(HGSOC:disease)', '1:variant', 'HGSOC:disease', 'variant_to_disease', {}),
        ('(1:variant)--[variant_to_oncogenicity]->(Oncogenic:oncogenicity)', '1:variant', 'Oncogenic:oncogenicity', 'variant_to_oncogenicity', {}),
        ('(1:variant)--[published]->(30073261:publication)', '1:variant', '30073261:publication', 'published', {}),
        ('(1:variant)--[published]->(16461907:publication)', '1:variant', '16461907:publication', 'published', {}),
        ('(1:variant)--[variant_affected_by_drug]->(2023-02-26:drug)', '1:variant', '2023-02-26:drug', 'variant_affected_by_drug', {}),
        ('(1:variant)--[variant_has_effect]->(Gain-of-function:functional_effect)', '1:variant', 'Gain-of-function:functional_effect', 'variant_has_effect', {}),
        ('(1:variant)--[variant_to_alteration]->(Amplification:alteration)', '1:variant', 'Amplification:alteration', 'variant_to_alteration', {}),
        ('(1:variant)--[variant_to_fda_evidence]->(LEVEL_Fda3:fda_evidence_level)', '1:variant', 'LEVEL_Fda3:fda_evidence_level', 'variant_to_fda_evidence', {}),
        ('(1:variant)--[variant_to_oncokb_evidence]->(LEVEL_3B:oncokb_evidence_level)', '1:variant', 'LEVEL_3B:oncokb_evidence_level', 'variant_to_oncokb_evidence', {})
    ]

    data_mapping = {f"tests/{directory_name}/data.csv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix", validate_output=True, raise_errors=False)

    bc_nodes = ontoweaver.ow2bc(nodes)
    bc_edges = ontoweaver.ow2bc(edges)

    # The fusion functions is not being used due to the large number of duplicates, resulting in the properties being
    # fused in varying orders. This is not normally an issue, as the properties are still the same.
    # fnodes, fedges = ontoweaver.fusion.reconciliate(bc_nodes, bc_edges, reconciliate_sep=",")

    logging.debug(bc_nodes)
    logging.debug(bc_edges)
    testing_functions.assert_equals(bc_nodes, expected_nodes)
    testing_functions.assert_equals(bc_edges, expected_edges)


if __name__ == "__main__":
    test_oncokb()
