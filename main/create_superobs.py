"""
Create Superobs for a Specific Observation Type

Superobs are created using the following process:

1. Determine which obs will be part of a superob using the model grid information. Obs within a
    single grid cell are identified as being part of a superob.
2. Perform a reduction operation (e.g., average, min, max) on the obs that are part of a superob.
3. Perform a second reduction on the coordinates (spatial and temporal) of the obs that are part of 
    a superob in order to define the coordinates of the superob.

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np
import xarray as xr

from pyDA_utils import bufr
from pyDA_utils import superob_reduction_fcts as srf


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input BUFR CSV file name
in_csv_fname =

# Output BUFR CSV file name
out_csv_fname = './tmp_superob.csv'

# Observation types to create superobs for
obs_types = [136, 236]

# RRFS grid information file name
rrfs_grid_fname = '../fix_data/RRFS_grid_max.nc'

# Reduction function used to create superobs
red_fct_superob = np.mean


"""
End create_superobs.py
"""
