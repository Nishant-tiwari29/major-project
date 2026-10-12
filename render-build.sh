#!/usr/bin/env bash
# exit on error
set -o errexit

echo "===> [1/4] Installing Python Backend Dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "===> [2/4] Building Frontend Single-Page Application..."
if command -v npm &> /dev/null
then
    cd frontend
    npm install
    npm run build
    cd ..
    echo "===> Frontend build completed successfully."
else
    echo "===> Warning: npm not found in path, skipping local frontend compilation."
fi

echo "===> [3/4] Initializing Database & Seed Data..."
export PYTHONPATH=backend
python backend/app/core/seed_data.py

echo "===> [4/4] Pre-compiling Machine Learning Models..."
python backend/app/ml/model_trainer.py

echo "===> Build complete! System ready for deployment."
