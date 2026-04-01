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

usage() {
  cat <<EOF
Usage: $(basename $0) [options]

  Run tap2sna-t2s.py on new t2s files and update accelerators.txt accordingly.

Options:
  -k  Keep snapshots and log files
EOF
  exit 1
}

KEEP=0
while getopts ":k" opt; do
  case $opt in
    k) KEEP=1 ;;
    *) usage ;;
  esac
done

ACCELERATORS=$SPECTRUM_TAPES/accelerators.txt
T2S=$T2SFILES_HOME/t2s
lfile=t2sfiles.txt

rm -f tap2sna.log tap2sna-full.log
$T2SFILES_HOME/tools/find-t2s-to-gen-acc.py $T2S > $lfile
if [[ -s $lfile ]]; then
  echo -e "Running tap2sna-t2s.py\n"
  $T2SFILES_HOME/tools/tap2sna-t2s.py $lfile -c accelerator=list
  echo -en "\nRunning refresh-accelerators.py..."
  $T2SFILES_HOME/tools/refresh-accelerators.py tap2sna-full.log
  echo "done"
else
  echo "No t2s files to process"
fi

rm $lfile
[[ $KEEP -eq 0 ]] && rm -rf snapshots tap2sna.log tap2sna-full.log
