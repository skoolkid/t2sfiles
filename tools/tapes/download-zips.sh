#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

if [[ -z $ZXDB ]]; then
  echo "ERROR: ZXDB environment variable not defined"
  exit 1
fi

if [[ -z $T2SFILES_USER_AGENT ]]; then
  echo "ERROR: T2SFILES_USER_AGENT environment variable not defined"
  exit 1
fi

usage() {
  cat <<EOF
Usage: $(basename $0) [options]

  Download zip archives mentioned in games.json.

Options:
  -h  Show this help.
EOF
  exit 1
}

json_file=$(dirname $ZXDB)/games.json
zxdb2json=${T2SFILES_HOME}/tools/zxdb2json.py

while getopts ":h" opt; do
  case $opt in
    h) usage ;;
    *) usage ;;
  esac
done

if [[ ! -f $json_file ]]; then
  echo "$json_file: file not found"
  exit 1
fi

site=$(basename $(pwd))
if [[ $site == spectrumcomputing.co.uk ]]; then
  pause=1
elif [[ $site == worldofspectrum.net ]]; then
  pause=3
else
  echo "Not in spectrumcomputing.co.uk or worldofspectrum.net; aborting"
  exit 1
fi

first=1
failed_log=failed.log
rm -f "$failed_log"
$zxdb2json -u | grep "https://$site" | while read url; do
  path=${url#https://${site}/}
  if [[ ! -f $path ]]; then
    if [[ $first == 0 ]]; then
      echo -e "Waiting $pause seconds...\n"
      sleep $pause
    fi
    first=0
    mkdir -p $(dirname "$path")
    if ! wget --user-agent "$T2SFILES_USER_AGENT" -O "$path" "$url"; then
      rm -v "$path"
      echo "$url" >> "$failed_log"
    fi
  fi
done

if [[ -f $failed_log ]]; then
  failed=$(wc -l < "$failed_log")
  echo "WARNING: $failed download(s) failed; see $failed_log"
fi
