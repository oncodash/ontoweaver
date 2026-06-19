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


Reconciliation (default behaviour)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OntoWeaver provides a way to solve the reconciliation problem with its
*high-level information fusion* feature. The fusion features allow to
reconciliate the nodes and edges produced by various *independent*
adapters, by adding a final step on the aggregated list of nodes and
edges.

The generic workflow is to first produce nodes and edges —as usual— then
call the ``fusion.reconciliate`` function on the produced nodes and
edges:

.. code-block:: python

   # Call the mappings:
   adapter_A = ontoweaver.tabular.extract_table(input_table_A, mapping_A)
   adapter_B = ontoweaver.tabular.extract_table(input_table_B, mapping_B)

   # Aggregate the nodes and edges:
   nodes = adapter_A.nodes + adapter_B.nodes
   edges = adapter_A.edges + adapter_B.edges

   # Reconciliate:
   fused_nodes, fused_edges = ontoweaver.fusion.reconciliate(nodes, edges, reconciliate_sep=";")

   # Then you can pass those to biocypher.write_nodes and biocypher.write_edges...


OntoWeaver provides the ``fusion.reconciliate`` function, that
implements a sane default reconciliation of nodes. It merges nodes
having the same identifier and the same type, taking care of not losing
any property. When nodes have the same property field showing different
values, it aggregates the values in a list.

This means that if the two following nodes come from two different
sources:

.. code-block:: python

   # From source A:
   ("id_1", "type_A", {"prop_1": "x"}),
   ("id_1", "type_A", {"prop_2": "y"}),

   # From source B:
   ("id_1", "type_A", {"prop_1": "z"})
   ("id_2", "type_A", {"prop_1": "z"})
   ("id_1", "type_b", {"prop_1": "z"})

Then, the result of the reconciliation step above would be:

.. code-block:: python

   # Note how "x" and "z" are separated by reconciliate_sep=";".
   ("id_1", "type_A", {"prop_1": "x;z", "prop_2": "y"})
   ("id_2", "type_A", {"prop_1": "z"})
   ("id_1", "type_B", {"prop_1": "z"})


Generic fusion
~~~~~~~~~~~~~~

Introduction
^^^^^^^^^^^^

OntoWeaver brings a set of features that also help solving fusion problems
that goes beyond properties reconciliation.

To do so, it is allows to manage two problems:

1. How to detect that two elements are duplicates?
2. How to fuse duplicated element in a single one?

The first problem is handled by the ``Congregater`` interface, which needs to
construct a dictionary associating a *key* with a list of duplicated elements.
The *key* is a representation of the elements in the form of a string. If two
elements have the same *key* then they are considered duplicates and put in the
same list, and will be fused together in the second step.

For the second problem, OntoWeaver provides three layers, depending on what one
wants to fuse. For fusing:

1. a whole *list of duplicated elements*, use objects implementing the low-level
   interface ``fusion.Fusioner``,
2. two duplicated elements, use objects implementing the low-level interface
   ``fuse.Fuser``,
3. two member variables (e.g. ID, label, properties, source or target) of two
   duplicated elements, use the mid-level interface ``merge.Merger``.


The simplest approach to fusion is to define how to:

1. decide that two nodes are identical,
2. fuse two identifiers,
3. fuse two type labels, and
4. fuse two properties dictionaries, and then
5. let OntoWeaver browse the nodes by pairs, until everything is fused.


Detecting duplicates
^^^^^^^^^^^^^^^^^^^^

For step 1, OntoWeaver provides the ``serialize`` module, which allows to extract
the part of a node (or an edge) that should be used when checking equality.

To produce such a *key* from an element, OntoWeaver provides ``Serializer``.
A serializer object takes the element as an input, and returns the string key
representing it. For instance, it can return the concatenation of a node's ID
and label, or the concatenation of an edge's source, target and the value of a
specific property.

For example, with 4 nodes all having the same label, using the ``IDLabel``
serializer, the ``Node`` congregater will detect three duplicated nodes:

::

    nodes ==
    ⎡ ┌node1───────┐  ┌node2───────┐  ┌node3───────┐  ┌node4───────┐  ⎤
    ⎢ │   ID: BRCA2┼┐ │   ID: BRCA2┼┐ │   ID: BRCA2┼┐ │   ID: BRCA2┼┐ ⎥
    ⎢ │Label: gene ┼┤ │Label: gene ┼┤ │Label: prot ┼┤ │Label: gene ┼┤ ⎥
    ⎢ │Props:      ││,│Props:      ││,│Props:      ││,│Props:      ││ ⎥
    ⎢ │⎧ source: A⎫││ │⎧ source: B⎫││ │⎧ source: B⎫││ │⎧ source: B⎫││ ⎥
    ⎢ │⎨version: 1⎬││ │⎨version: 2⎬││ │⎨version: 2⎬││ │⎨version: 3⎬││ ⎥
    ⎢ │⎩  level: I⎭││ │⎩  level: I⎭││ │⎩  level:II⎭││ │⎩  level: I⎭││ ⎥
    ⎣ └────────────┘│ └────────────┘│ └────────────┘│ └────────────┘│ ⎦
                    │               │               │               │
            >>> on_IDLabel = ontoweaver.serialize.IDLabel()         │
            >>> for n in nodes:     │               │               │
            >>>     on_IDLabel(n)   │               │               │
                    │               │               │               │
                    ▼               ▼               ▼               ▼
       keys = ["BRCA2gene"  ,  "BRCA2gene"  ,  "BRCA2prot"  ,  "BRCA2gene"]
      └───┬────────────────────────────────────────────────────────────────┘
          │                          
          │ >>> congregate = ontoweaver.congregate.Nodes(on_IDlabel)
          │ >>> congregate(nodes)     
          │                          
          ▼                          
    congregate.duplicates() ==
    ⎧             ⎡ ┌node1───────┐ ┌node2───────┐ ┌node4───────┐ ⎤ ⎫
    ⎪             ⎢ │   ID: BRCA2│ │   ID: BRCA2│ │   ID: BRCA2│ ⎥ ⎪
    ⎪             ⎢ │Label: gene │ │Label: gene │ │Label: gene │ ⎥ ⎪
    ⎪"BRCA2gene": ⎢ │Props:      │,│Props:      │,│Props:      │ ⎥ ⎪
    ⎪             ⎢ │⎧ source: A⎫│ │⎧ source: B⎫│ │⎧ source: B⎫│ ⎥ ⎪
    ⎪             ⎢ │⎨version: 1⎬│ │⎨version: 2⎬│ │⎨version: 3⎬│ ⎥ ⎪
    ⎪             ⎢ │⎩  level: I⎭│ │⎩  level: I⎭│ │⎩  level: I⎭│ ⎥ ⎪
    ⎪             ⎣ └────────────┘ └────────────┘ └────────────┘ ⎦ ⎪
    ⎨ ,                                                            ⎬
    ⎪             ⎡ ┌node3───────┐ ⎤                               ⎪
    ⎪             ⎢ │   ID: BRCA2│ ⎥                               ⎪
    ⎪             ⎢ │Label: prot │ ⎥                               ⎪
    ⎪"BRCA2prot": ⎢ │Props:      │ ⎥                               ⎪
    ⎪             ⎢ │⎧ source: B⎫│ ⎥                               ⎪
    ⎪             ⎢ │⎨version: 2⎬│ ⎥                               ⎪
    ⎪             ⎢ │⎩  level:II⎭│ ⎥                               ⎪
    ⎩             ⎣ └────────────┘ ⎦                               ⎭

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

.. code-block:: python

   on_ID = serialize.ID() # Instantiation.
   congregater = congregate.Nodes(on_ID) # Instantiation.
   congregater(my_nodes) # Actual processing call.
   # congregarter now holds a dictionary of duplicated nodes.


Fusing duplicates
^^^^^^^^^^^^^^^^^

For steps 2 to 4, OntoWeaver provides the ``merge`` module, which
provides ways to merge two nodes’ components into a single one. It is
separated into two submodules, depending on the type of the component:

- ``string`` for components that are strings (i.e. identifier and type
  label),
- ``dictry`` for components that are dictionaries (i.e. properties).

The ``string`` submodule provides:

- ``Function``: this is a generic merger that you instantiate by passing a
  function that takes two argument and returns a result. This way, you can use
  any existing binary function (i.e. that takes two argument and returns a
  single result) as a merger. Optionally, it can be instanciated with an additional
  unary function (i.e. that takes one argument and returns a single result), that
  is applied before the binary function, on both arguments of the merger call.
- ``UseKey``: replace the identifier with the serialization used at the
  congregation step,
- ``UseFirst``/``UseLast``: replace the type label with the first/last
  one seen,
- ``EnsureIdentical``: if two nodes’ components are not equal, raise an
  error,
- ``OrderedSet``: aggregate all the components of all the seen nodes
  into a single, lexicographically ordered list (joined by a
  user-defined separator).
- ``SpecificType``: looks for the type that brings a more precise information.
  It sets the value to the most generic common *subtype*
  (among the two given elements) in the taxonomy hierarchy.
  This is really only useful for merging labels.
- ``GenericType``: looks for the type that brings a more generic information.
  sets the value to the most specific common *supertype*
  (among the two given elements) in the taxonomy hierarchy.
  This is really only useful for merging labels.

Those two last labels mergers may be tricky to grasp.
The diagram below is an example, showing two fusions of two pairs of nodes,
coming from different sources. The nodes have different types (labels),
from the same taxonomy tree.

::
 
       Taxonomy                Graph nodes     Fusion operators  Merged labels
    ┌──────┴────────┐        ┌──────┴───────┐   ┌──────┴─────┐   ┌─────┴────┐
      root
      └ feature
        └ alteration ┄┄label┄ (Node {src:1}) ⎫
          ├ mutation                         ⎬┄┄ SpecificType ┄┄⏵ SNP
          │ └ SNP ┄┄┄┄┄label┄ (Node {src:2}) ⎭⎫
          │                                   ⎬┄ GenericType ┄┄┄⏵ alteration
          └ CNV ┄┄┄┄┄┄┄label┄ (Node {src:3})  ⎭
            └ CNA

If the two merged elements have incompatible types, both mergers will
raise an error.



The ``dictry`` submodule provides:

- ``PerProperty``: merge properties one by one, each with a different merger.
  This is somehow a "meta-merger", that encapsulates string mergers and apply
  them on the dictionary of properties. To be instantiated, it needs a
  dictionary mapping the name of each properties toward an instance of a
  StringMerger.
- ``Append``: merge all seen dictionaries in a single one, and aggregate
  all the values of all the duplicated fields into a single
  lexicographically ordered list (joined by a user-defined separator).

For example, to fuse “congregated” nodes, one can do:

.. code-block:: python

       # How to merge two components:
       use_first  = merge.string.UseFirst() # Instantiation.
       identicals = merge.string.EnsureIdentical()
       in_lists   = merge.dictry.Append(reconciliate_sep)

       # Assemble those function objects in an object that knows
       # how to apply them member by member:
       fuser = fuse.Members(base.Node,
               merge_ID    = use_first,  # How to merge two identifiers.
               merge_label = identicals, # How to merge two type labels.
               merge_prop  = in_lists,   # How to merge two properties dictionaries.
           )

       # Apply a "reduce" step (browsing pairs of nodes, until exhaustion):
       fusioner = Reduce(fuser) # Instantiation.
       fusioned_nodes = fusioner(congregater) # Call on the previously found duplicates.

For example, the three duplicated nodes shown in the previous section would be
merged into a single node in two steps:

::

    congregate.duplicates() ==
    ⎧             ⎡ ┌node1───────┐ ┌node2───────┐ ┌node4───────┐ ⎤ ⎫
    ⎪             ⎢ │   ID: BRCA2│ │   ID: BRCA2│ │   ID: BRCA2│ ⎥ ⎪
    ⎪             ⎢ │Label: gene │ │Label: gene │ │Label: gene │ ⎥ ⎪
    ⎨"BRCA2gene": ⎢ │Props:      │,│Props:      │,│Props:      │ ⎥ ⎬
    ⎪             ⎢ │⎧ source: A⎫│ │⎧ source: B⎫│ │⎧ source: B⎫│ ⎥ ⎪
    ⎪             ⎢ │⎨version: 1⎬│ │⎨version: 2⎬│ │⎨version: 3⎬│ ⎥ ⎪
    ⎪             ⎢ │⎩  level: I⎭│ │⎩  level: I⎭│ │⎩  level: I⎭│ ⎥ ⎪
    ⎩             ⎣ └────────────┘ └────────────┘ └────────────┘ ⎦ ⎭
                           ▲              ▲              │
                           │              └──────────────┘
                           │              FIRST Reduce step:
                           │              merge node2 and node3 into node2.
                           │              │
                           └──────────────┘
                         SECOND Reduce step:
                         merge node1 and node2,
                         one now have a single node.

Each ``Reduce`` step would consists in calling ``Members`` mergers on each variable
members, for example, for the second step:

::

    fuse.Members.merge \
      ⎛            ┌node1───────┐ ┌node2─────────┐ ⎞                     ┌node────────────┐
      ⎜            │   ID: BRCA2│ │   ID: BRCA2  │ ⎟ ──────UseFirst─────▶│   ID: BRCA2    │
      ⎜┌key──────┐ │Label: gene │ │Label: gene   │ ⎟ ──EnsureIdenticals─▶│Label: gene     │
      ⎜│BRCA2gene│,│Props:      │,│Props:        │ ⎟ ───────Append──────▶│Props:          │
      ⎜└─────────┘ │⎧ source: A⎫│ │⎧ source: B  ⎫│ ⎟   ┄┄┄┄{A}+{B}┄┄┄┄▷  │⎧ source: A,B  ⎫│
      ⎜            │⎨version: 1⎬│ │⎨version: 2,3⎬│ ⎟   ┄┄┄┄{1}+{2,3}┄┄▷  │⎨version: 1,2,3⎬│
      ⎜            │⎩  level: I⎭│ │⎩  level: I  ⎭│ ⎟   ┄┄┄┄{I}+{I}┄┄┄┄▷  │⎩  level: I    ⎭│
      ⎝            └────────────┘ └──────────────┘ ⎠                     └────────────────┘


Fusing properties separately
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the ``merge.dictry.PerProperty`` merger, you can apply different mergers
to different properties.
For instance, in order to apply Python's ``max`` function, you would do:

.. code::

    my_max = ontoweaver.merge.string.Function(max)
    # And pass my_max to the fusion engine.

    # This equivalent to instantiating the following class:
    class MyMax(ontoweaver.merge.string.StringMerger):
        def merge(self, key, lhs, rhs):
            self.set( max(lhs, rhs) )

.. note::

    As of now, OntoWeaver operates on property values that are always strings.

Calling Python's ``max`` function on two strings will return the farthests in
alphabetical order.

If you need to convert the property values to something else before calling the
binary function, ``Function`` allows a second parameter that is a unary function,
that will be called before the binary one.

That way, to select the max of the two property values interpreted as integers,
you would do:

.. code::

    my_max = ontoweaver.merge.string.Function(max, int)

    # This equivalent to instantiating the following class:
    class MyMax(ontoweaver.merge.string.StringMerger):
        def merge(self, key, lhs, rhs):
            self.set( max( int(lhs), int(rhs) ) )

Here is a diagram that shows an example, similar to the previous ones:

::

    fuse.Members.merge \
      ⎛            ┌node1───────┐ ┌node2─────────┐ ⎞                         ┌node────────────┐
      ⎜            │   ID: BRCA2│ │   ID: BRCA2  │ ⎟ ────────UseFirst───────▶│   ID: BRCA2    │
      ⎜┌key──────┐ │Label: gene │ │Label: gene   │ ⎟ ────EnsureIdenticals───▶│Label: gene     │
      ⎜│BRCA2gene│,│Props:      │,│Props:        │ ⎟ ──────PerProperty──────▶│Props:          │
      ⎜└─────────┘ │⎧ source: A⎫│ │⎧ source: B  ⎫│ ⎟   ┄┄┄┄OrderedSet┄┄┄┄┄▷  │⎧ source: A,B  ⎫│
      ⎜            │⎨version: 1⎬│ │⎨version: 3  ⎬│ ⎟   ┄Function(max,int)┄▷  │⎨version: 3    ⎬│
      ⎜            │⎩  level: I⎭│ │⎩  level: II ⎭│ ⎟   ┄┄┄Function(max)┄┄┄▷  │⎩  level: II   ⎭│
      ⎝            └────────────┘ └──────────────┘ ⎠                         └────────────────┘


Remaping edges
^^^^^^^^^^^^^^

Once this fusion step is done, is it possible that the edges that were
defined by the initial adapters refer to node IDs that do not exist
anymore. Fortunately, the fuser keeps track of which ID was replaced by
which one. And this can be used to remap the edges’ *target* and
*source* identifiers:

.. code-block:: python

   remaped_edges = remap_edges(edges, fuser.ID_mapping)

Finally, the same fusion step can be done on the resulting edges (some
of which are now duplicates, because they were remapped):

.. code-block:: python

       # Find duplicates:
       on_STL = serialize.edge.SourceTargetLabel()
       edges_congregater = congregate.Edges(on_STL)
       edges_congregater(edges)

       # How to fuse them:
       set_of_ID       = merge.string.OrderedSet(reconciliate_sep)
       identicals      = merge.string.EnsureIdentical()
       in_lists        = merge.dictry.Append(reconciliate_sep)
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

.. code-block:: python

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
