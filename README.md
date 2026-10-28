# NTPX S.I. G.O.D. Mode R2

## What works
Python 3.10+ local dashboard, SQLite memory, three agent switches, deterministic planning, optional local Ollama inference, and separately approved workspace tools (list/read/write). No autonomous shell execution. No model download bundled. No dependency beyond Python standard library for backend.

## Run
`python app.py` then open http://127.0.0.1:8765 . Run `python -m unittest discover -v -p 'test*.py'` for tests.

## Local inference
Install Ollama separately, run `ollama pull qwen2.5-coder:1.5b` and start the Ollama service. Set `NTPX_MODEL` to your installed model name if different. On Android Termux, the backend works without Ollama; Ollama integration requires a compatible local Ollama service, which may not be available on the device.

## Approval workflow
Create a mission, approve its plan, copy the task ID, propose a workspace action, and explicitly approve that action. The tools only operate within `workspace/`. There is no unrestricted code execution or arbitrary shell. This is an early controlled agent-workflow foundation, not a fully autonomous developer.

## Supported platforms
Run the Python backend and browser dashboard on a system with Python 3.10+. Android APK support is discontinued in R2.

## Security limitations
Single-user loopback development only. No user authentication, production HTTPS, robust CSRF tokens, sandboxed subprocess execution, quotas, or adversarial security certification. File write actions are explicitly approved but not OS-sandboxed; run under a dedicated unprivileged account. Avoid untrusted clients and files. Symlinks are rejected when they resolve outside workspace, but there are no guarantees against local concurrent filesystem attackers. Never expose the Python server to the public internet.

## Python-only R2
Run `python app.py` and open `http://127.0.0.1:8765`. Run `python -m unittest discover -v -p 'test*.py'` to verify. The Python Tests workflow remains enabled.
