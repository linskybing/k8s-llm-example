# Mounted at /sglang-site and put first on PYTHONPATH by n150/sglang-custom.yaml, so every Python process of the SGLang server
# runs it at startup -- including the scheduler that SGLang v0.5.8.post1 starts with multiprocessing "spawn"
# (engine.py set_start_method("spawn", force=True)), which does not inherit patches made in the launcher.
import os

if os.environ.get("SGLANG_TT_SITE") == "1":
    # the image's tt-metal (84b4c53) calls Generator.decode_forward_text, renamed decode_forward
    from models.tt_transformers.tt.generator import Generator
    Generator.decode_forward_text = Generator.decode_forward
    import sglang_tt_plugin  # noqa: F401  registers TTLlamaForCausalLM etc. in SGLang's ModelRegistry on import
