# hifiyaml
High-fidelity YAML processing with original structure and format preserved (such as comments, anchors, aliases, etc)

## Installation
```
pip install hifiyaml
```

## Quick demo
### 1. get an example YAML file
Let's use `jedivar.yaml` from [the RRFSv2 system](https://github.com/NOAA-EMC/rrfs-workflow/tree/rrfs-mpas-jedi) as an example.
```
wget https://raw.githubusercontent.com/NOAA-EMC/rrfs-workflow/refs/heads/rrfs-mpas-jedi/parm/jedivar.yaml
```
### 2. load the YAML data and dump a subcomponent YAML block using a querystr
Write the following statments into `test.py`:
```
import hifiyaml as hy
data = hy.load("jedivar.yaml")
querystr = "cost function/background error/components/1"
hy.dump(data, querystr)
hy.dump(data, querystr, 'ensbec.yaml')
```
run `python test.py`
