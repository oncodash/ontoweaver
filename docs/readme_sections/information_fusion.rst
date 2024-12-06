Information Fusion
------------------

When integrating several sources of information to create your own SKG,
you will inevitably face a case where two sources provide different
information for the same object. If you process each source with a
separate mapping applied to separate input tables, then each will
provide the same node, albeit with different properties.

This is an issue, as BioCypher does not provide a way to fuse both nodes
in a single one, while keeping all the properties. As of version 0.5, it
will use the last seen node, and discard the first one(s), effectively
loosing information (albeit with a warning). With a raw Biocypher
adapter, the only way to solve this problem is to implement a single
adapter, which reconciliate the data before producing nodes, which makes
the task difficult and the adapter code even harder to understand.

Reconciliation
~~~~~~~~~~~~~~

OntoWeaver provides a way to solve the reconciliation problem with its
*high-level information fusion* feature. The fusion features allow to
reconciliate the nodes and edges produced by various *independent*
adapters, by adding a final step on the aggregated list of nodes and
edges.

The generic workflow is to first produce nodes and edges —as usual— then
call the ``fusion.reconciliate`` function on the produced nodes and
edges:

.. code:: python

   # Call the mappings:
   adapter_A = ontoweaver.tabular.extract_all(input_table_A, mapping_A)
   adapter_B = ontoweaver.tabular.extract_all(input_table_B, mapping_B)

   # Aggregate the nodes and edges:
   nodes = adapter_A.nodes + adapter_B.nodes
   edges = adapter_A.edges + adapter_B.edges

   # Reconciliate:
   fused_nodes, fused_edges = ontoweaver.fusion.reconciliate(nodes, edges, separator=";")

   # Then you can pass those to biocypher.write_nodes and biocypher.write_edges...

High-level Interface
^^^^^^^^^^^^^^^^^^^^

OntoWeaver provides the ``fusion.reconciliate`` function, that
implements a sane default reconciliation of nodes. It merges nodes
having the same identifier and the same type, taking care of not losing
any property. When nodes have the same property field showing different
values, it aggregates the values in a list.

This means that if the two following nodes come from two different
sources:

.. code:: python

   # From source A:
   ("id_1", "type_A", {"prop_1": "x"}),
   ("id_1", "type_A", {"prop_2": "y"}),

   # From source B:
   ("id_1", "type_A", {"prop_1": "z"})

Then, the result of the reconciliation step above would be:

.. code:: python

   # Note how "x" and "z" are separated by separator=";".
   ("id_1", "type_A", {"prop_1": "x;z", "prop_2": "y"})

Mid-level Interfaces
^^^^^^^^^^^^^^^^^^^^

The simplest approach to fusion is to define how to:

1. decide that two nodes are identical,
2. fuse two identifiers,
3. fuse two type labels, and
4. fuse two properties dictionaries, and then
5. let OntoWeaver browse the nodes by pairs, until everything is fused.

For step 1, OntoWeaver provides the ``serialize`` module, which allows
to extract the part of a node or an edge) that should be used when
checking equality.

A node being composed of an identifier, a type label, and a properties
dictionary, the ``serialize`` module provides function objects
reflecting the useful combinations of those components:

- ``ID`` (only the identifier)
- ``IDLabel`` (the identifier and the type label)
- ``All`` (the identifier, the type label, and the properties)

The user can instantiate those function objects, and pass them to the
``congregate`` module, to find which nodes are duplicates of each other.
For example:

.. code:: python

   on_ID = serialize.ID() # Instantiation.
   congregater = congregate.Nodes(on_ID) # Instantiation.
   congregater(my_nodes) # Actual processing call.
   # congregarter now holds a dictionary of duplicated nodes.

For steps 2 to 4, OntoWeaver provides the ``merge`` module, which
provides ways to merge two nodes’ components into a single one. It is
separated into two submodules, depending on the type of the component:

- ``string`` for components that are strings (i.e. identifier and type
  label),
- ``dictry`` for components that are dictionaries (i.e. properties).

The ``string`` submodule provides:

- ``UseKey``: replace the identifier with the serialization used at the
  congregation step,
- ``UseFirst``/``UseLast``: replace the type label with the first/last
  one seen,
- ``EnsureIdentical``: if two nodes’ components are not equal, raise an
  error,
- ``OrderedSet``: aggregate all the components of all the seen nodes
  into a single, lexicographically ordered list (joined by a
  user-defined separator).

The ``dictry`` submodule provides:

- ``Append``: merge all seen dictionaries in a single one, and aggregate
  all the values of all the duplicated fields into a single
  lexicographically ordered list (joined by a user-defined separator).

For example, to fuse “congregated” nodes, one can do:

.. code:: python

       # How to merge two components:
       use_key    = merge.string.UseKey() # Instantiation.
       identicals = merge.string.EnsureIdentical()
       in_lists   = merge.dictry.Append(separator)

       # Assemble those function objects in an object that knows
       # how to apply them members by members:
       fuser = fuse.Members(base.Node,
               merge_ID    = use_key,    # How to merge two identifiers.
               merge_label = identicals, # How to merge two type labels.
               merge_prop  = in_lists,   # How to merge two properties dictionaries.
           )

       # Apply a "reduce" step (browsing pairs of nodes, until exhaustion):
       fusioner = Reduce(fuser) # Instantiation.
       fusioned_nodes = fusioner(congregater) # Call on the previously found duplicates.

Once this fusion step is done, is it possible that the edges that were
defined by the initial adapters refer to node IDs that do not exist
anymore. Fortunately, the fuser keeps track of which ID was replaced by
which one. And this can be used to remap the edges’ *target* and
*source* identifiers:

.. code:: python

   remaped_edges = remap_edges(edges, fuser.ID_mapping)

Finally, the same fusion step can be done on the resulting edges (some
of which are now duplicates, because they were remapped):

.. code:: python

       # Find duplicates:
       on_STL = serialize.edge.SourceTargetLabel()
       edges_congregater = congregate.Edges(on_STL)
       edges_congregater(edges)

       # How to fuse them:
       set_of_ID       = merge.string.OrderedSet(separator)
       identicals      = merge.string.EnsureIdentical()
       in_lists        = merge.dictry.Append(separator)
       use_last_source = merge.string.UseLast()
       use_last_target = merge.string.UseLast()
       edge_fuser = fuse.Members(base.GenericEdge,
               merge_ID     = set_of_ID,
               merge_label  = identicals,
               merge_prop   = in_lists,
               merge_source = use_last_source,
               merge_target = use_last_target
           )

       # Fuse them:
       edges_fusioner = Reduce(edge_fuser)
       fusioned_edges = edges_fusioner(edges_congregater)

Because all those steps are performed onto OntoWeaver’s internal
classes, they need to be converted back to Biocypher’s tuples:

.. code:: python

       return [n.as_tuple() for n in fusioned_nodes], [e.as_tuple() for e in fusioned_edges]

Low-level Interfaces
^^^^^^^^^^^^^^^^^^^^

Each of the steps mentioned in the previous section involves a functor
class that implements a step of the fusion process. Users may provide
their own implementation of those interfaces, and make them interact
with the others.

The first function interface is the ``congregate.Congregater``, whose
role is to consume a list of Biocypher tuples, find duplicated elements,
and store them in a dictionary mapping a key to a list of elements.

This allows to implementation of a de-duplication algorithm with a time
complexity in O(n·log n).

A ``Congregater`` is instantiated with a ``serialize.Serializer``,
indicating which part of an element is to be considered when checking
for equality.

The highest level fusion interface is ``fusion.Fusioner``, whose role is
to process a ``congregate.Congregater`` and return a set of fusioned
nodes.

OntoWeaver provides ``fusion.Reduce`` as an implementation of
``Fusioner``, which itself relies on an interface whose role is to fuse
two elements: ``fuse.Fuser``.

OntoWeaver provides a ``fuse.Members`` as an implementation, which
itself relies on ``merge.Merger``, which role is to fuse two elements’
*components*.

So, from the lower to the higher level, the following three interfaces
can be implemented:

1. ``merge.Merger`` —(used by)→ ``fuse.Members`` —(used by)→
   ``fusion.Reduce``
2. ``fuse.Fuser`` —(used by)→ ``fusion.Reduce``
3. ``fusion.Fusioner``

For instance, if you need a different way to *merge* elements
*components*, you should implement your own ``merge.Merger`` and use it
when instantiating ``fuse.Members``.

If you need a different way to *fuse* two *elements* (for instance for
deciding their type based on their properties), implement a
``fuse.Fuser`` and use it when instantiating a ``fusion.Reduce``.

If you need to decide how to fuse whole *sets* of duplicated nodes (for
instance if you need to know all duplicated nodes before deciding which
type to set), implement a ``fusion.Fusioner`` directly.
