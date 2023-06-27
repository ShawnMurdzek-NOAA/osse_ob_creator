"""
Create Perfect Simulated IMS Snow Observations from WRF Nature Run Output

Observations are written into a netcdf file in a manner consistent with IMS snow obs used by RRFS.
More information about IMS snow obs can be found here: https://usicecenter.gov/Products/ImsHome

NOTE: In order for these snow fields to be used by RRFS, the output files must be converted from
netcdf to grib2. Unfortunately, this requires a completely different Python environment b/c of
dependencies involved with packages that handle grib files (e.g., pygrib, iris_grib). 

shawn.s.murdzek@noaa.gov
Date Created: 2 May 2023
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

import create_ob_utils as cou 
import map_proj as mp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Directory containing wrfnat output from UPP
wrf_dir = '/work2/noaa/wrfruc/murdzek/nature_run_winter/UPP/'

# Directory containing real IMS snow grib2 data files
ims_dir = '/work2/noaa/wrfruc/murdzek/RRFS_input_data/snow/ims96/grib2/'

# Output directory for synthetic IMS snow files
fake_ims_dir = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_ims/'

# Start and end times for IMS snow files. Step is in hrs
ims_start = dt.datetime(2022, 2, 1, 22)
ims_end = dt.datetime(2022, 2, 7, 22)
ims_step = 24

# Use passed arguments, if they exist
if len(sys.argv) > 1:
    wrf_dir = sys.argv[1]
    ims_dir = sys.argv[2]
    fake_ims_dir = sys.argv[3]
    ims_start = dt.datetime.strptime(sys.argv[4], '%Y%m%d%H')
    ims_end = ims_start + dt.timedelta(hours=1)
    debug = 0 


#---------------------------------------------------------------------------------------------------
# Create Synthetic Observations
#---------------------------------------------------------------------------------------------------

# Timing
begin = dt.datetime.now()

#wrf_snow_field = 'SNOD_P0_L1_GLC0'
wrf_snow_field = 'SNOWC_P0_L1_GLC0'
wrf_ice_field = 'ICEC_P0_L1_GLC0'
ims_snow_field = 'SNOWC_P0_L1_GST0'
ims_ice_field = 'ICEC_P0_L1_GST0'

ntimes = int((ims_end - ims_start) / dt.timedelta(hours=ims_step) + 1)
for i in range(ntimes):
    t = ims_start + dt.timedelta(hours=(i*ims_step))
    start_loop = dt.datetime.now()
    print()
    print('t = %s' % t.strftime('%Y-%m-%d %H:%M:%S'))
    print('start time = %s' % start_loop.strftime('%Y%m%d %H:%M:%S'))
    ims_fname = '%s/%s.grib2' % (ims_dir, t.strftime('%y%j%H%M%S0000'))
    ims_real_ds = xr.open_dataset(ims_fname, engine='pynio')
    ims_snow = ims_real_ds[ims_snow_field].values
    ims_ice = ims_real_ds[ims_ice_field].values
    ims_shape = ims_snow.shape

    # Open wrfnat files
    wrf_ds = xr.open_dataset(wrf_dir + t.strftime('/%Y%m%d/wrfnat_%Y%m%d%H%M.grib2'), engine='pynio')
    wrf_snow = wrf_ds[wrf_snow_field].values
    wrf_ice = wrf_ds[wrf_ice_field].values
    imax_wrf = wrf_snow.shape[0] - 1
    jmax_wrf = wrf_snow.shape[1] - 1

    print('time to open GRIB files = %.2f s' % (dt.datetime.now() - start_loop).total_seconds())
    
    # Compute (x, y) coordinates of obs using a Lambert Conformal projection
    start_map_proj = dt.datetime.now()
    print('Performing map projection with obs...')
    x_ims, y_ims = mp.ll_to_xy_lc(np.ravel(ims_real_ds['gridlat_0'].values), 
                                  np.ravel(ims_real_ds['gridlon_0'].values))
    inear_ims = np.int32(np.around(y_ims))
    jnear_ims = np.int32(np.around(x_ims))
    print('Finished with map projection and computing nearest neighbors (time = %.3f s)' % 
          (dt.datetime.now() - start_map_proj).total_seconds())

    # Create output DataSet
    start_interp = dt.datetime.now()
    out_ds = ims_real_ds.copy()

    for wrf_field, ims_field, ims_field_name, fact in zip([wrf_snow, wrf_ice], 
                                                          [ims_snow, ims_ice], 
                                                          [ims_snow_field, ims_ice_field],
                                                          [100, 1]):
        unmasked_idx = np.where(~np.isnan(np.ravel(ims_field)) & (inear_ims >= 0) & 
                                (jnear_ims >= 0) & (inear_ims <= imax_wrf) & 
                                (jnear_ims <= jmax_wrf))[0]
        print('------------------------------------')
        print('%s: interpolating to %d gridpoints' % (ims_field_name, len(unmasked_idx)))
        for ct, ims_idx in enumerate(unmasked_idx):
            if (ct % 50000 == 0):
                print('ob number %d' % ct)
            i_wrf = inear_ims[ims_idx]
            j_wrf = jnear_ims[ims_idx]
            i_ims, j_ims = np.unravel_index(ims_idx, ims_shape)
            out_ds[ims_field_name][i_ims, j_ims] = fact*np.float32(wrf_field[i_wrf, j_wrf] > 0)

    print('Finished with interpolation (time = %.3f s)' % 
          (dt.datetime.now() - start_interp).total_seconds())

    # Save dataset to netcdf
    out_ds.to_netcdf('%s/%s.nc' % (fake_ims_dir, t.strftime('%y%j%H%M%S0000')))


"""
End create_ims_snow_obs.py
"""
