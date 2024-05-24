#!/bin/bash
source ~/.bashrc
here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $here
conda activate $HOME/miniconda3/envs/openhabstuff
python geohome.py
