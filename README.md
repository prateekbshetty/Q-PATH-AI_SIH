# Q-PATH AI

An end-to-end, dependency-free web application for the SIH26140 brief: AI-assisted quantum-algorithm learning. It includes an interactive circuit builder, deterministic state-vector simulator, adaptive feedback, misconception taxonomy/detection, learning fingerprint, and instructor dashboard.

## Run from GitHub

This repository requires only Python 3.10+—no database, package install, API key, or build step.

```bash
git clone <your-repository-url>
cd <repository-folder>
./start.sh
```

If your system does not permit executing the script, use `python3 app.py` instead.

Open [http://localhost:8000](http://localhost:8000). To run it in GitHub Codespaces, use the same command and open the forwarded port `8000`.

The included dev-container opens that port automatically in Codespaces, and the included GitHub Actions workflow compiles the app and checks the Bell-state simulator on every push or pull request.

## Architecture

- `app.py` — HTTP API, exact state-vector simulator (H, X, Y, Z, S, T, CX), validation, profile persistence, and misconception rules.
- `static/` — responsive single-page frontend with the learner lab, fingerprint, and instructor insights.
- `data/learning_data.json` — created automatically on first simulated attempt; intentionally ignored by Git.

The simulator—not the tutor—determines whether a circuit is correct. The tutor converts validated results and rules into actionable explanations, matching the technical-design requirement in the brief.

## Current scope

The demo supports up to three simulated qubits at the API level and two visual circuit rails. It is deliberately dependency-free so it runs immediately after cloning. For production, replace JSON persistence with PostgreSQL and the local simulator with Qiskit/Aer, while preserving the validation-before-LLM boundary.
