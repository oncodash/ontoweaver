import rdflib
import sqlite3
import tempfile
import ontoweaver
import pandas as pd

from . import testing_functions

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


def test_multi_files():
    testing_functions.create_parquet_files()
    lpf = ontoweaver.loader.LoadPandasFile()
    lpf.load(["./tests/parquets/numbers_part-1.parquet", "./tests/parquets/numbers_part-2.parquet"])


def test_multi_files_glob():
    testing_functions.create_parquet_files()
    lpf = ontoweaver.loader.LoadPandasFile()
    lpf.load(["./tests/parquets/numbers_*.parquet"])


def test_load_sql():
    with tempfile.TemporaryDirectory() as tmpdir:

        tmp = f"{tmpdir}/tmp.sqlite3"

        lsql = ontoweaver.loader.LoadSQL()
        assert lsql.allows([f"sqlite:///{tmp}"])

        # Create a table and insert data
        conn = sqlite3.connect(f"file:{tmp}")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE people (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        cursor.execute("INSERT INTO people (name) VALUES ('Johann')")
        conn.commit()
        conn.close()

        data = lsql.load([f"sqlite:///{tmp}"], query = "SELECT * FROM people")

        assert data.shape == (1,2)
        assert "Johann" in data.iloc[0]["name"]

