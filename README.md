
# Synthetic Observation Creator Code

Shawn Murdzek  
Cooperative Institute for Research in Environmental Sciences (CIRES) and CU Boulder  
Embedded in NOAA/OAR/Global Systems Laboratory  
shawn.s.murdzek@noaa.gov

## Description

The programs included here create synthetic observations for an Observing System Simulation Experiment (OSSE) by interpolating Nature Run (NR) output to predefined observation locations and adding appropriate random errors (either purely Gaussian or autocorrelated in time or space). The program relies heavily on CSV files that contain the output from prepBUFR files. These CSV files define the observation locations and all synthetic obs are saved to these CSV files so that they can be easily converted into prepBUFR files that can be read by data assimilation packages.

### Contents

1. `activate_python_env.sh`: Helper program that activates the Python environment necessary for this program.

2. `create_syn_ob_jobs.py`: Helper program that creates a bunch of bash jobs to create synthetic observations using the input parameters in `synthetic_ob_creator_param.yml`. 

3. `cron_run_synthetic_ob_creator.sh`: Bash script that runs `run_synthetic_ob_creator.py`. Can be run as a cron job.

4. `environment.yml`: Python environment used by this program.

5. `run_synthetic_ob_creator.py`: Helper program that submits a bunch of bash jobs (up to a certain limit). Failed jobs are also retried.

6. `synthetic_ob_creator_param.yml`: Input settings for the synthetic observation creation program.

7. `example/`: Example case.

8. `fix_data/`: Fixed input data (e.g., UAS site location text files).

9. `main/`: Various programs needed to create synthetic observations. Inputs can either be specified within each of these programs or within `synthetic_ob_creator_param.yml`.

    1. `add_obs_errors.py`: Reads a series of prepBUFR CSV files and adds random observation errors.

    2. `combine_bufr_csv.py`: Combines two BUFR CSV files into a single BUFR CSV file.
    
    3. `create_ims_snow_obs.py`: Creates snow cover and ice cover fields using NR output.
  
    4. `create_superobs.py`: Creates superobs from raw observations. Separate superobs are created for a set of input BUFR 3-digit types.
    
    5. `create_synthetic_obs.py`: Intepolates NR output to synthetic observation locations.

    6. `create_uas_csv.py`: Creates an "empty" CSV for UAS observations. This CSV can then be passed to `create_synthetic_obs.py`.
  
    7. `limit_uas_flights.py`: Limits UAS flights owing to local meteorology.
    
    8. `select_obtypes.py`: Controls which observation types (3-digit numbers) are within an observation CSV file.

    9. `uas_sites.py`: Determines UAS observation locations across CONUS given a specified observation spacing.

10. `plotting/`: Various utilities for making comparison plots between synthetic and real observations.

11. `tests/`: Contains various scripts to test whether the synthetic observations are being created correctly.

12. `utils/`: Miscellaneous scripts that might be helpful (or that I haven't bothered deleting yet!)

## Dependencies

This program has been tested using the Python environment found in `environment.yml`. In addition to these packages, the following are also needed:

- [pyDA_utils](https://github.com/ShawnMurdzek-NOAA/pyDA_utils)
- [prepbufr_decoder](https://github.com/ShawnMurdzek-NOAA/prepbufr_decoder)

To install pyDA_utils, I recommend cloning the repo and adding the location of pyDA_utils to the `PYTHONPATH` environment variable. prepbufr_decoder is a Fortran program and must be compiled prior to running osse_ob_creator. This program is used to convert prepBUFR files to CSVs and vice versa. 

## Running the Program

1. Update `activate_python_env.sh` with the appropriate Python environment.

2. Edit `synthetic_ob_creator_param.yml` with the desired parameters.

3. Run `python create_synthetic_obs.py` to create the job submission scripts

4. Run the jobs in one of two ways:
   
    1. If a single job is created for each observation file, run the program by adding `cron_run_synthetic_ob_creator.sh` to your crontab. E.g., `*/30 * * * * source /etc/profile && cd /path/to/osse_ob_creator && bash ./cron_run_synthetic_ob_creator.sh`

    2. If a single job is created for each task (i.e., multiple jobs per observation file), run using Rocoto. `create_synthetic_obs.py` will create a launch script in the `<rocoto>` directory that can be added to your crontab to run the Rocoto workflow.

## Testing

Before testing, the test data must be downloaded and linked (e.g., `ln -snf`) into the `tests/data` directory. Test data can be found on the MSU machines at `/work2/noaa/wrfruc/murdzek/src/bufr_test_data/osse_ob_creator`.

Limited testing capabilities can be found in the `tests` directory. There is currently only one formal test (linear_interp_test), which tests the ability to convert a prepBUFR file to a CSV, create "perfect" synthetic observations via linear interpolation, then convert the output CSV back to a prepBUFR file. All data needed to run this test are included in the `tests/data` directory. Because the Nature Run output files and the prepBUFR file only contain a very small subset of the total Nature Run output and prepBUFR observations, respectively, this test runs relatively quickly (in a few minutes). 

Steps to run a test:

1. Edit the appropriate YAML file (e.g., `linear_interp_test.yml`).

2. Select the tests to run by editing the beginning of the `run_tests.sh` script. There is also an option to re-create the test data from the full Nature Run output and the prepBUFR file with all the observations.

3. Run the test using `bash run_tests.sh`. The program will print output to the screen containing the status of the test and whether the test passed/failed.

4. Output from the test will be saved to a newly created directory that contains the name of the test. 

In addition to the formal tests listed above, there are also some miscellaneous scripts in the `tests/legacy` directory, which may be helpful in examining the performance of the osse_ob_creator program.

## Additional Documentation

- [Description of input parameters](https://github.com/ShawnMurdzek-NOAA/osse_ob_creator/blob/main/README_inputs.md)
- [Google Doc with additional information](https://docs.google.com/document/d/16MsvUlINpu_hmiUjFbt8qi1Pt4swB6jdJiHcpnMwmEI/edit?usp=sharing)
