"""
Plot Observation Differences Between Two Prepbufr CSV

This script should ideally be used to compare synthetic obs vs. real obs

Optional passed arguments:
    argv[1] = bufr_tag
    argv[2] = save_fname
    argv[3] = observation subsets to use
    argv[4] = domain

shawn.s.murdzek@noaa.gov
Date Created: 7 February 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import bufr
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import datetime as dt
import pandas as pd
import xarray as xr
import metpy.calc as mc
from metpy.units import units
import sys


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input BUFR CSV directory
bufr_dir = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_obs_csv/realistic/gsi_err_autoreg_0p5'

# Prepbufr file tag (e.g., 'rap', 'rap_e', 'rap_p')
bufr_tag = 'rap'

# Range of datetimes to use for the comparison
date_range = [dt.datetime(2022, 2, 1, 9) + dt.timedelta(hours=i) for i in range(4)]

# Dataset names
name1 = 'Sim Obs'
name2 = 'Real Obs'

# Output file name (include %s placeholders for domain, bufr_tag, variable name, and start and end 
# of date range)
save_fname = './ob_diffs_%s_%s_%s_%s_%s.png'

# Observation subsets
subsets = ['SFCSHP', 'ADPSFC', 'MSONET', 'GPSIPW']
subsets = ['MSONET']

# Variables to plot
#obs_vars = ['WSPD', 'WDIR', 'ELV', 'POB', 'TOB', 'QOB', 'UOB', 'VOB', 'ZOB', 'PWO']
obs_vars = ['QOB', 'POB']

# Domain to examine ('all', 'easternUS', 'westernUS')
domain = 'all'

# Option to only plot a certain prepBUFR ob type (set to None to not use this option)
ob_type = 188

# Option to only plot obs from stations that have Analysis_Use_Flag = 1
use_assim_sites = False
gsi_diag_fname = '/work2/noaa/wrfruc/murdzek/sp22_retro_diag/07/diag_conv_uv_anl.2022043007.nc4'

# Option to set simulated wind speeds below a certain threshold to 0
remove_small_sim_wspd = False
sim_wspd_thres = 4.

# Option to only compare winds if the real wind speed exceeds a threshold
only_compare_strong_winds = False
real_wspd_thres = 4.

# Option to used passed arguments
if len(sys.argv) > 1:
    bufr_tag = str(sys.argv[1])
    save_fname = str(sys.argv[2])
    if sys.argv[3] == 'all':
        subsets = ['SFCSHP', 'ADPSFC', 'MSONET', 'GPSIPW']
    else:
        subsets = [str(sys.argv[3])]
    domain = str(sys.argv[4])


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
      'WDIR':'WQM',
      'WSPD':'WQM'}

# Load borders
borders = cfeature.NaturalEarthFeature(category='cultural',
                                       scale='50m',
                                       facecolor='none',
                                       name='admin_1_states_provinces')

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
print('Done opening files')

# Only retain obs with DHR between 0 and -1 to prevent double-counting
# UNLESS ob is from GPSIPW, in which case keep all obs b/c DHR is always -1 for these obs
bufr_df_real = bufr_df_real.loc[np.logical_or(np.logical_and(bufr_df_real['DHR'] > -1, bufr_df_real['DHR'] <= 0),
                                              bufr_df_real['subset'] == 'GPSIPW')]
bufr_df_sim = bufr_df_sim.loc[np.logical_or(np.logical_and(bufr_df_sim['DHR'] > -1, bufr_df_sim['DHR'] <= 0),
                                            bufr_df_sim['subset'] == 'GPSIPW')]

bufr_df_real.reset_index(inplace=True, drop=True)
bufr_df_sim.reset_index(inplace=True, drop=True)

# Apply rounding so precision in simulated obs matches real obs
bufr_df_sim = bufr.match_bufr_prec(bufr_df_sim)
print('Done adjusting precision')

# Only retain obs from desired subset
boo = np.zeros(len(bufr_df_sim))
for s in subsets:
    boo[bufr_df_sim['subset'] == s] = 1
ind = np.where(boo)
bufr_df_sim = bufr_df_sim.loc[ind]
bufr_df_real = bufr_df_real.loc[ind]

# Only retain obs from a certain observation type if desired
if ob_type != None:
    bufr_df_sim = bufr_df_sim.loc[bufr_df_sim['TYP'] == ob_type]
    bufr_df_real = bufr_df_real.loc[bufr_df_real['TYP'] == ob_type]

# Only retain obs from desired domain
if domain == 'easternUS':
    bufr_df_real = bufr_df_real.loc[bufr_df_real['XOB'] >= 260]
    bufr_df_sim = bufr_df_sim.loc[bufr_df_sim['XOB'] >= 260]
elif domain == 'westernUS':
    bufr_df_real = bufr_df_real.loc[bufr_df_real['XOB'] < 260]
    bufr_df_sim = bufr_df_sim.loc[bufr_df_sim['XOB'] < 260]

# Only retain obs with Analysis_Use_Flag = 1
if use_assim_sites:
    bufr_df_real.reset_index(inplace=True, drop=True)
    bufr_df_sim.reset_index(inplace=True, drop=True)
    gsi_diag = xr.open_dataset(gsi_diag_fname).to_dataframe()
    assim_diag = gsi_diag.loc[gsi_diag['Analysis_Use_Flag'] == 1]
    all_sites = bufr_df_sim['SID'].values
    all_times = bufr_df_sim['DHR'].values
    use_idx = np.zeros(len(all_sites), dtype=bool)
    for i, (s, t) in enumerate(zip(assim_diag['Station_ID'].values, assim_diag['Time'].values)):
        s = s.strip().decode('utf-8')
        use_idx[np.logical_and(all_sites == s, np.isclose(t, all_times))] = True
    bufr_df_real = bufr_df_real.loc[use_idx]
    bufr_df_sim = bufr_df_sim.loc[use_idx]

bufr_df_real.reset_index(inplace=True, drop=True)
bufr_df_sim.reset_index(inplace=True, drop=True)
print('Done subsetting obs')

# Compute wind speed and direction from U and V components
bufr_df_sim = bufr.compute_wspd_wdir(bufr_df_sim)
bufr_df_real = bufr.compute_wspd_wdir(bufr_df_real)
print('Done computing WSPD and WDIR')

# Set sim wind obs to 0 if WPSD < sim_wspd_thres
if remove_small_sim_wspd:
    cond = bufr_df_sim['WSPD'] < sim_wspd_thres
    for f in ['WSPD', 'WDIR', 'UOB', 'VOB']:
        bufr_df_sim.loc[cond, f] = 0

# Only compare winds if real WSPD >= real_wspd_thres
if only_compare_strong_winds:
    cond = bufr_df_real['WSPD'] < real_wspd_thres
    bufr_df_sim.loc[cond, 'WQM'] = 3
    bufr_df_real.loc[cond, 'WQM'] = 3

for v in obs_vars:
    print('Plotting %s' % v)
    fig = plt.figure(figsize=(12, 8))
    plt.subplots_adjust(left=0.08, bottom=0.08, right=0.98, top=0.95, wspace=0.3)

    # Only plot if the quality marker is <= 2
    if v in qm.keys():
        cond = np.logical_and(bufr_df_sim[qm[v]] <= 2, bufr_df_real[qm[v]] <= 2)
        field1 = bufr_df_sim.loc[cond, v]
        field2 = bufr_df_real.loc[cond, v]
        diff = (field1 - field2).values
        lat = bufr_df_sim.loc[cond, 'YOB'].values
        lon = bufr_df_sim.loc[cond, 'XOB'].values
    else:
        field1 = bufr_df_sim[v]
        field2 = bufr_df_real[v]
        diff = (field1 - field2).values
        lat = bufr_df_sim['YOB'].values
        lon = bufr_df_sim['XOB'].values

    # Plot actual values
    maxval = max(np.percentile(field1, 99.75), np.percentile(field2, 99.75))
    minval = min(np.percentile(field1, 0.25), np.percentile(field2, 0.25))
    ax1list = []
    ax2list = []
    max_hist_val = 0
    for j, (f, ttl) in enumerate(zip([field1, field2], [name1, name2])):
        ax1 = fig.add_subplot(2, 3, j+1, projection=ccrs.PlateCarree())
        cax = ax1.scatter(lon, lat, s=2, c=f, cmap='plasma', vmin=minval, vmax=maxval,
                          transform=ccrs.PlateCarree())
        ax1.coastlines('50m')
        ax1.add_feature(borders, linewidth=0.5, edgecolor='k')
        ax1.set_xlim([-135, -50])
        ax1.set_ylim([20, 55])
        ax1.set_title(ttl, size=18)
        ax1list.append(ax1)

        ax2 = fig.add_subplot(2, 3, j+4)
        hist_out = ax2.hist(f, bins=40, range=(minval, maxval))
        ax2.set_xlabel('%s (%s)' % (v, meta[v]['units']), size=12)
        ax2.set_ylabel('counts', size=12)
        ax2.grid()
        ax2list.append(ax2)
        if hist_out[0].max() > max_hist_val:
            max_hist_val = hist_out[0].max()

    cbar = plt.colorbar(cax, ax=ax1list, orientation='horizontal')
    cbar.set_label('%s (%s)' % (v, meta[v]['units']), size=12)
    for j in range(2):
        ax2list[j].set_ylim(0, max_hist_val + (0.05*max_hist_val))

    # Plot differences
    dlim = np.nanpercentile(np.abs(diff), 99)
    ax1 = fig.add_subplot(2, 3, 3, projection=ccrs.PlateCarree())
    sort_idx = np.argsort(np.abs(diff))
    cax = ax1.scatter(lon[sort_idx], lat[sort_idx], s=2, c=diff[sort_idx], cmap='bwr', 
                      vmin=-dlim, vmax=dlim, transform=ccrs.PlateCarree())
    cbar = plt.colorbar(cax, ax=ax1, orientation='horizontal')
    cbar.set_label('%s diffs (%s)' % (v, meta[v]['units']), size=14)

    ax1.coastlines('50m')
    ax1.add_feature(borders, linewidth=0.5, edgecolor='k')
    ax1.set_xlim([-135, -50])
    ax1.set_ylim([20, 55])
    ax1.set_title('%s $-$ %s' % (name1, name2), size=18)
        
    ax2 = fig.add_subplot(2, 3, 6)
    ax2.hist(diff, bins=40, range=(-dlim, dlim))
    ax2.set_xlabel('%s diff (%s)' % (v, meta[v]['units']), size=12)
    ax2.set_ylabel('counts', size=12)
    ax2.grid()

    # Include some statistics
    plt.suptitle('Mean Diff = %.3e, Std Dev = %.3e, RMSD = %.3e, n = %d' % 
                 (np.mean(diff), np.std(diff), np.sqrt(np.mean(diff**2)), 
                  len(diff) - np.isnan(diff).sum()), size=16)

    plt.savefig(save_fname % (domain, bufr_tag, v, date_range[0].strftime('%Y%m%d%H'), 
                              date_range[-1].strftime('%Y%m%d%H')))
    plt.close()


"""
End plot_ob_diffs_2d.py  
"""
