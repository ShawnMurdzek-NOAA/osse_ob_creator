"""
Create BUFR CSV for UAS Observations

This CSV will be filled with bogus data. Use create_synthetic_obs.py to interpolate actual NR data to
UAS obs locations. Yet another script will be used for superobbing once UAS obs are created.

Optional command-line arguments:
    argv[1] = UAS valid time in YYYYMMDDHHMM format
    argv[2] = Output CSV file name
    argv[3] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
Date Created: 8 May 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import datetime as dt
import numpy as np
import pandas as pd
import sys
import yaml

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# UAS location file
uas_loc_fname = 'uas_site_locs_150km.txt'

# UAS flight start times
flight_times = [dt.datetime(2022, 4, 29, 12) + dt.timedelta(hours=i) for i in range(0, 13, 6)]

# UAS ob valid times (this is the timestamp on the BUFR CSV)
valid_times = [dt.datetime(2022, 4, 29, 12) + dt.timedelta(hours=i) for i in range(0, 13, 6)]

# Elapsed time after the valid time to stop collect UAS obs (s)
max_time = 1500.

# UAS ascent rate (m/s)
ascent_rate = 3.

# UAS sampling frequency (s)
sample_freq = 60.

# UAS maximum height (m)
max_height = 2000.

# Sample BUFR CSV file (needed to determine which fields to include)
sample_bufr_fname = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202202010000.rap.prepbufr.csv'

# Output BUFR CSV file (include %s placeholder for timestamp)
out_fname = '%s.bogus.prepbufr.csv'

# Option to use inputs from YAML file
if len(sys.argv) > 1:
    bufr_t = sys.argv[1]
    out_fname = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    valid_times = [dt.datetime.strptime(bufr_t, '%Y%m%d%H%M')]
    flight_times = [valid_times[0] + dt.timedelta(seconds=param['create_csv']['uas_offset'])]
    uas_loc_fname = param['shared']['uas_grid_file']
    max_time = param['create_csv']['max_time']
    ascent_rate = param['create_csv']['ascent_rate']
    sample_freq = param['create_csv']['sample_freq']
    max_height = param['create_csv']['max_height']
    sample_bufr_fname = param['create_csv']['sample_bufr_fname']


#---------------------------------------------------------------------------------------------------
# Create UAS BUFR CSV
#---------------------------------------------------------------------------------------------------

typ_thermo = 136
typ_wind = 236
subset = 'AIRCAR'
t29 = 11
quality_m = 2

# UAS locations in (x, y) space
uas_locs = pd.read_csv(uas_loc_fname)
nlocs = len(uas_locs)

# UAS sampling heights
uas_z = np.arange(0, max_height, ascent_rate*sample_freq)

# Sample BUFR file
sample_bufr = bufr.bufrCSV(sample_bufr_fname)
all_columns = list(sample_bufr.df.columns)

# Loop over each valid time
for valid, start in zip(valid_times, flight_times):

    # nfobs: Number of obs for a single flight from a single UAS
    # Need factor of 2 for total obs (ntobs) to account for both thermodynamic and kinematic obs
    nfobs = min(int(((valid - start).total_seconds() + max_time) / sample_freq), len(uas_z)) 
    ntobs = 2*nfobs*nlocs

    out_dict = {}
    for col in all_columns:  
        out_dict[col] = np.zeros(ntobs) * np.nan

    out_dict['nmsg'] = np.array([[i]*2*nfobs for i in range(1, nlocs+1)]).ravel()
    out_dict['subset'] = np.array([subset]*ntobs)
    out_dict['cycletime'] = np.array([valid.strftime('%Y%m%d%H')]*ntobs)
    out_dict['ntb'] = np.array(list(range(1, 2*nfobs+1))*nlocs)
    out_dict['SID'] = np.array([["UA%06d" % i]*2*nfobs for i in range(1, nlocs+1)], dtype=str).ravel()
    out_dict['XOB'] = np.array([[i]*2*nfobs for i in uas_locs['lon (deg E)'].values]).ravel() + 360.
    out_dict['YOB'] = np.array([[i]*2*nfobs for i in uas_locs['lat (deg N)'].values]).ravel()
    out_dict['DHR'] = np.array(list(np.arange((valid - start).total_seconds(), 
                                              max_time, sample_freq))[:nfobs]*2*nlocs) / 3600.
    out_dict['TYP'] = np.array(([typ_thermo]*nfobs + [typ_wind]*nfobs)*nlocs)
    out_dict['ELV'] = np.zeros(ntobs)
    out_dict['T29'] = np.array([t29]*ntobs)
    out_dict['POB'] = np.array([0.]*ntobs)
    out_dict['PQM'] = np.array([quality_m]*ntobs)
    out_dict['ZOB'] = np.array(list(uas_z[:nfobs])*2*nlocs)
    out_dict['ZQM'] = np.array([quality_m]*ntobs)
    for v in ['QOB', 'TOB', 'TDO']:
        out_dict[v] = np.array(([0.]*nfobs + [np.nan]*nfobs)*nlocs)
    for qm in ['TQM', 'QQM']:
        out_dict[qm] = np.array(([quality_m]*nfobs + [np.nan]*nfobs)*nlocs)
    for v in['UOB', 'VOB']:
        out_dict[v] = np.array(([np.nan]*nfobs + [0.]*nfobs)*nlocs)
    out_dict['WQM'] = np.array(([np.nan]*nfobs + [quality_m]*nfobs)*nlocs)
    out_dict['CAT'] = np.ones(ntobs)

    out_df = pd.DataFrame(out_dict)
    bufr.df_to_csv(out_df, out_fname % valid.strftime('%Y%m%d%H%M'))


"""
End create_uas_csv.py
"""
