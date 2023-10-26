"""
Check Output from Select Obs Test

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
# Check Contents of Select Obs CSV
#---------------------------------------------------------------------------------------------------

fname = glob.glob('./select_obs_test/select_csv/*.prepbufr.csv')[0]
csv_df = bufr.bufrCSV(fname).df

err = 0

# Check that correct observation types were rejected
print()
reject_obs = [130, 131, 132, 133, 134, 135]
keep_obs = [120, 180, 187, 220, 280, 287]
for o in reject_obs:
    if (np.sum(csv_df['TYP'] == o) != 0):
        print('observation type %d not removed properly' % o)
        err = 1
for o in keep_obs:
    if (np.sum(csv_df['TYP'] == o) == 0):
        print('observation type %d incorrectly removed' % o)
        err = 1

# Check that correct variables were set to NaN
print()
nan_vars = ['POB']
nan_obs = [180, 181, 183, 187, 188]
keep_vars = ['TOB']
keep_obs = [120, 220]
for o in nan_obs:
    for v in nan_vars:
        if not np.all(np.isnan(csv_df.loc[csv_df['TYP'] == o, v])):
            print('observation type %d, variable %s not set to NaN' % (o, v))
            err = 2
    for v in keep_vars:
        if np.all(np.isnan(csv_df.loc[csv_df['TYP'] == o, v])):
            print('observation type %d, variable %s incorrectly set to NaN' % (o, v))
            err = 2
for o in keep_obs:
    for v in nan_vars:
        if np.all(np.isnan(csv_df.loc[csv_df['TYP'] == o, v])):
            print('observation type %d, variable %s incorrectly set to NaN' % (o, v))
            err = 2

# Check that correct QMs were set to 5
print()
change_qm = ['PQM']
change_obs = [180, 181, 183, 187, 188]
keep_qm = ['TQM']
keep_obs = [120]
for o in change_obs:
    for v in change_qm:
        if not np.all(csv_df.loc[csv_df['TYP'] == o, v] == 5):
            print('observation type %d, variable %s not set to 5' % (o, v))
            err = 3
    for v in keep_qm:
        if np.all(csv_df.loc[csv_df['TYP'] == o, v] == 5):
            print('observation type %d, variable %s incorrectly set to 5' % (o, v))
            err = 3
for o in keep_obs:
    for v in change_qm:
        if np.all(csv_df.loc[csv_df['TYP'] == o, v] == 5):
            print('observation type %d, variable %s incorrectly set to 5' % (o, v))
            err = 3

print()
print(err)


"""
End check_select_obs_test.py
"""
