"""
Plot Full and Limited UAS Time Series

Optional command-line arguments:
    argv[1] = Time of prepbufr file (YYYYMMDDHHMM)
    argv[2] = Prepbufr file tag
    argv[3] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import matplotlib.pyplot as plt
import numpy as np
import sys
import yaml
import datetime as dt

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# BUFR file with reference UAS profile
bufr_file_ref = '/work2/noaa/wrfruc/murdzek/nature_run_spring/obs/uas_obs_35km_wspd20/limit_uas_csv/202204292300.rap.input.csv'

# BUFR file with limited UAS profile
bufr_file_limit = '/work2/noaa/wrfruc/murdzek/nature_run_spring/obs/uas_obs_35km_wspd20/limit_uas_csv/202204292300.rap.fake.prepbufr.csv'

# Variables to plot along with the threshold for limiting UAS obs
plot_vars = {'WSPD':20}

# Number of SIDs to plot
n_sid = 10

# Observation type to search/plot
obtype = 136

# Verbosity level
verbose = 1

# Output file name (include %s placeholder for SID)
out_fname = './uas_ref_limit_timeseries_%s.png'

# Use passed arguments, if they exist
if len(sys.argv) > 1:
    t_str = sys.argv[1]
    tag = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    bufr_file_limit = '%s/%s.%s.fake.prepbufr.csv' % (param['paths']['syn_limit_uas_csv'],
                                                      t_str, tag)
    bufr_file_ref = f"{param['paths'][param['limit_uas']['csv_ref_dir']]}/{t_str}.{tag}.fake.prepbufr.csv"
    plot_vars = param['limit_uas']['plot_timeseries']['plot_vars']
    n_sid = param['limit_uas']['plot_timeseries']['n_sid']
    obtype = param['limit_uas']['plot_timeseries']['obtype']
    out_fname = '%s/%s' % (param['paths']['plots'], t_str) + '/uas_ref_limit_timeseries_%s.png'


#---------------------------------------------------------------------------------------------------
# Make Plots
#---------------------------------------------------------------------------------------------------

# Read in BUFR CSV files
bufr_df = {}
for fname, key in zip([bufr_file_limit, bufr_file_ref], ['limit', 'ref']):
    if verbose > 0: print(f"reading {fname}")
    bufr_df[key] = bufr.bufrCSV(fname).df

    # Compute WSPD and RHOB if needed
    if 'WSPD' in plot_vars.keys():
        if verbose > 0: print(f"computing WSPD")
        bufr_df[key] = bufr.compute_wspd_wdir(bufr_df[key])
    if 'RHOB' in plot_vars.keys():
        if verbose > 0: print(f"computing RHOB")
        bufr_df[key] = bufr.compute_RH(bufr_df[key])

# Determine how many obs each SID has
sid_cts = {}
for key in bufr_df.keys():
    sid_cts[key] = {}
    sid_cts[key]['SID'], sid_cts[key]['n'] = np.unique(bufr_df[key].loc[bufr_df[key]['TYP'] == obtype, 'SID'], return_counts=True)

# Remove SIDs with no obs after accounting for limits
keep_idx = []
for i, sid in enumerate(sid_cts['ref']['SID']):
    if sid in sid_cts['limit']['SID']:
        keep_idx.append(i)
sid_cts['ref']['SID'] = sid_cts['ref']['SID'][keep_idx]
sid_cts['ref']['n'] = sid_cts['ref']['n'][keep_idx]

# Determine SIDs to plot by finding which SIDs had the largest reductions owing to the flight limits
plot_sid = sid_cts['ref']['SID'][np.argsort(sid_cts['ref']['n'] - sid_cts['limit']['n'])[::-1][:n_sid]]

# Create plots
for sid in plot_sid:
    print('plotting UAS %s' % sid)

    # Create figure
    fig, axes = plt.subplots(nrows=len(plot_vars), ncols=1, figsize=(6, 1+2*len(plot_vars)),
                             sharex=True)
    if len(plot_vars.keys()) == 1:
        axes = [axes]

    # Loop over each variable
    for v, ax in zip(plot_vars.keys(), axes):
        
        # Special case. Use logarithmic y-axis and set liqmix value for TYP != obtyp to be NaN
        # (this second step is necessary to prevent liqmix values from being plotted twice)
        if v == 'liqmix':
            ax.set_yscale('log')
            bufr_df['ref'].loc[bufr_df['ref']['TYP'] != obtype, 'liqmix'] = np.nan
            bufr_df['limit'].loc[bufr_df['limit']['TYP'] != obtype, 'liqmix'] = np.nan

        # Plot results
        bufr_df['ref'].loc[bufr_df['ref']['SID'] == sid].plot(x='DHR', y=v, ax=ax, kind='line',
                                                              legend=False, ylabel=v,
                                                              style=['-'], lw=1.5, c='b')
        if v in bufr_df['limit'].columns:
            bufr_df['limit'].loc[bufr_df['limit']['SID'] == sid].plot(x='DHR', y=v, ax=ax, 
                                                                      kind='line', legend=False, 
                                                                      style=['--'], lw=2, c='r')
        else:
            print(f"NOTE: {v} is not in limited dataset ('liqmix' will never be in the limited dataset)")

        ax.axhline(plot_vars[v], ls='--', c='k')
        ax.grid()

    plt.suptitle(f'Reference (blue) and Limited (red) Timeseries for {sid}', size=14)
    plt.savefig(out_fname % sid)
    plt.close()


"""
End plot_full_limited_uas_timeseries.py 
"""
