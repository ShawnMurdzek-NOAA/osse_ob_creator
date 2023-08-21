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

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

in_fname = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202202010000.rap.prepbufr.csv'
out_fname = 'test.csv'
obtypes = [120, 130, 131, 133, 134, 135]

# Option to use inputs from YAML file
if len(sys.argv) > 1:
    in_fname = sys.argv[1]
    out_fname = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    obtypes = param['select_obs']['obtypes']


#---------------------------------------------------------------------------------------------------
# Only Keep Certain Observation Types
#---------------------------------------------------------------------------------------------------

bufr_csv = bufr.bufrCSV(in_fname)
bufr_csv.select_obtypes(obtypes)
bufr.df_to_csv(bufr_csv.df, out_fname)


"""
End select_obtypes.py
"""
