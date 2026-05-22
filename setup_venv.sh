#!/usr/bin/env bash
set -e

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo ""
echo "Virtual environment created in .venv"
if [ -f .env ]; then
  echo "Found existing .env file."
else
  echo "Copy .env.example to .env and fill your secrets."
  echo "  cp .env.example .env"
fi
echo "Activate it with:"
echo "  source .venv/bin/activate"
echo "Run the app with:"
echo "  .venv/bin/python main_improved.py"
