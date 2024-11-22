"""
Limit UAS Flights Owing to Local Meteorology

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
import sys
import yaml
import datetime as dt

from pyDA_utils import bufr
import pyDA_utils.limit_prepbufr as lp


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

# Option to use input from YAML file 
if len(sys.argv) > 1:
    bufr_t = sys.argv[1]
    tag = sys.argv[2]
    with open(sys.argv[3], 'r') as fptr:
        param = yaml.safe_load(fptr)
    in_csv_fname = f"{param['paths']['syn_limit_uas_csv']}/{bufr_t}.{tag}.input.csv"
    out_csv_fname = f"{param['paths']['syn_limit_uas_csv']}/{bufr_t}.{tag}.output.csv"
    csv_ref_fname = f"{param['paths'][param['limit_uas']['csv_ref_dir']]}/{bufr_t}.{tag}.fake.prepbufr.csv"
    drop_col = param['limit_uas']['drop_col']
    if drop_col[0] == None:
        drop_col = []
    verbose = param['limit_uas']['verbose']
    limits_param = param['limit_uas']['limits']
else:
    raise NameError('limit_uas_flights.py is NOT configured to run without command line arguments!!')


#---------------------------------------------------------------------------------------------------
# Limit UAS Flights
#---------------------------------------------------------------------------------------------------

if verbose > 1:
    start = dt.datetime.now()
    print("start time =", start)

# Read in input prepBUFR file
bufr_obj = bufr.bufrCSV(in_csv_fname)
bufr_obj_ref = bufr.bufrCSV(csv_ref_fname)
keep_col = bufr_obj.df.columns.values

# Check how many obs we are starting with
if verbose > 0:
    all_typ = np.unique(bufr_obj.df['TYP'])
    nob_before = {}
    print()
    print("initial observation counts...")
    for t in all_typ:
        nob_before[t] = len(bufr_obj.df.loc[bufr_obj.df['TYP'] == t])
        print(f"{t} = {nob_before[t]}")
    print()

# Remove BUFR obs that exceed various limits
for typ in limits_param.keys():
    for lim_type in limits_param[typ]:

        if verbose > 0: print(f"Adding {lim_type} limits to {typ}")
        if verbose > 1: print('  applying limits', dt.datetime.now())

        # Wind speed limit
        if lim_type == 'wind':
            bufr_obj_ref = lp.wspd_limit(bufr_obj_ref, wind_type=typ,
                                         **limits_param[typ][lim_type]['lim_kw'])

        # Icing detection (using RH threshold)
        if lim_type == 'icing_RH':
            bufr_obj_ref = lp.detect_icing_RH(bufr_obj_ref, thermo_type=typ,
                                              **limits_param[typ][lim_type]['lim_kw'])

        # Icing detection (using ql threshold)
        if lim_type == 'icing_LIQMR':
            bufr_obj_ref = lp.detect_icing_LIQMR(bufr_obj_ref, thermo_type=typ,
                                                 **limits_param[typ][lim_type]['lim_kw'])

        # Remove BUFR obs that exceed the limit
        if verbose > 1: print('  removing obs   ', dt.datetime.now())
        bufr_obj.df = lp.remove_obs_after_lim(bufr_obj.df, bufr_obj_ref.df, typ, 
                                              **limits_param[typ][lim_type]['remove_kw'])
        bufr_obj_ref.df = lp.remove_obs_after_lim(bufr_obj_ref.df, bufr_obj_ref.df, typ, 
                                                  **limits_param[typ][lim_type]['remove_kw'])

# Print how many obs were removed
if verbose > 0: 
    print()
    print("final observation counts...")
    for t in all_typ:
        nob = len(bufr_obj.df.loc[bufr_obj.df['TYP'] == t])
        print(f"{t} = {nob} ({100*(nob_before[t] - nob) / nob_before[t]:.3f}% reduction)")
    print()

# Remove intermediate fields and save results
if verbose > 1: print('removing intermediate columns', dt.datetime.now())
for c in bufr_obj.df:
    if c not in keep_col:
        drop_col.append(c)
bufr_obj.df.drop(drop_col, axis=1, inplace=True)
bufr.df_to_csv(bufr_obj.df, out_csv_fname)

# Timing
if verbose > 1:
    print()
    print(dt.datetime.now())
    print(f"Total time for limit_uas_flights.py = {(dt.datetime.now() - start).total_seconds()} s")


"""
End limit_uas_flights.py
"""
