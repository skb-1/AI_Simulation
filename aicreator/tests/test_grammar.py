"""Unit tests for GBNF grammar conversion."""

from aicreator.commands import SpawnPrimitive
from aicreator.grammar import build_grammar, schema_to_gbnf_rule


def test_schema_to_gbnf():
    schema = SpawnPrimitive.model_json_schema()
    rule = schema_to_gbnf_rule("cmd-spawn-primitive", schema)
    assert "cmd-spawn-primitive ::=" in rule
    assert "action" in rule


def test_build_grammar():
    grammar = build_grammar()
    assert "root ::=" in grammar
    assert "command ::=" in grammar
    assert "cmd-spawn-primitive" in grammar
    assert "cmd-spawn-creature" in grammar
    assert "number ::=" in grammar
    assert "string ::=" in grammar
