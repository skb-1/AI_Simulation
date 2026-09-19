"""Converter from Pydantic JSON schemas to GBNF (GGML BNF) grammar."""

from __future__ import annotations

from typing import Any

from aicreator.commands import (
    Delete,
    Idle,
    Modify,
    SpawnCreature,
    SpawnPrimitive,
)


def _gbnf_escape_str(s: str) -> str:
    """Escape string for GBNF literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _prop_to_gbnf(name: str, prop: dict[str, Any]) -> str:
    """Generate GBNF snippet for a JSON object key-value pair."""
    prop_type = prop.get("type")
    const_val = prop.get("const")
    enum_vals = prop.get("enum")

    key_part = f'"\\"{_gbnf_escape_str(name)}\\"" ws ":" ws'

    if const_val is not None:
        val_str = f'"\\"{_gbnf_escape_str(str(const_val))}\\""'
        return f"{key_part} {val_str}"

    if enum_vals:
        alts = " | ".join(f'"\\"{_gbnf_escape_str(str(v))}\\""' for v in enum_vals)
        return f"{key_part} ({alts})"

    if prop_type == "string":
        return f"{key_part} string"
    if prop_type == "number":
        return f"{key_part} number"
    if prop_type == "integer":
        return f"{key_part} integer"
    if prop_type == "boolean":
        return f"{key_part} boolean"
    if prop_type == "array":
        prefix_items = prop.get("prefixItems")
        if prefix_items:
            items_gbnf = []
            for item in prefix_items:
                itype = item.get("type", "number")
                if itype == "integer":
                    items_gbnf.append("integer")
                else:
                    items_gbnf.append("number")
            tuple_inner = ' ws "," ws '.join(items_gbnf)
            return f'{key_part} "[" ws {tuple_inner} ws "]"'
        return f"{key_part} number-array"
    if prop_type == "object":
        return f"{key_part} string-number-dict"

    return f"{key_part} string"


def schema_to_gbnf_rule(rule_name: str, schema: dict[str, Any]) -> str:
    """Recursively convert a single Pydantic JSON schema into a GBNF rule."""
    properties = schema.get("properties", {})
    required = schema.get("required", list(properties.keys()))

    prop_rules: list[str] = []
    for prop_name in required:
        if prop_name in properties:
            prop_rules.append(_prop_to_gbnf(prop_name, properties[prop_name]))

    # For optional properties, wrap them
    optional_rules: list[str] = []
    for prop_name, prop_data in properties.items():
        if prop_name not in required:
            r = _prop_to_gbnf(prop_name, prop_data)
            optional_rules.append(f'(ws "," ws {r})?')

    parts = ' ws "," ws '.join(prop_rules)
    opt_parts = " ".join(optional_rules) if optional_rules else ""

    rule = f'{rule_name} ::= "{{" ws {parts}{opt_parts} ws "}}"'
    return rule


def build_grammar() -> str:
    """Build unified GBNF grammar for all Command models."""
    schemas = [
        ("cmd-spawn-primitive", SpawnPrimitive.model_json_schema()),
        ("cmd-spawn-creature", SpawnCreature.model_json_schema()),
        ("cmd-modify", Modify.model_json_schema()),
        ("cmd-delete", Delete.model_json_schema()),
        ("cmd-idle", Idle.model_json_schema()),
    ]

    rules = [
        r'root ::= "[" ws (command (ws "," ws command)*)? ws "]"',
        r"command ::= cmd-spawn-primitive | cmd-spawn-creature | cmd-modify | cmd-delete | cmd-idle",
    ]

    for name, schema in schemas:
        rules.append(schema_to_gbnf_rule(name, schema))

    # Core JSON primitives in GBNF
    rules.extend([
        r'string ::= "\"" ([^"\\\r\n] | "\\" ["\\/bfnrt])* "\""',
        r'number ::= "-"? [0-9]+ ("." [0-9]+)? ([eE] [-+]? [0-9]+)?',
        r'integer ::= "-"? [0-9]+',
        r'boolean ::= "true" | "false"',
        r'ws ::= [ \t\n\r]*',
        r'number-array ::= "[" ws (number (ws "," ws number)*)? ws "]"',
        r'string-number-dict ::= "{" ws (string ws ":" ws number (ws "," ws string ws ":" ws number)*)? ws "}"',
    ])

    return "\n".join(rules) + "\n"
