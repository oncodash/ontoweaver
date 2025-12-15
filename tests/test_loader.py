import rdflib
import ontoweaver
import pandas as pd

def test_loader():
    lpf = ontoweaver.loader.LoadPandasFile()
    lpf.load("./tests/simplest/data.csv")
    lpf.load("./tests/custom_transformer/data.tsv")

    data = [1,2,3]
    df = pd.DataFrame(data)
    lpd = ontoweaver.loader.LoadPandasDataframe()
    lpd.load(df)

    lrf = ontoweaver.loader.LoadOWLFile()
    lrf.load("./tests/test_preprocessing_ontology/OIM_test_preprocessing.owl")

    g = rdflib.Graph()
    g.parse("./tests/test_preprocessing_ontology/bc_OIM_test_preprocessing.owl")
    lrg = ontoweaver.loader.LoadOWLGraph()
    lrg.load(g)
