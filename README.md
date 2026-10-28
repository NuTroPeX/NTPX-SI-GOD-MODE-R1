# NTPX S.I. G.O.D. Mode R2

## What works
Python 3.10+ local dashboard, SQLite memory, three agent switches, deterministic planning, optional local Ollama inference, and separately approved workspace tools (list/read/write). No autonomous shell execution. No model download bundled. No dependency beyond Python standard library for backend.

## Run
`python app.py` then open http://127.0.0.1:8765 . Run `python -m unittest discover -v -p 'test*.py'` for tests.

## Local inference
Install Ollama separately, run `ollama pull qwen2.5-coder:1.5b` and start the Ollama service. Set `NTPX_MODEL` to your installed model name if different. On Android Termux, the backend works without Ollama; Ollama integration requires a compatible local Ollama service, which may not be available on the device.

## Approval workflow
Create a mission, approve its plan, copy the task ID, propose a workspace action, and explicitly approve that action. The tools only operate within `workspace/`. There is no unrestricted code execution or arbitrary shell. This is an early controlled agent-workflow foundation, not a fully autonomous developer.

## Android
The `android/` folder is a native Java WebView **client** for a running backend. It does not bundle Python or an AI model. Build via the GitHub Actions workflow after pushing this source to a repository. An APK is not included, and no Android build has been verified. Android localhost refers to the Android device, not a Windows PC. For a remote backend, use a trusted HTTPS endpoint with authentication before production; R2 backend is loopback-only and does not support remote access.

## Security limitations
Single-user loopback development only. No user authentication, production HTTPS, robust CSRF tokens, sandboxed subprocess execution, quotas, or adversarial security certification. File write actions are explicitly approved but not OS-sandboxed; run under a dedicated unprivileged account. Avoid untrusted clients and files. Symlinks are rejected when they resolve outside workspace, but there are no guarantees against local concurrent filesystem attackers. Never expose the Python server to the public internet.

## GitHub-ready package (R2)
Repository: https://github.com/NuTroPeX/NTPX-SI-GOD-MODE-R1

Upload **the contents of this directory**, preserving `.github/workflows/` and `android/`.
GitHub Actions > **Python Tests** verifies the Python suite. Actions > **Android Debug APK** > **Run workflow** attempts a debug APK build; retrieve the APK from the workflow's Artifacts after a successful run.

Android app is a WebView client requiring an independently running backend on the **same Android device** for `127.0.0.1`. It does not bundle Python or Ollama. The current backend intentionally binds to loopback, so remote PC backend access is not supported. Do not expose it to a network without adding authentication and secure transport.

Verification at packaging time: Python 3.13 unit suite 10/10 passed; Gradle/Android compilation not available in this environment; no live Ollama model test.

## Web R3 verification
The mission-to-approved-file-action workflow is covered by `test_workflow.py`. Select **Use task for tools** in the dashboard to populate the task ID. The dashboard is served by the Python backend; it is not a hosted standalone website.