"""
Quick Script To Help Decide if TOB is Tv or T

shawn.s.murdzek@noaa.gov
Date Created: 14 June 2023
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import bufr
import numpy as np
import metpy.calc as mc
from metpy.units import units


#---------------------------------------------------------------------------------------------------
# Input Parameters
#---------------------------------------------------------------------------------------------------

bufr_fname = '/work2/noaa/wrfruc/murdzek/real_obs/obs_rap_csv/202205020000.rap.prepbufr.csv'


#---------------------------------------------------------------------------------------------------
# Examine Whether Td Best Matches TDO When Assuming TOB is T or Tv
#---------------------------------------------------------------------------------------------------

bufr_csv = bufr.bufrCSV(bufr_fname)
bufr_csv.df = bufr_csv.df.loc[bufr_csv.df['QOB'] > 10000]

# First, determine how many TOBs (if any) are flagged as being Tv
print('Number of Tv obs flagged in BUFR file = %d' % np.sum(bufr_csv.df['tvflg'] == 0))

# Compute Td assuming TOB is sensible T
Td_sens = mc.dewpoint_from_specific_humidity(bufr_csv.df['POB'].values * units.hPa,
                                             bufr_csv.df['TOB'].values * units.degC,
                                             bufr_csv.df['QOB'].values * 1e-6).to('degC').magnitude
rmsd_sens = np.sqrt(np.nanmean((Td_sens - bufr_csv.df['TDO'].values)**2))
print('RMSD (assuming TOB = T) = %.3f' % rmsd_sens)

# Compute Td assuming TOB is virtual T
bufr_csv.df['tvflg'] = 0
bufr_csv.df = bufr.compute_Tsens(bufr_csv.df)
Td_virt = mc.dewpoint_from_specific_humidity(bufr_csv.df['POB'].values * units.hPa,
                                             bufr_csv.df['Tsens'].values * units.degC,
                                             bufr_csv.df['QOB'].values * 1e-6).to('degC').magnitude
rmsd_virt = np.sqrt(np.nanmean((Td_virt - bufr_csv.df['TDO'].values)**2))
print('RMSD (assuming TOB = Tv) = %.3f' % rmsd_virt)


"""
End TOB_T_Tv_comparison.py
"""
