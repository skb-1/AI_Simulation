# Local GGUF Models Directory

Place your quantized `.gguf` language model weights in this directory.

Recommended models:
- `Meta-Llama-3-8B-Instruct.Q4_K_M.gguf`
- `Mistral-7B-Instruct-v0.3.Q4_K_M.gguf`
- `Qwen2.5-7B-Instruct-Q4_K_M.gguf`
- `Phi-3-mini-4k-instruct-q4.gguf`

When starting `aicreator`, the engine automatically scans this folder for any `.gguf` files.
You can also point directly to any model file via:
```bash
aicreator --model /path/to/model.gguf
```
If no `.gguf` model is provided, `aicreator` automatically activates its high-fidelity simulated Creator engine for immediate interactive exploration.
