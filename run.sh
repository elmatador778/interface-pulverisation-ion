#!/usr/bin/env bash
# Lance la GUI CSiPI depuis la racine du projet
set -e
cd "$(dirname "$0")"
python src/main.py "$@"
