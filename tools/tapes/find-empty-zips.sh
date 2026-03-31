#!/usr/bin/env bash
find . -name '*.zip' | while read z; do
  [[ -s $z ]] || echo "http://spectrumcomputing.co.uk/${z#./}"
done
