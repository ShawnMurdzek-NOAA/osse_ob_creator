"""
Plot Raw and Superobbed UAS Vertical Profiles

Optional command-line arguments:
    argv[1] = Time of prepbufr file (YYYYMMDDHH)
    argv[2] = Prepbufr file tag
    argv[3] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
Date Created: 29 February 2024
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import xarray as xr
import matplotlib.pyplot as plt
import metpy.calc as mc
from metpy.units import units
import numpy as np
import sys
import yaml

import pyDA_utils.bufr as bufr
import pyDA_utils.plot_model_data as pmd
import pyDA_utils.map_proj as mp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# BUFR file with raw UAS profile
bufr_file_raw = '/work2/noaa/wrfruc/murdzek/nature_run_spring/obs/uas_hspace_150km_ctrl/err_uas_csv/202204291500.rap.fake.prepbufr.csv'

# BUFR file with superobbed UAS profile
bufr_file_superob = '/work2/noaa/wrfruc/murdzek/src/osse_ob_creator/main/tmp_superob.csv'

# Ob type for thermodynamic and wind measurements 
ob_typ_thermo = 136
ob_typ_wind = 236

# SIDs to plot
all_sid = ["'UA000001'", "'UA000053'", "'UA000180'"]

# Output file name (include %s placeholder for SID)
out_fname = './uas_raw_superob_compare_%s.png'

# Use passed arguments, if they exist
if len(sys.argv) > 1:
    t_str = sys.argv[1]
    tag = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    bufr_file_raw = '%s/%s.%s.input.csv' % (param['paths']['syn_superob_csv'],
                                            t_str, tag)
    bufr_file_superob = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_superob_csv'],
                                                        t_str, tag)
    ob_type_thermo = int(param['superobs']['plot_vprof']['ob_type_thermo'])
    ob_type_wind = int(param['superobs']['plot_vprof']['ob_type_wind'])
    all_sid = param['superobs']['plot_vprof']['all_sid']
    out_fname = '%s/%s' % (param['paths']['plots'], t_str) + '/uas_raw_superob_compare_%s.png'


#---------------------------------------------------------------------------------------------------
# Make Plots
#---------------------------------------------------------------------------------------------------

# Read in BUFR CSV files
bufr_csv_raw = bufr.bufrCSV(bufr_file_raw)
bufr_csv_superob = bufr.bufrCSV(bufr_file_superob)

# Create plots
for sid in all_sid:
    print('plotting UAS %s' % sid)

    # Extract the desired SID
    raw_thermo = bufr_csv_raw.df.loc[(bufr_csv_raw.df['SID'] == sid) & 
                                     (bufr_csv_raw.df['TYP'] == ob_typ_thermo)].copy()
    raw_wind = bufr_csv_raw.df.loc[(bufr_csv_raw.df['SID'] == sid) & 
                                   (bufr_csv_raw.df['TYP'] == ob_typ_wind)].copy()
    superob_thermo = bufr_csv_superob.df.loc[(bufr_csv_superob.df['SID'] == sid) & 
                                             (bufr_csv_superob.df['TYP'] == ob_typ_thermo)].copy()
    superob_wind = bufr_csv_superob.df.loc[(bufr_csv_superob.df['SID'] == sid) & 
                                           (bufr_csv_superob.df['TYP'] == ob_typ_wind)].copy()

    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(12, 8), sharey=True)

    for j, v in enumerate(['TOB', 'QOB', 'POB']):
        ax = axes[0, j]
        ax.plot(raw_thermo[v], raw_thermo['ZOB'], 'c-', label='raw')
        ax.plot(superob_thermo[v], superob_thermo['ZOB'], 'ko', label='superob')
        ax.set_xlabel('{v} ({u})'.format(v=v, u=bufr_csv_raw.meta[v]['units']), size=16)
        ax.grid()

    for j, v in enumerate(['UOB', 'VOB']):
        ax = axes[1, j]
        ax.plot(raw_wind[v], raw_wind['ZOB'], 'c-', label='raw')
        ax.plot(superob_wind[v], superob_wind['ZOB'], 'ko', label='superob')
        ax.set_xlabel('{v} ({u})'.format(v=v, u=bufr_csv_raw.meta[v]['units']), size=16)
        ax.grid()

    for j in range(2):
        axes[j, 0].set_ylabel('height (m)', size=16)

    plt.suptitle(f'ID = {sid}', size=20)
    axes[0, 0].legend()

    plt.savefig(out_fname % sid)


"""
End plot_raw_superob_uas_vprofs.py 
"""
