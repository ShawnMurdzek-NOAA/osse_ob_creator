"""
Create BUFR CSV for Surface Station Observations

This CSV will be filled with bogus data. Use create_synthetic_obs.py to interpolate actual NR data to
ob locations.

Optional command-line arguments:
    argv[1] = Obs valid time in YYYYMMDDHHMM format
    argv[2] = Output CSV file name
    argv[3] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import datetime as dt
import numpy as np
import pandas as pd
import sys
import yaml

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Obs location file
loc_fname = '../fix_data/uas_site_locs_150km.txt'

# Ob valid times (this is the timestamp on the BUFR CSV)
valid_times = [dt.datetime(2022, 5, 2, 2)]

# DHR values for sampling
DHR_vals = [0]

# Starting SID number
init_sid = 1

# Sample BUFR CSV file (needed to determine which fields to include)
sample_bufr_fname = '/work/noaa/wrfruc/murdzek/nature_run_spring/obs/perfect_conv/real_csv/202205010000.rap.prepbufr.csv'

# Output BUFR CSV file (include %s placeholder for timestamp)
out_fname = '%s.bogus.prepbufr.csv'

# Option to use inputs from YAML file
if len(sys.argv) > 1:
    bufr_t = sys.argv[1]
    out_fname = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    valid_times = [dt.datetime.strptime(bufr_t, '%Y%m%d%H%M')]
    loc_fname = param['shared']['uas_grid_file']
    DHR_vals = param['create_csv']['DHR_vals']
    init_sid = param['create_csv']['init_sid']
    sample_bufr_fname = param['create_csv']['sample_bufr_fname']


#---------------------------------------------------------------------------------------------------
# Create Sfc Station BUFR CSV
#---------------------------------------------------------------------------------------------------

typ_thermo = 187
typ_wind = 287
subset = 'ADPSFC'
SID_prefix = 'SFC'
t29 = 512  # Data dump type (https://www.emc.ncep.noaa.gov/mmb/data_processing/prepbufr.doc/table_6.htm)
quality_m = 2

# Ob locations in (x, y) space
ob_locs = pd.read_csv(loc_fname)
nlocs = len(ob_locs)

# Sample BUFR file
sample_bufr = bufr.bufrCSV(sample_bufr_fname)
all_columns = list(sample_bufr.df.columns)

# Loop over each valid time
for valid in valid_times:

    # Need factor of 2 for total obs (ntobs) to account for both thermodynamic and kinematic obs
    nDHR = len(DHR_vals)
    ntobs = 2*nDHR*nlocs

    out_dict = {}
    for col in all_columns:  
        out_dict[col] = np.zeros(ntobs) * np.nan

    out_dict['nmsg'] = np.array([[i]*2*nDHR for i in range(1, nlocs+1)]).ravel()
    out_dict['subset'] = np.array([subset]*ntobs)
    out_dict['cycletime'] = np.array([valid.strftime('%Y%m%d%H')]*ntobs)
    out_dict['ntb'] = np.array(list(range(1, 2*nDHR+1))*nlocs)
    out_dict['SID'] = np.array([[f"{SID_prefix}{i:05d}"]*2*nDHR for i in range(init_sid, nlocs+init_sid)], dtype=str).ravel()
    out_dict['XOB'] = np.array([[i]*2*nDHR for i in ob_locs['lon (deg E)'].values]).ravel() + 360.
    out_dict['YOB'] = np.array([[i]*2*nDHR for i in ob_locs['lat (deg N)'].values]).ravel()
    out_dict['DHR'] = np.array(DHR_vals*2*nlocs)
    out_dict['TYP'] = np.array(([typ_thermo]*nDHR + [typ_wind]*nDHR)*nlocs)
    out_dict['ELV'] = np.zeros(ntobs)
    out_dict['T29'] = np.array([t29]*ntobs)
    out_dict['POB'] = np.zeros(ntobs)
    out_dict['PQM'] = np.array([quality_m]*ntobs)
    for v in ['QOB', 'TOB', 'ZOB', 'TDO', 'PMO']:
        out_dict[v] = np.array(([0.]*nDHR + [np.nan]*nDHR)*nlocs)
    for qm in ['TQM', 'QQM', 'ZQM', 'PMQ']:
        out_dict[qm] = np.array(([quality_m]*nDHR + [np.nan]*nDHR)*nlocs)
    for v in['UOB', 'VOB']:
        out_dict[v] = np.array(([np.nan]*nDHR + [0.]*nDHR)*nlocs)
    out_dict['WQM'] = np.array(([np.nan]*nDHR + [quality_m]*nDHR)*nlocs)
    out_dict['CAT'] = np.array(([0]*nDHR + [6]*nDHR)*nlocs)    # Data level category (https://www.emc.ncep.noaa.gov/mmb/data_processing/table_local_await-val.htm#0-08-193)
    out_dict['tvflg'] = np.ones(ntobs)
    out_dict['vtcd'] = np.zeros(ntobs)

    out_df = pd.DataFrame(out_dict)
    bufr.df_to_csv(out_df, out_fname % valid.strftime('%Y%m%d%H%M'))


"""
End create_sfc_csv.py
"""
