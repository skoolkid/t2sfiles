#!/usr/bin/env bash
t2sdir=$1
if [[ -z $t2sdir ]]; then
    echo "Usage: $0 T2SDIR"
    exit 1
fi

grep -hr tape-sum "$t2sdir" | sort | uniq -c | grep ' [2-9] ' | cut -c 20- | while read md5; do
    echo -e "$md5:"
    grep -r $md5 "$t2sdir"
    echo
done
