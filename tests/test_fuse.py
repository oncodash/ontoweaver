import logging

import ontoweaver

nodes = [
    ("Source:1", "Source", {"p1":"z"}),
    ("Source:1", "Source", {"p2":"y"}), # Simple duplicate.
    ("Target:2", "Target", {}),
    ("Target:2", "Target1", {"p1":"x", "p2":"y"}),
    ("Target:2", "Target2", {"p2":"z"}),
]

on_ID = ontoweaver.serialize.ID()
congregater = ontoweaver.congregate.Nodes(on_ID)
congregater(nodes)

as_keys  = ontoweaver.merge.string.UseKey()
as_first = ontoweaver.merge.string.UseFirst()
in_lists = ontoweaver.merge.dictry.Append()
fuser = ontoweaver.fuse.Members(ontoweaver.base.Node,
        merge_ID    = as_keys,
        merge_label = as_first,
        merge_prop  = in_lists,
    )

fusioner = ontoweaver.fusion.Fusioner(fuser)
fusioned = fusioner(congregater)

logging.debug("Fusioned items:")
for f in fusioned:
    logging.debug("  "+repr(f))

assert(len(fusioned) == 2)
for e in fusioned:
    assert("p1" in e.properties)
    assert("p2" in e.properties)
    assert("y" in e.properties["p2"])

assert(len(fuser.ID_mapping) == 0) # Only self-mappings.

as_sets = ontoweaver.merge.string.OrderedSet(".")
in_lists2 = ontoweaver.merge.dictry.Append(";")
fuser2 = ontoweaver.fuse.Members(ontoweaver.base.Node,
        merge_ID    = as_keys,
        merge_label = as_sets,
        merge_prop  = in_lists2,
    )

fusioner2 = ontoweaver.fusion.Fusioner(fuser2)
fusioned2 = fusioner2(congregater)

logging.debug("Fusioned items:")
for f in fusioned2:
    logging.debug("  "+repr(f))

assert(len(fusioned2) == 2)
for e in fusioned2:
    assert("p1" in e.properties)
    assert("p2" in e.properties)
    assert("y" in e.properties["p2"])
