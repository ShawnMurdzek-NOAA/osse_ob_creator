
# Rotate Winds Utility Program

Shawn Murdzek  
NOAA/OAR/Global Systems Laboratory  
shawn.s.murdzek@noaa.gov

## Description


### Specific Programs

1. `create_rotate_wind_jobs.py`: Helper program that creates a bunch of bash jobs to rotate winds using the input parameters in `rotate_winds.yml`. 

2. `cron_run_rotate_winds.sh`: Bash script that runs `run_rotate_winds.py`. Can be run as a cron job.

3. `run_rotate_winds.py`: Helper program that submits a bunch of bash jobs (up to a certain limit). Failed jobs are also retried.

4. `rotate_winds.yml`: Input settings for the rotate wind utility program.

5. `tests`: Contains various scripts to test whether the winds are being rotated correctly.

## Running the Program

1. Update `activate_python_env.sh` with the appropriate Python environment.

2. Edit `rotate_winds.yml` with the desired parameters.

3. Run `python create_rotate_wind_jobs.py` to create the job submission scripts

4. Add `cron_run_rotate_winds.sh` to your crontab using the following line:

`*/30 * * * * source /etc/profile && cd /path/to/osse_ob_creator/utils/rotate_wind_util && bash ./cron_run_rotate_winds.sh`

## Testing 

To run the single test in the `tests/` directory, edit the `test.yml` file with the correct file names and variable/tolerance level combinations for the test, then run `bash run_tests.sh`.
