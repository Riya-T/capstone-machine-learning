# Ollama model variants

Ollama's OpenAI-compatible endpoint can't set the context window per request,
so the context size is fixed in a named model variant instead. The name goes
in the config, and therefore into the result keys.

`qwen2.5-coder-7b-ctx8k.json`: Qwen2.5-Coder-7B-Instruct with an 8192-token
context, used by `configs/pilot_local.yaml` for both writer and editor.

Create it once (shares the base model's weights; nothing is downloaded):

    curl -s http://localhost:11434/api/create -d @ollama/qwen2.5-coder-7b-ctx8k.json

Check it:

    curl -s http://localhost:11434/api/show -d '{"model": "qwen2.5-coder-7b-ctx8k"}' | grep num_ctx
