import logging

from . import base

class split(base.EdgeGenerator):

    def nodes(self):
       for i in self.id.split(self.separator):
           logging.debug(f"Make node `{i}` in {self.id.split(self.separator)}.")
           yield self.make_node(id = i)

    def edges(self):
       for i in self.id_target.split(self.separator):
           logging.debug(f"Make edge toward `{i}` in {self.id_target.split(self.separator)}.")
           yield self.make_edge(id_target = i)

