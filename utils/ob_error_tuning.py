"""
Determine Error Variance Needed for Conventional Observation Error Tuning

shawn.s.murdzek@noaa.gov
Date Created: 18 May 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import xarray as xr
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import pyDA_utils.gsi_fcts as gsi


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Paths to NCO_dirs folder for real-data and OSSE RRFS runs
path_real = '/work2/noaa/wrfruc/murdzek/RRFS_OSSE/real_red_data/winter/NCO_dirs'
path_osse = '/work2/noaa/wrfruc/murdzek/RRFS_OSSE/syn_data/winter_perfect/NCO_dirs'

dates = [dt.datetime(2022, 2, 1, 9) + dt.timedelta(hours=i) for i in range(4*24)]

initial_err_spread_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/errtable.perfect'
output_err_spread_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/1st_iter_assim_only/tmp/errtable.1st_iter.4day'

initial_err_mean_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/errtable_mean.perfect'
output_err_mean_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/1st_iter_assim_only/tmp/errtable_mean.1st_iter.4day'

# Observation types (set to None for all observation types)
ob_types = [181]

# 2D obs that use all obs for error tuning (rather than breaking down obs into different pressure 
# bins). These obs do not necessarily need to be 2D, but the option is primarily recommended for
# 2D obs. For this option to work properly, all values in the initial errtables must be the same
# for a given ob type / variable (in other words, the errtable values must be pressure independent)
ob_types_2d = [153, 180, 181, 182, 183, 187, 188, 280, 281, 282, 284, 287, 288]

# Option to use all obs or only those obs that are assimilated
# If use_assim_only = False, then only obs with Prep_QC_Mark < 3 are used
use_assim_only = True

# Option to use another errtable file as the upper bound for the error veriance tuning
use_upper_bound = True
upper_bound_spread_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/errtable.rrfs'

# Minimum number of observations required for error tuning
min_obs = 50

# Option to create plot with vertical profile of observation error statistics
make_plot = True
plot_fname = '/work2/noaa/wrfruc/murdzek/real_obs/errtables/1st_iter_assim_only/tmp/err_stat_vprof_1iter_4day.pdf'


#---------------------------------------------------------------------------------------------------
# Compare O-B Variances For Real and Simulated Obs
#---------------------------------------------------------------------------------------------------

# Extract data
start = dt.datetime.now()
print('start = %s' % start.strftime('%Y%m%d %H:%M:%S'))
print('reading GSI diag files...')
print()
print('Dates:')
for d in dates:
    print(d)
print()
real_omb_fnames = []
osse_omb_fnames = []
for v in ['t', 'q', 'uv', 'pw', 'ps']:
    for d in dates:
        real_omb_fnames.append('%s/ptmp/prod/rrfs.%s/%s/diag_conv_%s_ges.%s.nc4' % 
                               (path_real, d.strftime('%Y%m%d'), d.strftime('%H'), v, d.strftime('%Y%m%d%H')))
        osse_omb_fnames.append('%s/ptmp/prod/rrfs.%s/%s/diag_conv_%s_ges.%s.nc4' % 
                               (path_osse, d.strftime('%Y%m%d'), d.strftime('%H'), v, d.strftime('%Y%m%d%H')))
omf_df = {}
omf_df['real'] = gsi.read_diag(real_omb_fnames)
omf_df['osse'] = gsi.read_diag(osse_omb_fnames)

# Only retain obs with Analysis_Use_Flag = 1 if use_assim_only = True
for run in ['real', 'osse']:
    if use_assim_only:
        omf_df[run] = omf_df[run].loc[omf_df[run]['Analysis_Use_Flag'] == 1].copy()
    omf_df[run] = omf_df[run].loc[omf_df[run]['Prep_QC_Mark'] < 3].copy()

# Read initial errtable
init_spread_errtable = gsi.read_errtable(initial_err_spread_fname)
new_spread_errtable = init_spread_errtable.copy()
init_mean_errtable = gsi.read_errtable(initial_err_mean_fname)
new_mean_errtable = init_mean_errtable.copy()

# Read upper bound errtable
if use_upper_bound:
    upper_spread_errtable = gsi.read_errtable(upper_bound_spread_fname)

# Compute obs errors and necessary adjustments
if ob_types == None:
    ob_types = np.unique(omf_df['osse']['Observation_Type'])

# Create output PDF
if make_plot:
    pdf = PdfPages(plot_fname)

for typ in ob_types:

    if make_plot:
        fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(12, 8), sharey=True)
        plt.subplots_adjust(left=0.07, bottom=0.08, right=0.98, top=0.92)

    for j, (v, err) in enumerate(zip(['t', 'q', 'uv', 'pw', 'ps'], 
                                     ['Terr', 'RHerr', 'UVerr', 'PWerr', 'PSerr'])):
        print()
        print('computing errors for type = %d, var = %s' % (typ, v))
        prs_ctr = init_spread_errtable[typ]['prs'].values
        prs = np.zeros(len(prs_ctr))
        prs[1:] = 0.5 * (prs_ctr[:-1] + prs_ctr[1:])
        prs[0] = prs_ctr[0] + 0.5 * (prs_ctr[1] - prs_ctr[2])

        ob_err_stat = {}
        subset = {}
        for run in ['real', 'osse']:
            ob_err_stat[run] = {}
            for stat in ['mean', 'spread', 'n']:
                ob_err_stat[run][stat] = np.zeros(len(prs) - 1) * np.nan
            # Create subset for ob type and variable
            subset[run] = omf_df[run].loc[(omf_df[run]['Observation_Type'] == typ) & 
                                          (omf_df[run]['var'] == v)]
       
        # Skip to next typ/var combo if too few obs
        if len(subset['osse']) < min_obs:
            continue

        for k in range(len(prs) - 1):

            prs_subset = {}
            for run in ['real', 'osse']:
                prs_subset[run] = subset[run].loc[(subset[run]['Pressure'] < prs[k]) &
                                                  (subset[run]['Pressure'] >= prs[k+1])]

            if len(prs_subset['osse']) == 0:
                continue 
            elif (len(prs_subset['osse']) < min_obs) or (typ in ob_types_2d):
                # Use the variance computed using all obs in this case
                 for run in ['real', 'osse']:
                    prs_subset[run] = subset[run].copy()

            if len(prs_subset['osse']) < min_obs:
                continue

            for run in ['real', 'osse']:
                for stat, stat_fct in zip(['mean', 'spread', 'n'], [np.mean, np.var, len]):
                    if v == 'uv':
                        ob_err_stat[run][stat][k] = stat_fct(np.concatenate([prs_subset[run]['u_Obs_Minus_Forecast_adjusted'].values,
                                                                             prs_subset[run]['v_Obs_Minus_Forecast_adjusted'].values]))
                    elif v == 'q':
                        obs_q = prs_subset[run]['Observation'].values
                        background_q = obs_q - prs_subset[run]['Obs_Minus_Forecast_adjusted'].values
                        qs = prs_subset[run]['Forecast_Saturation_Spec_Hum'].values
                        omf_q = 10 * ((obs_q / qs) - (background_q / qs))
                        ob_err_stat[run][stat][k] = stat_fct(omf_q)
                    else:
                        ob_err_stat[run][stat][k] = stat_fct(prs_subset[run]['Obs_Minus_Forecast_adjusted'])

            # NOTE: The measure of spread in the error table is the standard deviation, but the 
            # variance is needed for tuning. Thus, we square the error table spread and take the 
            # square root of the result after tuning
            new_spread_errtable[typ][err][k] = np.sqrt(max(0, init_spread_errtable[typ][err][k]**2 + 
                                                           (ob_err_stat['real']['spread'][k] - ob_err_stat['osse']['spread'][k])))
            new_mean_errtable[typ][err][k] = (init_mean_errtable[typ][err][k] + 
                                              (ob_err_stat['real']['mean'][k] - ob_err_stat['osse']['mean'][k]))

            if use_upper_bound:
                new_spread_errtable[typ][err][k] = min(new_spread_errtable[typ][err][k], 
                                                       upper_spread_errtable[typ][err][k])

            print(('prs = %6.1f | Real n, mean, var = %6d, %10.3e, %10.3e | ' +
                   'OSSE n, mean, var = %6d, %10.3e, %10.3e | ' +
                   'Diff mean = %10.3e | New OSSE std = %10.3e') % 
                  (prs_ctr[k], ob_err_stat['real']['n'][k], ob_err_stat['real']['mean'][k], ob_err_stat['real']['spread'][k], 
                   ob_err_stat['osse']['n'][k], ob_err_stat['osse']['mean'][k], ob_err_stat['osse']['spread'][k], 
                   new_mean_errtable[typ][err][k], new_spread_errtable[typ][err][k]))

            # Only need one iteration over k if observation is 2D
            if typ in ob_types_2d:
                new_spread_errtable[typ][err][:] = new_spread_errtable[typ][err][k]
                new_mean_errtable[typ][err][:] = new_mean_errtable[typ][err][k]
                for run in ['real', 'osse']:
                    for stat in ['spread', 'mean']:
                        ob_err_stat[run][stat][:] = ob_err_stat[run][stat][k]
                break

        if make_plot:
            ax = axes[int(j/3), j%3]
            for run, c in zip(['real', 'osse'], ['k', 'r']):
                ax.plot(ob_err_stat[run]['spread'], prs_ctr[:-1], c=c, ls='--', label=run)
                ax.plot(ob_err_stat[run]['mean'], prs_ctr[:-1], c=c, ls='-')
            ax.legend()
            ax.grid()
            ax.set_yscale('log')
            ax.set_ylim([1100, 10])
            ax.set_xlabel('%s' % v, size=14)

    if make_plot:
        plt.suptitle('Type = %d O$-$B (mean: solid, variance: dashed)' % typ, size=20)
        for j in range(2):
            axes[j, 0].set_ylabel('pressure (mb)', size=14)
        pdf.savefig(fig)
        plt.close(fig)

if make_plot:
    pdf.close()

print('saving new errtables')
gsi.write_errtable(output_err_spread_fname, new_spread_errtable)
gsi.write_errtable(output_err_mean_fname, new_mean_errtable)

print('Done (elapsed time = %s s)' % (dt.datetime.now() - start).total_seconds())

"""
End conv_ob_err_tuning.py 
"""
