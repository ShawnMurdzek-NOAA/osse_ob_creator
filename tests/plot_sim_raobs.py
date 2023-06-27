"""
Plot Simulated Radiosonde Observations

shawn.s.murdzek@noaa.gov
Date Created: 17 March 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import metpy
from metpy.plots import SkewT, Hodograph
import metpy.calc as mc
from metpy.units import units


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# BUFR CSV file with simulated radiosonde data (this should be the "full" DataFrame for debugging)
#raob_bufr = '/mnt/lfs4/BMC/wrfruc/murdzek/nature_run_spring/synthetic_obs/202204291200.debug.adpupa.csv'
raob_bufr = '/work2/noaa/wrfruc/murdzek/nature_run_spring/synthetic_obs_csv/adpupa/202204300100.debug.adpupa.csv'

# Station IDs to plot
sid = [72476, 72520, 72694, 72649, 72202, 72456, 74389]
sid = [72520]

# Thinning wind barbs
thin = 4

# Output file name (leave %s placeholder for station ID)
out_fname = './raob_%s.png'


#---------------------------------------------------------------------------------------------------
# Create Plots
#---------------------------------------------------------------------------------------------------

raob_df = pd.read_csv(raob_bufr)

# Plot data from each radiosonde
for s in sid:
    print('plotting RAOB for %d' % s)
    subset = raob_df.loc[raob_df['SID'] == s]
    fig = plt.figure(figsize=(12, 8))

    ax1 = fig.add_subplot(1, 2, 1)
    ax1.plot(subset['adpupa_x'].values[0], subset['adpupa_y'].values[0], 'ko')
    ax1.plot(subset['adpupa_x'], subset['adpupa_y'])
    maxdist = np.amax(np.sqrt((subset['adpupa_x'].values[0] - subset['adpupa_x'].values)**2 + 
                              (subset['adpupa_y'].values[0] - subset['adpupa_y'].values)**2))
    ax1.grid()
    ax1.set_aspect('equal')
    ax1.set_xlabel('x (km)', size=12)
    ax1.set_ylabel('y (km)', size=12)
    ax1.set_title('max dist = %.2f km' % maxdist, size=16)

    Tidx = subset.index[np.logical_not(np.isnan(subset['TOB']))].values
    UVidx = subset.index[np.logical_not(np.isnan(subset['UOB']))].values
    if int(metpy.__version__.split('.')[0]) > 0:
        Td = mc.dewpoint_from_specific_humidity(subset.loc[Tidx, 'POB'].values * units.hPa,
                                                subset.loc[Tidx, 'TOB'].values * units.degC,
                                                subset.loc[Tidx, 'QOB'].values * units.mg / units.kg)
    else:
        Td = mc.dewpoint_from_specific_humidity(subset.loc[Tidx, 'QOB'].values * units.mg / units.kg,
                                                subset.loc[Tidx, 'TOB'].values * units.degC,
                                                subset.loc[Tidx, 'POB'].values * units.hPa)
    ax2 = SkewT(fig, subplot=(1, 2, 2), rotation=45)
    ax2.plot(subset.loc[Tidx, 'POB'].values, subset.loc[Tidx, 'TOB'].values, 'r-')
    ax2.plot(subset.loc[Tidx, 'POB'].values, Td.to('degC').magnitude, 'b-')
    ax2.plot_barbs(subset.loc[UVidx, 'POB'].values[::thin], subset.loc[UVidx, 'UOB'].values[::thin], 
                   subset.loc[UVidx, 'VOB'].values[::thin])

    # Configure Skew-T
    ax2.plot_dry_adiabats(linewidth=0.5)
    ax2.plot_moist_adiabats(linewidth=0.5)
    ax2.plot_mixing_lines(linewidth=0.5)
    ax2.ax.set_xlim(-40, 60)
    ax2.ax.set_ylim(1000, 100)

    plt.suptitle(s, size=20)
    plt.savefig(out_fname % s)
    plt.close()


"""
End plot_sim_raobs.py
"""
