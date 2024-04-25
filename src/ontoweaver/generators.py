import logging

from . import base
class split(base.Transformer):

    def nodes(self):
       separator = self.separator()
       for i in self.id.split(separator):
           logging.debug(f"Make node `{i}` in {self.id.split(separator)}.")
           yield self.make_node(id = i)

    def edges(self):
       separator = self.separator()
       for i in self.id_target.split(separator):
           logging.debug(f"Make edge toward `{i}` in {self.id_target.split(separator)}.")
           yield self.make_edge(id_target = i)

