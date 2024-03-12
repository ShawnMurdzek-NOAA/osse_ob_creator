"""
Extract RRFS Horizontal and Vertical Grid Information

Save RRFS horizontal and vertical grid to a separate netCDF file. Useful when defining a grid for
superobbing. Note that the RRFS vertical grid is not regular (i.e., a vertical level is not 
necessarily at the same pressure or height level all the time), so a horizontal reduction (e.g., 
average, min, max, etc.) is used to obtain the vertical grid.

This code is specific for FV3 dyn output netCDF files.

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import xarray as xr
import numpy as np
import metpy.constants as const
import metpy.calc as mc
from metpy.units import units


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input RRFS file name (it's probably best to use raw RRFS output rather than UPP output)
in_fname = '/work2/noaa/wrfruc/murdzek/RRFS_OSSE/syn_data_app_orion/spring_2iter/NCO_dirs/stmp/2022050610/fcst_fv3lam/dynf000.nc'

# Output netCDF file name
out_fname = '../fix_data/RRFS_grid_max.nc'

# Reduction function to use in the horizontal to obtain the vertical grid
red_fct = np.amax


#---------------------------------------------------------------------------------------------------
# Extract RRFS Grid
#---------------------------------------------------------------------------------------------------

# Open input grib file
in_ds = xr.open_dataset(in_fname)

# Compute height AGL for vertical grid
nz = in_ds['pfull'].size
hgt_z_lvls = np.zeros([nz+1, in_ds['grid_yt'].size, in_ds['grid_xt'].size])
for i in range(in_ds['pfull'].size):
    hgt_z_lvls[nz-i-1, :, :] = hgt_z_lvls[nz-i] - in_ds['delz'][0, nz-i-1, :, :].values
hgt_agl = xr.DataArray(data=red_fct(hgt_z_lvls, axis=(1, 2)),
                       coords={'phalf':in_ds['phalf']},
                       attrs={'long_name':'height above ground level',
                              'units':'m'})

# Compute terrain height
gp_sfc = in_ds['hgtsfc'][0, :, :].values * units.m * const.g
hgt_sfc = xr.DataArray(data=mc.geopotential_to_height(gp_sfc).to('m').magnitude,
                       coords={'grid_yt':in_ds['grid_yt'],
                               'grid_xt':in_ds['grid_xt']},
                       attrs={'long_name':'height of model surface',
                              'units':'m'})

# Save to output netCDF
out_ds = xr.Dataset(data_vars={'lat':in_ds['lat'],
                               'lon':in_ds['lon'],
                               'HGT_SFC':hgt_sfc,
                               'HGT_AGL':hgt_agl})
out_ds.to_netcdf(out_fname)


"""
End extract_RRFS_grid.py 
"""
