t2sfiles
========

This repository contains argument files for
[SkoolKit](https://github.com/skoolkid/skoolkit)'s `tap2sna.py`. Each one
produces a pristine snapshot of a ZX Spectrum game. For example, to produce a
pristine snapshot of Pyjamarama:

    $ tap2sna.py @t2s/p/pyjamarama.t2s
    Downloading https://worldofspectrum.org/pub/sinclair/games/p/PyjamaramaV1.tzx.zip
    Extracting Pyjamarama - v1.tzx
    Program: PYJAMARAMA
    Fast loading data block: 23755,472
    Data (6915 bytes)
    Data (31408 bytes)
    Simulation stopped (PC at start address): PC=32819
    Writing pyjamarama.z80

SkoolKit 9.1+ is required.

Pristine snapshots
------------------

What makes a snapshot 'pristine'? For the purposes of this repository, a
snapshot is regarded as pristine if it represents the state of the ZX
Spectrum's RAM and internal registers as they would be on real hardware after
the final byte of the game has loaded from tape (disregarding some
unpredictable and irrelevant properties, such as the exact values of
[FRAMES](https://skoolkid.github.io/rom/asm/5C78.html) and the R register).
In particular, the program counter (PC) must point at the first instruction
executed after the LOAD has finished that is not part of the game's custom
loading routine (if there is one). This instruction is typically somewhere in
RAM, but can be in the ROM if the game comprises some BASIC code. A good
candidate start address for games that run BASIC code before or during gameplay
is 0x053F (i.e. [SA/LD-RET](https://skoolkid.github.io/rom/asm/053F.html)).

t2s file naming and format
--------------------------

Each `t2s` file in this repository is named after the game for which it
produces a pristine snapshot. The filename is restricted to digits, lower case
letters, dots and hyphens. If the game name starts with 'The' (in any
language), that word goes at the end of the filename, e.g.
`great-escape-the.t2s`. If there are two or more files for a single game, or
two or more games with the same name, then one or more of the following
suffixes may be appended to the filenames to distinguish them:

* `-publisher` / `-author` (publisher or author)
* `-release-*` / `-v*` (release/version number)
* `-side-*`/ `-p*` (side number/letter or part number)
* `-128k` (the 128K version of a 48K/128K game)

The contents of each `t2s` file have the following format:

    <url>
    --tape-name "<name>"
    --tape-sum <md5sum>
    --start <address>
    <other options>
    ....

where:

* `<url>` is the URL of the zip archive that contains the TAP/TZX file
* `--tape-name "<name>"` specifies the name of the TAP/TZX file in the zip
  archive; this ensures that the correct file is chosen in case there is more
  than one
* `--tape-sum <md5sum>` specifies the MD5 checksum of the TAP/TZX file, in case
  the contents of the remote zip archive have changed or been updated (this
  does happen occasionally)
* `--start <address>` specifies the all-important start address (the value of
  the program counter in the snapshot that's produced)
* `<other options>` are any other `tap2sna.py` options required to make the
  simulated LOAD work (e.g. `--tape-start`, `--tape-stop`, `--sim-load-config`)

If both a TZX file and a TAP file exist for a game, the TZX file is preferred,
as it is probably a more accurate representation of the original tape.

Good places to obtain zip archives of Spectrum tape files are:

* [Spectrum Computing](https://spectrumcomputing.co.uk/)
* [World of Spectrum Classic](https://worldofspectrum.net/archive/)
* [World of Spectrum](https://worldofspectrum.org/archive)
* [The TZX Vault](https://tzxvault.org/)

Program counter (PC)
--------------------

How do you work out the value of the program counter for a pristine snapshot
(the argument of the `--start` option in the `t2s` file) of a particular game?
In general, it's not too difficult. The first step is to run `tap2sna.py` on
the TAP/TZX file without the `--start` option, which typically makes the
simulated LOAD stop when the final edge on the tape is detected. For example:

    $ tap2sna.py Zynaps.tzx

Now run SkoolKit's `trace.py` on the resultant snapshot to see where the
execution path leads now that the LOAD has completed:

    $ trace.py -vm 100 Zynaps.z80
    $FD29 RRA
    $FD2A RET NC
    $FD2B XOR C
    $FD2C AND $20
    $FD2E JR Z,$FD23
    ...
    $FD14 LD A,D
    $FD15 OR E
    $FD16 JR NZ,$FCE2
    $FD18 LD A,H
    $FD19 CP $01
    $FD1B RET
    $FE9C JR NC,$FE74
    $FE9E RET
    $FE54 LD HL,$FE62
    $FE57 LD DE,$5B00
    $FE5A LD BC,$0012
    $FE5D LDIR
    ...

If you're familiar with how loading routines look, you can make an educated
guess that the one for this game exits at $FE9E, and so the first instruction
executed that's not part of the loading routine is at $FE54 (65108). Which is
indeed the `--start` address in `zynaps.t2s`.

Some games, however, start before the tape has finished, so the technique
described above will not work. In that case, you can use `tap2sna.py` to
produce a log of every instruction executed during the simulated LOAD. For
example:

    $ tap2sna.py -c trace=load.log game.tzx

Now look at the last few hundred lines or so (or more, if needed) of `load.log`
to see where the loading routine ended.
