#!/usr/bin/env bash
if ! command -v fuse &> /dev/null; then
  echo "ERROR: fuse: command not found"
  exit 1
fi

if [[ ! -d tapes ]]; then
  echo "ERROR: tapes: directory not found"
  exit 1
fi

mkdir -p tapes-failed

shopt -s nullglob # Expand glob to empty string when no filenames match
for t in tapes/*; do
  fuse --no-confirm-actions "$t" &> /dev/null
  read -p "$t: OK? [Y/n] " ok
  [[ $ok == "n" ]] && mv -v "$t" tapes-failed
done
