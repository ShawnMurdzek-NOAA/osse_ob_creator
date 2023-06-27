"""
Create Perfect Simulated Conventional Observations from WRF Nature Run Output

Conventional obs are written into a new CSV file. Instrument errors and other obs (e.g.,  UAS) can 
then be added later. Conventional observations include the following: ADPSFC, SFCSHP, MSONET, 
GPSIPW, ADPUPA, AIRCAR, AIRCFT. Radiosonde drift is NOT accounted for in this program. Use
create_adpupa_obs.py to create realistic radiosonde obs with drift included. Obs in this script
are created used pure interpolation (linear in x, y, and t and logaritmic in p).

To Do:
1. Better handle unit conversions (e.g., the POB conversion from Pa to hPa is hard coded)

Prepbufr CSV files for real observations can be created using GSI-utils/bin/prepbufr_decode_csv.x.
To use this utility, do the following:

1. Copy the prepbufr file you wish to decode to GSI-utils/bin and rename it 'prepbufr'
2. Run ./prepbufr_decode_csv.x
3. Move resulting CSV file to wherever you choose

Passed Arguments:
    argv[1] = Directory containing WRF UPP output
    argv[2] = Directory containing real prepBUFR CSV files
    argv[3] = Output directory for simulated prepBUFR CSV files
    argv[4] = Time of prepbufr file (YYYYMMDDHH)
    argv[5] = Time for first UPP file (YYYYMMDDHH)
    argv[6] = Time for last UPP file (YYYYMMDDHH)
    argv[7] = Prepbufr file tag
    argv[8] = Prepbufr file suffix

shawn.s.murdzek@noaa.gov
Date Created: 22 November 2022
Environment: adb_graphics (Jet) or pygraf (Hera, Orion, Hercules)
RAM Required: 25 GB
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import xarray as xr
import numpy as np
import datetime as dt
import math
import os
import sys
import metpy.constants as const
import metpy.calc as mc
from metpy.units import units

import create_ob_utils as cou 
import bufr
import map_proj as mp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Directory containing wrfnat output from UPP
wrf_dir = '/work2/noaa/wrfruc/murdzek/nature_run_spring/UPP/'

# Directory containing real prepbufr CSV output
#bufr_dir = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/'
bufr_dir = './'

# Observation platforms to use (aka subsets, same ones used by BUFR)
obs_2d = ['ADPSFC', 'SFCSHP', 'MSONET', 'GPSIPW']
obs_3d = ['ADPUPA', 'AIRCAR', 'AIRCFT', 'RASSDA', 'PROFLR', 'VADWND']

# Variable to use for vertical interpolation for obs_3d platforms and type of interpolation 
# ('log' or 'linear'). Conversion is a factor applied to the model field to convert to the correct
# units. Ascend denotes whether the vertical coordinate increases or decreases with height.
vinterp = [{'subset':['ADPUPA', 'AIRCAR', 'AIRCFT'], 'var':'POB', 'type':'log', 
            'model_field':'PRES_P0_L105_GLC0', 'conversion':1e-2, 'ascend':False},
           {'subset':['RASSDA', 'PROFLR', 'VADWND'], 'var':'ZOB', 'type':'linear',
            'model_field':'HGT_P0_L105_GLC0', 'conversion':1, 'ascend':True}]

# Output directory for synthetic prepbufr CSV output
#fake_bufr_dir = '/work2/noaa/wrfruc/murdzek/nature_run_spring/sfc_stat_obs_csv/conv/'
fake_bufr_dir = './'

# PrepBUFR time
bufr_time = dt.datetime(2022, 4, 30, 0)

# Prepbufr tag ('rap', 'rap_e', or 'rap_p')
bufr_tag = 'sample'

# Prepbufr suffix
bufr_suffix = ''

# Start and end times for wrfnat UPP output. Step is in min
wrf_start = dt.datetime(2022, 4, 29, 21, 0)
wrf_end = dt.datetime(2022, 4, 30, 1, 0)
wrf_step = 15

# Option to set all entries for a certain BUFR field to NaN
nan_fields = ['MXGS', 'HOVI', 'MSST', 'DBSS', 'SST1', 'SSTQM', 'SSTOE', 'CDTP', 'GCDTT', 'CDTP_QM',
              'HOWV', 'CEILING', 'QIFN', 'TOCC', 'HLBCS', 'VSSO', 'CLAM', 'HOCB', 'PRWE', 'TFC', 
              'UFC', 'VFC', 'MXTM', 'MITM']

# Option to interpolate height obs (ZOB) for AIRCAR and AIRCFT platforms
# Heights reported by aircraft are calculated by integrating the hydrostatic balance eqn assuming
# the US Standard Atmosphere. Therefore, the heights for the simulated obs should be the same as the
# real obs b/c the pressures are the same.
interp_z_aircft = False

# Option to use (XDR, YDR) for ADPUPA obs rather than (XOB, YOB)
use_raob_drift = True

# Option to "correct" obs that occur near coastlines
coastline_correct = False 

# Option to use virtual temperature when tvflg = 0
use_Tv = False

# Option to add ceiling observations to surface-based platforms (ADPSFC, SFCSHP, MSONET)
add_ceiling = False
ceil_field = 'HGT_P0_L215_GLC0'
#ceil_field = 'CEIL_P0_L215_GLC0'  # Experimental ceiling diagnostic #1

# Option for debugging output (0 = none, 1 = some, 2 = a lot)
debug = 2

# Option to interpolate (lat, lon) coordinates for surface obs (ADPSFC, SFCSHP, MSONET)
# Helpful for debugging, but should usually be set to False b/c it increases runtime
interp_latlon = False

# Variables to interpolate along with their associated WRF fields
vars_2d = {'POB':'PRES_P0_L1_GLC0',   'ZOB':'HGT_P0_L1_GLC0',    'TOB':'TMP_P0_L103_GLC0', 
           'QOB':'SPFH_P0_L103_GLC0', 'PWO':'PWAT_P0_L200_GLC0', 'PMO':'PRMSL_P0_L101_GLC0'}
vars_2d_3d = {'UOB':'UGRD_P0_L103_GLC0', 'VOB':'VGRD_P0_L103_GLC0'}
vars_3d = {'POB':'PRES_P0_L105_GLC0', 'ZOB':'HGT_P0_L105_GLC0',  'TOB':'TMP_P0_L105_GLC0', 
           'QOB':'SPFH_P0_L105_GLC0', 'UOB':'UGRD_P0_L105_GLC0', 'VOB':'VGRD_P0_L105_GLC0'}

# Use passed arguments, if they exist
if len(sys.argv) > 1:
    wrf_dir = sys.argv[1]
    bufr_dir = sys.argv[2]
    fake_bufr_dir = sys.argv[3]
    bufr_time = dt.datetime.strptime(sys.argv[4], '%Y%m%d%H')
    wrf_start = dt.datetime.strptime(sys.argv[5], '%Y%m%d%H')
    wrf_end = dt.datetime.strptime(sys.argv[6], '%Y%m%d%H')
    bufr_tag = sys.argv[7]
    debug = 0 


#---------------------------------------------------------------------------------------------------
# Preprocessing
#---------------------------------------------------------------------------------------------------

# Timing
begin = dt.datetime.now()
print()
print('BEGINNING SYNTHETIC OB CREATION PROGRAM')
print('start time = %s' % begin.strftime('%Y-%m-%d %H:%M:%S'))
print()

# List to save time spent on each BUFR entry
if debug > 1:
    entry_times2d = []
    entry_timesv1 = []
    entry_timesv2 = []
    entry_times3d = []

# Convert wrf_step to decimal hours for ease of use
wrf_step_dec = wrf_step / 60.

ob_platforms = obs_2d + obs_3d

# Open BUFR file
bufr_fname = '%s/%s.%s.prepbufr.csv' % (bufr_dir, bufr_time.strftime('%Y%m%d%H%M'), bufr_tag)
bufr_csv = bufr.bufrCSV(bufr_fname)

# Only keep platforms if we are creating synthetic obs for them
obs = bufr_csv.df['subset'].unique()
if debug > 0:
    print('total # of BUFR entries = %d' % len(bufr_csv.df))
    print('available BUFR obs =', obs)
for s in obs:
    if s not in ob_platforms:
        bufr_csv.df.drop(index=np.where(bufr_csv.df['subset'] == s)[0], inplace=True)
        bufr_csv.df.reset_index(drop=True, inplace=True)
print('BUFR ob subsets =', bufr_csv.df['subset'].unique())

# Remove obs outside of the range of wrfnat files
hr_min = ((wrf_start - bufr_time).days * 24) + ((wrf_start - bufr_time).seconds / 3600.)
hr_max = ((wrf_end - bufr_time).days * 24) + ((wrf_end - bufr_time).seconds / 3600.)
bufr_csv.df.drop(index=np.where(np.logical_or(bufr_csv.df['DHR'] < hr_min, 
                                              bufr_csv.df['DHR'] > hr_max))[0], inplace=True)
bufr_csv.df.reset_index(drop=True, inplace=True)
if use_raob_drift:
    if not np.all(np.isnan(bufr_csv.df['HRDR'])):
        bufr_csv.df.drop(index=np.where(np.logical_or(bufr_csv.df['HRDR'] < hr_min, 
                                                      bufr_csv.df['HRDR'] > hr_max))[0], inplace=True)
        bufr_csv.df.reset_index(drop=True, inplace=True)

# Open wrfnat files
start_grib = dt.datetime.now()
hr_start = math.floor(bufr_csv.df['DHR'].min()*4) / 4
hr_end = math.ceil(bufr_csv.df['DHR'].max()*4) / 4 + (2*wrf_step_dec)
if use_raob_drift:
    if not np.all(np.isnan(bufr_csv.df['HRDR'])):
        hr_start = min([hr_start, math.floor(bufr_csv.df['HRDR'].min()*4) / 4])
        hr_end = max([hr_end, math.ceil(bufr_csv.df['HRDR'].max()*4) / 4 + (2*wrf_step_dec)])
print('min/max WRF hours = %.2f, %.2f' % (hr_min, hr_max))
print('min/max BUFR DHR = %.2f, %.2f' % (bufr_csv.df['DHR'].min(), bufr_csv.df['DHR'].max()))
print('min/max BUFR HRDR = %.2f, %.2f' % (bufr_csv.df['HRDR'].min(), bufr_csv.df['HRDR'].max()))
wrf_ds = {}
wrf_hr = np.arange(hr_start, hr_end, wrf_step_dec)
for hr in wrf_hr:
    wrf_t = bufr_time + dt.timedelta(hours=hr)
    print(wrf_dir + wrf_t.strftime('/%Y%m%d/wrfnat_%Y%m%d%H%M.grib2'))
    wrf_ds[hr] = xr.open_dataset(wrf_dir + wrf_t.strftime('/%Y%m%d/wrfnat_%Y%m%d%H%M.grib2'), 
                                 engine='pynio')

print('time to open GRIB files = %.2f s' % (dt.datetime.now() - start_grib).total_seconds())
    
# Extract size of latitude and longitude grids
shape = wrf_ds[list(wrf_ds.keys())[0]]['gridlat_0'].shape
imax = shape[0] - 2
jmax = shape[1] - 2
    
# Compute (x, y) coordinates of obs using a Lambert Conformal projection (assume model dx = model dy)
# Remove obs outside of the wrfnat domain
if debug > 0:
    start_map_proj = dt.datetime.now()
    print('Performing map projection with obs...')

model_dx = wrf_ds[wrf_hr[0]]['gridlat_0'].attrs['Dx'][0]
model_nz = len(wrf_ds[wrf_hr[0]]['lv_HYBL0'])
bufr_csv.df['xlc'], bufr_csv.df['ylc'] = mp.ll_to_xy_lc(bufr_csv.df['YOB'], bufr_csv.df['XOB'] - 360.,
                                                        dx=model_dx)
bufr_csv.df['i0'] = np.int32(np.floor(bufr_csv.df['ylc']))
bufr_csv.df['j0'] = np.int32(np.floor(bufr_csv.df['xlc']))

bufr_csv.df.drop(index=np.where(np.logical_or(bufr_csv.df['i0'] < 0, 
                                              bufr_csv.df['i0'] > imax))[0], inplace=True)
bufr_csv.df.reset_index(drop=True, inplace=True)
bufr_csv.df.drop(index=np.where(np.logical_or(bufr_csv.df['j0'] < 0, 
                                              bufr_csv.df['j0'] > jmax))[0], inplace=True)
bufr_csv.df.reset_index(drop=True, inplace=True)

# Compute interpolation weights
bufr_csv.df['iwgt'] = 1. - (bufr_csv.df['ylc'] - bufr_csv.df['i0'])
bufr_csv.df['jwgt'] = 1. - (bufr_csv.df['xlc'] - bufr_csv.df['j0'])

# Determine nearest neighbor for cloud ceiling
if add_ceiling:
    bufr_csv.df['inear'] = np.int32(np.around(bufr_csv.df['ylc']))
    bufr_csv.df['jnear'] = np.int32(np.around(bufr_csv.df['xlc']))

if debug > 0:
    print('Finished with map projection and computing horiz interp weights (time = %.3f s)' % 
          (dt.datetime.now() - start_map_proj).total_seconds())
    print('# BUFR entries remaining = %d' % len(bufr_csv.df))

# Round time offsets to 6 decimal places to eliminate machine error
# (this helps avoid some rare bugs in upper-air obs that leads to all obs being 0)
bufr_csv.df['DHR'] = np.around(bufr_csv.df['DHR'], 6)

# Create output DataFrame
out_df = bufr_csv.df.copy()
drop_idx = []

# Determine row indices for each ob type
ob_idx = {}
ob_idx['2d'] = []
ob_idx['3d'] = []
for o in ob_platforms:
    ob_idx[o] = list(np.where(out_df['subset'] == o)[0]) 
for o in obs_2d:
    ob_idx['2d'] = ob_idx['2d'] + ob_idx[o]
for o in obs_3d:
    ob_idx['3d'] = ob_idx['3d'] + ob_idx[o]

# Label each 3D ob with the appropriate group number for vertical interpolation
out_df['vgroup'] = -1 * np.ones(len(out_df), dtype=int)
for j, vinterp_d in enumerate(vinterp):
    for o in vinterp_d['subset']:
        if o in ob_idx.keys():
            out_df.loc[ob_idx[o], 'vgroup'] = j

# Initialize variables (other than vertical coordinate) for 3D obs as 1e9 (note that this is 
# different from NaN, which is used for missing values)
for i, vinterp_d in enumerate(vinterp):
    tmp_obs = list(vars_3d.keys())
    tmp_obs.remove(vinterp_d['var'])
    for v in tmp_obs:
        rows = np.intersect1d(np.where(out_df['vgroup'] == i), np.where(np.logical_not(np.isnan(out_df[v]))))
        out_df.loc[rows, v] = 1e9

# Set all ZOB values to NaN if we don't wish to interpolate ZOBs for AIRCAR and AIRCFT
if not interp_z_aircft:
    if 'AIRCAR' in ob_idx.keys():
        out_df.loc[ob_idx['AIRCAR'], 'ZOB'] = np.nan
    if 'AIRCFT' in ob_idx.keys():
        out_df.loc[ob_idx['AIRCFT'], 'ZOB'] = np.nan

# Use (XDR, YDR) for ADPUPA obs rather than (XOB, YOB)
if use_raob_drift:
    if 'ADPUPA' in ob_idx.keys():
        out_df.loc[ob_idx['ADPUPA'], 'XOB'] = out_df.loc[ob_idx['ADPUPA'], 'XDR']
        out_df.loc[ob_idx['ADPUPA'], 'YOB'] = out_df.loc[ob_idx['ADPUPA'], 'YDR']
        out_df.loc[ob_idx['ADPUPA'], 'DHR'] = out_df.loc[ob_idx['ADPUPA'], 'HRDR']

# Add some DataFrame columns
nrow = len(out_df)
extra_col_int = ['ki0']
extra_col_float = ['twgt', 'kwgt']
for c in extra_col_int:
    out_df[c] = np.zeros(nrow, dtype=int)
for c in extra_col_float:
    out_df[c] = np.zeros(nrow, dtype=float)
extra_col_int = extra_col_int + ['i0', 'j0', 'vgroup']
extra_col_float = extra_col_float + ['xlc', 'ylc', 'iwgt', 'jwgt']

if add_ceiling:
    extra_col_int = extra_col_int + ['inear', 'jnear']
    out_df['ceil'] = np.zeros(nrow) * np.nan


#---------------------------------------------------------------------------------------------------
# Create Obs Based on 2-D Fields
#---------------------------------------------------------------------------------------------------

print()
print('---------------')
print('2D Observations')
print('number of entries = %d' % len(ob_idx['2d']))
print('---------------')
print()

start2d = dt.datetime.now()

# Extract 2D fields ONLY
wrf_fields_2d = [vars_2d[k] for k in vars_2d.keys()]
wrf_fields_2d_3d = [vars_2d_3d[k] for k in vars_2d_3d.keys()]
if coastline_correct:
    wrf_fields_2d = wrf_fields_2d + ['LAND_P0_L1_GLC0']
if interp_latlon:
    wrf_fields_2d = wrf_fields_2d + ['gridlat_0', 'gridlon_0']
if add_ceiling:
    wrf_fields_2d = wrf_fields_2d + [ceil_field]
wrf_data = {}
for hr in wrf_hr:
    wrf_data[hr] = {}
    for f in wrf_fields_2d:
        wrf_data[hr][f] = wrf_ds[hr][f][:, :].values
    for f in wrf_fields_2d_3d:
        wrf_data[hr][f] = wrf_ds[hr][f][0, :, :].values

# Loop over each 2D observation
for j in ob_idx['2d']:
        
    if debug > 1:
        time_jstart = dt.datetime.now()
        print()

    # Determine WRF hour right before observation and weight for temporal interpolation
    ihr, twgt = cou.determine_twgt(wrf_hr, out_df.loc[j, 'DHR'])

    # Option to use only land gridpoints for land stations and only water gridpoints for 
    # marine stations
    if coastline_correct:
        i0 = out_df.loc[j, 'i0']
        j0 = out_df.loc[j, 'j0']
        hr = wrf_hr[ihr]
        f = 'LAND_P0_L1_GLC0'
        tmp_mask = np.array([wrf_data[hr][f][i0, j0], wrf_data[hr][f][i0, j0+1],
                             wrf_data[hr][f][i0+1, j0], wrf_data[hr][f][i0+1, j0+1]])
        print('number of nearby land gridpoints = %d' % tmp_mask.sum())
        if out_df.loc[j, 'subset'] in ['ADPSFC', 'MSONET']:
            landmask = tmp_mask
        elif out_df.loc[j, 'subset'] in ['SFCSHP']:
            landmask = np.float64(np.logical_not(tmp_mask))
        else:
            landmask = np.ones(4)
    else:
        landmask = np.ones(4)

    # Determine surface height above sea level and surface pressure
    sfch = cou.interp_x_y_t(wrf_data, wrf_hr, vars_2d['ZOB'], out_df.loc[j], ihr, twgt,
                            mask=landmask)
    sfcp = cou.interp_x_y_t(wrf_data, wrf_hr, vars_2d['POB'], out_df.loc[j], ihr, twgt,
                            mask=landmask) * 1e-2

    if debug > 1:
        time_sfc = dt.datetime.now()
        print('2D field: SID = %s, subset = %s, TYP = %d' % 
              (out_df.loc[j, 'SID'], out_df.loc[j, 'subset'], out_df.loc[j, 'TYP']))
        print('done determining twgt, sfch, and sfcp (%.6f s)' % 
              (time_sfc - time_jstart).total_seconds())
        print('twgt = %.3f, i0 = %d, j0 = %d' % 
              (twgt, out_df.loc[j, 'i0'], out_df.loc[j, 'j0']))
        print('DHR = %.3f, XOB = %.6f, YOB = %.6f' % 
              (out_df.loc[j, 'DHR'], out_df.loc[j, 'XOB'], out_df.loc[j, 'YOB']))
        print('sfch = %.6f, sfcp = %.6f' % (sfch, sfcp))
             
    # Surface obs only: Reset surface values to match NR and assign surface pressure values
    if out_df.loc[j, 'subset'] in ['ADPSFC', 'SFCSHP', 'MSONET']:
        for o, v in zip(['ZOB', 'ELV', 'POB', 'PRSS'], [sfch, sfch, sfcp, sfcp]):
            if not np.isnan(out_df.loc[j, o]):
                out_df.loc[j, o] = v

    # Interpolate temporally
    obs_name = []
    wrf_name = []
    for d in [vars_2d, vars_2d_3d]:
        for o in d.keys():
            if o not in ['ZOB', 'ELV', 'POB', 'PRSS']:
                obs_name.append(o)
                wrf_name.append(d[o])
    if interp_latlon:
        obs_name = obs_name + ['XOB', 'YOB']
        wrf_name = wrf_name + ['gridlon_0', 'gridlat_0']
    for o, m in zip(obs_name, wrf_name):
        if not np.isnan(out_df.loc[j, o]):
            if debug > 1:
                time_before_interp = dt.datetime.now()
            out_df.loc[j, o] = cou.interp_x_y_t(wrf_data, wrf_hr, m, out_df.loc[j], ihr, twgt,
                                                mask=landmask)
            if debug > 1:
                time_after_interp = dt.datetime.now()
                print('finished interp for %s (%.6f s)' % 
                      (o, (time_after_interp - time_before_interp).total_seconds()))
                entry_times2d.append((dt.datetime.now() - time_jstart).total_seconds())

    # Option to include cloud ceiling (interpolation is nearest neighbor)
    if add_ceiling and (out_df.loc[j, 'subset'] in ['ADPSFC', 'MSONET', 'SFCSHP']):
         inear = out_df.loc[j, 'inear']
         jnear = out_df.loc[j, 'jnear']
         HRnear = wrf_hr[np.argmin(np.abs(wrf_hr - out_df.loc[j, 'DHR']))]
         out_df.loc[j, 'ceil'] = wrf_data[HRnear][ceil_field][inear, jnear]

ndrop2d = len(drop_idx)
print()
print('Done with 2D Obs')
print('number of dropped obs = %d' % ndrop2d)
print('time = %s s' % (dt.datetime.now() - start2d).total_seconds())
print()


#---------------------------------------------------------------------------------------------------
# Create Obs Based on 3-D Fields
#---------------------------------------------------------------------------------------------------

print()
print('---------------')
print('3D Observations')
print('number of entries = %d' % len(ob_idx['3d']))
print('---------------')
print()

start3d = dt.datetime.now()

# Create array to save v1d arrays (vertical coordinate)
v1d = np.ones([model_nz, len(out_df)]) * 1e9
vdone = np.zeros(len(out_df), dtype=int)

# We will extract 3D fields one at a time b/c these 3D arrays are massive (~6.5 GB each), so it 
# is not feasible to load all of them at once. Ideally, only 1 should be loaded at any given
# time. Therefore, unlike the 2D obs, we will loop over each obs time interval and each WRF
# field.

# Another approach that could have been taken here is to lazily load each 3D field using Xarray
# datasets. While this would address the memory issues, it would create computational issues b/c
# the dataset will have to be queried for each BUFR entry and each variable, which is time 
# consuming. Tests comparing the use of Xarray datasets to regular Numpy arrays show that the
# Numpy array approach is ~23x faster.

# Loop over each vertical coordinate first to get weights for vertical interpolation
for vg, vinterp_d in enumerate(vinterp):
    for hr in wrf_hr: 

        # Determine indices of obs within wrf_step of this output time
        ind = np.where((out_df['DHR'] > (hr - wrf_step_dec)) & 
                       (out_df['DHR'] < (hr + wrf_step_dec)) &
                       (out_df['vgroup'] == vg))[0]

        # If no indices, move to next time
        if ind.size == 0:
            continue

        print()
        print('3D Vertical Coordinate: %s' % vinterp_d['model_field'])
        print()

        # Extract field from UPP
        # It seems rather silly to include [:, :, :] before calling .values, but this really
        # helps with memory management. Including these indices allows the program to deallocate
        # wrf3d when setting wrf3d = 0.
        if debug > 0:
            time_3d = dt.datetime.now()
        wrf3d = wrf_ds[hr][vinterp_d['model_field']][:, :, :].values
        if debug > 0:
            print('time to extract %s = %.6f s' % (vinterp_d['model_field'], 
                                                   (dt.datetime.now() - time_3d).total_seconds()))
            for l in os.popen('free -t -m -h').readlines():
                print(l)
            print()

        # Loop over each 3D observation within this time interval
        for j in ind:

            # Check to make sure that we didn't already drop this row
            if j in drop_idx:
                continue

            # Drop row if ob used for vertical interpolation is missing
            if np.isnan(out_df.loc[j, vinterp_d['var']]):
                drop_idx.append(j)
                continue

            if debug > 1:
                time_jstart = dt.datetime.now()
                print()

            # First half of vertical coordinate calculation
            if np.isclose(v1d[0, j], 1e9):         

                # Determine weight for temporal interpolation
                ihr, twgt = cou.determine_twgt(wrf_hr, out_df.loc[j, 'DHR'])
                out_df.loc[j, 'twgt']  = twgt 

                v1d[:, j] = twgt * vinterp_d['conversion'] * cou.interp_x_y(wrf3d, out_df.loc[j], threeD=True)

                if debug > 1:
                    print('total time for v1 = %.6f s' % 
                          (dt.datetime.now() - time_jstart).total_seconds())
                    entry_timesv1.append((dt.datetime.now() - time_jstart).total_seconds())

                # Special case: twgt = 1. In this case, we don't need to interpolate in time, so 
                # we can skip the second part of the vertical coordinate calculation
                if np.isclose(twgt, 1):
                    vdone[j] = 1

            # Second half of vertical coordinate calculation
            else:
                v1d[:, j] = v1d[:, j] + ((1.-out_df.loc[j, 'twgt']) * vinterp_d['conversion'] * 
                                         cou.interp_x_y(wrf3d, out_df.loc[j], threeD=True))
                vdone[j] = 1
                        
                if debug > 1:
                    print('total time for v2 = %.6f s' % 
                          (dt.datetime.now() - time_jstart).total_seconds())
                    entry_timesv2.append((dt.datetime.now() - time_jstart).total_seconds())

            if vdone[j]: 
                # Check for extrapolation
                if ((v1d[:, j].min() < out_df.loc[j, vinterp_d['var']]) and 
                    (v1d[:, j].max() > out_df.loc[j, vinterp_d['var']])):
                    if vinterp_d['ascend']:
                        out_df.loc[j, 'ki0'] = np.where(v1d[:, j] < out_df.loc[j, vinterp_d['var']])[0][-1]
                    else:
                        out_df.loc[j, 'ki0'] = np.where(v1d[:, j] > out_df.loc[j, vinterp_d['var']])[0][-1]
                    if debug > 1:
                        print('ki0 = %d' % out_df.loc[j, 'ki0'])
                    out_df.loc[j, vinterp_d['var']], out_df.loc[j, 'kwgt'] = cou.interp_wrf_1d(v1d[:, j], out_df.loc[j],
                                                                                               var=vinterp_d['var'],
                                                                                               itype=vinterp_d['type'])
                else:
                    drop_idx.append(j)
                    continue

                if debug > 1:
                    print('interpolated V = %.2f' % out_df.loc[j, vinterp_d['var']])
                    print('actual V = %.2f' % bufr_csv.df.loc[j, vinterp_d['var']])
          
        # Free up memory (shouldn't have to call garbage collector after this)
        wrf3d = 0.

# Loop over each variable
for o in vars_3d:

    # Loop over each WRF time
    for hr in wrf_hr: 

        # Determine indices of obs within wrf_step of this output time
        ind = np.where(np.logical_and(out_df['DHR'] > (hr - wrf_step_dec), 
                                      out_df['DHR'] < (hr + wrf_step_dec)))
        ind = np.intersect1d(ind, np.array(ob_idx['3d']))

        # If no indices, move to next time
        if ind.size == 0:
            continue

        print()
        print('3D Interp: %s' % vars_3d[o])
        print()

        # Extract field from UPP
        if debug > 0:
            time_3d = dt.datetime.now()
        wrf3d = wrf_ds[hr][vars_3d[o]][:, :, :].values
        if debug > 0:
            print('time to extract %s = %.6f s' % (vars_3d[o], (dt.datetime.now() - time_3d).total_seconds()))
            for l in os.popen('free -t -m -h').readlines():
                print(l)
            print()

        # Loop over each 3D observation within this time interval
        for j in ind:

            # Check to make sure that we didn't already drop this row
            if j in drop_idx:
                continue

            if debug > 1:
                time_jstart = dt.datetime.now()
                print()

            if (not np.isnan(out_df.loc[j, o]) and vinterp[out_df.loc[j, 'vgroup']]['var'] != o):
                if debug > 1:
                    time_before_interp = dt.datetime.now()
                twgt =  out_df.loc[j, 'twgt'] 
                if o == 'POB': unit_correct = 1e-2
                else: unit_correct = 1
                if np.isclose(out_df.loc[j, o], 1e9):
                    out_df.loc[j, o] = twgt * unit_correct * cou.interp_x_y_z(wrf3d, out_df.loc[j])
                else:
                    out_df.loc[j, o] = ((1.-twgt) * unit_correct * cou.interp_x_y_z(wrf3d, out_df.loc[j]) + 
                                        out_df.loc[j, o])
                if debug > 1:
                    time_after_interp = dt.datetime.now()
                    print('finished interp for %s (%.6f s)' % 
                          (o, (time_after_interp - time_before_interp).total_seconds()))

            if debug > 1:
                print('total time = %.6f s' % (dt.datetime.now() - time_jstart).total_seconds())
                entry_times3d.append((dt.datetime.now() - time_jstart).total_seconds())

        # Free up memory (shouldn't have to call garbage collector after this)
        wrf3d = 0.

print()
print('Done with 3D Obs')
print('number of dropped obs = %d' % (len(drop_idx) - ndrop2d))
print('time = %s s' % (dt.datetime.now() - start3d).total_seconds())
print()


#---------------------------------------------------------------------------------------------------
# Clean Up
#---------------------------------------------------------------------------------------------------

# Drop rows that we skipped as well as the extra columns we added
debug_df = out_df.copy()
out_df.drop(labels=extra_col_int, axis=1, inplace=True)
out_df.drop(labels=extra_col_float, axis=1, inplace=True)
out_df.drop(index=drop_idx, inplace=True)
out_df.reset_index(drop=True, inplace=True)
bufr_csv.df.drop(index=drop_idx, inplace=True)
bufr_csv.df.reset_index(drop=True, inplace=True)
debug_df.drop(index=drop_idx, inplace=True)
debug_df.reset_index(drop=True, inplace=True)

# Convert to proper units
out_df['QOB'] = out_df['QOB'] * 1e6
out_df['TOB'] = out_df['TOB'] - 273.15
out_df['PWO'] = (out_df['PWO'] / 997.) * 1000.
out_df['PMO'] = out_df['PMO'] * 1e-2
out_df['ELV'] = np.int64(out_df['ELV'])
idx_3d = np.where((out_df['subset'] == 'AIRCAR') | (out_df['subset'] == 'AIRCFT') | 
                  (out_df['subset'] == 'ADPUPA'))[0]
out_df.loc[idx_3d, 'ZOB'] = mc.geopotential_to_height(out_df.loc[idx_3d, 'ZOB'].values * units.m * const.g).to('m').magnitude
if interp_latlon:
    idx = np.where((out_df['subset'] == 'ADPSFC') | (out_df['subset'] == 'SFCSHP') |
                   (out_df['subset'] == 'MSONET'))[0] 
    out_df.loc[idx, 'XOB'] = out_df.loc[idx, 'XOB'] + 360.

# Compute derived quantities (TDO and Tv)
tv_idx = np.where(np.isclose(out_df['tvflg'], 0))[0]
print('number of Tv obs = %d' % len(tv_idx))
if use_Tv:
    mix_ratio = mc.mixing_ratio_from_specific_humidity(out_df.loc[tv_idx, 'QOB'].values * units.mg / units.kg)
    out_df.loc[tv_idx, 'TOB'] = mc.virtual_temperature(out_df.loc[tv_idx, 'TOB'].values * units.degC,
                                                       mix_ratio).to('degC').magnitude
else:
    out_df.loc[tv_idx, 'tvflg'] = 1
out_df = bufr.compute_dewpt(out_df)

# If we didn't interpolate ZOB for AIRCAR and AIRCFT, copy values from original BUFR file
if not interp_z_aircft:
    air_idx = np.where((out_df['subset'] == 'AIRCAR') | (out_df['subset'] == 'AIRCFT'))[0]
    out_df.loc[air_idx, 'ZOB'] = bufr_csv.df.loc[air_idx, 'ZOB']

# Reset (XOB, YOB) for ADPUPA obs if (XDR, YDR) was used for ADPUPA locations
if use_raob_drift:
    if 'ADPUPA' in ob_idx.keys():
        out_df.loc[ob_idx['ADPUPA'], 'XOB'] = bufr_csv.df.loc[ob_idx['ADPUPA'], 'XOB']
        out_df.loc[ob_idx['ADPUPA'], 'YOB'] = bufr_csv.df.loc[ob_idx['ADPUPA'], 'YOB']
        out_df.loc[ob_idx['ADPUPA'], 'DHR'] = bufr_csv.df.loc[ob_idx['ADPUPA'], 'DHR']

# Set certain fields all to NaN if desired
for field in nan_fields:
    out_df.loc[:, field] = np.nan
    bufr_csv.df.loc[:, field] = np.nan

# Write output DataFrame to a CSV file
# real_red.prepbufr.csv file can be used for assessing interpolation accuracy
bufr.df_to_csv(out_df, '%s/%s.%s.fake.prepbufr.csv%s' % (fake_bufr_dir, bufr_time.strftime('%Y%m%d%H%M'),  
                                                         bufr_tag, bufr_suffix))
bufr.df_to_csv(bufr_csv.df, '%s/%s.%s.real_red.prepbufr.csv%s' % (fake_bufr_dir, bufr_time.strftime('%Y%m%d%H%M'), 
                                                                  bufr_tag, bufr_suffix))

# Timing
print()
print('END OF PROGRAM')
if debug > 1:
    print()
    for a, s in zip([entry_times2d, entry_timesv1, entry_timesv2, entry_times3d],
                    ['2D', 'P1', 'P2', '3D']):
        if len(a) > 0:
            print('avg time per %s entries = %.6f s' % (s, np.mean(np.array(a))))
print('total time = %s s' % (dt.datetime.now() - begin).total_seconds())


"""
End create_conv_obs.py
"""
