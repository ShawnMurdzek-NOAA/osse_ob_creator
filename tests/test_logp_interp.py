"""
Test Method of Logarithmic Interpolation Along the Pressure Coordinate

shawn.s.murdzek@noaa.gov
Date Created: 21 March 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np
import xarray as xr
import metpy.interpolate as mi
import pandas as pd
import matplotlib.pyplot as plt

import bufr
import create_ob_utils as cou


#---------------------------------------------------------------------------------------------------
# Compare Interpolation Methods
#---------------------------------------------------------------------------------------------------

# Create some fake data
x = np.arange(100, 1, -1)
y = 3 + 2*np.log10(x)
xi = np.sort(np.random.uniform(2, 99, size=50))
yi_truth = 3 + 2*np.log10(xi)

# Interpolation using MetPy
yi_metpy = mi.log_interpolate_1d(xi, x, y)

# Interpolation using my functions
yi_custom = np.zeros(xi.size)
for i in range(xi.size):
    d = {'POB':xi[i]}
    d['pi0'] = np.where(x > xi[i])[0][-1]
    d['POB'], d['pwgt'] = cou.interp_wrf_p1d(x, d)
    yi_custom[i] = cou._linear_interp(y[d['pi0']], y[d['pi0']+1], d['pwgt'])

# Plot results
fig = plt.figure()
plt.plot(xi, yi_truth, 'ko', label='truth')
plt.plot(xi, yi_metpy, 'b-', lw=2, 
         label='MetPy (RMSE = %.2e)' % np.sqrt(np.mean((yi_metpy - yi_truth)**2)))
plt.plot(xi, yi_custom, 'r--', lw=2,
         label='Custom (RMSE = %.2e)' % np.sqrt(np.mean((yi_custom - yi_truth)**2)))
plt.legend()
plt.grid()
plt.show()


"""
End test_logp_interp.py 
"""
