#!/bin/bash
cd "$(dirname "$0")"
uv venv
uv run python main.py