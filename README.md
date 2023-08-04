
# Synthetic Observation Creator Code

Shawn Murdzek  
NOAA/OAR/Global Systems Laboratory  
shawn.s.murdzek@noaa.gov

## Description

The programs included here create synthetic observations for an Observing System Simulation Experiment (OSSE) by interpolating Nature Run (NR) output to predefined observation locations and adding appropriate random errors (either purely Gaussian or autocorrelated in time or space). The program relies heavily on CSV files that contain the output from prepBUFR files. These CSV files define the observation locations and all synthetic obs are saved to these CSV files so that they can be easily converted into prepBUFR files that can be read by data assimilation packages.

### Specific Programs

1. `activate_python_env.sh`: Helper program that activates the Python environment necessary for this program.

2. `create_syn_ob_jobs.py`: Helper program that creates a bunch of bash jobs to create synthetic observations using the input parameters in `synthetic_ob_creator_param.yml`. 

3. `cron_run_synthetic_ob_creator.sh`: Bash script that runs `run_synthetic_ob_creator.py`. Can be run as a cron job.

4. `run_synthetic_ob_creator.py`: Helper program that submits a bunch of bash jobs (up to a certain limit). Failed jobs are also retried.

5. `synthetic_ob_creator_param.yml`: Input settings for the synthetic observation creation program.

6. `main`: Various programs needed to create synthetic observations. Inputs can either be specified within each of these programs or within `synthetic_ob_creator_param.yml`.

    1. `add_obs_errors.py`: Reads a series of prepBUFR CSV files and adds random observation errors.

    2. `combine_bufr_csv.py`: Combines two BUFR CSV files into a single BUFR CSV file.
    
    3. `create_ims_snow_obs.py`: Creates snow cover and ice cover fields using NR output.
    
    4. `create_synthetic_obs.py`: Intepolates NR output to synthetic observation locations.

    5. `create_uas_csv.py`: Creates an "empty" CSV for UAS observations. This CSV can then be passed to `create_synthetic_obs.py`.

    6. `uas_sites.py`: Determines UAS observation locations across CONUS given a specified observation spacing.

7. `plotting`: Various utilities for making comparison plots between synthetic and real observations.

8. `tests`: Contains various scripts to test whether the synthetic observations are being created correctly.

9. `utils`: Miscellaneous scripts that might be helpful (or that I haven't bothered deleting yet!)

## Dependencies

In addition to several Python modules that are commonly used in meteorological research (e.g., NumPy, Matplotlib, Pandas, MetPy, etc.), the scripts found here also rely on modules found within [pyDA_utils](https://github.com/ShawnMurdzek-NOAA/pyDA_utils). To install pyDA_utils, I recommend cloning the repo and adding the location of pyDA_utils to the `PYTHONPATH` environment variable. 

## Test Data

The `tests` directory contains a sample prepBUFR CSV file for testing purposes. In order to create synthetic obs using this test CSV, NR data must be pulled from elsewhere (these files are too large to be stored on GitHub). 1-km WRF NR output can be found on NOAA HPSS. 

## Running the Program

1. Update `activate_python_env.sh` with the appropriate Python environment.

2. Edit `synthetic_ob_creator_param.yml` with the desired parameters.

3. Run `python create_synthetic_obs.py` to create the job submission scripts

4. Add `cron_run_synthetic_ob_creator.sh` to your crontab using the following line:

`*/30 * * * * source /etc/profile && cd /path/to/osse_ob_creator && bash ./cron_run_synthetic_ob_creator.sh`

## Additional Documentation

- [Description of input parameters](https://github.com/ShawnMurdzek-NOAA/osse_ob_creator/blob/main/README_inputs.md)
