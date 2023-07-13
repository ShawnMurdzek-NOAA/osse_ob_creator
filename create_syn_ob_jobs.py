"""
Master Script that Creates the Jobs for the Synthetic Obs Creation Program

Command line arguments:
    argv[1] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
Date Created: 15 June 2023
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
# Create and Submit Job Scripts
#---------------------------------------------------------------------------------------------------

# Read in input from YAML
in_yaml = sys.argv[1]
with open(in_yaml, 'r') as fptr:
    param = yaml.safe_load(fptr)

# Determine all the prepBUFR timestamps
bufr_times = [dt.datetime.strptime(param['shared']['bufr_start'], '%Y%m%d%H%M')]
bufr_end_time = dt.datetime.strptime(param['shared']['bufr_end'], '%Y%m%d%H%M')
while bufr_times[-1] < bufr_end_time:
    bufr_times.append(bufr_times[-1] + dt.timedelta(minutes=param['shared']['bufr_step']))

# Create job submission files
j_names = []
for bufr_t in bufr_times:

    # Determine first and last WRF file time
    wrf_start = None
    hr = 3
    while wrf_start == None:
        tmp = bufr_t - dt.timedelta(hours=hr)
        if os.path.isfile('%s/%s' % (param['paths']['model'], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M.grib2'))):
            wrf_start = tmp
            break
        hr = hr - 1

    tmp = bufr_t + dt.timedelta(hours=1)
    if os.path.isfile('%s/%s' % (param['paths']['model'], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M.grib2'))):
        wrf_end = tmp
    else:
        wrf_end = bufr_t
    
    for tag in param['shared']['bufr_tag']:
        real_bufr_fname = '%s/%s.%s.t%sz.prepbufr.tm00' % (param['paths']['real_bufr'], 
                                                           bufr_t.strftime('%Y%m%d%H'),
                                                           tag,
                                                           bufr_t.strftime('%H'))
        real_csv_fname = '%s/%s.%s.prepbufr.csv' % (param['paths']['real_csv'],
                                                    bufr_t.strftime('%Y%m%d%H%M'),
                                                    tag)
        fake_csv_perf_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_perf_csv'],
                                                              bufr_t.strftime('%Y%m%d%H%M'),
                                                              tag)
        fake_csv_err_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_err_csv'],
                                                              bufr_t.strftime('%Y%m%d%H%M'),
                                                              tag)
        fake_csv_comb_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_combine_csv'],
                                                              bufr_t.strftime('%Y%m%d%H%M'),
                                                              tag)
        fake_csv_final_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_final_csv'],
                                                               bufr_t.strftime('%Y%m%d%H%M'),
                                                               tag)
        fake_bufr_fname = '%s/%s.%s.t%sz.prepbufr.tm00' % (param['paths']['syn_bufr'], 
                                                           bufr_t.strftime('%Y%m%d%H'),
                                                           tag,
                                                           bufr_t.strftime('%H'))
        convert_csv_fname = real_csv_fname
        if not os.path.isfile(real_bufr_fname):
            continue 

        # Create job script
        j_names.append('%s/syn_obs_%s_%s.sh' % (param['paths']['log'], bufr_t.strftime('%Y%m%d%H%M'), tag))

        fptr = open(j_names[-1], 'w') 
        fptr.write('#!/bin/sh\n\n')
        fptr.write('#SBATCH -A %s\n' % param['jobs']['alloc'])
        fptr.write('#SBATCH -t %s\n' % param['jobs']['time'])
        fptr.write('#SBATCH --nodes=1 --ntasks=1\n')
        fptr.write('#SBATCH --mem=%s\n' % param['jobs']['mem'])
        fptr.write('#SBATCH -o %s/%s.%s.log\n' % (param['paths']['log'], 
                                                  bufr_t.strftime('%Y%m%d%H%M'), tag))
        fptr.write('#SBATCH --partition=%s\n\n' % param['jobs']['partition'])

        fptr.write('date\n\n')

        if param['convert_bufr']['use']:
            fptr.write('# Convert real prepBUFR to CSV\n')
            fptr.write('cd %s\n' % param['paths']['real_csv'])
            fptr.write('mkdir tmp_%s_%s\n' % (bufr_t.strftime('%Y%m%d%H%M'), tag))
            fptr.write('cd tmp_%s_%s\n' % (bufr_t.strftime('%Y%m%d%H%M'), tag))
            fptr.write('cp -r  %s/bin/* .\n' % param['paths']['bufr_code']) 
            fptr.write('source %s/env/bufr_%s.env\n' % (param['paths']['bufr_code'], param['shared']['machine']))
            fptr.write('cp %s ./prepbufr \n' % real_bufr_fname)
            fptr.write('./prepbufr_decode_csv.x\n')
            fptr.write('mv ./prepbufr.csv %s\n' % real_csv_fname)
            fptr.write('cd ..\n')
            fptr.write('rm -r %s/tmp_%s_%s\n\n' % (param['paths']['real_csv'], bufr_t.strftime('%Y%m%d%H%M'), tag))    

        if param['create_uas_grid']['use']:
            fptr.write('# Create UAS grid (not enabled yet)\n\n')

        if param['create_csv']['use']:
            fptr.write('# Create UAS CSV (not enabled yet)\n\n')

        if param['interpolator']['use']:
            fptr.write('# Perform interpolation from model grid to obs location\n')
            fptr.write('. ~/.bashrc\nmy_py\n')
            fptr.write('cd %s\n' % param['paths']['osse_code'])
            fptr.write('python create_synthetic_obs.py %s \\\n' % param['paths']['model'])
            fptr.write('                               %s \\\n' % param['paths']['real_csv'])
            fptr.write('                               %s \\\n' % param['paths']['syn_perf_csv'])
            fptr.write('                               %s \\\n' % bufr_t.strftime('%Y%m%d%H'))
            fptr.write('                               %s \\\n' % wrf_start.strftime('%Y%m%d%H'))
            fptr.write('                               %s \\\n' % wrf_end.strftime('%Y%m%d%H'))
            fptr.write('                               %s \n\n' % tag)
            convert_csv_fname = fake_csv_perf_fname        

        if param['obs_errors']['use']:
            fptr.write('# Add observation errors (not enabled yet)\n\n')
            fptr.write('. ~/.bashrc\nmy_py\n')
            fptr.write('# Insert code here to move input CSV file to param[paths][syn_err_csv]\n')
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('python add_obs_errors.py %s \\\n' % bufr_t.strftime('%Y%m%d%H%M'))
            fptr.write('                         %s \\\n' % tag)
            fptr.write('                         %s/%s \\\n' % (param['paths']['osse_code'], in_yaml))
            fptr.write('mv %s/%s.%s.output.csv %s\n' % (param['paths']['syn_err_csv'], 
                                                        bufr_t.strftime('%Y%m%d%H%M'), tag, 
                                                        fake_csv_err_fname))
            convert_csv_fname = fake_csv_err_fname        
        
        if param['combine_csv']['use']:
            fptr.write('# Combine CSV files (not enabled yet)\n\n')
            convert_csv_fname = fake_csv_final_fname        

        if param['convert_csv']['use']:
            fptr.write('# Convert synthetic ob CSV to prepBUFR\n')
            fptr.write('cd %s\n' % param['paths']['syn_bufr'])
            fptr.write('mkdir tmp_%s_%s\n' % (bufr_t.strftime('%Y%m%d%H%M'), tag))
            fptr.write('cd tmp_%s_%s\n' % (bufr_t.strftime('%Y%m%d%H%M'), tag))
            fptr.write('cp -r %s/bin/* .\n' % param['paths']['bufr_code']) 
            fptr.write('source %s/env/bufr_%s.env\n' % (param['paths']['bufr_code'], param['shared']['machine']))
            fptr.write('cp %s ./prepbufr.csv \n' % convert_csv_fname)
            fptr.write('./prepbufr_encode_csv.x\n')
            fptr.write('mv ./prepbufr %s\n' % fake_bufr_fname)
            fptr.write('cd ..\n')
            fptr.write('rm -r %s/tmp_%s_%s\n\n' % (param['paths']['syn_bufr'], bufr_t.strftime('%Y%m%d%H%M'), tag))

        if param['plots']['use']:
            fptr.write('# Make plots (not enabled yet)\n\n')

        fptr.write('date')
        fptr.close()
  
# Create CSV with job submission information
all_jobs = slurm.job_list(jobs=j_names)
all_jobs.save('%s/%s' % (param['paths']['log'], param['jobs']['csv_name']))
 

"""
End create_syn_ob_jobs.py
"""
