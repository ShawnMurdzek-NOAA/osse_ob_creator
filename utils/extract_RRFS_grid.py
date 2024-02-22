"""
Extract RRFS Horizontal and Vertical Grid Information

Save RRFS horizontal and vertical grid to a separate netCDF file. Useful when defining a grid for
superobbing. Note that the RRFS vertical grid is not regular (i.e., a vertical level is not 
necessarily at the same pressure or height level all the time), so a horizontal reduction (e.g., 
average, min, max, etc.) is used to obtain the vertical grid.

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

# Input RRFS natlev file name
in_fname = '/work2/noaa/wrfruc/murdzek/RRFS_OSSE/syn_data_app_orion/spring/NCO_dirs/ptmp/prod/rrfs.20220429/21/rrfs.t21z.natlev.f001.conus_3km.grib2'

# Output netCDF file name
out_fname = './RRFS_grid_max.nc'

# Reduction function to use in the horizontal to obtain the vertical grid
red_fct = np.amax


#---------------------------------------------------------------------------------------------------
# Extract RRFS Grid
#---------------------------------------------------------------------------------------------------

# Open input grib file
in_ds = xr.open_dataset(in_fname, engine='pynio')

# Compute height AGL for vertical grid
hgt_sfc = mc.geopotential_to_height(in_ds['HGT_P0_L1_GLC0'].values * units.m * const.g).to('m').magnitude
hgt_z_lvls = mc.geopotential_to_height(in_ds['HGT_P0_L105_GLC0'].values * units.m * const.g).to('m').magnitude
hgt_agl = xr.DataArray(data=red_fct(hgt_z_lvls - hgt_sfc, axis=(1, 2)),
                       coords={'lv_HYBL2':np.arange(1, np.shape(hgt_z_lvls)[0]+1)},
                       attrs={'long_name':'height above ground level',
                              'units':'m'})

# Save to output netCDF
out_ds = xr.Dataset(data_vars={'gridlat_0':in_ds['gridlat_0'],
                               'gridlon_0':in_ds['gridlon_0'],
                               'HGT_AGL':hgt_agl})
out_ds.to_netcdf(out_fname)


"""
End extract_RRFS_grid.py 
"""
