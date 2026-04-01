#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

T2S=$1
REASON=$2

if [[ -z $REASON ]]; then
  echo "Usage: $(basename $0) path/to/game.t2s DEM/NAG/RAH/RUI"
  echo
  echo "  DEM: Demo or pre-release"
  echo "  NAG: Not a game"
  echo "  RAH: Requires additional hardware"
  echo "  RUI: Requires user input while LOADing"
  exit 1
fi

if [[ ! -f $T2S ]]; then
  echo "ERROR: $T2S does not exist"
  exit 1
fi

if [[ $REASON != "DEM" && $REASON != "NAG" && $REASON != "RAH" && $REASON != "RUI" ]]; then
  echo "ERROR: Reason must be one of DEM/NAG/RAH/RUI"
  exit 1
fi

tape_sum=$(grep '^--tape-sum' $T2S | cut -f2 -d' ')
$T2SFILES_HOME/tools/add-tape.py $tape_sum $REASON
git rm $T2S
