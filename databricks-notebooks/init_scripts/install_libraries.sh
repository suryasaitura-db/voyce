#!/bin/bash
# Databricks init script for installing required libraries
# This script runs on cluster startup to install dependencies

set -e

echo "=================================================="
echo "Voice Feedback Platform - Library Installation"
echo "=================================================="

# Update pip
echo "[1/5] Updating pip..."
/databricks/python/bin/pip install --upgrade pip

# Install audio processing libraries
echo "[2/5] Installing audio processing libraries..."
/databricks/python/bin/pip install \
    openai-whisper \
    librosa \
    soundfile \
    pydub \
    --quiet

# Install ML and NLP libraries
echo "[3/5] Installing ML and NLP libraries..."
/databricks/python/bin/pip install \
    anthropic \
    openai \
    sentence-transformers \
    transformers \
    --quiet

# Install additional ML libraries
echo "[4/5] Installing additional ML libraries..."
/databricks/python/bin/pip install \
    scikit-learn \
    xgboost \
    lightgbm \
    mlflow \
    --quiet

# Install data processing libraries
echo "[5/5] Installing data processing libraries..."
/databricks/python/bin/pip install \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    --quiet

# System dependencies for audio processing (if needed)
if [ -f /etc/debian_version ]; then
    echo "Installing system dependencies (Debian/Ubuntu)..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        ffmpeg \
        libsndfile1 \
        portaudio19-dev \
        || true
fi

echo ""
echo "=================================================="
echo "Library Installation Complete!"
echo "=================================================="
echo ""
echo "Installed libraries:"
echo "  - openai-whisper (speech-to-text)"
echo "  - librosa (audio processing)"
echo "  - soundfile (audio I/O)"
echo "  - pydub (audio manipulation)"
echo "  - anthropic (Claude API)"
echo "  - openai (OpenAI API)"
echo "  - sentence-transformers (embeddings)"
echo "  - transformers (NLP models)"
echo "  - scikit-learn (ML)"
echo "  - xgboost (gradient boosting)"
echo "  - lightgbm (gradient boosting)"
echo "  - mlflow (experiment tracking)"
echo "  - pandas, numpy (data processing)"
echo "  - matplotlib, seaborn (visualization)"
echo ""
echo "System dependencies:"
echo "  - ffmpeg (audio/video processing)"
echo "  - libsndfile1 (audio file support)"
echo "  - portaudio19-dev (audio I/O)"
echo ""
echo "=================================================="

# Verify installations
echo "Verifying installations..."
python3 << EOF
import sys
import importlib

packages = [
    'whisper',
    'librosa',
    'soundfile',
    'pydub',
    'anthropic',
    'openai',
    'sentence_transformers',
    'sklearn',
    'xgboost',
    'lightgbm',
    'mlflow',
    'pandas',
    'numpy',
    'matplotlib',
    'seaborn'
]

failed = []
for package in packages:
    try:
        importlib.import_module(package)
        print(f"✓ {package}")
    except ImportError as e:
        print(f"✗ {package}: {str(e)}")
        failed.append(package)

if failed:
    print(f"\n⚠ Warning: Failed to import {len(failed)} packages: {', '.join(failed)}")
    sys.exit(1)
else:
    print(f"\n✓ All {len(packages)} packages verified successfully!")
    sys.exit(0)
EOF

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✓ All libraries installed and verified!"
    echo "=================================================="
else
    echo ""
    echo "=================================================="
    echo "⚠ Some libraries failed verification"
    echo "=================================================="
    exit 1
fi
