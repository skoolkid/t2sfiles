#!/usr/bin/env bash
destdir="$T2SFILES_HOME/t2s"
mkdir -p t2s-done
for l in a b c d e f g h i j k l m n o p q r s t u v w x y z; do
  mkdir -p $destdir/$l
  cp -pv t2s-ok/$l*.t2s $destdir/$l 2>/dev/null
  mv t2s-ok/$l*.t2s t2s-done 2>/dev/null
done
mkdir -p $destdir/0
cp -v t2s-ok/[0-9]*.t2s $destdir/0 2>/dev/null
mv t2s-ok/[0-9]*.t2s t2s-done 2>/dev/null
