#!/bin/sh

#SBATCH -A wrfruc
#SBATCH -t 08:00:00
#SBATCH --ntasks=1
#SBATCH --partition=orion
#SBATCH --mem=20GB

date
source ../activate_python_env.sh
python ob_error_tuning.py
date
