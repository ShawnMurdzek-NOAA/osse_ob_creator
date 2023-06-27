"""
Determine Precision for Each PrepBUFR Observation Type

shawn.s.murdzek@noaa.gov
Date Created: 6 April 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import bufr
import numpy as np
import pandas as pd
import metpy.calc as mc
from metpy.units import units


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

bufr_file = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202204300000.rap.prepbufr.csv'
out_fname = 'bufr_ob_precision.txt'
bufr_vars = ['TOB', 'QOB', 'PWO', 'POB', 'ZOB', 'ELV', 'UOB', 'VOB', 'WSPD', 'WDIR']


#---------------------------------------------------------------------------------------------------
# Count Number of Obs For Each Type
#---------------------------------------------------------------------------------------------------

# Load EMC PrepBUFR Table 5
table5 = pd.read_csv('../metadata/emc_bufr_table5.csv')
ob_types = table5['Report Type'].unique()

bufr_csv = bufr.bufrCSV(bufr_file)

# Compute wind speed and direction
bufr_csv.df['WSPD'] = mc.wind_speed(bufr_csv.df['UOB'].values * units.m / units.s,
                                    bufr_csv.df['VOB'].values * units.m / units.s).to(units.kt).magnitude
bufr_csv.df['WDIR'] = mc.wind_direction(bufr_csv.df['UOB'].values * units.m / units.s,
                                        bufr_csv.df['VOB'].values * units.m / units.s).magnitude

# Print results and save to output file
fptr = open(out_fname, 'w')
fptr.write('ob ID | var | first ten unique values\n')
for i, t in enumerate(ob_types):
    subset = bufr_csv.df.loc[bufr_csv.df['TYP'] == t].copy()
    for v in bufr_vars:    
        unique_vals = np.sort(np.unique(subset[v].values))
        if len(unique_vals) <= 1:
            continue
        nvals = min(10, len(unique_vals))
        fptr.write('%05d | %s |' % (t, v))
        for val in unique_vals[:nvals]:
            fptr.write(' %.3f' % val)
        fptr.write('\n')
    fptr.write('\n')
fptr.close()


"""
End determine_bufr_precision.py
"""
