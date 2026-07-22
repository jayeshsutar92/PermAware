#!/usr/bin/env bash
# NUKE 2.0: Permanently eliminate persistent hash mismatches caused by corrupted pip cache
set -e

echo "Purging corrupted pip cache to prevent hash mismatches..."
pip cache purge || true

echo "Installing deployment dependencies strictly from PyPI without cache..."
pip install --no-cache-dir -r deployment/requirements.txt
