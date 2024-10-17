
# Description of Parameters Found in synthetic_ob_creator_param.yml

Shawn Murdzek  
NOAA/OAR/Global Systems Laboratory  
shawn.s.murdzek@noaa.gov  

## General Blocks

### paths

Contains numerous paths that contain...

- **real_bufr**: Real observation prepBUFR files. Note that create_syn_ob_jobs.py will not run if this path does not point to the location of the real prepBUFR files. This only applies to this path, other paths can be set to blank strings if not needed.
- **real_csv**: Real observation CSV files. Decoded from the prepBUFR files in real_bufr.
- **syn_bogus_csv**: "Empty" observation CSV files. Used to define UAS observation locations and times.
- **syn_perf_csv**: "Perfect" (i.e., no added errors) synthetic observation CSV files. Synthetic observations are determined by interpolating Nature Run output to locations specified by the observation CSV files found in real_csv (if use = False in create_csv block) or syn_bogus_csv (if use = True in create_csv block).
- **syn_limit_uas_csv**: Synthetic UAS observations with flights terminated after certain meteorological conditions are met (e.g., high winds, icing). 
- **syn_err_csv**: Synthetic observation CSV files with added errors.
- **syn_combine_csv**: Combined observation CSV files (conventional obs + UAS obs).
- **syn_select_csv**: Observation CSV files with only certain observation types. Useful for data-denial experiments (OSEs).
- **syn_superob_csv**: Superobbed CSV files.
- **syn_bufr**: Synthetic observation prepBUFR files.
- **real_red_bufr**: Real observation prepBUFR files, but only containing observations at the same locations as the synthetic observation prepBUFR files.
- **model**: Nature Run model output.
- **log**: log files and job submission scripts.
- **plots**: Figures.  
- **osse_code**: osse_ob_creator program.
- **bufr_code**: prepbufr_decoder program.

### shared

Contains parameters needed for multiple components.

- **machine**: HPC machine name. Options: `orion`.
- **bufr_start**: Timestamp for first prepBUFR file (YYYYMMDDHHMM).
- **bufr_end**: Timestamp for last prepBUFR file (YYYYMMDDHHMM).
- **bufr_step**: Minutes between successive prepBUFR files.
- **bufr_tag**: List of prepBUFR tags to use (e.g., `rap`, `rap_e`, `rap_p`).
- **uas_grid_file**: File (including the path) containing UAS observation horizontal locations.
- **log_str**: String to include in the log file names (useful to prevent log files from being overwritten if the program is run multiple times).

### jobs

Contains parameters needed for the job submission files.

- **max**: Maximum number of jobs that can be in the queue at once for this particular user.
- **user**: HPC username.
- **alloc**: HPC allocation.
- **csv_name**: Name of the CSV file to track job submissions. No path is needed; the file will be placed in the log directory.
- **maxtries**: Maximum number of times that a job will be submitted if it fails.
- **mem**: Memory required for each job (the interpolator component requires ~30 GB).
- **time**: Maximum allowed walltime for each job.
- **partition**: HPC partition used for the jobs.

## Component Blocks

These are the individual parts of the program, which can be turned on/off individually using the `use` parameter. Note that only conventional OR UAS observations can be created, not both simultaneously.

### convert_bufr

Converts prepBUFR files to observation CSV files. Uses the `prepbufr_decoder` program.

### create_uas_grid

Creates a text file containing the horizontal locations of UAS sites. Uses `main/uas_sites.py`.

- **dx**: Spacing between UAS sites (m).
- **npts_we**: Number of UAS sites in the East-West direction.
- **npts_sn**: Number of UAS sites in the South-North direction.
- **land_closing**: Option to apply binary closing after applying landmask.
- **max_hole_size**: Maximum hole size. Gaps in the UAS network <= `max_hole_size` are filled. Set to 0 to turn off.
- **shp_fname**: File name (including the path) of the shapefile containing the outline of the US.
- **nshape**: Index in `shp_fname` that corresponds to the US.
- **proj_str**: Map projection string in proj4 format. See documentation [here](https://proj.org/operations/projections/lcc.html).
- **max_sites**: Max number of UAS sites to include in a single text file. Recommended value is 2500. If more sites are included in UAS text files, `interpolator` jobs may extend past 8 hours, which is often undesirable.
- **make_plot**: Option to make a plot showing the UAS sites.

### create_csv

Creates an "empty" observation CSV file that includes UAS observation locations (x, y, z, and t). Uses `main/create_uas_csv.py`.

- **max_time**: Elapsed time after CSV observation timestamp to stop collecting UAS obs (s).
- **ascent_rate**: UAS ascent speed (m/s).
- **sample_freq**: UAS sampling frequency (s).
- **max_height**: Maximum UAS flight altitude (m)
- **init_sid**: Number assigned to the first station ID. Useful when using multiple input text files and you don't want the station IDs to repeat.
- **sample_bufr_fname**: File (including the path) of an observation CSV. Needed to determine which fields to include in the "empty" observation CSV.
- **uas_offset**: Difference between the actual UAS flight time and the observation CSV timestamp (s).

### interpolator

Interpolates Nature Run output in space and time to observation locations specified in an observation CSV file. Uses `main/create_synthetic_obs.py`.

- **obs_2d**: List of 2-D observation subsets to use (e.g., ADPSFC, MSONET, etc.)
- **obs_3d**: List of 3-D observation subsets to use (e.g., ADPUPA, AIRCAR, etc.)
- **uas_obs**: Option to create UAS obs. Set to False if creating conventional obs, set to True for UAS obs. Controls whether vertical interpolation is in POB (conventional obs) or ZOB (UAS).
- **copy_winds**: Option to copy UOB and VOB to UFC and VFC. These fields are used in `read_prepbufr.f90` to create VAD observations.
- **interp_z_aircft**: Option to interpolate height obs (ZOB) for AIRCAR and AIRCFT platforms. Because altitudes are not actually measured by aircraft (instead, they are derived using the observed pressure and the US standard atmosphere), this should be set to `False`, unless UAS observations are used.
- **height_opt**: Reference for height observations. Options: `msl` = above mean sea level, `agl` = above ground level. Heights from prepBUFR files are in MSL, but heights from "empty" UAS observation CSV files are in AGL.
- **use_raob_drift**: Option to use (XDR, YDR) rather tha (XOB, YOB) for ADPUPA observations.
- **coastline_correct**: Option to "correct" observations that occur near coastlines. This does not appear to help much, so it should usually be set to `False`.
- **use_Tv**: Option to use virtual temperature when tvflg = 0. Not necessary for RAP prepBUFR files because all temperatures are sensible, not virtual.
- **add_ceiling**: Option to add ceiling observations to surface-based platforms (ADPSFC, SFCSHP, MSONET).
- **add_liq_mix**: Option to interpolate liquid water mixing ratio (cloud + rain mixing ratio) to the observations. This field is saved to a new CSV column labeled "liqmix".
- **debug**: Option to add additional output for debugging (0 = none, 1 = some, 2 = a lot).

### limit_uas

Limits synthetic UAS flights based on local meteorology (e.g., high winds). Uses `main/limit_uas_flights.py`.

- **in_csv_dir**: Which path from the `paths` section to pull observation CSVs from.
- **drop_col**: List of columns to drop after limiting UAS flights. This is useful for removing columns in the BUFR CSV files that are only included for limiting UAS flights (e.g., liqmix).
- **verbose**: Verbosity. Higher integers will print more output
- **limits**: Parameters for limiting UAS flights. Includes 3 levels:
    1. Observation type used to determine whether a limit is exceeded
    2. Method for limiting UAS flight ("wind", "icing_RH", or "icing_LIQMR"; options can also be found in `main/limit_uas_flights.py`)
    3. "lim_kw" and "remove_kw": Keyword arguments passed to either the method that determines whether a meteorological limit is exceeded or the method that actually removes the observations that exceed the meteorological limits, respectively. Keyword arguments can be found in `pyDA_utils/limit_prepbufr.py`.
- **plot_timeseries**: Parameters for plotting timeseries of UAS observations before and after meteorological limits are applied.
    - **plot_vars**: Variable to plot, along with a single value to plot as a dashed, horizontal line (useful for plotting the meteorological limit for that variable).
    - **n_sid**: Number of unique SIDs to plot. The program will automatically choose the SIDs that had the largest reductions owing to the meteorological limits.
    - **obtype**: Observation type to pull the SIDs for "n_sid" from.

### obs_errors 

Add observation errors to observations within an observation CSV file. Uses `main/add_obs_errors.py`.

- **errtable**: File (including path) containing error standard deviations. Same format as errtable in GSI.
- **autocor_POB_obs**: Observation types that will have errors correlated in the pressure dimension.
- **autocor_DHR_obs**: Observation types that will have errors correlated in the time (DHR) dimension.
- **autocor_ZOB_partition_DHR_obs**: Observation types that will be broken into groups based on the time (DHR) dimension and then have correlated errors in the height dimension (these correlated errors will "reset" with each time group).
- **auto_reg_parm**: Autoregression parameter for an AR1 process. $Error = N(0, stdev) + auto\\_reg\\_parm * \frac{previous\\ error}{d}$, where $stdev$ is specified in `errtable` and $d$ is the distance between two consecutive observations.
- **verbose**: Option to turn on verbose output (useful for debugging).
- **dewpt_check**: Option to check whether the reported dewpoint (TDO) is consistent with the reported temperature (TOB) and specific humidity (QOB).
- **plot_diff_hist**: Option to make plots of the observations before and after adding teh random errors.

### combine_csv

Combine two observation CSV files together. Useful when combining conventional and UAS observation CSVs together. Uses `main/combine_bufr_csv.py`.

- **csv_dirs**: List of observation CSV files (use full path).

### select_obs

Only keep certain observation types in an observation CSV file. Useful when performing data-denial experiments (i.e., OSEs). Uses `main/select_obtypes.py`.

- **in_csv_dir**: Which path from the `paths` section to pull observation CSVs from.
- **include_real_red**: Option to also select certain observations from real_red observation CSVs. Synthetic (fake) observation CSVs are always included.
- **ob_types**: PrepBUFR observation types (3-digit numbers) to keep.

### superobs

Create superobs for various BUFR types (i.e., 3-digit numbers). To see all superob options, see the superobbing source code from pyDA_utils [here](https://github.com/ShawnMurdzek-NOAA/pyDA_utils/blob/main/superob_prepbufr.py).

- **in_csv_dir**: Which path from the `paths` section to pull observation CSVs from.
- **map_proj**: Map projection to use for the "grid" superob grouping method.
- **map_proj_kw**: Keywords arguments passed to the map projection.
- **grouping**: Superob grouping strategy.
- **grouping_kw**: Keywords arguments passed to the superob grouping method (`grouping_kw` keyword argument in [pyDA_utils.superob_prepbufr.create_superobs](https://github.com/ShawnMurdzek-NOAA/pyDA_utils/blob/main/superob_prepbufr.py)).
- **reduction_kw**: Keywords arguments passed to the superob reduction method (`reduction_kw` keyword argument in [pyDA_utils.superob_prepbufr.create_superobs](https://github.com/ShawnMurdzek-NOAA/pyDA_utils/blob/main/superob_prepbufr.py)).
- **plot_vprof**: Parameters for creating vertical profile plots of superobs
    - **ob_type_thermo**: 3-digit BUFR type corresponding to the thermodynamic obs (e.g., 136)
    - **ob_type_wind**: 3-digit BUFR type corresponding to the wind obs (e.g., 236)
    - **all_sid**: SIDs to plot

### convert_syn_csv

Converts a synthetic observation CSV file back into a prepBUFR file. Uses the `prepbufr_decoder` program.

### convert_real_red_csv

Converts an observation CSV file with a subset of real observations (in order to match the observations in the synthetic observation CSV file) back into a prepBUFR file. Uses the `prepbufr_decoder` program.

### plots

Creates various plots based on the synthetic observations created. Uses various programs in the `plotting` subdirectory.

- **diff_2d**: Parameters for plots based on 2-D observations (e.g., ADPSFC, MSONET, GPSIPW, etc.)
    - **bufr_dir**: Which path from the `paths` section to pull observation CSVs from for the plots. Directory must contain both `fake` observation CSVs and `real_red` observation CSVs.
    - **subsets**: Observation subsets (e.g., ADPSFC, MSONET, etc.) to create plots for.
    - **obs_vars**: Observation fields (e.g., POB, TOB, etc.) to create plots for.
    - **domain**: Domain over which to take observations from. Options: `all`, `easternUS`, `westernUS`.
    - **ob_type**: Option to only plot certain observation types. To not use, set to `null`. To use, provide a list of observation types.
    - **use_assim_sites**: Option to only include observations that have Analysis_Use_Flag = 1 in the GSI diag files.
    - **gsi_diag_fname**: File (including path) for the GSI diag file used for `use_assim_sites`.
    - **remove_small_sim_wspd**: Option to set wind speeds from the synthetic observation CSV files to 0.
    - **sim_wspd_thres**: Threshold below which wind speeds from the synthetic observation CSVs are set to 0.
    - **only_compare_strong_winds**: Option to only compare winds if the real winds exceed a threshold.
    - **real_wspd_thres**: Real wind threshold below which winds are not compared.
- **diff_3d**: Parameters for plots based on 3-D observations (e.g., ADPUPA, AIRCAR, etc.)
    - **bufr_dir**: Which path from the `paths` section to pull observation CSVs from for the plots. Directory must contain both `fake` observation CSVs and `real_red` observation CSVs.
    - **exclude_sid**: Station IDs (SID) to exclude from the comparison plots.
- **diff_uas**: Parameters for plots based on UAS observations
    - **bufr_dir**: Which path from the `paths` section to pull observation CSVs from for the plots.
    - **nclose**: Controls how many comparisons are made. Comparisons are made between UAS observations and the closest Nature Run gridpoint. Only the UAS observations that are closest to a nearby Nature Run gridpoint are used.
