"""
Check wgrib2 Wind Rotation

Compare winds rotated from grid-relative to earth-relative using wgrib2 (w/ the new_grid_winds 
option) and using the gridrot_0 field in UPP

Command line arguments:
    argv[1] = YAML file with program parameters

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np
import xarray as xr
import sys
import yaml


#---------------------------------------------------------------------------------------------------
# Read in Parameters from Input YAML
#---------------------------------------------------------------------------------------------------

# Read in input from YAML
with open(sys.argv[1], 'r') as fptr:
    param = yaml.safe_load(fptr)


#---------------------------------------------------------------------------------------------------
# Examine Differences
#---------------------------------------------------------------------------------------------------

grid_rel_ds = xr.open_dataset(param['grid_rel_fname'], engine='pynio')
earth_rel_ds = xr.open_dataset(param['earth_rel_fname'], engine='pynio')

# Rotate winds to be earth-relative in grid_rel_ds
print('rotating winds to be earth-relative')
gridrot = grid_rel_ds['gridrot_0'].values
for key in param['diff_tolerance'].keys():
    if key[:4] in ['UEAR', 'VEAR']:
        suffix = key[4:]
        grid_rel_ds['UEAR'+suffix] = (np.sin(gridrot)*grid_rel_ds['VGRD'+suffix] +
                                      np.cos(gridrot)*grid_rel_ds['UGRD'+suffix])
        grid_rel_ds['VEAR'+suffix] = (np.cos(gridrot)*grid_rel_ds['VGRD'+suffix] -
                                      np.sin(gridrot)*grid_rel_ds['UGRD'+suffix])
        earth_rel_ds['UEAR'+suffix] = earth_rel_ds['UGRD'+suffix]
        earth_rel_ds['VEAR'+suffix] = earth_rel_ds['VGRD'+suffix]

# Compute some RMSDs
test_pass = True
for f in param['diff_tolerance'].keys():
    maxdiff = np.amax(np.abs(grid_rel_ds[f] - earth_rel_ds[f]))
    rmsd = np.sqrt(np.mean((grid_rel_ds[f] - earth_rel_ds[f])**2))
    print()
    print('RMSD for {f} = {v:.3e} (max diff = {d:.3e})'.format(f=f, v=rmsd, d=maxdiff))
    if rmsd >= float(param['diff_tolerance'][f]):
        print('Test Failed for {f}'.format(f=f))
        test_pass = False

# Final Results
print()
print('-------------------------------------------')
if test_pass:
    print('Test passes!')
else:
    print('Test failed')


"""
End check_wgrib2_wind_rotation.py
"""
