# hifiyaml User Guide

A high-fidelity WYSIWYG YAML parser and emitter that preserves exact formatting,
including comments, anchors, aliases, blank lines, and indentation.

## Installation

```bash
pip install hifiyaml
```

## Why hifiyaml?

Traditional YAML libraries (PyYAML, ruamel.yaml) parse YAML into Python objects,
which destroys comments, formatting, and ordering. `hifiyaml` treats YAML as
structured text — it reads the file into a list of lines and lets you query, extract,
modify, and drop blocks while preserving everything exactly as-is.

**Use cases:**
- Programmatically editing large YAML configs (CI/CD, scientific workflows)
- Preserving comments and formatting in version-controlled configs
- Template-based YAML generation with `@VAR@` substitution

---

## Quick Start

```python
import hifiyaml as hy

# Load a YAML file into a list of lines
data = hy.load("jedivar.yaml")

# Extract a block by query string
block = hy.get(data, "cost function/geometry")
print(block)

# Dump a block to stdout
hy.dump(data, "cost function/geometry")

# Dump a block to a file (with dedent to remove parent indentation)
hy.dump(data, "cost function/geometry", "geometry.yaml", do_dedent=True)
```

---

## Core Concepts

### Query Strings

A **querystr** is a `/`-separated path from a root key down to a target block:

```yaml
# jedivar.yaml
cost function:
  cost type: 3D-Var
  time window:
     begin: '@beginDate@'
     length: PT4H
  jb evaluation: false
  geometry:
    nml_file: ./namelist.atmosphere
    streams_file: ./streams.atmosphere
    deallocate non-da fields: true
    interpolation type: unstructured
```

| querystr | Result |
|----------|--------|
| `"cost function"` | The entire `cost function:` block (all children) |
| `"cost function/time window"` | The `time window:` block with begin and length |
| `"cost function/time window/begin"` | Just `begin: '@beginDate@'` |
| `"cost function/geometry"` | The `geometry:` block with all 4 keys |
| `"cost function/geometry/nml_file"` | Just `nml_file: ./namelist.atmosphere` |

**Rules:**
- Dictionary keys are matched by finding a line starting with `key:` (after stripping leading spaces)
- List indices are integers (0-based) that count `- ` entries
- Leading/trailing `/` are stripped automatically

---

## API Reference

### `load(fpath, replacements=None)`

Load a YAML file into a list of lines.

```python
# Simple load
data = hy.load("config.yaml")

# Load with template variable substitution
data = hy.load("template.yaml", replacements={
    "analysisDate": "2024-01-15T00:00:00Z",
    "outputDir": "/data/output"
})
```

Template variables in the YAML file use `@VAR@` syntax:
```yaml
date: '@analysisDate@'
output: '@outputDir@/result.nc'
```

---

### `get(data, querystr, do_dedent=False)`

Extract a YAML block as a list of lines. Includes leading comment lines.

```python
data = hy.load("jedivar.yaml")

# Get a block (preserves original indentation)
block = hy.get(data, "cost function/geometry")

# Get a block with outermost extra indentation removed
block = hy.get(data, "cost function/geometry", do_dedent=True)

# Get the entire document
full = hy.get(data, "")
```

---

### `dump(data, querystr="", fpath=None, do_dedent=False)`

Print a block to stdout or write it to a file.

```python
# Print to stdout
hy.dump(data, "cost function/geometry")

# Write to file
hy.dump(data, "cost function/geometry", "geometry.yaml")

# Print with dedent (root-level indentation)
hy.dump(data, "cost function/geometry", do_dedent=True)
```

---

### `drop(data, querystr)`

Remove a block from the data (in-place). Also removes leading comments.

```python
data = hy.load("jedivar.yaml")

# Remove the jb evaluation key
hy.drop(data, "cost function/jb evaluation")

# Write the modified file
hy.dump(data, fpath="jedivar_modified.yaml")
```

---

### `modify(data, querystr, newblock)`

Replace a block with new content (in-place). The new block is automatically
dedented and re-indented to match the target position.

```python
data = hy.load("jedivar.yaml")

# Replace with a string (single line)
hy.modify(data, "cost function/time window/begin", "begin: '2024-06-15T00:00:00Z'")

# Replace with a multi-line string
new_geometry = """\
geometry:
  nml_file: ./namelist.atmosphere_new
  streams_file: ./streams.atmosphere_new
  deallocate non-da fields: true
  interpolation type: unstructured"""
hy.modify(data, "cost function/geometry", new_geometry)

# Replace with a block loaded from another file
newblock = hy.load("new_geometry.yaml")
hy.modify(data, "cost function/geometry", newblock)

# Write result
hy.dump(data, fpath="jedivar_updated.yaml")
```

---

### `get_start_pos(data, querystr="", stop_on_error=False, linestr="")`

Find the starting line index of a block. Returns `(position, error_message)`.

```python
# Find by querystr
pos, err = hy.get_start_pos(data, "cost function/geometry")
if err is None:
    print(f"Block starts at line {pos}")

# Find by line content (useful for unique lines)
pos, err = hy.get_start_pos(data, linestr="- filter: Temporal Thinning")
```

---

### `next_pos(data, pos, querystr="")`

Find the end boundary (exclusive) of a block starting at `pos`.

```python
pos1, _ = hy.get_start_pos(data, "cost function/geometry")
pos2 = hy.next_pos(data, pos1, "cost function/geometry")
# data[pos1:pos2] is the complete block
print(f"Block spans lines {pos1} to {pos2-1}")
```

---

### `text_to_yblock(text)`

Convert a multi-line string to a list of lines (same format as `load()` output).

```python
text = """\
database:
  host: localhost
  port: 5432"""
block = hy.text_to_yblock(text)
```

---

### `dedent(block)`

Remove common leading indentation from a block (in-place).

```python
block = ['    host: localhost', '    port: 5432']
hy.dedent(block)
# block is now ['host: localhost', 'port: 5432']
```

---

### `strip_indentations(ystr)`

Parse the indentation of a single line.

```python
nspace, spaces, content = hy.strip_indentations("    host: localhost")
# nspace = 4, spaces = "    ", content = "host: localhost"
```

---

### `strip_leading_empty_lines(block)`

Remove leading empty lines from a block (in-place).

```python
block = ['', '', 'host: localhost']
hy.strip_leading_empty_lines(block)
# block is now ['host: localhost']
```

---

## Practical Examples

### Example 1: Modifying a CI/CD Pipeline

```yaml
# pipeline.yaml
stages:
  build:
    image: python:3.11
    script:
      - pip install -r requirements.txt
      - python setup.py build
  test:
    image: python:3.11
    script:
      - pytest tests/
  deploy:
    image: python:3.11
    script:
      - ./deploy.sh production
```

```python
import hifiyaml as hy

data = hy.load("pipeline.yaml")

# Change the deploy target
hy.modify(data, "stages/deploy/script", "script:\n  - ./deploy.sh staging")

# Add a new environment variable by modifying the test stage
test_block = hy.get(data, "stages/test", do_dedent=True)
# Insert an env line
idx = 1  # after "test:" line
test_block.insert(idx, "  environment: CI=true")
hy.modify(data, "stages/test", test_block)

hy.dump(data, fpath="pipeline_modified.yaml")
```

### Example 2: Template-Based Config Generation

```yaml
# template.yaml
application:
  name: myapp
  version: '@APP_VERSION@'
  database:
    host: '@DB_HOST@'
    port: '@DB_PORT@'
    credentials:
      user: '@DB_USER@'
```

```python
import hifiyaml as hy

# Generate configs for different environments
envs = {
    "dev": {"APP_VERSION": "1.0.0-dev", "DB_HOST": "localhost", "DB_PORT": "5432", "DB_USER": "dev_user"},
    "prod": {"APP_VERSION": "1.0.0", "DB_HOST": "db.prod.internal", "DB_PORT": "5432", "DB_USER": "app_svc"},
}

for env_name, replacements in envs.items():
    data = hy.load("template.yaml", replacements=replacements)
    hy.dump(data, fpath=f"config_{env_name}.yaml")
```

### Example 3: Extracting and Reassembling Blocks

```python
import hifiyaml as hy

data = hy.load("large_config.yaml")

# Extract individual components
db_block = hy.get(data, "services/database", do_dedent=True)
cache_block = hy.get(data, "services/cache", do_dedent=True)

# Write them as standalone files
hy.dump(data, "services/database", "database.yaml", do_dedent=True)
hy.dump(data, "services/cache", "cache.yaml", do_dedent=True)
```

### Example 4: Dropping Sections Conditionally

```python
import hifiyaml as hy

data = hy.load("config.yaml")

# Remove debug/development sections for production
sections_to_remove = [
    "debug",
    "development",
    "testing/mock_services",
]

for section in sections_to_remove:
    pos, err = hy.get_start_pos(data, section)
    if err is None:  # Only drop if it exists
        hy.drop(data, section)

hy.dump(data, fpath="config_production.yaml")
```

### Example 5: Working with List Elements

```yaml
# observers.yaml
observers:
  - obs space:
      name: aircraft
      type: H5File
  - obs space:
      name: radiosonde
      type: H5File
  - obs space:
      name: satellite
      type: H5File
```

```python
import hifiyaml as hy

data = hy.load("observers.yaml")

# Get the second observer (index 1)
block = hy.get(data, "observers/1", do_dedent=True)

# Drop the first observer
hy.drop(data, "observers/0")

# Modify the last observer's name
hy.modify(data, "observers/1/obs space/name", '      name: satellite_v2')
```

### Example 6: Finding Blocks by Line Content

```python
import hifiyaml as hy

data = hy.load("jedivar.yaml")

# Find a specific filter without navigating the full tree
pos, err = hy.get_start_pos(data, linestr="- filter: Temporal Thinning")
if err is None:
    pos2 = hy.next_pos(data, pos)
    filter_block = data[pos:pos2]
    print("\n".join(filter_block))
```

### Example 7: Building New Blocks Programmatically

```python
import hifiyaml as hy

data = hy.load("config.yaml")

# Create a new block from an f-string
new_observer = f"""\
- obs space:
    name: new_sensor
    type: H5File
    obsdatain:
      engine:
        type: H5File
        obsfile: data/obs/new_sensor.nc"""

newblock = hy.text_to_yblock(new_observer)

# You can now use this as a replacement or manually insert it
# For insertion at a specific position:
pos, _ = hy.get_start_pos(data, "observers/0")
end = hy.next_pos(data, pos, "observers/0")
# Insert before the first observer
for i, line in enumerate(newblock):
    data.insert(pos + i, "  " + line)  # indent to match
```

---

## Tips & Best Practices

1. **Always work on a copy if you need the original:**
   ```python
   import copy
   data_copy = copy.copy(data)  # shallow copy of the list is sufficient
   ```

2. **Comments belong to the block below them:**
   Leading comment lines immediately before a block (at same or lesser indentation)
   are included when you `get()`, `drop()`, or `modify()` that block.

3. **Use `do_dedent=True` for standalone output:**
   When extracting a block to use as a standalone file, use `do_dedent=True` to
   remove the parent indentation.

4. **For list elements, include `- ` in replacements:**
   When modifying a list element, your new block must start with `- `:
   ```python
   hy.modify(data, "items/0", "- new_item: value")
   ```

5. **Flow-style collections are single-line:**
   `hifiyaml` treats `[1, 2, 3]` and `{a: 1, b: 2}` as opaque line content.
   Modify the entire line, not individual elements.

6. **The data list is mutable:**
   `drop()` and `modify()` change `data` in-place. Use `dump()` to write the
   final result.

7. **Use `linestr` for unique lines:**
   When a block has a unique identifying line (like a filter name), use
   `get_start_pos(data, linestr="...")` instead of navigating the full path.
