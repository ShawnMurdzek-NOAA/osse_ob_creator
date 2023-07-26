"""
Submit Jobs for the Synthetic Observation Creation Program

Command line arguments:
    argv[1] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import sys
import yaml

import pyDA_utils.slurm_util as slurm


#---------------------------------------------------------------------------------------------------
# Submit Job Scripts
#---------------------------------------------------------------------------------------------------

# Read in input from YAML
with open(sys.argv[1], 'r') as fptr:
    param = yaml.safe_load(fptr)

# Read in DataFrame with job info, then submit jobs
job_csv_fname = '%s/%s' % (param['paths']['log'], param['jobs']['csv_name'])
job_obj = slurm.job_list(fname=job_csv_fname)
job_obj.update(param['jobs']['user'], param['jobs']['maxtries'])
job_obj.submit_jobs(param['jobs']['user'], param['jobs']['max'])
job_obj.save(job_csv_fname)


"""
End run_synthetic_ob_creator.py
"""
