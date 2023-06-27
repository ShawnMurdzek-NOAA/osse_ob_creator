"""
Plot Observation Locations from a Prepbufr CSV

shawn.s.murdzek@noaa.gov
Date Created: 13 October 2022
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import bufr
import matplotlib.pyplot as plt
import numpy as np


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

fname = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202202011800.rap.prepbufr.csv'
save_fname = './bufr_ob_locs_2022020118.png'


#---------------------------------------------------------------------------------------------------
# Plot BUFR Observation Locations
#---------------------------------------------------------------------------------------------------

bufr_df = bufr.bufrCSV(fname)

ob_types = bufr_df.df['subset'].unique()

nrows = 3
ncols = 4
fig = plt.figure(figsize=(12, 8))
for i, ob in enumerate(ob_types):
    print('Plotting %s' % ob)
    data = bufr_df.df.loc[bufr_df.df['subset'] == ob]
    ax = bufr.plot_obs_locs(data['XOB'] - 360, data['YOB'], nrows=nrows, ncols=ncols, axnum=(i+1), 
                            fig=fig, lw=0, marker='.', markersize=2)
    ax.set_xlim([-170, -40])
    ax.set_ylim([0, 80])

    # There isn't really a clean way to determine the number of observations. In fact, "observation"
    # is poorly defined. Is a radiosonde a single ob, or is each level a different ob? Is a single
    # aircraft path one ob, or is each reporting time an ob? To make matters more confusing, some
    # obs are separated between thermodynamic and kinematic obs (e.g., aircraft obs), and it's not
    # guaranteed that both types of obs will be reported at each report time.
    nsid = len(data['SID'].unique())
    ax.set_title('%s ($n_{stations}$ = %d)' % (ob, nsid), size=14)

plt.subplots_adjust(left=0.02, bottom=0.02, right=0.98, top=0.93)
plt.suptitle(bufr_df.df['cycletime'].values[0], size=18)
plt.savefig(save_fname)


"""
End plot_bufr_obs_locs.py  
"""
