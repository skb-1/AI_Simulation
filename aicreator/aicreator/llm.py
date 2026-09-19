"""LLM engine interface using llama-cpp-python with GBNF grammar constraints."""

from __future__ import annotations

import glob
import json
import os
import random
import time
from typing import Iterator

from aicreator.grammar import build_grammar
from aicreator.prompts import SYSTEM_PROMPT


def find_gguf_models(search_dir: str = "models") -> list[str]:
    """Scan directory for .gguf model weights."""
    return sorted(glob.glob(os.path.join(search_dir, "*.gguf")))


def _procedural_creator_fallback(user_prompt: str) -> str:
    """Intelligent fallback generator synthesizing commands matching user intent."""
    p_lower = user_prompt.lower()
    commands = []

    if "лес" in p_lower or "дерев" in p_lower or "forest" in p_lower or "tree" in p_lower:
        # Spawn forest of cylinders (trunks) and cones/spheres (crowns)
        for i in range(8):
            rx = random.uniform(-15.0, 15.0)
            rz = random.uniform(-15.0, 15.0)
            commands.append({
                "action": "spawn",
                "type": "cylinder",
                "position": [rx, -1.0, rz],
                "scale": [0.4, 3.0, 0.4],
                "color": [0, 143, 17],
            })
            commands.append({
                "action": "spawn",
                "type": "cone",
                "position": [rx, 2.5, rz],
                "scale": [1.5, 2.5, 1.5],
                "color": [0, 255, 65],
            })
        commands.append({
            "action": "spawn_creature",
            "kind": "animal",
            "species": "deer",
            "position": [2.0, 0.0, 2.0],
            "name": "Bambi",
            "traits": {"speed": 2.2, "aggression": 0.0},
        })

    elif "волк" in p_lower or "олен" in p_lower or "стая" in p_lower or "wolf" in p_lower:
        # Wolves and deer
        for i in range(3):
            commands.append({
                "action": "spawn_creature",
                "kind": "animal",
                "species": "wolf",
                "position": [random.uniform(-10, -5), 0.0, random.uniform(-5, 5)],
                "name": f"Wolf_{i+1}",
                "traits": {"speed": 3.0, "aggression": 0.9},
            })
        for i in range(4):
            commands.append({
                "action": "spawn_creature",
                "kind": "animal",
                "species": "deer",
                "position": [random.uniform(5, 10), 0.0, random.uniform(-5, 5)],
                "name": f"Deer_{i+1}",
                "traits": {"speed": 2.5, "aggression": 0.0},
            })

    elif "замок" in p_lower or "крепост" in p_lower or "castle" in p_lower or "tower" in p_lower:
        # Castle towers & walls
        tower_coords = [(-6, -6), (6, -6), (6, 6), (-6, 6)]
        for tx, tz in tower_coords:
            commands.append({
                "action": "spawn",
                "type": "cylinder",
                "position": [float(tx), 2.0, float(tz)],
                "scale": [1.8, 6.0, 1.8],
                "color": [0, 255, 65],
            })
            commands.append({
                "action": "spawn",
                "type": "cone",
                "position": [float(tx), 5.5, float(tz)],
                "scale": [2.2, 2.0, 2.2],
                "color": [0, 143, 17],
            })
        # Central keep
        commands.append({
            "action": "spawn",
            "type": "cube",
            "position": [0.0, 2.0, 0.0],
            "scale": [4.0, 5.0, 4.0],
            "color": [0, 255, 65],
        })

    elif "дракон" in p_lower or "dragon" in p_lower:
        commands.append({
            "action": "spawn_creature",
            "kind": "animal",
            "species": "dragon",
            "position": [0.0, 4.0, 0.0],
            "name": "Smaug",
            "traits": {"speed": 3.5, "aggression": 0.95},
        })
        commands.append({
            "action": "spawn_creature",
            "kind": "animal",
            "species": "unicorn",
            "position": [5.0, 0.0, 3.0],
            "name": "Celestia",
            "traits": {"speed": 2.8, "aggression": 0.0},
        })

    elif "жизнь" in p_lower or "life" in p_lower or "больше жизни" in p_lower:
        species_pool = [
            ("wolf", "Fenrir", 0.9),
            ("deer", "Eikthyrnir", 0.0),
            ("bird", "Hugin", 0.1),
            ("horse", "Sleipnir", 0.1),
            ("human", "Neo", 0.3),
            ("dragon", "Nidhogg", 0.9),
            ("robot", "Sentinel", 0.6),
        ]
        for spec, cname, agg in species_pool:
            rx = random.uniform(-12.0, 12.0)
            rz = random.uniform(-12.0, 12.0)
            commands.append({
                "action": "spawn_creature",
                "kind": "human" if spec == "human" else "animal",
                "species": spec,
                "position": [rx, 0.0, rz],
                "name": cname,
                "traits": {"speed": random.uniform(1.8, 3.2), "aggression": agg},
            })

    else:
        # Generic synthesis: geometric altar + creature
        commands.append({
            "action": "spawn",
            "type": "torus",
            "position": [0.0, 0.5, 0.0],
            "scale": [2.5, 0.8, 2.5],
            "color": [0, 255, 65],
        })
        commands.append({
            "action": "spawn",
            "type": "cube",
            "position": [0.0, 1.2, 0.0],
            "scale": [1.5, 1.5, 1.5],
            "color": [0, 143, 17],
        })
        spec_word = "wolf"
        for w in p_lower.split():
            clean_w = w.strip(",.!?")
            if len(clean_w) > 3:
                spec_word = clean_w
                break
        commands.append({
            "action": "spawn_creature",
            "kind": "animal",
            "species": spec_word,
            "position": [3.0, 0.0, 2.0],
            "name": spec_word.capitalize(),
            "traits": {"speed": 2.0, "aggression": 0.2},
        })

    return json.dumps(commands, indent=2)


class CreatorLLM:
    """Local LLM engine with GBNF grammar constraints and simulated fallback."""

    __slots__ = (
        "model_path",
        "llm",
        "grammar_str",
        "grammar",
        "threads",
        "is_simulated",
    )

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path
        self.threads = os.cpu_count() or 4
        self.grammar_str = build_grammar()
        self.grammar = None
        self.llm = None
        self.is_simulated = True

        if model_path and os.path.isfile(model_path):
            try:
                from llama_cpp import Llama, LlamaGrammar

                self.grammar = LlamaGrammar.from_string(
                    self.grammar_str, verbose=False
                )
                self.llm = Llama(
                    model_path=model_path,
                    n_gpu_layers=0,
                    n_threads=self.threads,
                    n_batch=512,
                    n_ctx=4096,
                    use_mmap=True,
                    verbose=False,
                )
                self.is_simulated = False
            except Exception:
                self.is_simulated = True

    def stream_generate(self, user_prompt: str) -> Iterator[str]:
        """Stream generation tokens chunk-by-chunk."""
        if not self.is_simulated and self.llm is not None:
            full_prompt = (
                f"{SYSTEM_PROMPT}\n\nUser: {user_prompt}\nAI Creator:\n"
            )
            try:
                stream = self.llm(
                    full_prompt,
                    grammar=self.grammar,
                    stream=True,
                    max_tokens=2048,
                    temperature=0.2,
                )
                for chunk in stream:
                    text_chunk = chunk["choices"][0]["text"]
                    if text_chunk:
                        yield text_chunk
                return
            except Exception:
                pass

        # Simulated fallback generation streaming character chunks
        out_json = _procedural_creator_fallback(user_prompt)
        chunk_size = 4
        for i in range(0, len(out_json), chunk_size):
            time.sleep(0.015)
            yield out_json[i : i + chunk_size]
