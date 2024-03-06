"""
Combine An Arbitrary Number of BUFR CSV Files

Optional command-line arguments:
    argv[1] = Text file containing names of input prepBUFR CSV files
    argv[2] = Name of combined prepBUFR CSV file

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

bufr_list_fname = ''
output_fname = ''

# Option to use command-line arguments
if len(sys.argv) > 1:
    bufr_list_fname = sys.argv[1]
    output_fname = sys.argv[2]


#---------------------------------------------------------------------------------------------------
# Combine CSV Files
#---------------------------------------------------------------------------------------------------

# Extract BUFR CSV file names to combine
csv_in_list = []
fptr = open(bufr_list_fname, 'r')
for l in fptr:
    csv_in_list.append(bufr.bufrCSV(l).df)
fptr.close()

# Combine BUFR CSV files
out_csv = bufr.combine_bufr(csv_in_list)
bufr.df_to_csv(out_csv, output_fname)


"""
End combine_bufr_csv.py 
"""
