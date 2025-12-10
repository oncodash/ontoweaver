import rdflib
import pathlib
import pandas as pd
from abc import ABCMeta as ABSTRACT, abstractmethod

from . import tabular

class Loader(metaclass = ABSTRACT):
    def __call__(self, data, **kwargs):
        if self.allows(data):
            return self.load(data, **kwargs)

    @abstractmethod
    def allows(self, data):
        raise NotImplementedError()

    @abstractmethod
    def load(self, data, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def adapter(self):
        return NotImplementedError()


class LoadPandasDataframe(Loader):
    def allows(self, data):
        return type(data) == pd.DataFrame

    def load(self, df, **kwargs):
        return df

    def adapter(self):
        return tabular.PandasAdapter

class LoadPandasFile(Loader):
    """Read a file with Pandas, using its extension to guess its format.

    If no additional arguments are passed, it will call the
    Pandas `read_*` function with `filter_na = False`, which makes empty cell
    values to be loaded as empty strings instead of NaN values.

    Args:
        filename: The name of the data file the user wants to map.
        separator (str, optional): The separator used in the data file. Defaults to None.
        kwargs: A dictionary of arguments to pass to pandas.read_* functions.

    Raises:
        exception.FeatureError: if the extension is unknown.

    Returns:
        A Pandas DataFrame.
    """

    def __init__(self):
            # We probably don't want NaN as a default,
            # since they tend to end up in a label.
            #'c' engine does not support regex separators (separators > 1 char and different
            # from '\s+' are interpreted as regex) which results in an error.
        self.read_funcs = {
            '.csv'    : (pd.read_csv, {
                "sep": ",",
                'na_filter': True,
                'engine': 'python'
            }),
            '.tsv'    : (pd.read_csv, {
                "sep": "\t",
                'na_filter': True,
                'engine': 'python'
            }),
            '.txt'    : (pd.read_csv, {
                'na_filter': True,
                'engine': 'python'
            }),
            '.dat'    : (pd.read_csv, {
                'na_filter': True,
                'engine': 'python'
            }),

            '.xls'    : (pd.read_excel,   {'na_filter': True}),
            '.xlsx'   : (pd.read_excel,   {'na_filter': True}),
            '.xlsm'   : (pd.read_excel,   {'na_filter': True}),
            '.xlsb'   : (pd.read_excel,   {'na_filter': True}),
            '.odf'    : (pd.read_excel,   {'na_filter': True}),
            '.ods'    : (pd.read_excel,   {'na_filter': True}),
            '.odt'    : (pd.read_excel,   {'na_filter': True}),

            '.json'   : (pd.read_json,    {'na_filter': True}),
            '.html'   : (pd.read_html,    {'na_filter': True}),
            '.xml'    : (pd.read_xml,     {'na_filter': True}),
            '.hdf'    : (pd.read_hdf,     {'na_filter': True}),
            '.feather': (pd.read_feather, {'na_filter': True}),
            '.parquet': (pd.read_parquet, {'na_filter': True}),
            '.pickle' : (pd.read_pickle,  {'na_filter': True}),
            '.orc'    : (pd.read_orc,     {'na_filter': True}),
            '.sas'    : (pd.read_sas,     {'na_filter': True}),
            '.spss'   : (pd.read_spss,    {'na_filter': True}),
            '.stata'  : (pd.read_stata,   {'na_filter': True}),
        }


    def allows(self, filename):
        if type(filename) == str or type(filename) == pathlib.Path:
            ext = pathlib.Path(filename).suffix 
            if ext in self.read_funcs:
                return True

        return False


    def load(self, filename, **kwargs):
        ext = pathlib.Path(filename).suffix
        if not self.allows(filename):
            msg = f"File format '{ext}' of file '{filename}' is not supported (I can only read one of: {' ,'.join(self.read_funcs.keys())})"
            logger.error(msg)
            raise exceptions.FeatureError(msg)

        f  = self.read_funcs[ext][0]
        kw = self.read_funcs[ext][1]
        # Overwrite default named arguments with the passed ones.
        kw.update(kwargs)
        return f(filename, **kw)


    def adapter(self):
        return tabular.PandasAdapter


class LoadRDFGraph(Loader):
    def allows(self, data):
        return type(data) == rdflib.Graph

    def load(self, g, **kwargs):
        return g

    def adapter(self):
        return tabular.RDFAutoAdapter


class LoadRDFFile(Loader):
    def __init__(self):
        self.allowed = [".owl", ".xml", ".n3", ".turtle", ".ttl", ".nt", ".trig", ".trix", ".json-ld"]

    def allows(self, filename):
        if type(filename) == str or type(filename) == pathlib.Path:
            ext = pathlib.Path(filename).suffix
            if ext in self.allowed:
                return True

        msg = f"File format '{ext}' of file '{filename}' is not supported (I can only read one of: {', '.join(self.allowed)})"
        logger.warning(msg)
        return False


    def load(self, filename, **kwargs):
        ext = pathlib.Path(filename).suffix
        if not self.allows(filename):
            msg = f"File format '{ext}' of file '{filename}' is not supported (I can only read one of: {' ,'.join(self.allowed)})"
            logger.error(msg)
            raise exceptions.FeatureError(msg)

        g = rdflib.Graph()

        if ext == ".owl":
            g.parse(filename, format = "xml")
        else:
            g.parse(filename) # Guess the format based on extension.

        return g


    def adapter(self):
        return tabular.OWLAutoAdapter


