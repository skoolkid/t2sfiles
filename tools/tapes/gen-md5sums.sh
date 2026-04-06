#!/usr/bin/env bash
if [[ -z $SPECTRUM_TAPES ]]; then
  echo "ERROR: SPECTRUM_TAPES environment variable not defined"
  exit 1
fi

if [[ -d $SPECTRUM_TAPES ]]; then
  MD5SUMS=$SPECTRUM_TAPES/md5sums.txt
else
  echo "ERROR: SPECTRUM_TAPES=$SPECTRUM_TAPES: directory not found"
  exit 1
fi

find $SPECTRUM_TAPES/{spectrumcomputing.co.uk,worldofspectrum.net} -type f \( -iname '*.tap' -o -iname '*.tzx' \) -print0 | xargs -0 md5sum > $MD5SUMS &&
echo "Wrote $MD5SUMS"
