#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "$0" )" &> /dev/null && pwd )

sudo umount $SCRIPT_DIR/pmacct
sudo umount $SCRIPT_DIR/pmacct-gauze
sudo umount $SCRIPT_DIR/netgauze
