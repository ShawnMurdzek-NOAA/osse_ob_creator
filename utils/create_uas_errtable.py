"""
Add UAS Errors to an Existing GSI Error Table

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np

import pyDA_utils.gsi_fcts as gsi


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Error standard deviations (it is assumed that the errors do not vary with pressure)
# Units: Terr (degC), RHerr (percent / 10), UVerr (m/s), PSerr (mb), PWerr (mm)
errors = {'Terr': 0.5,
          'RHerr': 0.5,
          'UVerr': 0.6,
          'PSerr': 0.0,
          'PWerr': 0.0}

# UAS observation type
thermo_type = 136
wind_type = 236

# Input and output errtable names
in_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/2nd_iter_assim_only/errtable.2nd_iter.7day'
out_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/2nd_iter_assim_only/include_uas/errtable.7day'


#---------------------------------------------------------------------------------------------------
# Add UAS Errors
#---------------------------------------------------------------------------------------------------

in_errtable = gsi.read_errtable(in_fname)

n_prs_bins = len(in_errtable[100]['prs'])

for key in ['Terr', 'RHerr', 'PSerr', 'PWerr']:
    in_errtable[thermo_type][key] = np.ones(n_prs_bins) * errors[key]

for key in ['UVerr']:
    in_errtable[wind_type][key] = np.ones(n_prs_bins) * errors[key]

gsi.write_errtable(out_fname, in_errtable)


"""
End create_uas_errtable.py
"""
