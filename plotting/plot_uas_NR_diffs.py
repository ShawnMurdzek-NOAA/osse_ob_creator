"""
Plot Differences Between UAS Soundings and Closest NR Gridpoint

Optional command-line arguments:
    argv[1] = Prepbufr file tag
    argv[2] = Time of prepbufr file (YYYYMMDDHH)
    argv[3] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
Date Created: 9 May 2023
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

# Input BUFR file and obs TYP to use
bufr_file = '/work2/noaa/wrfruc/murdzek/nature_run_spring/obs/uas_hspace_150km_ctrl/err_uas_csv/202204291500.rap.fake.prepbufr.csv'
ob_typ_thermo = 136
ob_typ_wind = 236

# Option to compare to a superobbed BUFR file
compare_superob = False
bufr_file_superob = '/work2/noaa/wrfruc/murdzek/src/osse_ob_creator/main/tmp_superob.csv'

# UPP file for comparison
upp_file = '/work2/noaa/wrfruc/murdzek/nature_run_spring/UPP/20220429/wrfnat_202204291500_er.grib2'

# Make plots for the closest n UAS profiles
nclose = 2

# Output file name (include %d placeholder for nclose)
out_fname = './uas_NR_compare_%d.png'

# Use passed arguments, if they exist
if len(sys.argv) > 1:
    tag = sys.argv[1]
    t_str = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    bufr_file = '%s/%s.%s.fake.prepbufr.csv' % (param['paths'][param['plots']['diff_uas']['bufr_dir']],
                                                t_str, tag)
    upp_file = '%s/%s/wrfnat_%s_er.grib2' % (param['paths']['model'], t_str[:8], t_str)
    out_fname = '%s/%s' % (param['paths']['plots'], t_str) +'/uas_NR_compare_%d.png'
    nclose = param['plots']['diff_uas']['nclose']


#---------------------------------------------------------------------------------------------------
# Make Plots
#---------------------------------------------------------------------------------------------------

# Determine UAS obs closest to NR gridpoints
bufr_csv = bufr.bufrCSV(bufr_file)
bufr_csv.df = bufr.compute_wspd_wdir(bufr_csv.df)
bufr_csv.df['xlc'], bufr_csv.df['ylc'] = mp.ll_to_xy_lc(bufr_csv.df['YOB'], bufr_csv.df['XOB'] - 360.)
bufr_csv.df['xnear'] = np.int32(np.around(bufr_csv.df['xlc']))
bufr_csv.df['ynear'] = np.int32(np.around(bufr_csv.df['ylc']))
bufr_csv.df['dist'] = np.sqrt((bufr_csv.df['xlc'] - bufr_csv.df['xnear'])**2 +
                              (bufr_csv.df['ylc'] - bufr_csv.df['ynear'])**2)
ntop = np.sort(np.unique(bufr_csv.df['dist'].values))[nclose-1]
plot_df = bufr_csv.df.loc[np.logical_and(np.logical_or(bufr_csv.df['TYP'] == ob_typ_thermo,
                                                       bufr_csv.df['TYP'] == ob_typ_wind),
                                         bufr_csv.df['dist'] <= ntop)]

# Read in superobbed BUFR file
if compare_superob:
    bufr_csv_superob = bufr.bufrCSV(bufr_file_superob)
    bufr_csv_superob.df = bufr.compute_wspd_wdir(bufr_csv_superob.df)

# Open UPP file
upp_ds = xr.open_dataset(upp_file, engine='pynio')

# Create plot
for i, nmsg in enumerate(np.unique(plot_df['nmsg'])):
    subset = plot_df.loc[plot_df['nmsg'] == nmsg].copy()
    subset.reset_index(drop=True, inplace=True)
    print('plotting UAS %s' % subset.loc[0, 'SID'])

    upp_lat = upp_ds['gridlat_0'][subset.loc[0, 'ynear'], subset.loc[0, 'xnear']].values
    upp_lon = upp_ds['gridlon_0'][subset.loc[0, 'ynear'], subset.loc[0, 'xnear']].values

    max_uas_wspd = subset['WSPD'].max()

    fig = plt.figure(figsize=(7, 8))
    out = pmd.PlotOutput([upp_ds], 'upp', fig, 1, 1, 1)
    out.skewt(upp_lon, upp_lat, hodo_range=(max_uas_wspd+1))

    out.skew.plot(subset['POB'], subset['TOB'], 'c--', lw=3.5)
    Td = mc.dewpoint_from_specific_humidity(subset['POB'].values*units.hPa, 
                                            subset['TOB'].values*units.degC,
                                            subset['QOB'].values*units.mg/units.kg).to('degC').magnitude
    out.skew.plot(subset['POB'], Td, 'c--', lw=3.5)
    out.h.plot(subset['UOB'], subset['VOB'], c='c', ls='--')

    if compare_superob:
        subset_superob = bufr_csv_superob.df.loc[bufr_csv_superob.df['nmsg'] == nmsg].copy()
        out.skew.plot(subset_superob['POB'], subset_superob['TOB'], 'ko', lw=3.5)
        Td = mc.dewpoint_from_specific_humidity(subset_superob['POB'].values*units.hPa, 
                                                subset_superob['TOB'].values*units.degC,
                                                subset_superob['QOB'].values*units.mg/units.kg).to('degC').magnitude
        out.skew.plot(subset_superob['POB'], Td, 'ko', lw=3.5)
        out.h.plot(subset_superob['UOB'], subset_superob['VOB'], c='k')
        plt.suptitle('UAS (dashed) vs NR nearest gridpoint (solid) vs Superob (dots)\n' + 
                     r'%.3f$^{\circ}$N, %.3f$^{\circ}$E (d = %.3f km)' % 
                     (upp_lat, upp_lon, subset.loc[0, 'dist']), size=16)

    else:
        plt.suptitle('UAS (dashed) vs NR nearest gridpoint (solid)\n' + 
                     r'%.3f$^{\circ}$N, %.3f$^{\circ}$E (d = %.3f km)' % 
                     (upp_lat, upp_lon, subset.loc[0, 'dist']), size=16)
    plt.savefig(out_fname % i)


"""
End plot_uas_NR_diffs.py 
"""
