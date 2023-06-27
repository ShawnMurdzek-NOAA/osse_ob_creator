"""
Create Perfect UAS Observations

Observations errors and superobbing are performed in separate scripts.

shawn.s.murdzek@noaa.gov
Date Created: 9 May 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import datetime as dt
import numpy as np
import pandas as pd
import xarray as xr
import sys
import math
import metpy.constants as const
import metpy.calc as mc
from metpy.units import units

import create_ob_utils as cou
import bufr
import map_proj as mp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# UAS location file
uas_loc_fname = 'uas_site_locs_TEST.txt'

# Directory containing wrfnat output from UPP and time between UPP output files (min)
wrf_dir = '/work2/noaa/wrfruc/murdzek/nature_run_spring/UPP/'
wrf_step = 15.

# UAS flight start times
flight_time = dt.datetime(2022, 4, 29, 12)

# UAS ob valid times (this is the timestamp on the BUFR CSV)
valid_time = dt.datetime(2022, 4, 29, 12)

# Elapsed time after the valid time to stop collect UAS obs (s)
max_time = 1500.

# UAS ascent rate (m/s)
ascent_rate = 50.

# UAS sampling frequency (s)
sample_freq = 1.

# UAS maximum height (m)
max_height = 2000.

# Output BUFR CSV file
out_fname = ('/work2/noaa/wrfruc/murdzek/nature_run_spring/synthetic_obs_csv/perfect_uas/%s.uas.prepbufr.csv' % 
             valid_time.strftime('%Y%m%d%H%M'))
out_fname = 'test.uas.prepbufr.csv'


#---------------------------------------------------------------------------------------------------
# Create UAS BUFR CSV
#---------------------------------------------------------------------------------------------------

program_start = dt.datetime.now()
print('PROGRAM START (time = %s)' % program_start.strftime('%Y%m%d %H:%M:%S'))

typ_thermo = 132
typ_wind = 232
subset = 'ADPUPA'
t29 = 11
quality_m = 2

# UAS locations in (x, y) space
uas_locs = pd.read_csv(uas_loc_fname)
nlocs = len(uas_locs)

# UAS sampling heights
uas_z = np.arange(10, max_height, ascent_rate*sample_freq)

nfobs = min(int(((valid_time - flight_time).total_seconds() + max_time) / sample_freq), len(uas_z)) 
ntobs = 2*nfobs*nlocs

# Create output BUFR CSV DataFrame
print('creating empty DataFrame (nfobs = %d, nlocs = %d, ntobs = %d)' % (nfobs, nlocs, ntobs))
out_dict = {}
for col in ['nmsg', 'subset', 'cycletime', 'ntb', 'SID', 'XOB', 'YOB', 'DHR', 'TYP', 'ELV',  
            'SAID', 'T29', 'POB', 'QOB', 'TOB', 'ZOB', 'UOB', 'VOB', 'PWO', 'CAT', 'PRSS', 
            'PQM', 'QQM', 'TQM', 'ZQM', 'WQM', 'NUL', 'PWQ', 'POE', 'QOE', 'TOE', 'NUL.1',
            'WOE', 'NUL.2', 'PWE']:
    out_dict[col] = np.zeros(ntobs) * np.nan

out_dict['nmsg'] = np.array([[i]*2*nfobs for i in range(1, nlocs+1)]).ravel()
out_dict['subset'] = np.array([subset]*ntobs)
out_dict['cycletime'] = np.array([valid_time.strftime('%Y%m%d%H')]*ntobs)
out_dict['ntb'] = np.array(list(range(1, 2*nfobs+1))*nlocs)
out_dict['SID'] = np.array([['D%07d' % i]*2*nfobs for i in range(1, nlocs+1)]).ravel()
out_dict['XOB'] = np.array([[i]*2*nfobs for i in uas_locs['lon (deg E)'].values]).ravel() + 360.
out_dict['YOB'] = np.array([[i]*2*nfobs for i in uas_locs['lat (deg N)'].values]).ravel()
out_dict['DHR'] = np.array(list(np.arange((valid_time - flight_time).total_seconds(), 
                                          max_time, sample_freq))[:nfobs]*2*nlocs) / 3600. 
out_dict['TYP'] = np.array(([typ_thermo]*nfobs + [typ_wind]*nfobs)*nlocs)
out_dict['ELV'] = np.zeros(ntobs)
out_dict['T29'] = np.array([t29]*ntobs)
out_dict['POB'] = np.array([0.]*ntobs)
out_dict['PQM'] = np.array([quality_m]*ntobs)
out_dict['ZOB'] = np.array(list(uas_z[:nfobs])*2*nlocs)
out_dict['ZQM'] = np.array([quality_m]*ntobs)
for v, qm in zip(['QOB', 'TOB'], ['QQM', 'TQM']):
    out_dict[v] = np.array(([0.]*nfobs + [np.nan]*nfobs)*nlocs)
    out_dict[qm] = np.array(([quality_m]*nfobs + [np.nan]*nfobs)*nlocs)
for v in['UOB', 'VOB']:
    out_dict[v] = np.array(([np.nan]*nfobs + [0.]*nfobs)*nlocs)
out_dict['WQM'] = np.array(([np.nan]*nfobs + [quality_m]*nfobs)*nlocs)
out_dict['CAT'] = np.ones(ntobs)

out_df = pd.DataFrame(out_dict)

# Determine necessary UPP files to open
upp_starttime = flight_time
upp_starttime.replace(minute=math.floor(flight_time.minute / wrf_step), second=0)
uas_endtime = valid_time + dt.timedelta(hours=out_dict['DHR'].max())
upp_endtime = uas_endtime
upp_end_min = math.ceil(uas_endtime.minute / wrf_step)
if upp_end_min < 60:
    upp_endtime.replace(minute=upp_end_min, second=0)
else:
    upp_endtime.replace(hour=uas_endtime.hour+1, minute=0, second=0)
wrf_step_dec = wrf_step / 60.

# Open UPP files
print('opening UPP files & extracting 2D fields')
wrf_ds = {}
wrf_data = {}
wrf_hr = []
time = upp_starttime
while time < (upp_endtime + dt.timedelta(minutes=wrf_step)):
    wrf_hr.append((time - valid_time).total_seconds() / 3600.)
    wrf_ds[wrf_hr[-1]] = xr.open_dataset('%s/%s' % (wrf_dir, time.strftime('%Y%m%d/wrfnat_%Y%m%d%H%M.grib2')), 
                                         engine='pynio')
    wrf_data[wrf_hr[-1]] = {}
    for v in ['HGT_P0_L1_GLC0']:
        if v == 'HGT_P0_L1_GLC0':
            wrf_data[wrf_hr[-1]][v] = mc.geopotential_to_height(wrf_ds[wrf_hr[-1]][v].values * units.m * const.g).to('m').magnitude
        else:
            wrf_data[wrf_hr[-1]][v] = wrf_ds[wrf_hr[-1]][v][:, :].values
    time = time + dt.timedelta(minutes=wrf_step)

shape = wrf_ds[wrf_hr[0]]['HGT_P0_L105_GLC0'].shape
imax = shape[1] - 2
jmax = shape[2] - 2

# Compute (x, y) coordinates of obs using a Lambert Conformal projection
print('Performing map projection with obs...')
out_df['xlc'], out_df['ylc'] = mp.ll_to_xy_lc(out_df['YOB'], out_df['XOB'] - 360.)
out_df['i0'] = np.int32(np.floor(out_df['ylc']))
out_df['j0'] = np.int32(np.floor(out_df['xlc']))

# Remove obs outside of the wrfnat domain
out_df.drop(index=np.where(np.logical_or(out_df['i0'] < 0, out_df['i0'] > imax))[0], inplace=True)
out_df.reset_index(drop=True, inplace=True)
out_df.drop(index=np.where(np.logical_or(out_df['j0'] < 0, out_df['j0'] > jmax))[0], inplace=True)
out_df.reset_index(drop=True, inplace=True)

# Compute interpolation weights
out_df['iwgt'] = 1. - (out_df['ylc'] - out_df['i0'])
out_df['jwgt'] = 1. - (out_df['xlc'] - out_df['j0'])

# Add some DataFrame columns
nrow = len(out_df)
extra_col_int = ['zi0']
extra_col_float = ['twgt', 'zwgt']
for c in extra_col_int:
    out_df[c] = np.zeros(nrow, dtype=int)
for c in extra_col_float:
    out_df[c] = np.zeros(nrow, dtype=float)
extra_col_int = extra_col_int + ['i0', 'j0']
extra_col_float = extra_col_float + ['xlc', 'ylc', 'iwgt', 'jwgt']

# Perform 3D interpolation
obs_name = ['ZOB', 'POB', 'TOB', 'QOB', 'UOB', 'VOB']
wrf_name = ['HGT_P0_L105_GLC0', 'PRES_P0_L105_GLC0', 'TMP_P0_L105_GLC0', 
            'SPFH_P0_L105_GLC0', 'UGRD_P0_L105_GLC0', 'VGRD_P0_L105_GLC0']

z1d = np.zeros([100, len(out_df)])
zdone = np.zeros(len(out_df), dtype=int)
drop_idx = []

for o, f in zip(obs_name, wrf_name):

    print()
    print('WRF field = %s' % f)

    # Loop over each WRF time
    for hr in wrf_hr:

        # Determine indices of obs within wrf_step of this output time
        ind = np.where(np.logical_and(out_df['DHR'] > (hr - wrf_step_dec),
                                      out_df['DHR'] < (hr + wrf_step_dec)))[0]

        # If no indices, move to next time
        if ind.size == 0:
            continue

        print('hour = %.3f (nobs = %d)' % (hr, len(ind)))

        # Extract field from UPP
        wrf3d = wrf_ds[hr][f][:, :, :].values

        # Convert from geopotential to geometric height
        if o == 'ZOB':
            wrf3d = mc.geopotential_to_height(wrf3d * units.m * const.g).to('m').magnitude

        print('Done extracting field')

        # Loop over each UAS observation within this time interval
        for j in ind:

            if o == 'ZOB':

                # First half of height calculation (Z1)
                if np.isclose(z1d[0, j], 0.):

                    # Determine weight for temporal interpolation
                    ihr, twgt = cou.determine_twgt(wrf_hr, out_df.loc[j, 'DHR'])
                    out_df.loc[j, 'twgt']  = twgt

                    # Determine surface height above sea level
                    sfch = mc.geopotential_to_height(cou.interp_x_y_t(wrf_data, wrf_hr, 
                                                                      'HGT_P0_L1_GLC0', 
                                                                      out_df.loc[j],
                                                                      ihr, twgt) * units.m * const.g).to('m').magnitude

                    out_df.loc[j, 'ELV'] = sfch
                    out_df.loc[j, 'ZOB'] = out_df.loc[j, 'ZOB'] + sfch

                    # The calculation below only gives use part of the z1d array. The rest of this 
                    # of this array will be determined when we loop over the other 3D
                    # height array
                    z1d[:, j] = twgt * cou.interp_x_y(wrf3d, out_df.loc[j], threeD=True)

                    # Special case: twgt = 1. In this case, we don't need to interpolate in time, so 
                    # we can skip the Z2 section of the conditional
                    if np.isclose(twgt, 1):
                        zdone[j] = 1

                # Second half of height calculation (Z2)
                else:
                    z1d[:, j] = z1d[:, j] + ((1.-out_df.loc[j, 'twgt']) *
                                             cou.interp_x_y(wrf3d, out_df.loc[j], threeD=True))
                    zdone[j] = 1

                if zdone[j]:
                    # Check for extrapolation
                    if (z1d[0, j] < out_df.loc[j, 'ZOB']):
                        out_df.loc[j, 'zi0'] = np.where(z1d[:, j] < out_df.loc[j, 'ZOB'])[0][-1]
                        if out_df.loc[j, 'zi0'] >= (z1d.shape[0] - 1):
                            # Prevent extrapolation in vertical
                            drop_idx.append(j)
                            continue
                        out_df.loc[j, 'ZOB'], out_df.loc[j, 'zwgt'] = cou.interp_wrf_1d(z1d[:, j], out_df.loc[j], i0_name='zi0',
                                                                                        var='ZOB', itype='linear')
                    else:
                        drop_idx.append(j)
                        continue

            # Perform interpolation for other variables (not height)
            else:

                if (not np.isnan(out_df.loc[j, o]) and (j not in drop_idx)):
                    twgt =  out_df.loc[j, 'twgt']
                    if np.isclose(out_df.loc[j, o], 0):
                        out_df.loc[j, o] = twgt * cou.interp_x_y_z(wrf3d, out_df.loc[j], 
                                                                   wgt_name='zwgt', i0_name='zi0')
                    else:
                        out_df.loc[j, o] = ((1.-twgt) * cou.interp_x_y_z(wrf3d, out_df.loc[j], 
                                                                         wgt_name='zwgt', i0_name='zi0') +
                                            out_df.loc[j, o])

        # Free up memory (shouldn't have to call garbage collector after this)
        wrf3d = 0.

# Drop the extra columns we added
debug_df = out_df.copy()
out_df.drop(labels=extra_col_int, axis=1, inplace=True)
out_df.drop(labels=extra_col_float, axis=1, inplace=True)
out_df.drop(index=drop_idx, inplace=True)
out_df.reset_index(drop=True, inplace=True)
debug_df.drop(index=drop_idx, inplace=True)
debug_df.reset_index(drop=True, inplace=True)

# Convert to proper units
out_df['POB'] = out_df['POB'] * 1e-2
out_df['QOB'] = out_df['QOB'] * 1e6
out_df['TOB'] = out_df['TOB'] - 273.15
out_df['ELV'] = np.int64(out_df['ELV'])

bufr.df_to_csv(out_df, out_fname)

print('elapsed time = %.1f s' % (dt.datetime.now() - program_start).total_seconds())


"""
End create_uas_obs.py
"""
