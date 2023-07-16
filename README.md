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

Most of the files in this repository work with SkoolKit 8.10, but some require
SkoolKit 9.0.

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
`great-escape-the.t2s`. If there are two or more games with the same name, the
publisher's name is appended to distinguish them, e.g.
`battle-of-britain-pss.t2s`. If a game consists of multiple parts (as with many
adventure games), `-p1`, `-p2` etc. is appended to the name to indicate the
part number. If a game tape consists of multiple sides that may be different,
`-side-1`, `-side-a` etc. is appended to the name to indicate the side number
or letter.

The contents of each `t2s` file have the following format:

    <url>
    <z80 filename>
    --sim-load
    --tape-name <name>
    --tape-sum <md5sum>
    --start <address>
    <other options>
    ....

where:

* `<url>` is the URL of the zip archive that contains the TAP/TZX file
* `<z80 filename>` is the name of the Z80 snapshot file to generate; this is
  always the same as the name of the `t2s` file (with `t2s` replaced by `z80`)
* `--sim-load` instructs `tap2sna.py` to perform a simulated LOAD on a freshly
  booted 48K ZX Spectrum
* `--tape-name <name>` specifies the name of the TAP/TZX file in the zip
  archive; this is usually optional, but ensures that the correct file is
  chosen in case there is more than one
* `--tape-sum <md5sum>` specifies the MD5 checksum of the TAP/TZX file, in case
  the contents of the remote zip archive have changed or been updated (this
  does happen occasionally)
* `--start <address>` specifies the all-important start address (the value of
  the program counter in the Z80 snapshot that's produced)
* `<other options>` are any other `tap2sna.py` options required to make the
  simulated LOAD work (e.g. `--tape-start`, `--tape-stop`, `--sim-load-config`)

If both a TZX file and a TAP file exists for a game, the TZX file is preferred,
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

    $ tap2sna.py --sim-load Zynaps.tzx zynaps.z80

Now run SkoolKit's `trace.py` on the resultant snapshot to see where the
execution path leads now that the LOAD has completed:

    $ trace.py -v --max-operations 100 zynaps.z80
    $FD29 1F       RRA
    $FD2A D0       RET NC
    $FD2B A9       XOR C
    $FD2C E620     AND $20
    $FD2E 28F3     JR Z,$FD23
    ...
    $FD14 7A       LD A,D
    $FD15 B3       OR E
    $FD16 20CA     JR NZ,$FCE2
    $FD18 7C       LD A,H
    $FD19 FE01     CP $01
    $FD1B C9       RET
    $FE9C 30D6     JR NC,$FE74
    $FE9E C9       RET
    $FE54 2162FE   LD HL,$FE62
    $FE57 11005B   LD DE,$5B00
    $FE5A 011200   LD BC,$0012
    $FE5D EDB0     LDIR
    ...

If you're familiar with how loading routines look, you can make an educated
guess that the one for this game exits at $FE9E, and so the first instruction
executed that's not part of the loading routine is at $FE54 (65108). Which is
indeed the `--start` address in `zynaps.t2s`.

Some games, however, start before the tape has finished, so the technique
described above will not work. In that case, you can use `tap2sna.py` to
produce a log of every instruction executed during the simulated LOAD. For
example:

    $ tap2sna.py --sim-load -c trace=load.log game.tzx game.z80

Now look at the last few hundred lines or so (or more, if needed) of `load.log`
to see where the loading routine ended.
