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
# Create Job Scripts
#---------------------------------------------------------------------------------------------------

# Read in input from YAML
in_yaml = sys.argv[1]
with open(in_yaml, 'r') as fptr:
    param = yaml.safe_load(fptr)

# Copy YAML to log directory
os.system('cp %s %s' % (in_yaml, param['paths']['log']))

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
        if (os.path.isfile('%s/%s' % (param['paths']['model'], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M_er.grib2'))) or
            os.path.isfile('%s/%s' % (param['paths']['model'], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M_er.nc')))):
            wrf_start = tmp
        hr = hr - 0.25

    wrf_end = None
    hr = 1
    while wrf_end == None:
        tmp = bufr_t + dt.timedelta(hours=hr)
        if (tmp == wrf_start):
            wrf_end = wrf_start
        if (os.path.isfile('%s/%s' % (param['paths']['model'], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M_er.grib2'))) or
            os.path.isfile('%s/%s' % (param['paths']['model'], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M_er.nc')))):
            wrf_end = tmp
        hr = hr - 0.25

    t_str = bufr_t.strftime('%Y%m%d%H%M')
    
    for tag in param['shared']['bufr_tag']:

        print('creating job script for time = %s, tag = %s' % (t_str, tag))

        real_bufr_fname = '%s/%s.%s.t%sz.prepbufr.tm00' % (param['paths']['real_bufr'], 
                                                           bufr_t.strftime('%Y%m%d%H'),
                                                           tag,
                                                           bufr_t.strftime('%H'))
        real_csv_fname = '%s/%s.%s.prepbufr.csv' % (param['paths']['real_csv'], t_str, tag)
        fake_csv_bogus_fname = param['paths']['syn_bogus_csv'] + '/%s.' + tag + '.prepbufr.csv'
        fake_csv_perf_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_perf_csv'], t_str, tag)
        real_red_csv_fname = '%s/%s.%s.real_red.prepbufr.csv' % (param['paths']['syn_perf_csv'], t_str, tag)
        in_csv_limit_uas_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths'][param['limit_uas']['in_csv_dir']], t_str, tag)
        fake_csv_limit_uas_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_limit_uas_csv'], t_str, tag)
        fake_csv_err_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_err_csv'], t_str, tag)
        csv_comb_list_fname = '%s/combine_csv_list_%s_%s.txt' % (param['paths']['syn_combine_csv'], t_str, tag)
        fake_csv_comb_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_combine_csv'], t_str, tag)
        in_csv_select_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths'][param['select_obs']['in_csv_dir']], t_str, tag)
        fake_csv_select_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_select_csv'], t_str, tag)
        in_csv_superob_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths'][param['superobs']['in_csv_dir']], t_str, tag)
        fake_csv_superob_fname = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_superob_csv'], t_str, tag)
        fake_bufr_fname = '%s/%s.%s.t%sz.prepbufr.tm00' % (param['paths']['syn_bufr'], 
                                                           bufr_t.strftime('%Y%m%d%H'),
                                                           tag,
                                                           bufr_t.strftime('%H'))
        real_red_bufr_fname = '%s/%s.%s.t%sz.prepbufr.tm00' % (param['paths']['real_red_bufr'], 
                                                               bufr_t.strftime('%Y%m%d%H'),
                                                               tag,
                                                               bufr_t.strftime('%H'))
        convert_csv_fname = real_csv_fname
        if not os.path.isfile(real_bufr_fname):
            continue 

        # Create job script
        j_names.append('%s/syn_obs_%s_%s_%s.sh' % (param['paths']['log'], t_str, tag, param['shared']['log_str']))

        fptr = open(j_names[-1], 'w') 
        fptr.write('#!/bin/sh\n\n')
        fptr.write('#SBATCH -A %s\n' % param['jobs']['alloc'])
        fptr.write('#SBATCH -t %s\n' % param['jobs']['time'])
        fptr.write('#SBATCH --nodes=1 --ntasks=1\n')
        fptr.write('#SBATCH --mem=%s\n' % param['jobs']['mem'])
        fptr.write('#SBATCH -o %s/%s.%s.%s.log\n' % (param['paths']['log'], t_str, tag, param['shared']['log_str']))
        fptr.write('#SBATCH --partition=%s\n\n' % param['jobs']['partition'])
            
        fptr.write('date\n\n')

        if param['convert_bufr']['use']:
            fptr.write('# Convert real prepBUFR to CSV\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Convert real prepBUFR to CSV"\n')
            fptr.write('echo ""\n')
            fptr.write('cd %s\n' % param['paths']['real_csv'])
            fptr.write('mkdir tmp_%s_%s\n' % (t_str, tag))
            fptr.write('cd tmp_%s_%s\n' % (t_str, tag))
            fptr.write('cp -r  %s/bin/* .\n' % param['paths']['bufr_code']) 
            fptr.write('source %s/env/bufr_%s.env\n' % (param['paths']['bufr_code'], param['shared']['machine']))
            fptr.write('cp %s ./prepbufr \n' % real_bufr_fname)
            fptr.write('./prepbufr_decode_csv.x\n')
            fptr.write('mv ./prepbufr.csv %s\n' % real_csv_fname)
            fptr.write('cd ..\n')
            fptr.write('rm -r %s/tmp_%s_%s\n\n' % (param['paths']['real_csv'], t_str, tag))    

        if param['create_uas_grid']['use']:
            fptr.write('# Create UAS grid\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Create UAS grid"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python uas_sites.py %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))

        if param['create_csv']['use']:
            fptr.write('# Create UAS CSV\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Create UAS CSV"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python create_uas_csv.py %s \\\n' % t_str)
            fptr.write('                         %s \\\n' % fake_csv_bogus_fname)
            fptr.write('                         %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))
            convert_csv_fname = fake_csv_bogus_fname

        if param['interpolator']['use']:
            fptr.write('# Perform interpolation from model grid to obs location\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Perform interpolation from model grid to obs location"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python create_synthetic_obs.py %s \\\n' % param['paths']['model'])
            if param['create_csv']['use']:
                fptr.write('                               %s \\\n' % param['paths']['syn_bogus_csv'])
            else:
                fptr.write('                               %s \\\n' % param['paths']['real_csv'])
            fptr.write('                               %s \\\n' % param['paths']['syn_perf_csv'])
            fptr.write('                               %s \\\n' % bufr_t.strftime('%Y%m%d%H'))
            fptr.write('                               %s \\\n' % wrf_start.strftime('%Y%m%d%H%M'))
            fptr.write('                               %s \\\n' % wrf_end.strftime('%Y%m%d%H%M'))
            fptr.write('                               %s \\\n' % tag)
            fptr.write('                               %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))
            convert_csv_fname = fake_csv_perf_fname        

        if param['limit_uas']['use']:
            fptr.write('# Limiting UAS flights\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Limiting UAS flights"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cp %s %s/%s.%s.input.csv\n' % (in_csv_limit_uas_fname,
                                                       param['paths']['syn_limit_uas_csv'], 
                                                       t_str, tag))
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python limit_uas_flights.py %s \\\n' % t_str)
            fptr.write('                            %s \\\n' % tag)
            fptr.write('                            %s/%s \n' % (param['paths']['osse_code'], in_yaml))
            fptr.write('mv %s/%s.%s.output.csv %s\n\n' % (param['paths']['syn_limit_uas_csv'], 
                                                          t_str, tag, 
                                                          fake_csv_limit_uas_fname))
            if param['limit_uas']['plot_timeseries']['use']:
                fptr.write('mkdir %s/%s\n' % (param['paths']['plots'], t_str))
                fptr.write('cd %s/plotting\n' % param['paths']['osse_code'])
                fptr.write('python plot_full_limited_uas_timeseries.py %s \\\n' % t_str)
                fptr.write('                                           %s \\\n' % tag)
                fptr.write('                                           %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))
            convert_csv_fname = fake_csv_limit_uas_fname        

        if param['obs_errors']['use']:
            fptr.write('# Add observation errors\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Add observation errors"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cp %s %s/%s.%s.input.csv\n' % (fake_csv_perf_fname,
                                                       param['paths']['syn_err_csv'], 
                                                       t_str, tag))
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python add_obs_errors.py %s \\\n' % t_str)
            fptr.write('                         %s \\\n' % tag)
            fptr.write('                         %s/%s \n' % (param['paths']['osse_code'], in_yaml))
            fptr.write('mv %s/%s.%s.output.csv %s\n\n' % (param['paths']['syn_err_csv'], 
                                                          t_str, tag, 
                                                          fake_csv_err_fname))
            convert_csv_fname = fake_csv_err_fname        

        if param['combine_csv']['use']:

            # First, create file with CSV file names to be combined
            comb_fptr = open(csv_comb_list_fname, 'w')
            for d in param['combine_csv']['csv_dirs']:
                comb_fptr.write('%s/%s.%s.fake.prepbufr.csv\n' % (d, t_str, tag))
            comb_fptr.close()

            fptr.write('# Combine CSV files\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Combine CSV files"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python combine_bufr_csv.py %s \\\n' % csv_comb_list_fname)
            fptr.write('                           %s \n\n' % fake_csv_comb_fname)
            convert_csv_fname = fake_csv_comb_fname        
        
        if param['select_obs']['use']:
            fptr.write('# Only select certain ob types for CSV files\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Selecting certain obs for CSV files"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python select_obtypes.py %s \\\n' % in_csv_select_fname)
            fptr.write('                         %s \\\n' % fake_csv_select_fname)
            fptr.write('                         %s/%s \n' % (param['paths']['osse_code'], in_yaml))
            if param['select_obs']['include_real_red']:
                in_csv_real = '/'.join(in_csv_select_fname.split('/')[:-1] + 
                                       [in_csv_select_fname.split('/')[-1].replace('fake', 'real_red')])
                out_csv_real = '/'.join(fake_csv_select_fname.split('/')[:-1] + 
                                        [fake_csv_select_fname.split('/')[-1].replace('fake', 'real_red')])
                fptr.write('python select_obtypes.py %s \\\n' % in_csv_real)
                fptr.write('                         %s \\\n' % out_csv_real)
                fptr.write('                         %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))
            convert_csv_fname = fake_csv_select_fname        

        if param['superobs']['use']:
            fptr.write('# Creating superobs\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Create superobs"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('cp %s %s/%s.%s.input.csv\n' % (in_csv_superob_fname,
                                                       param['paths']['syn_superob_csv'], 
                                                       t_str, tag))
            fptr.write('cd %s/main\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            fptr.write('python create_superobs.py %s \\\n' % t_str)
            fptr.write('                          %s \\\n' % tag)
            fptr.write('                          %s/%s \n' % (param['paths']['osse_code'], in_yaml))
            fptr.write('mv %s/%s.%s.output.csv %s\n\n' % (param['paths']['syn_superob_csv'], 
                                                          t_str, tag, 
                                                          fake_csv_superob_fname))
            if param['superobs']['plot_vprof']['use']:
                fptr.write('mkdir %s/%s\n' % (param['paths']['plots'], t_str))
                fptr.write('cd %s/plotting\n' % param['paths']['osse_code'])
                fptr.write('python plot_raw_superob_uas_vprofs.py %s \\\n' % t_str)
                fptr.write('                                          %s \\\n' % tag)
                fptr.write('                                          %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))
            convert_csv_fname = fake_csv_superob_fname        

        if param['convert_syn_csv']['use']:
            fptr.write('# Convert synthetic ob CSV to prepBUFR\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Convert synthetic ob CSV to prepBUFR"\n')
            fptr.write('echo ""\n')
            fptr.write('cd %s\n' % param['paths']['syn_bufr'])
            fptr.write('mkdir tmp_%s_%s\n' % (t_str, tag))
            fptr.write('cd tmp_%s_%s\n' % (t_str, tag))
            fptr.write('cp -r %s/bin/* .\n' % param['paths']['bufr_code']) 
            fptr.write('source %s/env/bufr_%s.env\n' % (param['paths']['bufr_code'], param['shared']['machine']))
            fptr.write('cp %s ./prepbufr.csv \n' % convert_csv_fname)
            fptr.write('./prepbufr_encode_csv.x\n')
            fptr.write('mv ./prepbufr %s\n' % fake_bufr_fname)
            fptr.write('cd ..\n')
            fptr.write('rm -r %s/tmp_%s_%s\n\n' % (param['paths']['syn_bufr'], t_str, tag))
        
        if param['convert_real_red_csv']['use']:
            fptr.write('# Convert real_red ob CSV to prepBUFR\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Convert real_red ob CSV to prepBUFR"\n')
            fptr.write('echo ""\n')
            fptr.write('cd %s\n' % param['paths']['real_red_bufr'])
            fptr.write('mkdir tmp_%s_%s\n' % (t_str, tag))
            fptr.write('cd tmp_%s_%s\n' % (t_str, tag))
            fptr.write('cp -r %s/bin/* .\n' % param['paths']['bufr_code']) 
            fptr.write('source %s/env/bufr_%s.env\n' % (param['paths']['bufr_code'], param['shared']['machine']))
            if param['select_obs']['use'] and param['select_obs']['include_real_red']:
                fptr.write('cp %s ./prepbufr.csv \n' % out_csv_real)
            else:
                fptr.write('cp %s ./prepbufr.csv \n' % real_red_csv_fname)
            fptr.write('./prepbufr_encode_csv.x\n')
            fptr.write('mv ./prepbufr %s\n' % real_red_bufr_fname)
            fptr.write('cd ..\n')
            fptr.write('rm -r %s/tmp_%s_%s\n\n' % (param['paths']['real_red_bufr'], t_str, tag))

        if param['plots']['use']:
            fptr.write('# Make plots\n')
            fptr.write('echo ""\n')
            fptr.write('echo "=============================================================="\n')
            fptr.write('echo "Make plots"\n')
            fptr.write('echo ""\n')
            fptr.write('source %s/activate_python_env.sh\n' % param['paths']['osse_code'])
            fptr.write('mkdir %s/%s\n' % (param['paths']['plots'], t_str))
            fptr.write('cd %s/plotting\n' % param['paths']['osse_code'])
            fptr.write('echo "Using osse_ob_creator version `git describe`"\n')
            if param['create_csv']['use']:
                fptr.write('python plot_uas_NR_diffs.py %s \\\n' % tag)
                fptr.write('                            %s \\\n' % t_str)
                fptr.write('                            %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))
            else:
                fptr.write('python plot_ob_diffs_2d.py %s \\\n' % tag)
                fptr.write('                           %s \\\n' % t_str)
                fptr.write('                           %s/%s \n' % (param['paths']['osse_code'], in_yaml))
                fptr.write('python plot_ob_diffs_vprof.py %s \\\n' % tag)
                fptr.write('                              %s \\\n' % t_str)
                fptr.write('                              %s/%s \n\n' % (param['paths']['osse_code'], in_yaml))

        fptr.write('date')
        fptr.close()
  
# Create CSV with job submission information
all_jobs = slurm.job_list(jobs=j_names)
all_jobs.save('%s/%s' % (param['paths']['log'], param['jobs']['csv_name']))
 

"""
End create_syn_ob_jobs.py
"""
