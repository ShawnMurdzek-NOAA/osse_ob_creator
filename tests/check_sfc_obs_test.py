"""
Check Output from sfc obs Test

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import glob
import numpy as np
import pandas as pd
import yaml

import pyDA_utils.bufr as bufr

# Initialize error as 0
err = 0

#---------------------------------------------------------------------------------------------------
# Check Bogus Sfc Ob CSV BUFR File
#---------------------------------------------------------------------------------------------------

# Read in files
bogus_csv = bufr.bufrCSV('./sfc_obs_test/bogus_csv/202202011200.rap.prepbufr.csv')
sfc_obs_locs = pd.read_csv('../fix_data/sfc_site_locs_150km.txt')
with open('sfc_obs_test.yml', 'r') as fptr:
    param = yaml.safe_load(fptr)

# Check that the size of the bogus CSV file is as expected
nDHR = len(param['create_csv']['DHR_vals'])
if len(bogus_csv.df) != (2 * nDHR * len(sfc_obs_locs)): 
    print()
    print('ERROR: Bogus CSV file does not have expected number of entries')
    print(f"Size of bogus CSV file = {len(bogus_csv.df)}")
    print(f"Expected size = {2 * nDHR * len(sfc_obs_locs)}")
    err = 10

# Check (lat, lon) coordinates
bogus_lat = bogus_csv.df.loc[(bogus_csv.df['TYP'] == 187) & (bogus_csv.df['DHR'] == 0), 'YOB'].values
bogus_lon = bogus_csv.df.loc[(bogus_csv.df['TYP'] == 187) & (bogus_csv.df['DHR'] == 0), 'XOB'].values
txt_lat = sfc_obs_locs['lat (deg N)'].values
txt_lon = sfc_obs_locs['lon (deg E)'].values

for (lat, lon) in zip(bogus_lat, bogus_lon):
    if (~np.any(np.isclose(lat, txt_lat)) or ~np.any(np.isclose(lon, txt_lon + 360))):
        print()
        print('ERROR: (lat, lon) coordinates in bogus CSV file and input text file do not match')
        err = 10

# Check that PMO values are not NaN
bogus_pmo = bogus_csv.df.loc[bogus_csv.df['TYP'] == 187, 'PMO'].values
if np.any(np.isnan(bogus_pmo)):
    print()
    print('ERROR: PMO values in bogus CSV file are NaN. They should not be NaN')
    err = 10

print()
print(err)


"""
End check_sfc_obs_test.py
"""
