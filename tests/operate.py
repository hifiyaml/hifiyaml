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
    print(f"{os.path.basename(args[0])} <file> <dump|drop|modify|next_pos> <querystr> [newblock_str] [nodedent]")
    exit()

newblock_str, dedent = "", True   # default values

yfile = args[1]
operator = args[2]
if nargs > 2:
    querystr = args[3]
else:
    hy.printd("!!no querystr provided!!")
    sys.exit(1)
if nargs > 3:
    if operator == "modify":
        newblock_str = args[4]
        if os.path.exists(newblock_str):
            newblock = hy.load(newblock_str)
        else:
            newblock = newblock_str
    elif operator == "dump":
        dedent = (args[4] != "nodedent")
    elif operator == "next_pos":
        pos1 = int(args[4])

data = hy.load(yfile)

if operator == "dump":
    hy.dump(data, querystr, do_dedent=dedent)

elif operator == "next_pos":
    print(hy.next_pos(data, pos1, querystr))

elif operator == "drop":
    hy.drop(data, querystr)
    hy.dump(data)

elif operator == "modify":
    if newblock_str:
        hy.modify(data, querystr, newblock)
        hy.dump(data)
    else:
        print("newblock_str cannot be empty for the modify operator")
