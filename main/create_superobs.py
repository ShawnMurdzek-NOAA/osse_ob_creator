"""
Create Superobs for a Specific Observation Type

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np
import xarray as xr
import yaml
import datetime as dt
import pandas as pd

from pyDA_utils import bufr
import pyDA_utils.superob_prepbufr as sp
import pyDA_utils.map_proj as mp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input BUFR CSV file name
in_csv_fname = '/work2/noaa/wrfruc/murdzek/nature_run_spring/obs/uas_hspace_150km_ctrl/err_uas_csv/202204291500.rap.fake.prepbufr.csv'

# Output BUFR CSV file name
out_csv_fname = './tmp_superob.csv'

# Parameters for creating superobs
map_proj = mp.ll_to_xy_lc
map_proj_kw={'dx':3, 'knowni':899, 'knownj':529}
grouping = 'grid'
grouping_kw = {'grid_fname':'../fix_data/RRFS_grid_max.nc',
               'subtract_360_lon_grid':True}
reduction_kw = {136:{'var_dict':{'TOB':{'method':'vert_cressman', 
                                        'qm_kw':{'field':'TQM', 'thres':2},
                                        'reduction_kw':{'R':'max'}},
                                 'QOB':{'method':'vert_cressman', 
                                        'qm_kw':{'field':'QQM', 'thres':2},
                                        'reduction_kw':{'R':'max'}},
                                 'POB':{'method':'vert_cressman', 
                                        'qm_kw':{'field':'PQM', 'thres':2},
                                        'reduction_kw':{'R':'max'}},
                                 'XOB':{'method':'mean', 
                                        'qm_kw':{'field':'TQM', 'thres':2},
                                        'reduction_kw':{}},
                                 'YOB':{'method':'mean', 
                                        'qm_kw':{'field':'TQM', 'thres':2},
                                        'reduction_kw':{}},
                                 'ZOB':{'method':'mean', 
                                        'qm_kw':{'field':'TQM', 'thres':2},
                                        'reduction_kw':{}},
                                 'DHR':{'method':'mean', 
                                        'qm_kw':{'field':'TQM', 'thres':2},
                                        'reduction_kw':{}}}},
                236:{'var_dict':{'UOB':{'method':'vert_cressman', 
                                        'qm_kw':{'field':'WQM', 'thres':2},
                                        'reduction_kw':{'R':'max'}},
                                 'VOB':{'method':'vert_cressman', 
                                        'qm_kw':{'field':'WQM', 'thres':2},
                                        'reduction_kw':{'R':'max'}},
                                 'XOB':{'method':'mean', 
                                        'qm_kw':{'field':'WQM', 'thres':2},
                                        'reduction_kw':{}},
                                 'YOB':{'method':'mean', 
                                        'qm_kw':{'field':'WQM', 'thres':2},
                                        'reduction_kw':{}},
                                 'ZOB':{'method':'mean', 
                                        'qm_kw':{'field':'WQM', 'thres':2},
                                        'reduction_kw':{}},
                                 'DHR':{'method':'mean', 
                                        'qm_kw':{'field':'WQM', 'thres':2},
                                        'reduction_kw':{}}}}}
   

#---------------------------------------------------------------------------------------------------
# Create Superobs
#---------------------------------------------------------------------------------------------------

# Create superob object
print('Creating superob object...')
sp_obj = sp.superobPB(in_csv_fname, 
                      map_proj=map_proj, 
                      map_proj_kw=map_proj_kw)

# Create superobs
out_df_list = []
for o in reduction_kw.keys():
    start = dt.datetime.now()
    print()
    print(f'Creating superobs for type = {o}')
    print('Start time = ', start)
    out_df_list.append(sp_obj.create_superobs(obtypes=[o],
                                              grouping=grouping,
                                              grouping_kw=grouping_kw,
                                              reduction_kw=reduction_kw[o]))
    sp_obj.df = sp_obj.full_df.copy()
    print('Finished. Elapsed time = {t} s'.format(t=(dt.datetime.now() - start).total_seconds()))

# Save results
print()
print('saving superobbed CSV')
out_df = pd.concat(out_df_list)
out_df.drop(labels=['XMP', 'YMP', 'SFC', 'superob_groups'], axis=1, inplace=True)
bufr.df_to_csv(out_df, out_csv_fname)


"""
End create_superobs.py
"""
