"""
Scatterplots of ZOB vs. POB

If ZOBs are computed directly from POBs assuming the US Standard Atmosphere, the agreement between
these two should be perfect

shawn.s.murdzek@noaa.gov
Date Created: 1 March 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

import bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# BUFR CSV file name
fname = '/work2/noaa/wrfruc/murdzek/src/GSI-utils/bin/prepbufr.csv'

# Observation subsets to plot. Each will get its own subplot
subsets = ['AIRCAR', 'AIRCFT', 'ADPUPA', 'VADWND', 'RASSDA', 'PROFLR']

# Variables to plot in the scatterplot
var1 = 'ZOB'
var2 = 'POB'

# Option to use an inverse log scale for the y-axis (good for pressure)
yaxis_log = True

# Output file name
out_fname = './ZOB_POB_scatter.png'


#---------------------------------------------------------------------------------------------------
# Create Plots
#---------------------------------------------------------------------------------------------------

bufr_csv = bufr.bufrCSV(fname)

nplots = len(subsets)
fig, axes = plt.subplots(nrows=1, ncols=nplots, figsize=(3+3*nplots, 6), sharey=True)

for i, s in enumerate(subsets):
    if nplots > 1:
        ax = axes[i]
    else:
        ax = axes

    ind = np.where(bufr_csv.df['subset'] == s)[0]
    ax.scatter(bufr_csv.df.loc[ind, var1], bufr_csv.df.loc[ind, var2], s=2)
    
    ax.grid()
    ax.set_xlabel('%s (%s)' % (var1, bufr_csv.meta[var1]['units']), size=12)
    ax.set_title(s, size=16)

    if i == 0:
        ax.set_ylabel('%s (%s)' % (var2, bufr_csv.meta[var2]['units']), size=12)

    if yaxis_log:
        ax.set_yscale('log')
        ax.set_ylim([1100, 100])

plt.savefig(out_fname)
plt.show()
plt.close()


"""
End ZOB_POB_scatterplot.py
"""

