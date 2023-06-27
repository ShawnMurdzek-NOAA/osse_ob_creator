"""
Determine Locations of UAS Observation Sites

List of CartoPy map projections: https://scitools.org.uk/cartopy/docs/latest/reference/projections.html
Primer on map projections: https://www.e-education.psu.edu/geog160/node/1918

shawn.s.murdzek@noaa.gov
Date Created: 28 March 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mplpath
import pyproj
import scipy.interpolate as si
import datetime as dt
import xarray as xr
import shapefile
import scipy.ndimage as sn


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Spacing between UAS sites (m)
dx = 35000.

# Grid points in east-west and north-south directions (similar to e_we and e_sn in WPS namelist)
npts_we = 155
npts_sn = 91

# Nature run output (for landmask)
upp_file = '/work2/noaa/wrfruc/murdzek/nature_run_spring/UPP/20220429/wrfnat_202204291200.grib2'

# Apply binary closing after applying landmask?
# Goal here is to include UAS sites over small inland bodies of water (i.e., not the Great Lakes).
# Using binary closing is a bit aggressive, as it adds some UAS sites over the Great Lakes when
# dx = 35000.
land_closing = False

# Maximum "hole" size. Gaps in the UAS network <= max_hole_size are filled. Set to 0 to not use 
# this method. Removal of holes is applied after landmask, but before US mask.
max_hole_size = 2

# Shapefile (and shape index) containing the outline of the US
shp_fname = '/home/smurdzek/.local/share/cartopy/shapefiles/natural_earth/cultural/ne_50m_admin_0_countries'
nshape = 16

# Map projection in proj4 format. See documentation here for Lambert Conformal parameters: 
# https://proj.org/operations/projections/lcc.html
proj_str = '+proj=lcc +lat_0=39 +lon_0=-96 +lat_1=33 +lat_2=45'

# Output text file to dump UAS site (lat, lon) coordinates
out_file = 'uas_site_locs_35km.txt'

# Options for plotting UAS sites
make_plot = True
plot_save_fname = 'uas_sites.pdf'
#lon_lim = [-76.75, -73.5]
#lat_lim = [38.75, 41.5]
lon_lim = [-127, -65]
lat_lim = [23, 49]


#---------------------------------------------------------------------------------------------------
# Compute (lat, lon) coordinates of UAS Sites
#---------------------------------------------------------------------------------------------------

x_uas, y_uas = np.meshgrid(np.arange(-0.5*npts_we*dx, 0.5*npts_we*dx + (0.1*dx), dx),
                           np.arange(-0.5*npts_sn*dx, 0.5*npts_sn*dx + (0.1*dx), dx))
shape_uas = x_uas.shape
x_uas = x_uas.ravel()
y_uas = y_uas.ravel()

# Create projection and convert to (lat, lon) coordinates
proj = pyproj.Proj(proj_str)
lon_uas, lat_uas = proj(x_uas, y_uas, inverse=True)

# Extract and apply landmask
upp_ds = xr.open_dataset(upp_file, engine='pynio')
landmask = upp_ds['LAND_P0_L1_GLC0'].values.ravel()
lat_upp = upp_ds['gridlat_0'].values.ravel()
lon_upp = upp_ds['gridlon_0'].values.ravel()

print('performing landmask interpolation (%s)' % dt.datetime.now().strftime('%H:%M:%S'))
interp_fct = si.NearestNDInterpolator(list(zip(lon_upp, lat_upp)), landmask)
uas_mask_land = np.array(interp_fct(list(zip(lon_uas, lat_uas))), dtype=bool)

if land_closing:
    uas_mask_land_2d = np.reshape(uas_mask_land, shape_uas)
    uas_mask_land_2d = sn.binary_closing(uas_mask_land_2d)
    uas_mask_land = uas_mask_land_2d.ravel()

if max_hole_size > 0:
    uas_mask_land_2d = np.reshape(uas_mask_land, shape_uas)
    uas_mask_land_labeled = sn.label(np.logical_not(uas_mask_land_2d))[0]
    for label in np.unique(uas_mask_land_labeled):
        if np.sum(uas_mask_land_labeled == label) <= max_hole_size: 
            label_idx = np.where(uas_mask_land_labeled == label)
            uas_mask_land_2d[label_idx[0], label_idx[1]] = True
    uas_mask_land = uas_mask_land_2d.ravel()

lon_uas = lon_uas[uas_mask_land]
lat_uas = lat_uas[uas_mask_land]
print('done with landmask interpolation (%s)' % dt.datetime.now().strftime('%H:%M:%S'))

# Remove UAS sites outside of the US
# pyshp documentation: https://pypi.org/project/pyshp/#reading-shapefiles
full_shp = shapefile.Reader(shp_fname)
us_shape = full_shp.shapes()[nshape]
uas_mask_us = np.zeros(len(lon_uas))
for istart, iend in zip(us_shape.parts[:-1], us_shape.parts[1:]):
    polygon = mplpath.Path(us_shape.points[istart:iend], closed=True)
    uas_mask_us = np.logical_or(uas_mask_us, polygon.contains_points(list(zip(lon_uas, lat_uas))))
lon_uas = lon_uas[uas_mask_us]
lat_uas = lat_uas[uas_mask_us]

# Save results
fptr = open(out_file, 'w')
fptr.write('lon (deg E),lat (deg N)\n')
for lon, lat in zip(lon_uas, lat_uas):
    fptr.write('%.3f,%.3f\n' % (lon, lat))
fptr.close()


#---------------------------------------------------------------------------------------------------
# Make Plot
#---------------------------------------------------------------------------------------------------

if make_plot:
    proj_cartopy = ccrs.PlateCarree()
    #proj_cartopy = ccrs.LambertConformal()
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=proj_cartopy)

    ax.plot(lon_uas, lat_uas, 'r.', transform=proj_cartopy)

    scale = '10m'
    ax.coastlines(scale)
    borders = cfeature.NaturalEarthFeature(category='cultural',
                                           scale=scale,
                                           facecolor='none',
                                           name='admin_1_states_provinces')
    ax.add_feature(borders)
    lakes = cfeature.NaturalEarthFeature(category='physical',
                                           scale=scale,
                                           facecolor='none',
                                           name='lakes')
    ax.add_feature(lakes)
    ax.set_extent([lon_lim[0], lon_lim[1], lat_lim[0], lat_lim[1]])

    plt.savefig(plot_save_fname)
    plt.show()


"""
End uas_sites.py
"""
