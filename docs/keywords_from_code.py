#!/usr/bin/env -S uv run --script
import re
import ontoweaver

if __name__ == "__main__":

    mp = ontoweaver.base.MappingParser
    doc = ""
    for k in dir(mp):
        if re.match(r"^\s*k_([a-z_]+)", k):
            doc += f"- ``{'`` = ``'.join(getattr(mp, k))}``\\n"

    print(doc)
