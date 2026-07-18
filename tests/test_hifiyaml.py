"""Comprehensive tests for hifiyaml package."""
import os
import sys
import copy

# Use hifiyaml from the repo
here = os.path.dirname(__file__)
hifiyaml_path = os.path.join(here, "..")
if hifiyaml_path not in sys.path:
    sys.path.insert(0, hifiyaml_path)

import hifiyaml as hy  # noqa: E402
import pytest  # noqa: E402


# ============================================================
# Fixtures
# ============================================================

SIMPLE_YAML = """\
server:
  host: localhost
  port: 8080
  database:
    name: mydb
    port: 5432
    credentials:
      user: admin
      password: secret
  cache:
    - redis
    - memcached
    - varnish"""

COMMENTED_YAML = """\
# Top-level comment
application:
  # Database section
  database:
    host: localhost
    port: 5432
  # Cache section
  cache:
    enabled: true"""

LIST_YAML = """\
observers:
  - obs space:
      name: aircraft
      type: H5File
  - obs space:
      name: radiosonde
      type: H5File
  - obs space:
      name: satellite
      type: H5File"""

ANCHOR_YAML = """\
_defaults: &defaults
  adapter: postgres
  host: localhost

development:
  <<: *defaults
  database: myapp_dev

production:
  <<: *defaults
  database: myapp_prod"""

TEMPLATE_YAML = """\
config:
  date: '@runDate@'
  output: '@outputDir@/result.nc'
  name: '@appName@'"""

NESTED_LIST_YAML = """\
filters:
  - filter: RejectList
    filter variables:
    - name: airTemperature
    where:
    - variable: QualityMarker/airTemperature
      is_in: 4-15
    action:
      name: reduce obs space
  - filter: Domain Check
    where:
      - variable:
          name: MetaData/timeOffset
        minvalue: -900
        maxvalue: 900
  - filter: Bounds Check
    filter variables:
    - name: airTemperature
    minvalue: 100
    maxvalue: 400"""

FLOW_STYLE_YAML = """\
settings:
  variables: [temp, pressure, humidity]
  options: {debug: true, verbose: false}
  simple: value"""

MULTIBLOCK_YAML = """\
section_a:
  key1: value1
  key2: value2

section_b:
  key3: value3
  key4: value4

section_c:
  key5: value5"""

EMPTY_LINES_YAML = """\
top:
  first: 1

  second: 2

  third: 3"""


@pytest.fixture
def simple_data():
    return hy.text_to_yblock(SIMPLE_YAML)


@pytest.fixture
def commented_data():
    return hy.text_to_yblock(COMMENTED_YAML)


@pytest.fixture
def list_data():
    return hy.text_to_yblock(LIST_YAML)


@pytest.fixture
def anchor_data():
    return hy.text_to_yblock(ANCHOR_YAML)


@pytest.fixture
def template_file(tmp_path):
    f = tmp_path / "template.yaml"
    f.write_text(TEMPLATE_YAML)
    return str(f)


@pytest.fixture
def nested_list_data():
    return hy.text_to_yblock(NESTED_LIST_YAML)


@pytest.fixture
def flow_style_data():
    return hy.text_to_yblock(FLOW_STYLE_YAML)


@pytest.fixture
def multiblock_data():
    return hy.text_to_yblock(MULTIBLOCK_YAML)


# ============================================================
# Tests: load()
# ============================================================

class TestLoad:
    def test_load_basic(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text("key: value\nlist:\n  - item1\n  - item2\n")
        data = hy.load(str(f))
        assert data[0] == "key: value"
        assert data[1] == "list:"
        assert data[2] == "  - item1"
        assert data[3] == "  - item2"

    def test_load_preserves_trailing_whitespace(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text("key: value   \nother: data  \n")
        data = hy.load(str(f))
        assert data[0] == "key: value   "
        assert data[1] == "other: data  "

    def test_load_preserves_leading_whitespace(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text("parent:\n    child: value\n")
        data = hy.load(str(f))
        assert data[1] == "    child: value"

    def test_load_with_replacements(self, template_file):
        data = hy.load(template_file, replacements={
            "runDate": "2024-01-15",
            "outputDir": "/data/out",
            "appName": "myapp"
        })
        assert "date: '2024-01-15'" in data[1]
        assert "output: '/data/out/result.nc'" in data[2]
        assert "name: 'myapp'" in data[3]

    def test_load_with_partial_replacements(self, template_file):
        data = hy.load(template_file, replacements={"runDate": "2024-01-15"})
        assert "2024-01-15" in data[1]
        # Unreplaced variables stay as-is
        assert "@outputDir@" in data[2]

    def test_load_with_no_replacements(self, template_file):
        data = hy.load(template_file)
        assert "@runDate@" in data[1]

    def test_load_empty_file(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        data = hy.load(str(f))
        assert data == []


# ============================================================
# Tests: text_to_yblock()
# ============================================================

class TestTextToYblock:
    def test_basic(self):
        block = hy.text_to_yblock("line1\nline2\nline3")
        assert block == ["line1", "line2", "line3"]

    def test_single_line(self):
        block = hy.text_to_yblock("single")
        assert block == ["single"]

    def test_empty_string(self):
        block = hy.text_to_yblock("")
        assert block == []  # splitlines() on empty string returns []

    def test_preserves_indentation(self):
        text = "parent:\n  child: value\n    grandchild: deep"
        block = hy.text_to_yblock(text)
        assert block[1] == "  child: value"
        assert block[2] == "    grandchild: deep"


# ============================================================
# Tests: strip_indentations()
# ============================================================

class TestStripIndentations:
    def test_no_indentation(self):
        nspace, spaces, content = hy.strip_indentations("key: value")
        assert nspace == 0
        assert spaces == ""
        assert content == "key: value"

    def test_with_indentation(self):
        nspace, spaces, content = hy.strip_indentations("    key: value")
        assert nspace == 4
        assert spaces == "    "
        assert content == "key: value"

    def test_empty_string(self):
        nspace, spaces, content = hy.strip_indentations("")
        assert nspace == 0
        assert spaces == ""
        assert content == ""

    def test_only_spaces(self):
        nspace, spaces, content = hy.strip_indentations("     ")
        assert nspace == 5
        assert spaces == "     "
        assert content == ""

    def test_list_item(self):
        nspace, spaces, content = hy.strip_indentations("  - item")
        assert nspace == 2
        assert spaces == "  "
        assert content == "- item"


# ============================================================
# Tests: strip_leading_empty_lines()
# ============================================================

class TestStripLeadingEmptyLines:
    def test_with_leading_empty_lines(self):
        block = ["", "", "key: value", "other: data"]
        hy.strip_leading_empty_lines(block)
        assert block == ["key: value", "other: data"]

    def test_no_leading_empty_lines(self):
        block = ["key: value", "other: data"]
        hy.strip_leading_empty_lines(block)
        assert block == ["key: value", "other: data"]

    def test_all_empty_lines(self):
        block = ["", "", ""]
        hy.strip_leading_empty_lines(block)
        assert block == []

    def test_empty_block(self):
        block = []
        hy.strip_leading_empty_lines(block)
        assert block == []

    def test_preserves_trailing_empty_lines(self):
        block = ["", "key: value", "", "other: data", ""]
        hy.strip_leading_empty_lines(block)
        assert block == ["key: value", "", "other: data", ""]


# ============================================================
# Tests: dedent()
# ============================================================

class TestDedent:
    def test_basic_dedent(self):
        block = ["    key1: value1", "    key2: value2"]
        hy.dedent(block)
        assert block == ["key1: value1", "key2: value2"]

    def test_nested_dedent(self):
        block = ["    parent:", "      child: value"]
        hy.dedent(block)
        assert block == ["parent:", "  child: value"]

    def test_no_indentation(self):
        block = ["key1: value1", "key2: value2"]
        hy.dedent(block)
        assert block == ["key1: value1", "key2: value2"]

    def test_with_comments(self):
        block = ["# comment", "    key: value", "    other: data"]
        hy.dedent(block)
        # Comment might have less indentation, dedent uses first non-comment line
        assert block[1] == "key: value"
        assert block[2] == "other: data"

    def test_all_comments_no_action(self):
        block = ["# comment1", "# comment2"]
        original = block.copy()
        hy.dedent(block)
        assert block == original

    def test_mixed_indentation_with_child(self):
        block = ["  parent:", "    child: value", "    other: data"]
        hy.dedent(block)
        assert block == ["parent:", "  child: value", "  other: data"]


# ============================================================
# Tests: get_start_pos()
# ============================================================

class TestGetStartPos:
    def test_find_top_level_key(self, simple_data):
        pos, err = hy.get_start_pos(simple_data, "server")
        assert err is None
        assert simple_data[pos].strip().startswith("server")

    def test_find_nested_key(self, simple_data):
        pos, err = hy.get_start_pos(simple_data, "server/database/name")
        assert err is None
        assert "name: mydb" in simple_data[pos]

    def test_find_deeply_nested(self, simple_data):
        pos, err = hy.get_start_pos(simple_data, "server/database/credentials/user")
        assert err is None
        assert "user: admin" in simple_data[pos]

    def test_key_not_found(self, simple_data):
        pos, err = hy.get_start_pos(simple_data, "nonexistent")
        assert err is not None
        assert "not found" in err

    def test_nested_key_not_found(self, simple_data):
        pos, err = hy.get_start_pos(simple_data, "server/nonexistent")
        assert err is not None

    def test_list_index(self, list_data):
        pos, err = hy.get_start_pos(list_data, "observers/0")
        assert err is None
        assert "- obs space:" in list_data[pos]

    def test_list_index_1(self, list_data):
        pos, err = hy.get_start_pos(list_data, "observers/1")
        assert err is None
        # Should find the second observer
        pos2 = hy.next_pos(list_data, pos, "observers/1")
        block = list_data[pos:pos2]
        assert any("radiosonde" in line for line in block)

    def test_list_index_2(self, list_data):
        pos, err = hy.get_start_pos(list_data, "observers/2")
        assert err is None
        pos2 = hy.next_pos(list_data, pos, "observers/2")
        block = list_data[pos:pos2]
        assert any("satellite" in line for line in block)

    def test_linestr_search(self, nested_list_data):
        pos, err = hy.get_start_pos(nested_list_data, linestr="- filter: Bounds Check")
        assert err is None
        assert "Bounds Check" in nested_list_data[pos]

    def test_linestr_not_found(self, nested_list_data):
        pos, err = hy.get_start_pos(nested_list_data, linestr="- filter: NonExistent")
        assert err is not None

    def test_empty_querystr_and_linestr(self, simple_data):
        pos, err = hy.get_start_pos(simple_data, querystr="", linestr="")
        assert pos == -1


# ============================================================
# Tests: next_pos()
# ============================================================

class TestNextPos:
    def test_next_peer(self, simple_data):
        pos, _ = hy.get_start_pos(simple_data, "server/host")
        npos = hy.next_pos(simple_data, pos, "server/host")
        assert "port:" in simple_data[npos]

    def test_next_peer_skips_children(self, simple_data):
        pos, _ = hy.get_start_pos(simple_data, "server/database")
        npos = hy.next_pos(simple_data, pos, "server/database")
        assert "cache:" in simple_data[npos]

    def test_end_of_data(self, simple_data):
        pos, _ = hy.get_start_pos(simple_data, "server/cache")
        npos = hy.next_pos(simple_data, pos, "server/cache")
        assert npos == len(simple_data)

    def test_list_element_next(self, list_data):
        pos, _ = hy.get_start_pos(list_data, "observers/0")
        npos = hy.next_pos(list_data, pos, "observers/0")
        # Next position should be the start of the second observer
        assert "- obs space:" in list_data[npos]

    def test_pos_negative_one(self, simple_data):
        npos = hy.next_pos(simple_data, -1)
        assert npos == len(simple_data)

    def test_multiblock_sections(self, multiblock_data):
        pos, _ = hy.get_start_pos(multiblock_data, "section_a")
        npos = hy.next_pos(multiblock_data, pos, "section_a")
        # Should point to section_b (skipping the empty line)
        assert "section_b:" in multiblock_data[npos]


# ============================================================
# Tests: get()
# ============================================================

class TestGet:
    def test_get_single_value(self, simple_data):
        block = hy.get(simple_data, "server/host")
        assert len(block) == 1
        assert "host: localhost" in block[0]

    def test_get_block_with_children(self, simple_data):
        block = hy.get(simple_data, "server/database")
        assert any("name: mydb" in line for line in block)
        assert any("port: 5432" in line for line in block)
        assert any("credentials:" in line for line in block)

    def test_get_with_dedent(self, simple_data):
        block = hy.get(simple_data, "server/database", do_dedent=True)
        # First non-comment line should have no indentation
        for line in block:
            if line.strip() and not line.strip().startswith("#"):
                assert not line.startswith(" ")
                break

    def test_get_without_dedent(self, simple_data):
        block = hy.get(simple_data, "server/database")
        # Should have original indentation
        for line in block:
            if "database:" in line:
                assert line.startswith("  ")
                break

    def test_get_full_document(self, simple_data):
        block = hy.get(simple_data, "")
        assert block == simple_data[0:len(simple_data)]

    def test_get_includes_leading_comments(self, commented_data):
        block = hy.get(commented_data, "application/database")
        assert any("# Database section" in line for line in block)

    def test_get_list_element(self, list_data):
        block = hy.get(list_data, "observers/1")
        assert any("radiosonde" in line for line in block)

    def test_get_preserves_inline_comments(self):
        yaml_text = "config:\n  key: value # important comment\n  other: data"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "config/key")
        assert "# important comment" in block[0]

    def test_get_flow_style_list(self, flow_style_data):
        block = hy.get(flow_style_data, "settings/variables")
        assert any("[temp, pressure, humidity]" in line for line in block)


# ============================================================
# Tests: dump()
# ============================================================

class TestDump:
    def test_dump_to_file(self, simple_data, tmp_path):
        outfile = str(tmp_path / "output.yaml")
        hy.dump(simple_data, "server/database", fpath=outfile)
        assert os.path.exists(outfile)
        with open(outfile) as f:
            content = f.read()
        assert "name: mydb" in content
        assert "port: 5432" in content

    def test_dump_full_document(self, simple_data, tmp_path):
        outfile = str(tmp_path / "full.yaml")
        hy.dump(simple_data, "", fpath=outfile)
        with open(outfile) as f:
            lines = f.readlines()
        assert len(lines) == len(simple_data)

    def test_dump_with_dedent(self, simple_data, tmp_path):
        outfile = str(tmp_path / "dedented.yaml")
        hy.dump(simple_data, "server/database", fpath=outfile, do_dedent=True)
        with open(outfile) as f:
            first_line = f.readline()
        assert first_line.startswith("database:")

    def test_dump_to_stdout(self, simple_data, capsys):
        hy.dump(simple_data, "server/host")
        captured = capsys.readouterr()
        assert "host: localhost" in captured.out


# ============================================================
# Tests: drop()
# ============================================================

class TestDrop:
    def test_drop_block(self, simple_data):
        original_len = len(simple_data)
        hy.drop(simple_data, "server/cache")
        assert len(simple_data) < original_len
        assert not any("cache" in line for line in simple_data)
        assert not any("redis" in line for line in simple_data)

    def test_drop_single_value(self, simple_data):
        hy.drop(simple_data, "server/host")
        assert not any("host: localhost" in line for line in simple_data)
        # Other keys should remain
        assert any("port: 8080" in line for line in simple_data)

    def test_drop_nested(self, simple_data):
        hy.drop(simple_data, "server/database/credentials")
        assert not any("user: admin" in line for line in simple_data)
        assert not any("password: secret" in line for line in simple_data)
        # Parent should remain
        assert any("name: mydb" in line for line in simple_data)

    def test_drop_empty_querystr(self, simple_data):
        original = simple_data.copy()
        hy.drop(simple_data, "")
        assert simple_data == original  # No change

    def test_drop_nonexistent_key(self, simple_data):
        original = simple_data.copy()
        hy.drop(simple_data, "nonexistent")
        assert simple_data == original  # No change, no error

    def test_drop_list_element(self, list_data):
        hy.drop(list_data, "observers/1")
        # radiosonde should be gone
        assert not any("radiosonde" in line for line in list_data)
        # Others should remain
        assert any("aircraft" in line for line in list_data)
        assert any("satellite" in line for line in list_data)

    def test_drop_with_leading_comments(self, commented_data):
        hy.drop(commented_data, "application/database")
        assert not any("Database section" in line for line in commented_data)
        assert not any("host: localhost" in line for line in commented_data)

    def test_drop_preserves_other_blocks(self, multiblock_data):
        hy.drop(multiblock_data, "section_b")
        assert any("section_a:" in line for line in multiblock_data)
        assert any("key1: value1" in line for line in multiblock_data)
        assert any("section_c:" in line for line in multiblock_data)
        assert not any("key3: value3" in line for line in multiblock_data)


# ============================================================
# Tests: modify()
# ============================================================

class TestModify:
    def test_modify_single_value(self, simple_data):
        hy.modify(simple_data, "server/host", "host: 10.0.0.1")
        assert any("host: 10.0.0.1" in line for line in simple_data)
        assert not any("host: localhost" in line for line in simple_data)

    def test_modify_preserves_indentation(self, simple_data):
        hy.modify(simple_data, "server/database/name", "name: production_db")
        for line in simple_data:
            if "production_db" in line:
                # Should have same indentation as the original
                nspace = hy.strip_indentations(line)[0]
                assert nspace == 4  # same as original "    name: mydb"
                break

    def test_modify_with_multiline_string(self, simple_data):
        new_db = "database:\n  name: newdb\n  port: 3306\n  engine: mysql"
        hy.modify(simple_data, "server/database", new_db)
        assert any("newdb" in line for line in simple_data)
        assert any("mysql" in line for line in simple_data)
        assert not any("mydb" in line for line in simple_data)

    def test_modify_with_block_list(self, simple_data):
        new_block = ["database:", "  name: replaced", "  port: 9999"]
        hy.modify(simple_data, "server/database", new_block)
        assert any("replaced" in line for line in simple_data)
        assert any("9999" in line for line in simple_data)

    def test_modify_empty_querystr_noop(self, simple_data):
        original = simple_data.copy()
        hy.modify(simple_data, "", "anything")
        assert simple_data == original

    def test_modify_nonexistent_key(self, simple_data):
        original = simple_data.copy()
        hy.modify(simple_data, "nonexistent", "value: new")
        assert simple_data == original  # No change

    def test_modify_list_element(self, list_data):
        new_observer = "- obs space:\n    name: ground_station\n    type: CSV"
        hy.modify(list_data, "observers/0", new_observer)
        assert any("ground_station" in line for line in list_data)
        assert not any("aircraft" in line for line in list_data)

    def test_modify_aligns_indentation(self):
        yaml_text = "top:\n  nested:\n    deep:\n      key: old_value"
        data = hy.text_to_yblock(yaml_text)
        hy.modify(data, "top/nested/deep/key", "key: new_value")
        for line in data:
            if "new_value" in line:
                nspace = hy.strip_indentations(line)[0]
                assert nspace == 6  # matches original "      key:"
                break

    def test_modify_with_loaded_file(self, tmp_path):
        # Write main file
        main_file = tmp_path / "main.yaml"
        main_file.write_text("config:\n  database:\n    host: old\n    port: 1234\n")
        # Write replacement file
        repl_file = tmp_path / "new_db.yaml"
        repl_file.write_text("database:\n  host: new_host\n  port: 5678\n")

        data = hy.load(str(main_file))
        newblock = hy.load(str(repl_file))
        hy.modify(data, "config/database", newblock)
        assert any("new_host" in line for line in data)
        assert not any("old" in line for line in data)


# ============================================================
# Tests: Comment handling
# ============================================================

class TestCommentHandling:
    def test_leading_comments_included_in_get(self):
        yaml_text = "items:\n  # Important note\n  key: value\n  other: data"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "items/key")
        assert any("Important note" in line for line in block)

    def test_inline_comments_preserved(self):
        yaml_text = "config:\n  host: localhost # primary server\n  port: 8080"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "config/host")
        assert "# primary server" in block[0]

    def test_commented_out_block_not_matched(self):
        yaml_text = "items:\n  # key: old_value\n  key: real_value"
        data = hy.text_to_yblock(yaml_text)
        pos, err = hy.get_start_pos(data, "items/key")
        assert err is None
        assert "real_value" in data[pos]

    def test_drop_removes_leading_comments(self):
        yaml_text = "top:\n  # Comment for A\n  a: 1\n  b: 2"
        data = hy.text_to_yblock(yaml_text)
        hy.drop(data, "top/a")
        assert not any("Comment for A" in line for line in data)
        assert any("b: 2" in line for line in data)

    def test_multiline_comments_before_block(self):
        yaml_text = "items:\n  # Line 1\n  # Line 2\n  key: value\n  other: data"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "items/key")
        assert any("Line 1" in line for line in block)
        assert any("Line 2" in line for line in block)


# ============================================================
# Tests: Anchor & Alias preservation
# ============================================================

class TestAnchorAlias:
    def test_anchors_preserved_in_load(self, anchor_data):
        assert any("&defaults" in line for line in anchor_data)

    def test_aliases_preserved_in_load(self, anchor_data):
        assert any("*defaults" in line for line in anchor_data)

    def test_get_block_with_anchor(self, anchor_data):
        block = hy.get(anchor_data, "_defaults")
        assert any("&defaults" in line for line in block)

    def test_modify_preserves_unrelated_anchors(self, anchor_data):
        hy.modify(anchor_data, "development/database", "database: new_dev_db")
        # Anchor should still be there
        assert any("&defaults" in line for line in anchor_data)


# ============================================================
# Tests: Edge cases
# ============================================================

class TestEdgeCases:
    def test_empty_data(self):
        data = []
        pos, err = hy.get_start_pos(data, "key")
        assert err is not None

    def test_single_line_data(self):
        data = ["key: value"]
        block = hy.get(data, "key")
        assert block == ["key: value"]

    def test_deeply_nested_query(self):
        yaml_text = "a:\n  b:\n    c:\n      d:\n        e: deep"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "a/b/c/d/e")
        assert any("deep" in line for line in block)

    def test_key_with_special_characters(self):
        yaml_text = 'config:\n  "special:key": value\n  normal: data'
        data = hy.text_to_yblock(yaml_text)
        # hifiyaml matches by substring, so this should work
        pos, err = hy.get_start_pos(data, 'config/"special:key"')
        assert err is None

    def test_value_with_colon(self):
        yaml_text = "urls:\n  api: http://localhost:8080\n  db: postgres://localhost:5432"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "urls/api")
        assert any("http://localhost:8080" in line for line in block)

    def test_empty_lines_between_blocks(self, multiblock_data):
        block = hy.get(multiblock_data, "section_b")
        assert any("key3: value3" in line for line in block)

    def test_flow_style_list_as_opaque(self, flow_style_data):
        block = hy.get(flow_style_data, "settings/variables")
        # Entire flow-style list is one line
        assert len(block) == 1
        assert "[temp, pressure, humidity]" in block[0]

    def test_multiline_flow_list_indented(self):
        # Multi-line flow-style requires continuation lines to be indented
        yaml_text = "config:\n  numbers: [1, 2, 3,\n      4, 5, 6]\n  name: test"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "config/numbers")
        assert len(block) == 2
        assert "4, 5, 6]" in block[1]
        block2 = hy.get(data, "config/name")
        assert any("test" in line for line in block2)

    def test_multiline_flow_dict_indented(self):
        yaml_text = "settings:\n  person: {name: Alice,\n      age: 30}\n  next: val"
        data = hy.text_to_yblock(yaml_text)
        block = hy.get(data, "settings/person")
        assert len(block) == 2
        assert "age: 30}" in block[1]
        block2 = hy.get(data, "settings/next")
        assert any("val" in line for line in block2)

    def test_modify_then_get_roundtrip(self, simple_data):
        hy.modify(simple_data, "server/host", "host: newhost")
        block = hy.get(simple_data, "server/host")
        assert "newhost" in block[0]

    def test_multiple_operations(self, simple_data):
        # Drop, then modify, then get
        hy.drop(simple_data, "server/cache")
        hy.modify(simple_data, "server/host", "host: modified")
        block = hy.get(simple_data, "server/host")
        assert "modified" in block[0]
        assert not any("cache" in line for line in simple_data)

    def test_data_integrity_after_modify(self, simple_data):
        # Ensure no data corruption
        original_has_port = any("port: 8080" in line for line in simple_data)
        hy.modify(simple_data, "server/host", "host: changed")
        still_has_port = any("port: 8080" in line for line in simple_data)
        assert original_has_port == still_has_port

    def test_list_out_of_bounds(self, list_data, capsys):
        # When list index exceeds actual elements, get_start_pos returns an error
        pos, err = hy.get_start_pos(list_data, "observers/99")
        assert err is not None


# ============================================================
# Tests: Integration with demo.yaml
# ============================================================

class TestIntegrationDemo:
    @pytest.fixture
    def demo_data(self):
        demo_path = os.path.join(here, "demo.yaml")
        if os.path.exists(demo_path):
            return hy.load(demo_path)
        pytest.skip("demo.yaml not found")

    def test_dump_obs_filter_0(self, demo_data):
        block = hy.get(demo_data, "cost function/observations/observers/0/obs filters/0", do_dedent=True)
        assert any("RejectList" in line for line in block)

    def test_dump_obs_filter_1(self, demo_data):
        block = hy.get(demo_data, "cost function/observations/observers/0/obs filters/1", do_dedent=True)
        assert any("Domain Check" in line for line in block)

    def test_dump_obs_filter_with_comments(self, demo_data):
        block = hy.get(demo_data, "cost function/observations/observers/0/obs filters/2", do_dedent=True)
        assert any("Bounds Check" in line for line in block)

    def test_modify_distribution_name(self, demo_data):
        data = copy.copy(demo_data)
        hy.modify(data, "cost function/observations/observers/0/distribution/name", 'name: "Halo"')
        block = hy.get(data, "cost function/observations/observers/0/distribution/name")
        assert any("Halo" in line for line in block)

    def test_drop_filter(self, demo_data):
        data = copy.copy(demo_data)
        hy.drop(data, "cost function/observations/observers/0/obs filters/1")
        # The Domain Check filter should be gone
        # Check the block was removed (Domain Check was filter index 1)
        block_after = hy.get(data, "cost function/observations/observers/0/obs filters/0", do_dedent=True)
        assert any("RejectList" in line for line in block_after)

    def test_modify_bec_component(self, demo_data):
        bec_path = os.path.join(here, "bec_bump.yaml")
        if not os.path.exists(bec_path):
            pytest.skip("bec_bump.yaml not found")
        data = copy.copy(demo_data)
        newblock = hy.load(bec_path)
        hy.modify(data, "cost function/background error/components/0", newblock)
        assert any("SABER" in line for line in data)

    def test_next_pos_from_line(self, demo_data):
        # Line 641 in original test
        if len(demo_data) > 641:
            npos = hy.next_pos(demo_data, 641)
            assert isinstance(npos, int)
            assert npos > 641

    def test_dump_observers_1_obs_operator(self, demo_data, capsys):
        """Test that querying a key in a non-first list item works (the .../N/key fix)."""
        block = hy.get(demo_data, "observations/observers/1/obs operator", do_dedent=True)
        assert block[0] == "obs operator:"
        assert any("VertInterp" in line for line in block)
        assert any("name: airTemperature" in line for line in block)
        # Should NOT include content from the next sibling key (linear obs operator)
        assert not any("linear obs operator" in line for line in block)
        # Should not trigger out-of-bounds warning during list traversal
        captured = capsys.readouterr()
        assert "out of the list index" not in captured.err

    def test_invalid_key_in_block_returns_error(self, demo_data, capsys):
        """Test that querying a non-existent key within a block returns empty and emits error."""
        block = hy.get(demo_data, "observations/observers/1/obs filters/0/obs operator")
        assert block == []
        captured = capsys.readouterr()
        assert "obs operator" in captured.err


# ============================================================
# Tests: Serialization roundtrip
# ============================================================

class TestRoundtrip:
    def test_load_dump_roundtrip(self, tmp_path):
        original = "server:\n  host: localhost\n  port: 8080\n"
        infile = tmp_path / "input.yaml"
        infile.write_text(original)
        outfile = tmp_path / "output.yaml"

        data = hy.load(str(infile))
        hy.dump(data, "", fpath=str(outfile))

        with open(str(outfile)) as f:
            result = f.read()
        # Each line should match (dump adds \n to each line)
        assert result.strip() == original.strip()

    def test_get_dump_preserves_content(self, simple_data, tmp_path):
        outfile = str(tmp_path / "block.yaml")
        block = hy.get(simple_data, "server/database")
        # Manually write
        with open(outfile, 'w') as f:
            for line in block:
                f.write(line + '\n')
        # Reload
        reloaded = hy.load(outfile)
        assert reloaded == block


# ============================================================
# Tests: printd (debug output)
# ============================================================

class TestPrintd:
    def test_printd_output(self, capsys):
        hy.printd("test", "message", 123)
        captured = capsys.readouterr()
        assert "test message 123" in captured.err
