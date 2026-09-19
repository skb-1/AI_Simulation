"""LLM engine interface using llama-cpp-python or Native Pure-Python GGUF Engine."""

from __future__ import annotations

import glob
import json
import os
import random
import time
from typing import Iterator

from aicreator.gguf_engine import GGUFInferenceEngine, GGUFModel
from aicreator.grammar import build_grammar
from aicreator.prompts import SYSTEM_PROMPT


def find_gguf_models(search_dirs: list[str] | None = None) -> list[dict[str, str | int]]:
    """Scan directories for .gguf model weights and return metadata list."""
    if search_dirs is None:
        search_dirs = ["models", "aicreator/models", "."]

    found: list[dict[str, str | int]] = []
    seen: set[str] = set()

    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        for p in sorted(glob.glob(os.path.join(s_dir, "*.gguf"))):
            abs_p = os.path.abspath(p)
            if abs_p not in seen and os.path.isfile(abs_p):
                seen.add(abs_p)
                size_mb = os.path.getsize(abs_p) // (1024 * 1024)
                found.append({
                    "path": abs_p,
                    "rel_path": p,
                    "name": os.path.basename(p),
                    "size_mb": size_mb,
                })
    return found


def _procedural_creator_fallback(user_prompt: str) -> str:
    """Intelligent fallback generator synthesizing commands matching user intent."""
    p_lower = user_prompt.lower()
    commands = []

    if "лес" in p_lower or "дерев" in p_lower or "forest" in p_lower or "tree" in p_lower:
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

    elif "робот" in p_lower or "robot" in p_lower:
        for i in range(3):
            commands.append({
                "action": "spawn_creature",
                "kind": "animal",
                "species": "robot",
                "position": [random.uniform(-6, 6), 0.0, random.uniform(-6, 6)],
                "name": f"Unit_{i+1}",
                "traits": {"speed": 2.0, "aggression": 0.4},
            })

    else:
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
    """Local LLM engine with GBNF grammar constraints, pure-Python GGUF fallback, and hot-reloading."""

    __slots__ = (
        "model_path",
        "llm",
        "gguf_engine",
        "grammar_str",
        "grammar",
        "threads",
        "is_simulated",
        "temperature",
        "n_ctx",
    )

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = None
        self.threads = os.cpu_count() or 4
        self.grammar_str = build_grammar()
        self.grammar = None
        self.llm = None
        self.gguf_engine = None
        self.is_simulated = True
        self.temperature = 0.2
        self.n_ctx = 4096

        if model_path:
            self.load_model(model_path)

    def load_model(
        self,
        model_path: str | None,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
        temperature: float = 0.2,
    ) -> tuple[bool, str]:
        """Dynamically load GGUF model via llama-cpp-python or pure-Python GGUF engine."""
        self.temperature = temperature
        self.n_ctx = n_ctx
        if n_threads:
            self.threads = n_threads

        if not model_path or model_path.strip() == "" or model_path.lower() == "builtin":
            self.llm = None
            self.gguf_engine = None
            self.model_path = None
            self.is_simulated = True
            return True, "Активирован встроенный процедурный генератор AI Creator."

        if not os.path.isfile(model_path):
            alt_path = os.path.join("models", model_path)
            if os.path.isfile(alt_path):
                model_path = alt_path
            else:
                return False, f"Файл модели не найден: {model_path}"

        # 1. Try loading via llama_cpp if library is installed
        try:
            from llama_cpp import Llama, LlamaGrammar

            self.grammar = LlamaGrammar.from_string(
                self.grammar_str, verbose=False
            )
            self.llm = Llama(
                model_path=model_path,
                n_gpu_layers=n_gpu_layers,
                n_threads=self.threads,
                n_batch=512,
                n_ctx=n_ctx,
                use_mmap=True,
                verbose=False,
            )
            self.gguf_engine = None
            self.model_path = model_path
            self.is_simulated = False
            model_name = os.path.basename(model_path)
            return True, f"Модель успешно загружена через llama-cpp: {model_name}"
        except Exception:
            self.llm = None

        # 2. Native Pure-Python GGUF Engine (Works without llama_cpp or C-compilers)
        try:
            engine = GGUFInferenceEngine(
                model_path=model_path,
                n_ctx=n_ctx,
                threads=self.threads,
                temperature=temperature,
            )
            self.gguf_engine = engine
            self.model_path = model_path
            self.is_simulated = False
            m = engine.model
            msg = (
                f"Модель {m.name} успешно загружена через встроенный GGUF Engine "
                f"({m.architecture}, {m.tensor_count} тензоров, квантование {m.quantization_str})"
            )
            return True, msg
        except Exception as err:
            self.gguf_engine = None
            self.llm = None
            self.is_simulated = True
            return False, f"Ошибка загрузки GGUF файла: {err}"

    def get_model_info(self) -> dict[str, str | int | bool | float]:
        """Return current model metadata and engine state."""
        if self.llm is not None:
            engine_str = "llama-cpp-python"
        elif self.gguf_engine is not None:
            m = self.gguf_engine.model
            engine_str = f"Native GGUF ({m.architecture}, {m.quantization_str})"
        else:
            engine_str = "Built-in Procedural AI"

        return {
            "model_path": self.model_path or "",
            "model_name": os.path.basename(self.model_path) if self.model_path else "Встроенный генератор (Built-in)",
            "is_simulated": self.is_simulated,
            "engine": engine_str,
            "threads": self.threads,
            "n_ctx": self.n_ctx,
            "temperature": self.temperature,
        }

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
                    temperature=self.temperature,
                )
                for chunk in stream:
                    text_chunk = chunk["choices"][0]["text"]
                    if text_chunk:
                        yield text_chunk
                return
            except Exception:
                pass

        if not self.is_simulated and self.gguf_engine is not None:
            for token in self.gguf_engine.generate(user_prompt):
                yield token
            return

        # Simulated fallback generation streaming character chunks
        out_json = _procedural_creator_fallback(user_prompt)
        chunk_size = 4
        for i in range(0, len(out_json), chunk_size):
            time.sleep(0.005)
            yield out_json[i : i + chunk_size]
