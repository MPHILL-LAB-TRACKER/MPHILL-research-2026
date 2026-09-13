#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/var/native"
c++ -std=c++17 -O2 -Wall -Wextra "$ROOT/native/worker.cpp" -lsqlite3 -ljson-c -o "$ROOT/var/native/ted2-worker"
printf 'Native worker compiled: %s\n' "$ROOT/var/native/ted2-worker"
