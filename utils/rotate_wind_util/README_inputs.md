# Description of Parameters Found in rotate_winds.yml

Shawn Murdzek  
NOAA/OAR/Global Systems Laboratory  
shawn.s.murdzek@noaa.gov

## Parameters

- **start_time**: Time of first GRIB2 file with winds that need to be rotated.
- **end_time**: Time of the last GRIB2 file with winds that need to be rotated.
- **time_step**: Time between GRIB2 files (in minutes).
- **file_tmpl_in**: Template for input GRIB2 files. Use same conventions for strftime/strptime from Python's datetime module.
- **file_tmpl_out**: Template for output GRIB2 files. Use same conventions for strftime/strptime from Python's datetime module.
- **run_dir**: Run directory. Log files and bash scripts will be saved here.
- **tag**: Optional string to add to the log files and bash scripts.
    
- **job_max**: Maximum number of jobs.
- **user**: User name on the machine being used.
- **alloc**: Allocation to use when submitting batch jobs.
- **csv_name**: Name of CSV file to save job information.
- **maxtries**: Maximum number of tries for each job.
- **job_mem**: Memory for each job.
- **job_time**: Walltime limit for each job.
- **partition**: Partition to use for the batch jobs.
