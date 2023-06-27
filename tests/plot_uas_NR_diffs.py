"""
Plot Differences Between UAS Soundings and Closest NR Gridpoint

shawn.s.murdzek@noaa.gov
Date Created: 9 May 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import xarray as xr
import bufr
import plot_model_data as pmd
import matplotlib.pyplot as plt
import map_proj as mp
import metpy.calc as mc
from metpy.units import units
import numpy as np


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input BUFR file and obs TYP to use
#bufr_file = '/work2/noaa/wrfruc/murdzek/nature_run_spring/synthetic_obs_csv/perfect_uas/202204291200.uas.prepbufr.csv'
bufr_file = '/work2/noaa/wrfruc/murdzek/src/py_scripts/synthetic_obs/test.uas.prepbufr.csv'
ob_typ_thermo = 132
ob_typ_wind = 232

# UPP file for comparison
upp_file = '/work2/noaa/wrfruc/murdzek/nature_run_spring/UPP/20220429/wrfnat_202204291200.grib2'

# Make plots for the closest n UAS profiles
nclose = 2

# Output file name (include %d placeholder for nclose)
out_fname = './uas_NR_compare_%d.png'


#---------------------------------------------------------------------------------------------------
# Make Plots
#---------------------------------------------------------------------------------------------------

# Determine UAS obs closest to NR gridpoints
bufr_csv = bufr.bufrCSV(bufr_file)
bufr_csv.df['xlc'], bufr_csv.df['ylc'] = mp.ll_to_xy_lc(bufr_csv.df['YOB'], bufr_csv.df['XOB'] - 360.)
bufr_csv.df['xnear'] = np.int32(np.around(bufr_csv.df['xlc']))
bufr_csv.df['ynear'] = np.int32(np.around(bufr_csv.df['ylc']))
bufr_csv.df['dist'] = np.sqrt((bufr_csv.df['xlc'] - bufr_csv.df['xnear'])**2 +
                              (bufr_csv.df['ylc'] - bufr_csv.df['ynear'])**2)
ntop = np.sort(np.unique(bufr_csv.df['dist'].values))[nclose-1]
plot_df = bufr_csv.df.loc[np.logical_and(np.logical_or(bufr_csv.df['TYP'] == ob_typ_thermo,
                                                       bufr_csv.df['TYP'] == ob_typ_wind),
                                         bufr_csv.df['dist'] <= ntop)]

# Open UPP file
upp_ds = xr.open_dataset(upp_file, engine='pynio')

# Create plot
for i, nmsg in enumerate(np.unique(plot_df['nmsg'])):
    subset = plot_df.loc[plot_df['nmsg'] == nmsg].copy()
    subset.reset_index(drop=True, inplace=True)

    upp_lat = upp_ds['gridlat_0'][subset.loc[0, 'ynear'], subset.loc[0, 'xnear']].values
    upp_lon = upp_ds['gridlon_0'][subset.loc[0, 'ynear'], subset.loc[0, 'xnear']].values

    fig = plt.figure(figsize=(7, 8))
    out = pmd.PlotOutput([upp_ds], 'upp', fig, 1, 1, 1)
    out.skewt(upp_lon, upp_lat)

    out.skew.plot(subset['POB'], subset['TOB'], 'c--', lw=3.5)
    Td = mc.dewpoint_from_specific_humidity(subset['POB'].values*units.hPa, 
                                            subset['TOB'].values*units.degC,
                                            subset['QOB'].values*units.mg/units.kg).to('degC').magnitude
    out.skew.plot(subset['POB'], Td, 'c--', lw=3.5)
    out.h.plot(subset['UOB'], subset['VOB'], c='c', ls='--')

    plt.suptitle(r'%.3f$^{\circ}$N, %.3f$^{\circ}$E (d = %.3f km)' % 
                 (upp_lat, upp_lon, subset.loc[0, 'dist']), size=16)
    plt.savefig(out_fname % i)


"""
End plot_uas_NR_diffs.py 
"""
