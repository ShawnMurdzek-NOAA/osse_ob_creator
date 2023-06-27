"""
Create BUFR CSV for UAS Observations

This CSV will be filled with bogus data. Use create_conv_obs.py to interpolate actual NR data to
UAS obs locations. Yet another script will be used for superobbing once UAS obs are created.

shawn.s.murdzek@noaa.gov
Date Created: 8 May 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import datetime as dt
import numpy as np
import pandas as pd
import bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# UAS location file
uas_loc_fname = 'uas_site_locs_35km.txt'

# UAS flight start times
#flight_times = [dt.datetime(2022, 4, 29, 12) + dt.timedelta(hours=i) for i in range(0, 168, 6)]
flight_times = [dt.datetime(2022, 4, 29, 12) + dt.timedelta(hours=i) for i in range(0, 13, 6)]

# UAS ob valid times (this is the timestamp on the BUFR CSV)
#valid_times = [dt.datetime(2022, 4, 29, 12) + dt.timedelta(hours=i) for i in range(0, 168, 6)]
valid_times = [dt.datetime(2022, 4, 29, 12) + dt.timedelta(hours=i) for i in range(0, 13, 6)]

# Elapsed time after the valid time to stop collect UAS obs (s)
max_time = 1500.

# UAS ascent rate (m/s)
ascent_rate = 3.

# UAS sampling frequency (s)
sample_freq = 60.

# UAS maximum height (m)
max_height = 2000.

# Output BUFR CSV file (include %s placeholder for timestamp)
out_fname = '%s.uas.bogus.prepbufr.csv'


#---------------------------------------------------------------------------------------------------
# Create UAS BUFR CSV
#---------------------------------------------------------------------------------------------------

typ_thermo = 132
typ_wind = 232
subset = 'ADPUPA'
t29 = 11
quality_m = 2

# UAS locations in (x, y) space
uas_locs = pd.read_csv(uas_loc_fname)
nlocs = len(uas_locs)

# UAS sampling heights
uas_z = np.arange(0, max_height, ascent_rate*sample_freq)

# Loop over each valid time
for valid, start in zip(valid_times, flight_times):
    nfobs = min(int(((valid - start).total_seconds() + max_time) / sample_freq), len(uas_z)) 
    ntobs = 2*nfobs*nlocs

    out_dict = {}
    for col in ['nmsg', 'subset', 'cycletime', 'ntb', 'SID', 'XOB', 'YOB', 'DHR', 'TYP', 'ELV',  
                'SAID', 'T29', 'POB', 'QOB', 'TOB', 'ZOB', 'UOB', 'VOB', 'PWO', 'CAT', 'PRSS', 
                'PQM', 'QQM', 'TQM', 'ZQM', 'WQM', 'NUL', 'PWQ', 'POE', 'QOE', 'TOE', 'NUL.1',
                'WOE', 'NUL.2', 'PWE']:
        out_dict[col] = np.zeros(ntobs) * np.nan

    out_dict['nmsg'] = np.array([[i]*2*nfobs for i in range(1, nlocs+1)]).ravel()
    out_dict['subset'] = np.array([subset]*ntobs)
    out_dict['cycletime'] = np.array([valid.strftime('%Y%m%d%H')]*ntobs)
    out_dict['ntb'] = np.array(list(range(1, 2*nfobs+1))*nlocs)
    out_dict['SID'] = np.array([['D%07d' % i]*2*nfobs for i in range(1, nlocs+1)]).ravel()
    out_dict['XOB'] = np.array([[i]*2*nfobs for i in uas_locs['lon (deg E)'].values]).ravel() + 360.
    out_dict['YOB'] = np.array([[i]*2*nfobs for i in uas_locs['lat (deg N)'].values]).ravel()
    out_dict['DHR'] = np.array(list(np.arange((valid - start).total_seconds(), 
                                              max_time, sample_freq))[:nfobs]*2*nlocs) / 3600.
    out_dict['TYP'] = np.array(([typ_thermo]*nfobs + [typ_wind]*nfobs)*nlocs)
    out_dict['ELV'] = np.zeros(ntobs)
    out_dict['T29'] = np.array([t29]*ntobs)
    out_dict['POB'] = np.array([1000.]*ntobs)
    out_dict['PQM'] = np.array([quality_m]*ntobs)
    out_dict['ZOB'] = np.array(list(uas_z[:nfobs])*2*nlocs)
    out_dict['ZQM'] = np.array([quality_m]*ntobs)
    for v, qm in zip(['QOB', 'TOB'], ['QQM', 'TQM']):
        out_dict[v] = np.array(([300.]*nfobs + [np.nan]*nfobs)*nlocs)
        out_dict[qm] = np.array(([quality_m]*nfobs + [np.nan]*nfobs)*nlocs)
    for v in['UOB', 'VOB']:
        out_dict[v] = np.array(([np.nan]*nfobs + [300.]*nfobs)*nlocs)
    out_dict['WQM'] = np.array(([np.nan]*nfobs + [quality_m]*nfobs)*nlocs)
    out_dict['CAT'] = np.ones(ntobs)

    out_df = pd.DataFrame(out_dict)
    bufr.df_to_csv(out_df, out_fname % valid.strftime('%Y%m%d%H%M'))


"""
End create_uas_csv.py
"""
