"""
Determine the Minimum and Maximum DHR Values for Different Types of Prepbufr Files

shawn.s.murdzek@noaa.gov
Date Created: 24 March 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import os
import pandas as pd
import bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

bufr_csv_path = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv'


#---------------------------------------------------------------------------------------------------
# Compute Min/Max DHR
#---------------------------------------------------------------------------------------------------

# Get file names
fnames = os.listdir(bufr_csv_path)

dhr = {}
for f in fnames:
    if f[-3:] == 'csv':
        tag = f.split('.')[1]
        if tag not in dhr.keys():
            dhr[tag] = {'min':[], 'max':[], 'time':[]}
        print(f)
        bufr_csv = bufr.bufrCSV('%s/%s' % (bufr_csv_path, f))
        dhr[tag]['min'].append(bufr_csv.df['DHR'].min()) 
        dhr[tag]['max'].append(bufr_csv.df['DHR'].max())
        dhr[tag]['time'].append(f.split('.')[0]) 

for tag in dhr.keys():
    dhr[tag] = pd.DataFrame.from_dict(dhr[tag])


"""
End prepbufr_dhr.py
"""
