from ontoweaver.ontoweave import parse_data_map as pdm

def test_parse_data_map():

    d,m,k = pdm("data.csv:map.yaml")
    assert d == "data.csv"
    assert m == "map.yaml"
    assert not k

    d,m,k = pdm('data.csv{}:map.yaml')
    assert d == "data.csv"
    assert m == "map.yaml"
    assert not k

    d,m,k = pdm('data.csv{"dtype":"string"}:map.yaml')
    assert d == "data.csv"
    assert m == "map.yaml"
    assert k == {"dtype": "string"}

    d,m,k = pdm('data.csv{"dtypes":{"A":"string","B":"Int64"},"sep":","}:map.yaml')
    assert d == "data.csv"
    assert m == "map.yaml"
    assert k == {"dtypes":{"A":"string", "B":"Int64"}, "sep":","}

    d,m,k = pdm('mysql+mysqldb://johann@localhost/test:map.yaml')
    assert d == "mysql+mysqldb://johann@localhost/test"
    assert m == "map.yaml"
    assert not k

    d,m,k = pdm('mysql+mysqldb://johann:pass@dead:beef:cafe:babe:dead:beef:cafe:babe/test{"query":"SELECT * FROM table"}:map.yaml')
    assert d == 'mysql+mysqldb://johann:pass@dead:beef:cafe:babe:dead:beef:cafe:babe/test'
    assert m == "map.yaml"
    assert k == {"query":"SELECT * FROM table"}

