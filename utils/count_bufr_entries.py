"""
Count Number of BUFR Entries for Each Observation Type

shawn.s.murdzek@noaa.gov
Date Created: 6 April 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import bufr
import numpy as np
import glob
import pandas as pd


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

bufr_dir = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv'
out_fname = 'bufr_ob_counts.txt'

#---------------------------------------------------------------------------------------------------
# Count Number of Obs For Each Type
#---------------------------------------------------------------------------------------------------

# Load EMC PrepBUFR Table 5
table5 = pd.read_csv('../metadata/emc_bufr_table5.csv')
ob_types = table5['Report Type'].unique()

ob_count = np.zeros(ob_types.size)
all_bufr_files = glob.glob(bufr_dir + '/*.rap.prepbufr.csv')
nfiles = len(all_bufr_files)
for i, f in enumerate(all_bufr_files):
    print('%s (%d of %d)' % (f, i+1, nfiles))
    bufr_df = bufr.bufrCSV(f)
    for j, t in enumerate(ob_types):
        ob_count[j] = ob_count[j] + np.sum(bufr_df.df['TYP'] == t)

# Print results and save to output file
fptr = open(out_fname, 'w')
print('ob ID |   number   | description')
fptr.write('ob ID |   number   | description\n')
for i, t in enumerate(ob_types):
    print('%05d | %010d | %s' % (t, ob_count[i], table5.loc[table5['Report Type'] == t]['Description'].values[0]))
    fptr.write('%05d | %010d | %s\n' % (t, ob_count[i], table5.loc[table5['Report Type'] == t]['Description'].values[0]))
fptr.close()


"""
End count_bufr_entries.py
"""
