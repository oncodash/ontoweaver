import re
import ast
import glob
import pandas as pd

def strip_yaml(content):
    code = []
    for line in content.split('\n'):
        # Remove comments in line
        code.append( re.sub(r'#.*$', '', line) )
        # print(line.strip(),"->",code[-1].strip())
    return '\n'.join(code)


def strip_python(script):
    code = ''
    lines = ast.unparse(ast.parse(script))
    for line in lines:
        if line.lstrip()[:1] not in ("'", '"'):
            code += line
    return code


def count(filename):
    sample = []
    with open(filename) as fd:
        content = fd.read()
        if filename.endswith(".py"):
            code = strip_python(content)
        else:
            code = strip_yaml(content)

        for line in code.split("\n"):
            if line.strip() == "":
                continue
            else:
                # print(line.strip())
                sample.append(len(line.split()))
    return sample


def token_stats(glb = "*/**/*mapping*.yaml"):
    sample = []
    for f in glob.glob(glb, recursive = True):
        sample += count(f)
    return pd.DataFrame(sample).describe()


def test_token_stats():
    stats = token_stats("*/**/*mapping*.yaml")
    print(stats)


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 1:
        print(token_stats("*/**/*mapping*.yaml"))
    else:
        print(token_stats(sys.argv[1]))

