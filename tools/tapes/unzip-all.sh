#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

if [[ -z $SPECTRUM_TAPES ]]; then
  echo "ERROR: SPECTRUM_TAPES is not set"
  exit 1
fi
if [[ ! -d $SPECTRUM_TAPES ]]; then
  echo "ERROR: $SPECTRUM_TAPES: directory not found"
  exit 1
fi

UNZIP="$T2SFILES_HOME/tools/tapes/unzip.py"
GEN_MD5SUMS="$T2SFILES_HOME/tools/tapes/gen-md5sums.sh"

force=0
if [[ $1 == --force ]]; then
  force=1
elif [[ -n $1 ]]; then
  echo "Usage: $(basename $0) [--force]"
  echo
  echo "Extract all zip archives not yet extracted. If '--force' is used, previously"
  echo "extracted zip archives are re-extracted."
  exit 1
fi

error_log=unzip-all-errors.log
>$error_log

find $SPECTRUM_TAPES/spectrumcomputing.co.uk -name '*.zip' | while read z; do
  zdir=${z%.zip}
  if [[ $force == 1 ]] || [[ ! -d $zdir ]]; then
    rm -rf "$zdir"
    mkdir "$zdir"
    if ! $UNZIP "$z" "$zdir"; then
      echo "Failed to extract $z" >> $error_log
      rm -rf "$zdir"
    fi
  fi
done

echo "Generating md5 sums..."
$GEN_MD5SUMS

if [[ -s $error_log ]]; then
  echo -e "\nFailed to extract some zip archives; see $error_log"
else
  rm -f $error_log
fi
