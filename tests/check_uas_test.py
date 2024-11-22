"""
Check Output from UAS Test

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import sys
import glob
import numpy as np
import pandas as pd
import yaml

import pyDA_utils.bufr as bufr

# Initialize error as 0
err = 0

#---------------------------------------------------------------------------------------------------
# Check Bogus UAS CSV BUFR File
#---------------------------------------------------------------------------------------------------

# Read in files
bogus_csv = bufr.bufrCSV('./uas_test/bogus_csv/202202011200.rap.prepbufr.csv')
uas_locs = pd.read_csv('./data/uas_site_locs_TEST.txt')
with open('uas_test.yml', 'r') as fptr:
    param = yaml.safe_load(fptr)

# Check (lat, lon) coordinates
bogus_lat = np.unique(bogus_csv.df['YOB'].values)
bogus_lon = np.unique(bogus_csv.df['XOB'].values)
txt_lat = uas_locs['lat (deg N)'].values
txt_lon = uas_locs['lon (deg E)'].values

print()
print('bogus lats =', bogus_lat)
print('bogus lons =', bogus_lon)
print('text lats =', txt_lat)
print('text lons =', txt_lon)

if len(bogus_lat) != len(txt_lat):
    print()
    print('ERROR: Number of (lat, lon) coordinates in bogus CSV file and input text file differ')
    print('Number of coordinates in bogus CSV file = {n}'.format(n=len(bogus_lat)))
    print('Number of coordinates in input text file = {n}'.format(n=len(txt_lat)))
    err = 10

for (lat, lon) in zip(bogus_lat, bogus_lon):
    if (~np.any(np.isclose(lat, txt_lat)) or ~np.any(np.isclose(lon, txt_lon + 360))):
        print()
        print('ERROR: (lat, lon) coordinates in bogus CSV file and input text file do not match')
        err = 10

# Check number of vertical levels
nlvls = 1 + int(param['create_csv']['sample_freq'] * 
                (param['create_csv']['max_height'] / param['create_csv']['ascent_rate']))
bogus_nlvls = len(bogus_csv.df.loc[(bogus_csv.df['TYP'] == 136) & (bogus_csv.df['SID'] == "'UA000001'")])
print()
print(f'expected nlvls = {nlvls}')
print(f'actual nlvls = {bogus_nlvls}')
if nlvls != bogus_nlvls:
    print('ERROR: Number of vertical levels in bogus CSV file does not match expectations') 
    err = 10


#---------------------------------------------------------------------------------------------------
# Check Superob UAS CSV BUFR File
#---------------------------------------------------------------------------------------------------

# Read in file
superob_csv = bufr.bufrCSV('./uas_test/superob_uas/202202011200.rap.fake.prepbufr.csv')
superob_df = bufr.compute_RH(superob_csv.df)

# Check that RH never exceeds 100%
max_rh = np.amax(superob_df['RHOB'])
print()
print(f'max RH in superob CSV = {max_rh}')
if max_rh > 100.1:
    print('ERROR: RH in superobs exceeds 100%')
    err = 10

# Check number of superobs is less than the number of original obs
size_bogus = len(bogus_csv.df)
size_superob = len(superob_df)
print()
print(f'size bogus CSV = {size_bogus}')
print(f'size superob CSV = {size_superob}')
if size_superob >= size_bogus:
    print('ERROR: Number of superobs is >= number of raw obs')
    err = 10


#---------------------------------------------------------------------------------------------------
# Check Limited UAS CSV BUFR File
#---------------------------------------------------------------------------------------------------

# Read in file
original_csv = bufr.bufrCSV('./uas_test/limit_uas/202202011200.rap.input.csv')
original_df = bufr.compute_wspd_wdir(original_csv.df)
limit_uas_csv = bufr.bufrCSV('./uas_test/limit_uas/202202011200.rap.fake.prepbufr.csv')
limit_uas_df = bufr.compute_wspd_wdir(limit_uas_csv.df)
ref_csv = bufr.bufrCSV('./uas_test/perf_csv/202202011200.rap.fake.prepbufr.csv')
ref_df = bufr.compute_wspd_wdir(ref_csv.df)

# Check that 'liqmix' column is dropped in the new DataFrame
if 'liqmix' in limit_uas_df.columns:
    print("ERROR: 'liqmix' not dropped from output of limit_uas_flights.py")
    err = 10
if 'liqmix' not in original_df.columns:
    print("ERROR: 'liqmix' not in input for limit_uas_flights.py")
    err = 10

# Check that original_df and ref_df are the same size and arae larger than limit_uas_df
if len(original_df) != len(ref_df):
    print("ERROR: 'original_df' and 'ref_df' are different sizes!")
    err = 10
if len(limit_uas_df) >= len(original_df):
    print("ERROR: 'limit_uas_df' is the same size or larger than 'original_df'")
    err = 10

# Check that the WSPD threshold is only exceeded at most 4 times in ref_df
for sid in np.unique(limit_uas_df['SID'].values):
    ref_1_sid = ref_df.loc[ref_df['SID'] == sid]
    limit_1_sid = limit_uas_df.loc[limit_uas_df['SID'] == sid]
    n_wspd = np.sum(ref_1_sid.loc[:len(limit_1_sid), 'WSPD'] > 300)
    if n_wspd > 4:
        print('ERROR: WSPD threshold exceeded too many times in limit_uas_flights.py output')
        err = 10

print()
print(err)


"""
End check_uas_test.py
"""
