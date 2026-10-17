# Antigravity Operating Rules (ALWAYS ENFORCE)

1. **Source of Truth:** Before writing or modifying any code, read `.agent/TRD.md`, `.agent/APP_FLOW.md`, `.agent/IMPLEMENTATION_PLAN.md`, and `.agent/TESTING.md`.
2. **OS & Environment:** Windows 11, Python 3.12, RTX 3050 (6GB VRAM), 16GB RAM. Always use `pathlib.Path` for file paths. Never assume macOS/Linux shell commands.
3. **Non-Destructive Coding ("No-Nuke" Rule):** Never delete, overwrite, or truncate existing functional code when adding features or debugging. Apply surgical, modular edits.
4. **Architecture:** Strictly Object-Oriented Programming (OOP), strongly typed (`typing` + `pydantic` v2), modular, and offline-capable where possible.
5. **No Blind Text-to-Cypher:** Agents must interact with FalkorDB through deterministic, parameterized Cypher tool methods defined in `TRD.md`, never raw unvalidated LLM string execution.