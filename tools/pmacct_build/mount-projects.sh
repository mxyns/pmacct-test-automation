#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "$0" )" &> /dev/null && pwd )

$SCRIPT_DIR/unmount-projects.sh
mkdir -p $SCRIPT_DIR/pmacct
sudo mount --bind /home/taayoma5/CLionProjects/pmacct/ $SCRIPT_DIR/pmacct
mkdir -p $SCRIPT_DIR/pmacct-gauze
sudo mount --bind /home/taayoma5/RustroverProjects/pmacct-gauze $SCRIPT_DIR/pmacct-gauze
mkdir -p $SCRIPT_DIR/netgauze
sudo mount --bind /home/taayoma5/RustroverProjects/netgauze $SCRIPT_DIR/netgauze
