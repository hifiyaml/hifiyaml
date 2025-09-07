#!/usr/bin/env python
import os
import sys

# for hifiyaml tests, we use the hifiyaml in this repo
#   instead of the installed hifiyaml
here = os.path.dirname(__file__)
hifiyaml_path = os.path.join(here, "..")
if hifiyaml_path not in sys.path:
    sys.path.insert(0, hifiyaml_path)
import hifiyaml as hy  # noqa: E402

args = sys.argv
nargs = len(args) - 1
if nargs < 3:
    print(f"{os.path.basename(args[0])} <file> <dump|drop|modify> <querystr> [newblock] [nodedent]")
    exit()

newblock, dedent = "", True   # default values

yfile = args[1]
operator = args[2]
if nargs > 2:
    querystr = args[3]
else:
    hy.printd("!!no querystr provided!!")
    sys.exit(1)
if nargs > 3:
    if operator == "modify":
        newblock = args[4]
    elif operator == "dump":
        dedent = (args[4] != "nodedent")

data = hy.load(yfile)

if operator == "dump":
    hy.dump(data, querystr, do_dedent=dedent)
elif operator == "drop":
    hy.drop(data, querystr)
elif operator == "modify":
    if newblock:
        hy.modify(data, querystr, newblock)
    else:
        print("newblock cannot be empty for the modify operator")
