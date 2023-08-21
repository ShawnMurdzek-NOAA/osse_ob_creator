"""
Check Output from Linear Interpolation Test

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import sys
import glob
import numpy as np

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Compare Real_Red an Synthetic BUFR CSV Files
#---------------------------------------------------------------------------------------------------

fnames = {}
fnames['real'] = glob.glob('./linear_interp_test/perfect_conv/*.real_red.prepbufr.csv')[0]
fnames['fake'] = glob.glob('./linear_interp_test/perfect_conv/*.fake.prepbufr.csv')[0]

dfs = {}
for key in fnames.keys():
    dfs[key] = bufr.bufrCSV(fnames[key]).df

# Tolerances roughly come from 2*(BUFR precision)
tolerance = {'TOB':0.2, 'QOB':2, 'UOB':0.2, 'VOB':0.2, 'PMO':0.2}

err = 0
for key in tolerance.keys():
    diff = dfs['real'][key].values - dfs['fake'][key].values
    maxdiff = np.nanmax(np.abs(diff))
    print()
    print('differences for %s' % key)
    print('RMSD = %.5f' % np.sqrt(np.nanmean(diff*diff)))
    print('max abs diff = %.5f' % maxdiff)
    print('max allowed diff = %.2f' % tolerance[key])
    if maxdiff > tolerance[key]:
        err = 10
        idiff = np.where(np.abs(diff) > tolerance[key])[0]
        print('ERROR: maxdiff exceeds max allowed diff for the following ob types!')
        print(dfs['real']['TYP'].iloc[idiff].values)

print()
print(err)


"""
End check_linear_interp_test.py
"""
