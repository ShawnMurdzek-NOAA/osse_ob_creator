"""
Master Script that Submits Jobs to Create Synthetic Obs

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


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# BUFR time stamps
bufr_time = [dt.datetime(2022, 4, 29, 12) + dt.timedelta(hours=i) for i in range(0, 13, 6)]

# Parameters passed to create_conv_obs.py for each prepBUFR time
nfiles = len(bufr_time)
wrf_dir = ['/work2/noaa/wrfruc/murdzek/nature_run_spring/UPP'] * nfiles
bufr_dir = ['/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv'] * nfiles
fake_bufr_dir = ['/work2/noaa/wrfruc/murdzek/nature_run_spring/synthetic_obs_csv/conv/data'] * nfiles
log_dir = ['/work2/noaa/wrfruc/murdzek/nature_run_spring/synthetic_obs_csv/conv/log'] * nfiles

# BUFR tags
bufr_tag = ['rap', 'rap_e', 'rap_p']
bufr_tag = ['rap']

# Parameters for controlling number of jobs, allocation, maxtries, etc
max_jobs = 25
user = 'smurdzek'
allocation = 'wrfruc'
job_csv_name = '/work2/noaa/wrfruc/murdzek/nature_run_spring/synthetic_obs_csv/conv/log/synthetic_ob_creator_jobs.csv'
maxtries = 3

# Location of Python script
py_dir = os.popen('pwd').read().strip()


#---------------------------------------------------------------------------------------------------
# Function to Grab Information from Slurm Job Scheduler
#---------------------------------------------------------------------------------------------------

def slurm_job_info(job_df, user, maxtries):
    """
    Returns information about active and completed jobs from Slurm

    Parameters 
    ----------
    job_df : pd.DataFrame
        DataFrame containing job information
    user : string
        User ID
    maxtries : integer
        Maximum number of attempts for each job

    Returns
    -------
    job_df : pd.DataFrame
        DataFrame containing updated job information
    njobs : integer
        Number jobs queued or running 

    """

    # Determine number of queued/running jobs
    njobs = len(os.popen('squeue -u %s' % user).read().split('\n')) - 2

    # Determine job statuses and mark jobs as either completed or need to be resubmitted
    idx = np.where(np.logical_and(job_df['submitted'], ~job_df['completed']))[0]
    for i in idx:
        jobID = job_df.loc[i, 'jobID']
        sacct_out = os.popen('sacct --jobs=%d' % jobID).read().split('\n')[2].split()
        if sacct_out[5] == 'COMPLETED':
            if sacct_out[6] == '0:0':
                job_df.loc[i, 'completed'] = True
            else:
                if job_df.loc[i, 'tries'] < maxtries:
                    job_df.loc[i, 'submitted'] = False

    return job_df, njobs


#---------------------------------------------------------------------------------------------------
# Create and Submit Job Scripts
#---------------------------------------------------------------------------------------------------

# Read in (or create) DataFrame with job info
if os.path.isfile(job_csv_name):
    sub_jobs = pd.read_csv(job_csv_name)
else:
    tmp_dict = {'date':[], 'idate':[], 'tag':[]}
    for i, t in enumerate(bufr_time):
        for tag in bufr_tag:
            tmp_dict['date'].append(t)
            tmp_dict['idate'].append(i)
            tmp_dict['tag'].append(tag)
    sub_jobs = pd.DataFrame(tmp_dict)
    sub_jobs['submitted'] = [False] * len(sub_jobs)
    sub_jobs['completed'] = [False] * len(sub_jobs)
    sub_jobs['jobID'] = np.zeros(len(sub_jobs), dtype=int)
    sub_jobs['tries'] = np.zeros(len(sub_jobs), dtype=int)

# Determine current job statuses
sub_jobs, njobs = slurm_job_info(sub_jobs, user, maxtries)
print('njobs = %d' % njobs)

# Submit new jobs
while njobs < max_jobs:

    # End script if all jobs have been submitted
    if np.all(sub_jobs['submitted']):
        break

    cond = np.logical_and(sub_jobs['submitted'] == False, sub_jobs['tries'] < maxtries)
    idx = np.where(cond)[0][0]
    idate = sub_jobs.loc[idx, 'idate']

    # Skip to next job if the required prepBUFR file does not exist
    fname = '%s/%s.%s.prepbufr.csv' % (bufr_dir[idate], bufr_time[idate].strftime('%Y%m%d%H00'),
                                       sub_jobs.loc[idx, 'tag'])
    if not os.path.isfile(fname):
        sub_jobs.loc[idx, 'submitted'] = True
        sub_jobs.loc[idx, 'completed'] = True
        sub_jobs.loc[idx, 'tries'] = 0
        continue

    # Determine first and last WRF file time
    wrf_start = None
    hr = 3
    while wrf_start == None:
        tmp = bufr_time[idate] - dt.timedelta(hours=hr)
        if os.path.isfile('%s/%s' % (wrf_dir[idate], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M.grib2'))):
            wrf_start = tmp
            break
        hr = hr - 1

    tmp = bufr_time[idate] + dt.timedelta(hours=1)
    if os.path.isfile('%s/%s' % (wrf_dir[idate], tmp.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M.grib2'))):
        wrf_end = tmp
    else:
        wrf_end = bufr_time[idate]

    # Create job script
    j_name = '%s/syn_obs_%s_%s.sh' % (log_dir[idate], bufr_time[idate].strftime('%Y%m%d%H%M'), 
                                      sub_jobs.loc[idx, 'tag'])
    fptr = open(j_name, 'w') 
    fptr.write('#!/bin/sh\n\n')
    fptr.write('#SBATCH -A %s\n' % allocation)
    fptr.write('#SBATCH -t 08:00:00\n')
    fptr.write('#SBATCH --nodes=1 --ntasks=1\n')
    fptr.write('#SBATCH --mem=30GB\n')
    fptr.write('#SBATCH -o %s/%s.%s.log\n' % (log_dir[idate], bufr_time[idate].strftime('%Y%m%d%H%M'),
                                              sub_jobs.loc[idx, 'tag']))
    fptr.write('#SBATCH --partition=orion\n\n')
    fptr.write('date\n. ~/.bashrc\nmy_py\n\n')
    fptr.write('python %s/create_conv_obs.py %s \\\n' % (py_dir, wrf_dir[idate]))
    fptr.write('                             %s \\\n' % bufr_dir[idate])
    fptr.write('                             %s \\\n' % fake_bufr_dir[idate])
    fptr.write('                             %s \\\n' % bufr_time[idate].strftime('%Y%m%d%H'))
    fptr.write('                             %s \\\n' % wrf_start.strftime('%Y%m%d%H'))
    fptr.write('                             %s \\\n' % wrf_end.strftime('%Y%m%d%H'))
    fptr.write('                             %s \n\n' % sub_jobs.loc[idx, 'tag'])
    fptr.write('date')
    fptr.close()
   
    # Submit job and mark it as submitted
    sub_jobs.loc[idx, 'jobID'] = int(os.popen('sbatch %s' % j_name).read().strip().split(' ')[-1])
    print()
    print('submitted job %d' % sub_jobs.loc[idx, 'jobID'])
    sub_jobs.loc[idx, 'tries'] = sub_jobs.loc[idx, 'tries'] + 1
    sub_jobs.loc[idx, 'submitted'] = True

    # Wait a few seconds for the job to submit, then check number of jobs
    time.sleep(5)
    sub_jobs, njobs = slurm_job_info(sub_jobs, user, maxtries)
    print('njobs = %d' % njobs)

# Save updated job submission CSV
sub_jobs.to_csv(job_csv_name)


"""
End run_synthetic_ob_creator.py
"""
