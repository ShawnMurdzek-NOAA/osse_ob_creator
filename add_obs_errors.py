"""
Add Observation Errors to a BUFR CSV File

Also include some code to plot histograms of the difference between the perfect obs and obs with 
added errors. These plots provide a sanity check to ensure that the distribution of the differences
is approximately Gaussian with a standard deviation close to the prescribed errors.

shawn.s.murdzek@noaa.gov
Date Created: 15 February 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import glob

import metpy.calc as mc
from metpy.units import units

import meteo_util as mu
import gsi_fcts as gf
import bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# For debugging
in_fnames = ['/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202205030000.rap.prepbufr.csv']
out_fnames = ['./tmp.prepbufr.csv']

#in_dir = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_obs_csv/perfect'
#out_dir = '/work2/noaa/wrfruc/murdzek/nature_run_winter/synthetic_obs_csv/realistic/gsi_err_autoreg_0p5'

#fnames = glob.glob('%s/*.fake.prepbufr.csv' % in_dir)
#for i in range(len(fnames)):
#    fnames[i] = fnames[i].split('/')[-1]

#in_fnames = ['%s/%s' % (in_dir, f) for f in fnames]
#out_fnames = ['%s/%s' % (out_dir, f) for f in fnames]

errtable = '/work2/noaa/wrfruc/murdzek/real_obs/errtable.rrfs'

# Observation types to use autocorrelated errors for
autocor_POB_obs = [120, 220]
autocor_DHR_obs = [130, 131, 133, 134, 135, 230, 231, 233, 234, 235]
autocor_ZOB_partition_DHR_obs = [126, 223, 224, 227, 228, 229]
auto_reg_parm = 0.5

# Verbose output when adding obs errors?
verbose = False

# Option to perform dewpoint check (i.e., is the dewpoint consistent with the errors added to TOB 
# and QOB?)
dewpt_check = True

# Option to check obs errors by plotting differences between obs w/ and w/out errors (plots will
# be made for the last BUFR CSV file)
plot_diff_hist = True

# Option to check autocorrelated obs errors by plotting timeseries or vertical profiles of errors
# from a single station (plots will be made for the last BUFR CSV file)
check_autocorr_err = True
timeseries_ob_types = [133,           135,           233,           235]
timeseries_stations = ['3OXWUWJA', 'CNJCA111', '3OXWUWJA', 'CNJCA111']
vprof_ob_types = [120,     120,     220,     220]
vprof_stations = ['72520', '72476', '72520', '72476']

# Option to check autocorrelated obs errors with DHR partitioning by creating 2D plots of errors
# from a single station (plots will be made for the last BUFR CSV file)
check_autocorr_partition_err = True
autocorr_partition_ob_types = [126, 224, 227]
autocorr_partition_stations = ['SLDUT', 'KFDX', 'CFDUT']


#---------------------------------------------------------------------------------------------------
# Add Observation Errors
#---------------------------------------------------------------------------------------------------

start = dt.datetime.now()
print('start time = %s' % start.strftime('%H:%M:%S'))

for i, (in_name, out_name) in enumerate(zip(in_fnames, out_fnames)):

    print('-------------------------------------------------')
    print('file %d of %d' % (i+1, len(in_fnames)))
    cycle_start = dt.datetime.now()

    in_csv = bufr.bufrCSV(in_name)

    remaining_obs = []
    for o in np.int32(in_csv.df['TYP'].unique()):
        if ((o not in autocor_POB_obs) and (o not in autocor_DHR_obs) and 
            (o not in autocor_ZOB_partition_DHR_obs)):
            remaining_obs.append(o)

    #in_csv.df = in_csv.df.loc[in_csv.df['TYP'] == 192]
    #in_csv.df = in_csv.df.iloc[:10]
    #in_csv.df.reset_index(inplace=True, drop=True)
    #out_df = bufr.add_obs_err(in_csv.df, errtable, ob_typ=[192], verbose=verbose)

    # Add random errors
    out_df = bufr.add_obs_err(in_csv.df, errtable, ob_typ=autocor_POB_obs, correlated='POB', 
                              auto_reg_parm=auto_reg_parm, min_d=10., verbose=verbose)
    out_df = bufr.add_obs_err(out_df, errtable, ob_typ=autocor_DHR_obs, correlated='DHR', 
                              auto_reg_parm=auto_reg_parm, verbose=verbose)
    out_df = bufr.add_obs_err(out_df, errtable, ob_typ=autocor_ZOB_partition_DHR_obs, 
                              correlated='DHR', partition_dim='DHR',
                              auto_reg_parm=auto_reg_parm, min_d=50., verbose=verbose)
    out_df = bufr.add_obs_err(out_df, errtable, ob_typ=remaining_obs, verbose=verbose)

    # Make precision match what is typically found in a prepBUFR file
    out_df = bufr.match_bufr_prec(out_df)

    bufr.df_to_csv(out_df, out_name)

    print('time = %.2f s' % (dt.datetime.now() - cycle_start).total_seconds())

end = dt.datetime.now()
print('elapsed time = %s s' % (end - start).total_seconds()) 


#---------------------------------------------------------------------------------------------------
# Dewpoint Check
#---------------------------------------------------------------------------------------------------

out_df = bufr.compute_RH(out_df)
out_df = bufr.compute_Tsens(out_df)
Td_from_RH = mc.dewpoint_from_relative_humidity(out_df['Tsens'].values * units.degC, 
                                                out_df['RHOB'].values * 0.01).to('degC').magnitude
Td_rmse = np.sqrt(np.nanmean((Td_from_RH - out_df['TDO'])**2))

print()
print('Td RMSE (TDO vs. Td computed w/ RH) = %.3e degC' % Td_rmse)
print()


#---------------------------------------------------------------------------------------------------
# Plot Histograms of Differences
#---------------------------------------------------------------------------------------------------

obs_err_names = {'TOB':'Terr', 'RHOB':'RHerr', 'UOB':'UVerr', 'VOB':'UVerr', 'PRSS':'PSerr', 
                'PWO':'PWerr', 'PMO':'PSerr'}

if plot_diff_hist:

    # Compute RH
    in_csv.df = bufr.compute_RH(in_csv.df)
    out_df = bufr.compute_RH(out_df)
    in_csv.meta['RHOB'] = {}
    in_csv.meta['RHOB']['units'] = '%'

    # Read in error tables
    etable = gf.read_errtable(errtable)
    eprs = etable[100]['prs'].values
    for e in etable.keys():
        etable[e]['RHerr'] = etable[e]['RHerr'] * 10
    typ = out_df['TYP'].unique()

    for t in typ:

        tind = np.where(out_df['TYP'] == t)[0]
        obs = []
        errs = []
        for o in obs_err_names.keys():
            if not np.all(np.isnan(in_csv.df.loc[tind, o])):
                obs.append(o)
                errs.append(obs_err_names[o])

        # Check to see if errors vary with pressure
        vprof = False
        for e in errs:
            if ((len(np.unique(etable[t][e])) > 2) and 
                (np.sum(np.isnan(etable[t][e])) < (len(etable[t][e])-1))):
                vprof = True
                continue

        # Configure plot
        if vprof:
            fig, axes = plt.subplots(nrows=2, ncols=len(obs), figsize=(2+(4*len(obs)), 8), sharey=True)
            plt.subplots_adjust(left=0.08, bottom=0.08, right=0.98, top=0.92, hspace=0.35)
        else:
            fig, axes = plt.subplots(nrows=1, ncols=len(obs), figsize=(2+(4*len(obs)), 6))
            plt.subplots_adjust(left=0.08, bottom=0.08, right=0.98, top=0.9)

        for j, (o, e) in enumerate(zip(obs, errs)):

            # Compute difference before and after adding obs errors
            diff = out_df.loc[tind, o].values - in_csv.df.loc[tind, o].values
            prs = out_df.loc[tind, 'POB'].values
            idiff = np.where(np.logical_not(np.isnan(diff)))[0]
            if len(idiff) > 0:
                diff = diff[idiff]
                prs = prs[idiff]
            else:
                continue

            if vprof:

                # Create histogram that depends on pressure as well as vertical profiles of standard
                # deviations
                cts = np.zeros([len(eprs)-1, 21])
                stdev = np.zeros(len(eprs)-1)
                num = np.zeros(len(eprs)-1)
                maxval = np.amax(np.abs(diff))
                bins = np.linspace(-maxval - (0.25*maxval), maxval + (0.25*maxval), 22)
                eprs_plt = (eprs[1:] + eprs[:-1]) / 2.
                for k in range(len(eprs)-1):
                    idx = np.where(np.logical_and(prs <= eprs[k], prs > eprs[k+1]))[0]
                    if len(idx) == 0:
                        continue  
                    cts[k, :] = np.histogram(diff[idx], bins=bins)[0]
                    cts[k, np.isclose(cts[k, :], 0)] = np.nan
                    stdev[k] = np.std(diff[idx])
                    num[k] = len(idx)

                # Top plot: Histogram
                if len(obs) > 1:
                    ax1 = axes[0, j] 
                else:
                    ax1 = axes[0]    
                x2d, y2d = np.meshgrid((bins[1:] + bins[:-1]) / 2., eprs_plt)
                cax = ax1.contourf(x2d, y2d, cts)
                cbar = plt.colorbar(cax, ax=ax1)
                cbar.set_label('counts') 
                ax1.set_xlabel('%s (%s)' % (o, in_csv.meta[o]['units']), size=12)
                if j == 0:  
                    ax1.set_ylabel('pressure (%s)' % in_csv.meta['POB']['units'], size=12)
                ax1.set_ylim([eprs.max(), eprs.min()])
                ax1.grid()

                # Bottom plot: Vertical profile of standard deviations
                if len(obs) > 1:
                    ax2 = axes[1, j] 
                else:
                    ax2 = axes[1]    
                ax21 = ax2.twiny()
                ax2.plot(stdev, eprs_plt, 'b-', label='actual')
                ax2.plot(etable[t][e], eprs, 'r-', label='errtable')
                ax21.plot(num, eprs_plt, 'k--', label='counts')
                ax2.set_xlabel('std %s (%s)' % (o, in_csv.meta[o]['units']), size=12)
                ax21.set_xlabel('data counts', size=12)
                if j == 0:  
                    ax2.set_ylabel('pressure (%s)' % in_csv.meta['POB']['units'], size=12)
                ax2.set_ylim([eprs.max(), eprs.min()])
                ax2.legend()
                ax2.grid()

            else:

                # Plot regular histogram
                ax = axes[j]
                ax.hist(diff)
                ax.set_title('%s (std = %.3e, estd = %.3e)' % (o, np.std(diff), etable[t].loc[0, e]))
                ax.set_xlabel('%s (%s)' % (o, in_csv.meta[o]['units']), size=12)
                ax.set_ylabel('counts', size=12)
                ax.grid()

        plt.suptitle('Type = %d Difference Histograms' % t, size=16)
        plt.savefig('diff_hist_%d.png' % t)
        plt.close()


#---------------------------------------------------------------------------------------------------
# Plot Timeseries and Vertical Profiles from a Single Station
#---------------------------------------------------------------------------------------------------

if check_autocorr_err:

    # Compute RH
    in_csv.df = bufr.compute_RH(in_csv.df)
    out_df = bufr.compute_RH(out_df)
    in_csv.meta['RHOB'] = {}
    in_csv.meta['RHOB']['units'] = '%'

    # Create plots for vertical profiles
    for typ, sid in zip(vprof_ob_types, vprof_stations):
        
        if typ == 153:
            obs = ['PWO']
        elif typ < 200:
            obs = ['TOB', 'RHOB']
        else:
            obs = ['UOB', 'VOB']

        # Configure plot
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 8), sharey=True)
        plt.subplots_adjust(left=0.08, bottom=0.08, right=0.98, top=0.92, hspace=0.35)

        tind = np.where(np.logical_and(out_df['TYP'] == typ, out_df['SID'] == sid))[0]

        for j, o in enumerate(obs):

            # Compute difference before and after adding obs errors
            diff = out_df.loc[tind, o].values - in_csv.df.loc[tind, o].values
            prs = out_df.loc[tind, 'POB'].values
            idiff = np.where(np.logical_not(np.isnan(diff)))[0]
            if len(idiff) > 0:
                diff = diff[idiff]
                prs = prs[idiff]
            else:
                continue

            # Plot differences
            axes[j].plot(diff, prs, lw=2)
            
            axes[j].grid()
            axes[j].axvline(0, c='k')
            axes[j].set_ylim([1100, 0])
            axes[j].set_xlabel('%s (%s)' % (o, in_csv.meta[o]['units']), size=12)
            axes[j].set_title('autocorrelation = %.3f' % np.corrcoef(diff[:-1], diff[1:])[0, 1], size=14)

        axes[0].set_ylabel('pressure (%s)' % in_csv.meta['POB']['units'], size=12)
        plt.suptitle('Type = %d, SID = %s Differences' % (typ, sid), size=16)
        plt.savefig('diff_autocorr_vprof_%d_%s.png' % (typ, sid))
        plt.close()

    # Create plots for timeseries
    for typ, sid in zip(timeseries_ob_types, timeseries_stations):
        
        if typ == 153:
            obs = ['PWO']
        elif typ < 200:
            obs = ['TOB', 'RHOB']
        else:
            obs = ['UOB', 'VOB']

        # Configure plot
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 6), sharex=True)
        plt.subplots_adjust(left=0.08, bottom=0.08, right=0.98, top=0.88)

        tind = np.where(np.logical_and(out_df['TYP'] == typ, out_df['SID'] == sid))[0]

        for j, o in enumerate(obs):

            # Compute difference before and after adding obs errors
            diff = out_df.loc[tind, o].values - in_csv.df.loc[tind, o].values
            dhr = out_df.loc[tind, 'DHR'].values
            idiff = np.where(np.logical_not(np.isnan(diff)))[0]
            if len(idiff) > 0:
                diff = diff[idiff]
                dhr = dhr[idiff]
            else:
                continue

            # Sort arrays by time (DHR)
            sort_idx = np.argsort(dhr)
            dhr = dhr[sort_idx]
            diff = diff[sort_idx]

            axes[j].plot(dhr, diff, lw=2)
            
            axes[j].grid()
            axes[j].axvline(0, c='k')
            axes[j].set_xlabel('time (hr)', size=12)
            axes[j].set_ylabel('%s (%s)' % (o, in_csv.meta[o]['units']), size=12)
            axes[j].set_title('autocorrelation = %.3f' % np.corrcoef(diff[:-1], diff[1:])[0, 1], size=14)

        plt.suptitle('Type = %d, SID = %s Differences' % (typ, sid), size=16)
        plt.savefig('diff_autocorr_time_%d_%s.png' % (typ, sid))
        plt.close()


#---------------------------------------------------------------------------------------------------
# Plot Errors From Stations With Autocorrelation and Partitioning with DHR
#---------------------------------------------------------------------------------------------------

if check_autocorr_partition_err:

    # Compute RH
    in_csv.df = bufr.compute_RH(in_csv.df)
    out_df = bufr.compute_RH(out_df)
    in_csv.meta['RHOB'] = {}
    in_csv.meta['RHOB']['units'] = '%'

    # Create plots for vertical profiles
    for typ, sid in zip(autocorr_partition_ob_types, autocorr_partition_stations):
        
        if typ == 153:
            obs = ['PWO']
        elif typ < 200:
            obs = ['TOB', 'RHOB']
        else:
            obs = ['UOB', 'VOB']

        # Configure plot
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 8), sharey=True)
        plt.subplots_adjust(left=0.08, bottom=0.08, right=0.98, top=0.92, hspace=0.35)

        tind = np.where(np.logical_and(out_df['TYP'] == typ, out_df['SID'] == sid))[0]

        for j, o in enumerate(obs):

            # Compute difference before and after adding obs errors
            diff = out_df.loc[tind, o].values - in_csv.df.loc[tind, o].values
            zob = out_df.loc[tind, 'ZOB'].values
            dhr = out_df.loc[tind, 'DHR'].values
            idiff = np.where(np.logical_not(np.isnan(diff)))[0]
            if len(idiff) > 0:
                diff = diff[idiff]
                zob = zob[idiff]
                dhr = dhr[idiff]
            else:
                continue

            # Plot differences
            maxval = np.amax(np.abs(diff))
            cax = axes[j].scatter(dhr, zob, c=diff, marker='o', cmap='seismic', vmin=-maxval, 
                                  vmax=maxval)
            
            axes[j].grid()
            axes[j].set_xlabel('DHR (hr)', size=12)

            cbar = plt.colorbar(cax, ax=axes[j], orientation='horizontal')
            cbar.set_label('%s (%s)' % (o, in_csv.meta[o]['units']), size=12)

        axes[0].set_ylabel('height (%s)' % in_csv.meta['ZOB']['units'], size=12)
        plt.suptitle('Type = %d, SID = %s Differences' % (typ, sid), size=16)
        plt.savefig('diff_autocorr_partition_%d_%s.png' % (typ, sid))
        plt.close()


"""
End add_obs_errors.py 
"""
