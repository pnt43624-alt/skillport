from __future__ import annotations

from pathlib import Path

import pytest

from skillport.adapters import render_for_tool, write_skill
from skillport.models import Skill, SkillError
from skillport.registry import load_skills_from_source, search_catalog


SAMPLE = """---
name: demo-skill
description: A demo skill used in tests for validation and conversion.
license: MIT
metadata:
  tags: [test]
  globs: "**/*.py"
---

## Instructions

Do the thing carefully.
"""


def test_parse_and_validate(tmp_path: Path):
    p = tmp_path / "SKILL.md"
    p.write_text(SAMPLE, encoding="utf-8")
    skill = Skill.load(p)
    assert skill.name == "demo-skill"
    assert skill.validate() == []


def test_invalid_name():
    skill = Skill(name="Bad_Name", description="x" * 10, body="body")
    errs = skill.validate()
    assert any("name" in e for e in errs)


def test_cursor_conversion():
    skill = Skill.from_skill_md(SAMPLE)
    out = render_for_tool(skill, "cursor")
    assert "alwaysApply:" in out
    assert "demo-skill" in out
    assert "Do the thing carefully." in out
    
def test_jetbrains_conversion():
    skill = Skill.from_skill_md(SAMPLE)
    out = render_for_tool(skill, "jetbrains")

    assert "demo-skill" in out
    assert "Do the thing carefully." in out


def test_zed_conversion():
    skill = Skill.from_skill_md(SAMPLE)
    out = render_for_tool(skill, "zed")

    assert "demo-skill" in out
    assert "Do the thing carefully." in out

def test_install_to_project(tmp_path: Path):
    skill = Skill.from_skill_md(SAMPLE)
    dest = write_skill(tmp_path, "claude", skill)
    assert dest.exists()
    assert "demo-skill" in dest.read_text(encoding="utf-8")
    dest2 = write_skill(tmp_path, "cursor", skill)
    assert dest2.suffix == ".mdc"


def test_agents_md_append(tmp_path: Path):
    skill = Skill.from_skill_md(SAMPLE)
    p1 = write_skill(tmp_path, "agents", skill)
    p2 = write_skill(tmp_path, "agents", skill, force=True)
    text = p2.read_text(encoding="utf-8")
    assert text.count("skillport:demo-skill:start") == 1


def test_catalog_search():
    hits = search_catalog("review")
    assert any(h.name == "pr-review" for h in hits)


def test_load_builtin():
    skills = load_skills_from_source("commit")
    assert len(skills) == 1
    assert skills[0].name == "commit"
    assert skills[0].validate() == []


def test_missing_frontmatter():
    with pytest.raises(SkillError):
        Skill.from_skill_md("# just markdown\n")
