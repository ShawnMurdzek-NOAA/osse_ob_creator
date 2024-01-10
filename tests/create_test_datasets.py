"""
Create Datasets for osse_ob_creator Tests

shawn.s.murdzek@noaa.gov
Date Created: 17 August 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import xarray as xr
import numpy as np

import pyDA_utils.bufr as bufr
import pyDA_utils.map_proj as mp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input files
input_upp1 = '/work2/noaa/wrfruc/murdzek/nature_run_winter/UPP/20220201/wrfnat_202202011200_er.grib2'
input_upp2 = '/work2/noaa/wrfruc/murdzek/nature_run_winter/UPP/20220201/wrfnat_202202011215_er.grib2'
input_bufr_csv = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202202011200.rap.prepbufr.csv'

# Output directory
output_dir = './'

# Subset domain specifications (relative to the bottom lower-left corner of the NR domain. Other
# regions cannot be used b/c this would change the indices of the NR gridpoints, which would violate
# the map projection used in the create_synthetic_obs.py program)
xlen = 25
ylen = 30

# BUFR CSV variables and their associated UPP fields. (Don't include pressure or height b/c those
# are vertical coordinates).
vars_2d = {'TOB':'TMP_P0_L103_GLC0', 'QOB':'SPFH_P0_L103_GLC0', 'PWO':'PWAT_P0_L200_GLC0', 
           'PMO':'PRMSL_P0_L101_GLC0'}
vars_2d_3d = {'UOB':'UGRD_P0_L103_GLC0', 'VOB':'VGRD_P0_L103_GLC0'}
vars_3d = {'TOB':'TMP_P0_L105_GLC0',
           'QOB':'SPFH_P0_L105_GLC0', 'UOB':'UGRD_P0_L105_GLC0', 'VOB':'VGRD_P0_L105_GLC0'}

# Min and max values for each variable
# Range of winds are made large on purpose to exaggerate any potential interpolation errors
var_min = {'TOB':-30, 'QOB':0, 'PWO':0, 'PMO':990, 'UOB':-90, 'VOB':-90}
var_max = {'TOB':20, 'QOB':5000, 'PWO':10, 'PMO':1010, 'UOB':90, 'VOB':90}

# Observation types to retain (one of each type will be retained)
obs_2d = [292, 192, 281, 181, 284, 183, 287, 187, 193, 293, 280, 180, 294, 194, 282, 295, 195, 288, 
          188, 153]
obs_3d = [120, 220, 133, 233, 130, 230, 131, 231, 135, 235, 134, 234]


#---------------------------------------------------------------------------------------------------
# Define Linear Functions for Atmospheric Variables 
#---------------------------------------------------------------------------------------------------

def fake_linear_data(x, y, z, t, minval, maxval, xrng, yrng, zrng, trng):
    """
    Create fake linear data

    Parameters
    ----------
    x, y, z, t : float or arrays
        Observation locations
    minval, maxval : float
        Minimum and maximum values allowed
    xrng, yrng, zrng, trng : float or arrays
        Range of x, y, z, and t values

    Returns
    -------
    out_data : float or array
        Fake data created via linear functions

    """

    rng = maxval - minval

    out_data = (minval + 0.3 * (rng/xrng) * x + 0.3 * (rng/yrng) * y + 0.5 * (rng/zrng) * z + 
                0.15 * (rng/trng) * t) 

    return out_data


#---------------------------------------------------------------------------------------------------
# Create Reduced Datasets
#---------------------------------------------------------------------------------------------------

upp1_full = xr.open_dataset(input_upp1, engine='pynio')
upp2_full = xr.open_dataset(input_upp2, engine='pynio')
ob_csv_full = bufr.bufrCSV(input_bufr_csv)

# Only retain variables that are needed for interpolation
upp_vars = ['PRES_P0_L1_GLC0', 'PRES_P0_L105_GLC0', 'HGT_P0_L1_GLC0', 'HGT_P0_L105_GLC0']
for d in [vars_2d, vars_2d_3d, vars_3d]:
    for key in d.keys():
        upp_vars.append(d[key])

upp1_red = upp1_full[upp_vars].isel(xgrid_0=list(range(xlen)), ygrid_0=list(range(ylen))) 
upp2_red = upp2_full[upp_vars].isel(xgrid_0=list(range(xlen)), ygrid_0=list(range(ylen)))

# Determine ranges of each dimension that remain in the UPP file
minlon = upp1_red['gridlon_0'][:, 0].values.max()
maxlon = upp1_red['gridlon_0'][:, -1].values.min()
minlat = upp1_red['gridlat_0'][0, :].values.max()
maxlat = upp1_red['gridlat_0'][-1, :].values.min()
lon_rng = maxlon - minlon
lat_rng = maxlat - minlat
p_rng = (np.log10(upp1_red['PRES_P0_L105_GLC0'].values.max()) - 
         np.log10(upp1_red['PRES_P0_L105_GLC0'].values.min()))

# Reduce number of observations in observation CSV
idx = []
for t in (obs_2d + obs_3d):
    idx.append(ob_csv_full.df.loc[ob_csv_full.df['TYP'] == t].index[0])
ob_df_red = ob_csv_full.df.loc[idx]
ob_df_red.reset_index(inplace=True, drop=True)

# Change nmsg and ntb in observation DataFrame
nmsg = np.ones(len(ob_df_red))
ntb = np.ones(len(ob_df_red))
for i in range(1, len(ob_df_red)):
    if (ob_df_red['nmsg'][i] == ob_df_red['nmsg'][i-1]):
        nmsg[i] = nmsg[i-1]
        ntb[i] = ntb[i-1] + 1
    else:
        nmsg[i] = nmsg[i-1] + 1
ob_df_red['nmsg'] = np.int64(nmsg)
ob_df_red['ntb'] = np.int64(ntb)

# Change observation DHR to match reduced domain
ob_df_red.loc[ob_df_red['DHR'] < 0, 'DHR'] = 0.05
ob_df_red.loc[ob_df_red['DHR'] >= 0.25, 'DHR'] = 0.2

# Force some of the 2D obs to have a DHR that is not 0.0
for i in range(2):
    ob_df_red.loc[ob_df_red['TYP'] == obs_2d[i], 'DHR'] = 0.2

# Change observation XOB and YOB to match reduced domain
nobs = len(ob_df_red)
XOB = np.ones(nobs) * (minlon + 0.01*lon_rng)
YOB = np.ones(nobs) * (minlat + 0.01*lat_rng)
for i in range(1, len(ob_df_red)):
    if np.isclose(ob_df_red['XOB'][i], ob_df_red['XOB'][i-1]):
        XOB[i] = XOB[i-1]
        YOB[i] = YOB[i-1]
    else:
        XOB[i] = minlon + (np.random.uniform() * lon_rng)
        YOB[i] = minlat + (np.random.uniform() * lat_rng)
ob_df_red['XOB'] = 360. + XOB
ob_df_red['YOB'] = YOB

# Force some of the 3D obs to lie on Nature Run gridpoints
for i in range(4):
    ob_df_red.loc[ob_df_red['TYP'] == obs_3d[i], 'XOB'] = upp1_red['gridlon_0'].values[2, 5] + 360.
    ob_df_red.loc[ob_df_red['TYP'] == obs_3d[i], 'YOB'] = upp1_red['gridlat_0'].values[2, 5]

# Force some of the 3D obs to have DHR = 0 and some to have DHR != 0
ob_df_red.loc[ob_df_red['TYP'] == obs_3d[2], 'DHR'] = 0.2
for i in range(3, 6):
    ob_df_red.loc[ob_df_red['TYP'] == obs_3d[i], 'DHR'] = 0


#---------------------------------------------------------------------------------------------------
# Create Fake, Linear Data
#---------------------------------------------------------------------------------------------------

# Observations
x_obs, y_obs = mp.ll_to_xy_lc(ob_df_red['YOB'].values, ob_df_red['XOB'].values - 360.)
for i in range(len(ob_df_red)):
    if ob_df_red.loc[i, 'TYP'] in obs_2d:
        for v in var_min.keys():
            ob_df_red.loc[i, v] = fake_linear_data(x_obs[i], y_obs[i], 0, ob_df_red.loc[i, 'DHR'], 
                                                   var_min[v], var_max[v], xlen, ylen, p_rng, 
                                                   0.25)
    else:
        for v in var_min.keys():
            ob_df_red.loc[i, v] = fake_linear_data(x_obs[i], y_obs[i], 
                                                   np.log10(ob_df_red.loc[i, 'POB'] * 100), 
                                                   ob_df_red.loc[i, 'DHR'], 
                                                   var_min[v], var_max[v], xlen, ylen, p_rng, 
                                                   0.25)
 
# Nature run UPP output
x_upp, y_upp = np.meshgrid(np.arange(xlen), np.arange(ylen))
y3d_upp, _, x3d_upp = np.meshgrid(np.arange(ylen), np.arange(upp1_red['PRES_P0_L105_GLC0'].shape[0]), 
                                  np.arange(xlen))
for v in vars_2d:
    upp1_red[vars_2d[v]].values = fake_linear_data(x_upp, y_upp, 0, 0, var_min[v], var_max[v], 
                                                   xlen, ylen, p_rng, 0.25)
    upp2_red[vars_2d[v]].values = fake_linear_data(x_upp, y_upp, 0, 0.25, var_min[v], var_max[v], 
                                                   xlen, ylen, p_rng, 0.25)
for v in vars_2d_3d:
    upp1_red[vars_2d_3d[v]].values = np.array([fake_linear_data(x_upp, y_upp, 0, 0, var_min[v], 
                                                             var_max[v], xlen, ylen, p_rng, 0.25),
                                               fake_linear_data(x_upp, y_upp, 0.1*p_rng, 0, var_min[v], 
                                                             var_max[v], xlen, ylen, p_rng, 0.25)])
    upp2_red[vars_2d_3d[v]].values = np.array([fake_linear_data(x_upp, y_upp, 0, 0.25, var_min[v], 
                                                                var_max[v], xlen, ylen, p_rng, 0.25),
                                               fake_linear_data(x_upp, y_upp, 0.1*p_rng, 0.25, var_min[v], 
                                                                var_max[v], xlen, ylen, p_rng, 0.25)])
for v in vars_3d:
    upp1_red[vars_3d[v]].values = fake_linear_data(x3d_upp, y3d_upp, 
                                                   np.log10(upp1_red['PRES_P0_L105_GLC0'].values), 0, 
                                                   var_min[v], var_max[v], xlen, ylen, p_rng, 0.25)
    upp2_red[vars_3d[v]].values = fake_linear_data(x3d_upp, y3d_upp, 
                                                   np.log10(upp2_red['PRES_P0_L105_GLC0'].values), 0.25, 
                                                   var_min[v], var_max[v], xlen, ylen, p_rng, 0.25)

# Convert units for UPP output
for ds in [upp1_red, upp2_red]:
    ds['TMP_P0_L103_GLC0'].values = ds['TMP_P0_L103_GLC0'].values + 273.15
    ds['TMP_P0_L105_GLC0'].values = ds['TMP_P0_L105_GLC0'].values + 273.15
    ds['SPFH_P0_L103_GLC0'].values = ds['SPFH_P0_L103_GLC0'].values * 1e-6
    ds['SPFH_P0_L105_GLC0'].values = ds['SPFH_P0_L105_GLC0'].values * 1e-6
    ds['PRMSL_P0_L101_GLC0'].values = ds['PRMSL_P0_L101_GLC0'].values * 100
    ds['PWAT_P0_L200_GLC0'].values = ds['PWAT_P0_L200_GLC0'].values * 1000. / 997.


#---------------------------------------------------------------------------------------------------
# Output Results
#---------------------------------------------------------------------------------------------------

bufr_time = input_bufr_csv.split('/')[-1].split('.')[0][:-2]
bufr_tag = input_bufr_csv.split('/')[-1].split('.')[1]
bufr.df_to_csv(ob_df_red, '%s/%s.%s.t%sz.prepbufr.csv' % (output_dir, bufr_time, bufr_tag, bufr_time[-2:]))
upp1_red.to_netcdf('%s/%s.nc' % (output_dir, input_upp1.split('/')[-1].split('.')[0]))
upp2_red.to_netcdf('%s/%s.nc' % (output_dir, input_upp2.split('/')[-1].split('.')[0]))


"""
End create_test_datasets.py
"""
