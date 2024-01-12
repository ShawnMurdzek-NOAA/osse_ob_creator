"""
Master Script that Creates the Jobs to Rotate Wind Components from Grid-Relative to Earth-Relative

Command line arguments:
    argv[1] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
Date Created: 8 January 2024
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np
import os
import sys
import datetime as dt
import time
import pandas as pd
import yaml

import pyDA_utils.slurm_util as slurm


#---------------------------------------------------------------------------------------------------
# Create Job Scripts
#---------------------------------------------------------------------------------------------------

# Read in input from YAML
in_yaml = sys.argv[1]
with open(in_yaml, 'r') as fptr:
    param = yaml.safe_load(fptr)

# Determine all the prepBUFR timestamps
wgrib2_times = [dt.datetime.strptime(param['start_time'], '%Y%m%d%H%M')]
wgrib2_end_time = dt.datetime.strptime(param['end_time'], '%Y%m%d%H%M')
while wgrib2_times[-1] < wgrib2_end_time:
    wgrib2_times.append(wgrib2_times[-1] + dt.timedelta(minutes=param['time_step']))

# Copy grid_defn.pl to run directory
os.system('cp grid_defn.pl {d}/'.format(d=param['run_dir']))

# Create jobs
j_names = []
for wgrib2_t in wgrib2_times:

    t_str = wgrib2_t.strftime('%Y%m%d%H%M')
    in_fname = wgrib2_t.strftime(param['file_tmpl_in'])
    out_fname = wgrib2_t.strftime(param['file_tmpl_out'])
    job_fname = '{d}/rotate_winds_{t}.sh'.format(d=param['run_dir'], t=t_str)

    print('creating job submission script for {t}'.format(t=t_str))

    j_names.append(job_fname)
    fptr = open(job_fname, 'w')

    # Job specs
    fptr.write('#!/bin/sh\n\n')
    fptr.write('#SBATCH -A %s\n' % param['alloc'])
    fptr.write('#SBATCH -t %s\n' % param['job_time'])
    fptr.write('#SBATCH --nodes=1 --ntasks=1\n')
    fptr.write('#SBATCH --mem=%s\n' % param['job_mem'])
    fptr.write('#SBATCH -o %s/%s.%s.rotate_wind.log\n' % (param['run_dir'], t_str, param['tag']))
    fptr.write('#SBATCH --partition=%s\n\n' % param['partition'])

    # wgrib2 command to rotate winds
    fptr.write('date\n')
    fptr.write('module load wgrib2\n')
    fptr.write('wgrib2 {in_fname} \\\n'.format(in_fname=in_fname))
    fptr.write('       -set_grib_type same \\\n')
    fptr.write('       -new_grid_winds earth \\\n')
    fptr.write('       -new_grid_interpolation neighbor \\\n')
    fptr.write('       -new_grid `./grid_defn.pl {in_fname}` \\\n'.format(in_fname=in_fname))
    fptr.write('       {out_fname}\n'.format(out_fname=out_fname))
    fptr.write('date')

    fptr.close()

# Create CSV with job submission information
all_jobs = slurm.job_list(jobs=j_names)
all_jobs.save('%s/%s' % (param['run_dir'], param['csv_name']))
 

"""
End create_rotate_wind_jobs.py
"""
