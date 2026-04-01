#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

usage() {
  cat <<EOF
Usage: $(basename $0) TARGET_DIR

  Create a directory for testing uncommitted t2s files.
EOF
  exit 1
}

TARGET_DIR=$1
[[ -z $TARGET_DIR ]] && usage
if [[ -e $TARGET_DIR ]]; then
  echo "ERROR: $TARGET_DIR already exists"
  exit 1
fi

mkdir -p $TARGET_DIR/t2s
git -C $T2SFILES_HOME status --short | grep -o 't2s/./.*\.t2s' | xargs cp -pvt $TARGET_DIR/t2s
ln -s $T2SFILES_HOME/tools/t2s-gen/2-t2s-test.sh $TARGET_DIR/1-t2s-test.sh
ln -s $T2SFILES_HOME/tools/t2s-gen/3-test-t2s-snapshots.sh $TARGET_DIR/2-test-t2s-snapshots.sh
