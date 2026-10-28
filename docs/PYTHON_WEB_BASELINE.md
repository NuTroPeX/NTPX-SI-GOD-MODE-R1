# Python + Web Release Baseline

Scope: Python 3.10+ loopback HTTP backend, SQLite, bundled web dashboard, and unit/HTTP regression tests.

Android APK compilation is **excluded** from this release target by project decision. The legacy `android/` source directory remains for historical reference; no APK is required for acceptance.

## Local validation

```sh
python -m unittest discover -v -p 'test*.py'
python app.py
```

Open http://127.0.0.1:8765 on the machine running the server. The web dashboard is not independently hosted.

## Acceptance gates

- All Python tests pass in GitHub Actions on the proposed commit.
- The dashboard responds with HTML on loopback; unknown paths return 404.
- Approval-gated file operations remain protected by regression tests.
- No production or remote deployment is claimed without authentication, HTTPS, and a separate security review.
- A green CI run does not establish browser usability, Ollama availability, or production readiness.

## Deployment constraints

No automatic remote exposure, no unreviewed writes to the default branch, and no automated merge. This branch adds regression coverage and release documentation only.
