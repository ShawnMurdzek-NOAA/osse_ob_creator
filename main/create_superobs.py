"""
Create Superobs for a Specific Observation Type

Optional command-line arguments:
    argv[1] = BUFR time in YYYYMMDDHHMM format 
    argv[2] = BUFR tag 
    argv[3] = YAML file with program parameters

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
import sys

from pyDA_utils import bufr
import pyDA_utils.superob_prepbufr as sp
import pyDA_utils.map_proj as mp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Input BUFR CSV file name
in_csv_fname = '/work2/noaa/wrfruc/murdzek/nature_run_spring/obs/uas_hspace_150km_ctrl/err_uas_csv/202204291500.rap.fake.prepbufr.csv'

# Output BUFR CSV file name
out_csv_fname = './tmp_superob_yaml.csv'

# Parameters for creating superobs
map_proj = mp.ll_to_xy_lc
map_proj_kw={'dx':6, 'knowni':449, 'knownj':264}
grouping = 'grid'
grouping_kw = {'grid_fname':'../fix_data/RRFS_grid_mean_twice_gspacing.nc',
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
                                 'POB':{'method':'vert_cressman', 
                                        'qm_kw':{'field':'PQM', 'thres':2},
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

# Option to use input from YAML file 
if len(sys.argv) > 1:
    bufr_t = sys.argv[1]
    tag = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    in_csv_fname = '{parent}/{t}.{tag}.input.prepbufr.csv'.format(parent=param['paths']['syn_superob_csv'],
                                                                  t=bufr_t, tag=tag)
    out_csv_fname = '{parent}/{t}.{tag}.output.prepbufr.csv'.format(parent=param['paths']['syn_superob_csv'],
                                                                    t=bufr_t, tag=tag)
    if param['superobs']['map_proj'] == 'll_to_xy_lc':
        map_proj = mp.ll_to_xy_lc
    map_proj_kw = param['superobs']['map_proj_kw']
    grouping = param['superobs']['grouping']
    grouping_kw = param['superobs']['grouping_kw']
    reduction_kw = param['superobs']['reduction_kw']


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
