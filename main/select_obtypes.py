"""
Restrict BUFR CSV Files to Only Contain Certain Observation Types

Optional command-line arguments:
    argv[1] = Input bufr CSV file
    argv[2] = Output bufr CSV file
    argv[3] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
Date Created: 14 August 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import yaml
import sys
import numpy as np

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

in_fname = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202202010000.rap.prepbufr.csv'
out_fname = 'test.csv'
obtypes = [120, 130, 131, 133, 134, 135]

# Option to set certain variables from certain ob types to missing
missing_var = {'POB':[180, 181, 182, 183, 187, 188, 280, 281, 282, 283, 287, 288],
               'PRSS':[120, 180, 181, 182, 183, 187, 188, 220, 280, 281, 282, 283, 287, 288]}

# Option to adjust quality marker flags to 5 (do not assimilate)
qm_to_5 = {'PQM':[180, 181, 182, 183, 187, 188, 280, 281, 282, 283, 287, 288],
           'PMQ':[120, 180, 181, 182, 183, 187, 188, 220, 280, 281, 282, 283, 287, 288]}

# Option to use inputs from YAML file
if len(sys.argv) > 1:
    in_fname = sys.argv[1]
    out_fname = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    obtypes = param['select_obs']['obtypes']
    missing_var = param['select_obs']['missing_var']
    qm_to_5 = param['select_obs']['qm_to_5']


#---------------------------------------------------------------------------------------------------
# Only Keep Certain Observation Types
#---------------------------------------------------------------------------------------------------

bufr_csv = bufr.bufrCSV(in_fname)

# Only select certain observation types
bufr_csv.select_obtypes(obtypes)

# Set certain variables to missing
for v in missing_var:
    for typ in missing_var[v]:
        bufr_csv.df.loc[bufr_csv.df['TYP'] == typ, v] = np.nan

# Set certain QM flags to 5
for v in qm_to_5:
    for typ in qm_to_5[v]:
        bufr_csv.df.loc[bufr_csv.df['TYP'] == typ, v] = 5

bufr.df_to_csv(bufr_csv.df, out_fname)


"""
End select_obtypes.py
"""
