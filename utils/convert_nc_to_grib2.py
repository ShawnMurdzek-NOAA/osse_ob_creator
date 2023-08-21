"""
Convert a NetCDF file to GRIB2

This script opens an existing grib2 file, changes some of the fields using netCDF fields, then
saves the result.

Working with pygrib can be a bit of a pain, so pygrib uses its own environment

shawn.s.murdzek@noaa.gov
Date Created: 3 May 2023
Environment: /work2/noaa/wrfruc/murdzek/conda/pygrib
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import xarray as xr
import pygrib as pyg
import numpy as np
import sys


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# netcdf and grib files
nc_fname = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_ims/220322200000000.nc'
grib_fname = '/work2/noaa/wrfruc/murdzek/RRFS_input_data/snow/ims96/grib2/220322200000000.grib2'
save_fname = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_ims/220322200000000.grib2'

# Fields to copy from netcdf to grib. Key is grib message number, value is netcdf field
fields = {1:'ICEC_P0_L1_GST0',
          2:'SNOWC_P0_L1_GST0',
          3:'ICEC_P0_L1_GST0',
          4:'SNOWC_P0_L1_GST0'}

# Option to use arguments passed from the command line
if len(sys.argv) > 1:
    day = int(sys.argv[1])
    nc_fname = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_ims/22%03d2200000000.nc' % day
    grib_fname = '/work2/noaa/wrfruc/murdzek/RRFS_input_data/snow/ims96/grib2/22%03d2200000000.grib2' % day
    save_fname = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_ims/22%03d2200000000.grib2' % day
    


#---------------------------------------------------------------------------------------------------
# Copy NetCDF Field to Grib File
#---------------------------------------------------------------------------------------------------

nc_ds = xr.open_dataset(nc_fname)
grb_in = pyg.open(grib_fname)
grb_out = open(save_fname, 'wb')

for i in range(1, grb_in.messages+1):
    print('writing message %d' % i)
    grb = grb_in[i]

    if i in fields.keys():
        new_data = nc_ds[fields[i]].values
        grb_data = grb.values

        # NOTE: pygrib can't handle NaNs, so we'll use the mask from pygrib to only copy non-NaN 
        # values from the netcdf field to the grib field
        grb_data[~grb_data.mask] = new_data[~grb_data.mask]

        grb.values = grb_data

    # Convert message back to binary and write to output file
    msg = grb.tostring()
    grb_out.write(msg)  
  
nc_ds.close()
grb_in.close()
grb_out.close()


"""
End convert_nc_to_grib2.py 
"""
