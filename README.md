# Agent SDK Roadmap Loop

Python-owned roadmap loop with a Python-native Claude integration.

## What this repo is

This repo demonstrates the same loop pattern as the CLI version, but keeps the model interaction inside Python.

## Files

- `roadmap_loop_agent_sdk.py`
- `tasks.yaml`
- `justfile`
- `AGENT_SDK_NOTES.md`

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install anthropic pyyaml
```

Set API key:
```bash
export ANTHROPIC_API_KEY=<your-key>
```

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial Agent SDK roadmap loop"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```
