"""
Create a Sample Prepbufr CSV

shawn.s.murdzek@noaa.gov
Date Created: 18 October 2022
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import numpy as np

import pyDA_utils.bufr as bufr


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

fname = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202202011200.rap.prepbufr.csv'
save_fname = './202202011200.sample.prepbufr.csv'

lat_lim = [39, 47]
lon_lim = [280, 290]
dhr_lim = [-1, 0]


#---------------------------------------------------------------------------------------------------
# Create Sample PrepBUFR CSV
#---------------------------------------------------------------------------------------------------

bufr_csv = bufr.bufrCSV(fname)
cond = ((bufr_csv.df['XOB'] >= lon_lim[0]) & (bufr_csv.df['XOB'] <= lon_lim[1]) &
        (bufr_csv.df['YOB'] >= lat_lim[0]) & (bufr_csv.df['YOB'] <= lon_lim[1]) &
        (((bufr_csv.df['DHR'] >= dhr_lim[0]) & (bufr_csv.df['DHR'] <= dhr_lim[1])) |
         ((bufr_csv.df['HRDR'] >= dhr_lim[0]) & (bufr_csv.df['HRDR'] <= dhr_lim[1]) & 
          ~np.isnan(bufr_csv.df['HRDR']))))
out_df = bufr_csv.df.loc[cond]

bufr.df_to_csv(out_df, save_fname)


"""
End create_sample_csv.py  
"""
