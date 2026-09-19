"""Unit tests for local LLM token streaming and command parsing."""

from aicreator.commands import parse_commands_json
from aicreator.llm import CreatorLLM


def test_llm_stream_generation():
    llm = CreatorLLM()
    tokens = list(llm.stream_generate("Создай лес"))
    assert len(tokens) > 0
    full_json = "".join(tokens)
    cmds = parse_commands_json(full_json)
    assert len(cmds) > 0
