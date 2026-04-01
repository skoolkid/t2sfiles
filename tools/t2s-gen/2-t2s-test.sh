#!/usr/bin/env bash
if ! command -v tap2sna.py &> /dev/null; then
  echo "ERROR: tap2sna.py: command not found"
  exit 1
fi

USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0"
SC_MIN_WAIT=1  # Minimum wait time (in seconds) between downloads from spectrumcomputing.co.uk
MIN_WAIT=1     # Minimum wait time (in seconds) between downloads from other sites
mkdir -p t2s-snapshots
mkdir -p t2s-failed
errors=t2s-test-errors.log
sc_wait=0
other_wait=0

find t2s -name '*.t2s' | sort | while read t; do
  t2sname=$(basename "$t")
  z=t2s-snapshots/$(basename "$t" .t2s).z80
  if [ -f "$z" ]; then
    echo "Skipping $t - $z already exists"
  else
    url=$(grep -o 'https://.*\.zip' $t)
    if [[ $url == */spectrumcomputing.co.uk/* ]]; then
      if [[ $sc_wait -gt 0 ]]; then
        echo -e "Waiting $sc_wait second(s)...\n"
        sleep $sc_wait
      fi
      sc_wait=$SC_MIN_WAIT
    elif [[ $other_wait -gt 0 ]]; then
      echo -e "Waiting $other_wait second(s)...\n"
      sleep $other_wait
      sc_wait=$(( sc_wait - other_wait ))
    fi
    other_wait=$MIN_WAIT
    echo "Trying $t..."
    logfile=t2s-snapshots/$t2sname.log
    t0=$(date +%s)
    tap2sna.py -u "$USER_AGENT" -d t2s-snapshots @$t 2>&1 | tee $logfile
    failed=${PIPESTATUS[0]}
    grep -qF "(timed out)" $logfile && failed=1
    if [[ $failed -ne 0 ]]; then
      echo "FAILED"
      error=$(grep '\(ERROR\|timed out\)' $logfile)
      echo "$t failed: $error" >> $errors
      mv -v $t $logfile t2s-failed
      [[ -f $z ]] && mv -v $z t2s-failed
    else
      echo "OK"
    fi
    t1=$(date +%s)
    delta=$(( t1 - t0 ))
    sc_wait=$(( sc_wait - delta ))
    other_wait=$(( other_wait - delta ))
  fi
  echo
done
