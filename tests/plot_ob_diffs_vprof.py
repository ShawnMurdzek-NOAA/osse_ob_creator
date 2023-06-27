"""
Plot Observation Differences Between Two Prepbufr CSV

This script should ideally be used to compare synthetic obs vs. real obs

shawn.s.murdzek@noaa.gov
Date Created: 14 February 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import bufr
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
import pandas as pd
import metpy.calc as mc
from metpy.units import units
import sys


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input BUFR CSV directory
bufr_dir = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_obs_csv/perfect_conv/data'
#bufr_dir = '../'

# Prepbufr file tag (e.g., 'rap', 'rap_e', 'rap_p')
bufr_tag = 'rap'
#bufr_tag = 'sample'

# Range of datetimes to use for the comparison
date_range = [dt.datetime(2022, 2, 1, 0) + dt.timedelta(hours=i) for i in range(15)]
#date_range = [dt.datetime(2022, 4, 30, 0)]

# Output file name (include %s placeholders for bufr_tag and start and end dates)
save_fname = './ob_diffs_rassda_vprof_%s_%s_%s.png'

# Observation subsets
#subsets = ['AIRCFT', 'AIRCAR']
subsets = ['RASSDA']
#subsets = ['VADWND']
#subsets = ['ADPUPA']

# Variables to plot
obs_vars = ['POB', 'ZOB', 'TOB', 'QOB', 'UOB', 'VOB', 'WSPD', 'WDIR', 'TDO']

# SIDs to exclude.
# Some aircraft have bad temperature data (e.g., T < -50 degC below 500 hPa), but TQM < 2, so
# the values are still plotted
exclude_sid = ['00000775']

# Vertical coordinate (POB or ZOB)
vcoord = 'ZOB'

# Bins for binning each variable in the vertical. First entry is left-most edge whereas all 
# subsequent entries are the right edge of the bin. Must be in descending order.
pbins = np.arange(1050, 95, -10)

# Title
title = 'synthetic obs $-$ real obs'


#---------------------------------------------------------------------------------------------------
# Plot BUFR Observation Differences
#---------------------------------------------------------------------------------------------------

# Dictionary giving quality marker fields for each variable (only plot quality markers 0-2)
qm = {'POB':'PQM',
      'QOB':'QQM',
      'TOB':'TQM',
      'ZOB':'ZQM',
      'UOB':'WQM',
      'VOB':'WQM',
      'PWO':'PWQ',
      'WSPD':'WQM',
      'WDIR':'WQM',
      'TDO':'QQM'}

# Bins for vertical plotting. First entry is left-most edge whereas all subsequent entries are the 
# right edge of the bin. POB is in mb and ZOB is in m
if vcoord == 'POB': vbins = np.arange(1050, 95, -10)
elif vcoord == 'ZOB': vbins = np.arange(0, 10000, 100)

# Open files
real_ob_dfs = []
sim_ob_dfs = []
for d in date_range:
    date_str = d.strftime('%Y%m%d%H%M')
    try:
        real_bufr_csv = bufr.bufrCSV('%s/%s.%s.real_red.prepbufr.csv' % (bufr_dir, date_str, bufr_tag))
    except FileNotFoundError:
        # Skip to next file
        continue
    real_ob_dfs.append(real_bufr_csv.df)
    sim_bufr_csv = bufr.bufrCSV('%s/%s.%s.fake.prepbufr.csv' % (bufr_dir, date_str, bufr_tag))
    sim_ob_dfs.append(sim_bufr_csv.df)
    meta = sim_bufr_csv.meta
bufr_df_real = pd.concat(real_ob_dfs, ignore_index=True)
bufr_df_sim = pd.concat(sim_ob_dfs, ignore_index=True)

# Remove excluded SIDs
for s in exclude_sid:
    bufr_df_real = bufr_df_real.loc[bufr_df_real['SID'] != s]
    bufr_df_sim = bufr_df_sim.loc[bufr_df_sim['SID'] != s]

# Only retain obs with DHR between 0 and -1 to prevent double-counting
bufr_df_real = bufr_df_real.loc[np.logical_and(bufr_df_real['DHR'] > -1, bufr_df_real['DHR'] <= 0)]
bufr_df_sim = bufr_df_sim.loc[np.logical_and(bufr_df_sim['DHR'] > -1, bufr_df_sim['DHR'] <= 0)]

bufr_df_real.reset_index(inplace=True)
bufr_df_sim.reset_index(inplace=True)

# Only retain obs from desired subset
boo = np.zeros(len(bufr_df_sim))
for s in subsets:
    boo[bufr_df_sim['subset'] == s] = 1
ind = np.where(boo)
bufr_df_sim = bufr_df_sim.loc[ind]
bufr_df_real = bufr_df_real.loc[ind]

bufr_df_sim = bufr.match_bufr_prec(bufr_df_sim)

# Compute wind speed and direction from U and V components
bufr_df_sim = bufr.compute_wspd_wdir(bufr_df_sim)
bufr_df_real = bufr.compute_wspd_wdir(bufr_df_real)

nrows = 2
ncols = int(np.ceil(len(obs_vars) / nrows))
fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(10, 6), sharey=True)
plt.subplots_adjust(left=0.1, bottom=0.08, right=0.98, top=0.88, hspace=0.4, wspace=0.1)
for i, v in enumerate(obs_vars):
    print('Plotting %s' % v)
    ax = axes[int(i/ncols), i%ncols]

    # Only plot if the quality marker is <= 2
    if v in qm.keys():
        cond = np.logical_and(bufr_df_sim[qm[v]] <= 2, bufr_df_real[qm[v]] <= 2)
        diff = bufr_df_sim.loc[cond, v] - bufr_df_real.loc[cond, v]
        if vcoord == 'POB': vert = bufr_df_sim.loc[cond, 'POB'].values
        elif vcoord == 'ZOB': vert = bufr_df_sim.loc[cond, 'ZOB'].values
    else:
        diff = bufr_df_sim[v] - bufr_df_real[v]
        if vcoord == 'POB': vert = bufr_df_sim.loc[cond, 'POB'].values
        elif vcoord == 'ZOB': vert = bufr_df_sim.loc[cond, 'ZOB'].values
    
    # Compute various percentiles for each bin along the vertical coordinate
    var_percentiles = {}
    pcts = [0, 10, 25, 50, 75, 90, 100]
    for p in pcts:
        var_percentiles[p] = np.ones(len(vbins)-1) * np.nan
    for j in range(len(vbins) - 1):
        subset = diff[np.logical_and(vert <= vbins[j:(j+2)].max(), vert > vbins[j:(j+2)].min())]
        if len(subset) > 0:
            for p in pcts:
                var_percentiles[p][j] = np.nanpercentile(subset, p)

    if vcoord == 'POB': bin_ctr = np.log10(vbins[:-1] + (0.5 * (vbins[1:] - vbins[:-1])))
    elif vcoord == 'ZOB': bin_ctr = vbins[:-1] + (0.5 * (vbins[1:] - vbins[:-1]))
    ax.plot(var_percentiles[50], bin_ctr, 'b-', lw=2)
    ax.fill_betweenx(bin_ctr, var_percentiles[25], var_percentiles[75], color='b', alpha=0.4)
    ax.fill_betweenx(bin_ctr, var_percentiles[10], var_percentiles[90], color='b', alpha=0.2)
    ax.plot(var_percentiles[0], bin_ctr, 'b-', lw=0.75)
    ax.plot(var_percentiles[100], bin_ctr, 'b-', lw=0.75)
    ax.axvline(0, c='k', lw='1')
    ax.grid()

    if vcoord == 'POB':
        ax.set_ylim([np.log10(pbins.max()), np.log10(pbins.min())])
        ticks = np.array([1000, 850, 700, 500, 400, 300, 200, 100])
        ax.set_yticks(np.log10(ticks))
        ax.set_yticklabels(ticks)
    elif vcoord == 'ZOB':
        ax.set_ylim([vbins.min(), vbins.max()])
    ax.set_title('%s ($n$ = %d)' % (v, len(diff)), size=12)
    ax.set_xlabel('%s' % meta[v]['units'], size=12)

for i in range(2):
    axes[i, 0].set_ylabel('%s (%s)' % (vcoord, meta[vcoord]['units']), size=12)

plt.suptitle(title, size=18)
plt.savefig(save_fname % (bufr_tag, date_range[0].strftime('%Y%m%d%H'), 
                          date_range[-1].strftime('%Y%m%d%H')))
plt.close()


"""
End plot_ob_diffs_vprof.py  
"""
