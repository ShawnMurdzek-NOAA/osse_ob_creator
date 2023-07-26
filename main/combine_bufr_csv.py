"""
Combine Two BUFR CSV Files

Optional command-line arguments:
    argv[1] = Name of first prepBUFR CSV file
    argv[2] = Name of second prepBUFR CSV file
    argv[3] = Name of combined prepBUFR CSV file

shawn.s.murdzek@noaa.gov
Date Created: 25 July 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import pandas as pd
import sys

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

bufr1_fname = ''
bufr2_fname = ''
output_fname = ''

# Option to use command-line arguments
if len(sys.argv) > 1:
    bufr1_fname = sys.argv[1]
    bufr2_fname = sys.argv[2]
    output_fname = sys.argv[3]


#---------------------------------------------------------------------------------------------------
# Combine CSV Files
#---------------------------------------------------------------------------------------------------

bufr1 = bufr.bufrCSV(bufr1_fname)
bufr2 = bufr.bufrCSV(bufr2_fname)
out_csv = bufr.combine_bufr(bufr1.df, bufr2.df)
bufr.df_to_csv(out_csv, output_fname)


"""
End combine_bufr_csv.py 
"""
