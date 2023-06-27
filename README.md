
# Synthetic Observation Creator Code

Shawn Murdzek  
NOAA/OAR/Global Systems Laboratory  
shawn.s.murdzek@noaa.gov

## Description

The programs included here create synthetic observations for an Observing System Simulation Experiment (OSSE) by interpolating Nature Run (NR) output to predefined observation locations and adding appropriate random errors (either purely Gaussian or autocorrelated in time or space). The program relies heavily on CSV files that contain the output from prepBUFR files. These CSV files define the observation locations and all synthetic obs are saved to these CSV files so that they can be easily converted into prepBUFR files that can be read by data assimilation packages.

### Specific Programs

1. `create\_synthetic\_obs.py`: The main program that reads a prepBUFR CSV file, interpolates NR output to the desired locations, and saves the output in a new prepBUFR CSV file. 

2. `run\_synthetic\_ob\_creator.py`: A helper program that creates slurm job submission scripts to run create\_synthetic\_obs.py for several prepBUFR CSV files. For creating several synthetic observation CSV files, it is recommended that this script be run regularly using a crontab.

3. `add\_obs\_errors.py`: Reads a series of prepBUFR CSV files and adds random observation errors.

4. `create\_ims\_snow\_obs.py`: Creates snow cover and ice cover fields using NR output.

5. `uas\_sites.py`: Determines UAS observation locations across CONUS given a specified observation spacing.

6. `tests`: Contains various scripts to test whether the synthetic observations are being created correctly. Most of these tests consist of comparisons between real and synthetic observations during the first few hours of the NR.

7. `utils`: Miscellaneous scripts that might be helpful (or that I haven't bothered deleting yet!)

## Dependencies

In addition to several Python modules that are commonly used in meteorological research (e.g., NumPy, Matplotlib, Pandas, MetPy, etc.), the scripts found here also rely on modules found within [pyDA_utils](https://github.com/ShawnMurdzek-NOAA/pyDA_utils). To install pyDA_utils, I recommend cloning the repo and adding the location of pyDA_utils to the `PYTHONPATH` environment variable. 

## Test Data

The `tests` directory contains a sample prepBUFR CSV file for testing purposes. In order to create synthetic obs using this test CSV, NR data must be pulled from elsewhere (these files are too large to be stored on GitHub). 1-km WRF NR output can be found on NOAA HPSS. 
