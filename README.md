# hifiyaml
High-fidelity YAML parser that preserves formatting.    
Original YAML structure and formatting are preserved, including comments, anchors, aliases, etc.    
Check wiki at https://github.com/hifiyaml/hifiyaml/wiki

## Installation
```
pip install hifiyaml
```

## Quick demo
### 1. Get an example YAML file
Use `jedivar.yaml` from [the RRFSv2 system](https://github.com/NOAA-EMC/rrfs-workflow/tree/rrfs-mpas-jedi) as an example.
```
wget https://raw.githubusercontent.com/NOAA-EMC/rrfs-workflow/refs/heads/rrfs-mpas-jedi/parm/jedivar.yaml
```
### 2. Load the YAML data and dump a YAML block using a querystr
Write the following statments into `test.py`:
```
import hifiyaml as hy
data = hy.load("jedivar.yaml")
querystr = "cost function/background error/components/1"
hy.dump(data, querystr)   # dump to stdout
hy.dump(data, querystr, 'ensbec.yaml')   # dump to the file 'ensbec.yaml'
```
run `python test.py`, check the stdout and the `ensbec.yaml` file.

NOTE: **A querystr** is a string describing the path from the top level key (or index if a list) to the destination level key (or index), separated with `/`.  
For the following simple YAML file,
```
demo:
  configuration:
    suite: YAML
    detail:
      - meaning:
          - Y: Yelling
          - A: At
          - M: My
          - L: Laptop
```
A query string `demo/configuration/detail/0/meaning` will return one dictionary item with "meaning" as the key and a list of 4 items as the value, i.e:
```
- meaning:
    - Y: Yelling
    - A: At
    - M: My
    - L: Laptop
```

### 3. Availabe functions.
`hifiyaml` currently provides the following functions:
```
load, get, dump, drop, modify, next_pos, get_start_pos, dedent, text_to_yblock, strip_indentations, strip_leading_empty_lines
```
