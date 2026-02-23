import rdflib
import ontoweaver
import pandas as pd

def test_loader():
    lpf = ontoweaver.loader.LoadPandasFile()
    lpf.load(["./tests/simplest/data.csv"])
    lpf.load(["./tests/custom_transformer/data.tsv"])

    data = [1,2,3]
    df = pd.DataFrame(data)
    lpd = ontoweaver.loader.LoadPandasDataframe()
    lpd.load([df])

    lrf = ontoweaver.loader.LoadOWLFile()
    lrf.load(["./tests/test_preprocessing_ontology/OIM_test_preprocessing.owl"])

    g = rdflib.Graph()
    g.parse("./tests/test_preprocessing_ontology/bc_OIM_test_preprocessing.owl")
    lrg = ontoweaver.loader.LoadOWLGraph()
    lrg.load([g])


def create_parquet_files():
    df1 = pd.DataFrame({"a":[1,2], "b":[3,4]})
    df1.to_parquet("./tests/parquets/numbers_part-1.parquet")

    df2 = pd.DataFrame({"a":[5,6], "b":[7,8]})
    df2.to_parquet("./tests/parquets/numbers_part-2.parquet")


def test_multi_files():
    create_parquet_files()
    lpf = ontoweaver.loader.LoadPandasFile()
    lpf.load(["./tests/parquets/numbers_part-1.parquet", "./tests/parquets/numbers_part-2.parquet"])


def test_multi_files_glob():
    create_parquet_files()
    lpf = ontoweaver.loader.LoadPandasFile()
    lpf.load(["./tests/parquets/numbers_*.parquet"])

