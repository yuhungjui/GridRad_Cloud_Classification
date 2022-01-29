## ________________________________________________________________________________________________
'''

Convective/Stratiform identification for 3D Reflectivity from derived dBZ of WRF Simulations.

The Convective/Stratiform Masking algorithm is updated for the Lambert-conformal-gridded WRF CONUS data.

Output the Convective/Stratiform (C/S) Mask information to CONUS dBZ data.
 
For [High Resolution WRF Simulations of the Current and Future Climate of North America](https://rda.ucar.edu/datasets/ds612.0/).

How to run:
python wrf_dbz_CSMask_output.py [CTRL3D/PGW3D] [start_date_yyyymmdd] [end_date_yyyymmdd]
 
Hungjui Yu - 20211217

'''
## ________________________________________________________________________________________________

import sys
import time
import datetime as dt
import pytz
from netCDF4 import (Dataset, MFDataset)
import numpy as np
import xarray as xr
import pandas as pd
import wrf

modules_path = '/glade/work/hungjui/Research_Test/WRF_dBZ_Cloud_Classification/WRF_dBZ_Class_CONUS1/Modules'
if ( modules_path not in sys.path ):
    sys.path = [modules_path] + sys.path
    # print(sys.path)
    
import conv_stra_mask as csm

## ________________________________________________________________________________________________
# %%
# **Set input files paths and names:**

def set_input_names(file_date):

    # file_path_1_conus = '/gpfs/fs1/collections/rda/data/ds612.0'
    file_path_1_dbz = '/glade/scratch/hungjui/DATA_WRF_CONUS_1_dBZ_v1.0'
    file_path_2 = '/' + wrf_sim_type # '/CTRL3D'
    file_path_3 = '/{}'.format(file_date.strftime('%Y'))

    file_names = dict( dbz = file_path_1_dbz
                           + file_path_2 
                           + file_path_3 
                           + '/wrf3d_d01_' + wrf_sim_type[0:-2] + '_dbz_{}.nc'.format(file_date.strftime('%Y%m%d'))
                     )
    
    return file_names


## ________________________________________________________________________________________________
# %%
# **Function: Convective/Stratiform separation:**

def CS_separation(refl, lat, lon):

    cs, cc, bkgnd = csm.conv_stra_sep(refl, lat, lon, 4, 'L', 'SHY')

    cs[np.where(refl <= 0.0)] = np.nan
    cs[np.where(np.isnan(refl))] = -1
    
    return cs

## ________________________________________________________________________________________________
# %%
# ### Main Function:
# %%

def main_function(file_date_time):
    
    ## Set file datetime:
    # file_date_time = dt.datetime(2013, 9, 13, 0, 0, 0, tzinfo=pytz.utc)
    # print('\nProcessing: {}'.format(file_date_time.strftime('%Y%m%d')), end=': ')
    
    ## Set input files paths and names:
    file_name_dict = set_input_names(file_date_time)

    ## Get the 3-hourly time list:
    nc_wrf_dbz = Dataset(file_name_dict['dbz'], mode='r')
    wrf_3hour_list = wrf.extract_times(nc_wrf_dbz, timeidx=wrf.ALL_TIMES, meta=False, do_xtime=False)
    nc_wrf_dbz.close()
    
    ## Open dBZ data array and append calculated data:
    ds_wrf_dbz = xr.open_dataset(file_name_dict['dbz'])
    
    ## Set sigma level index:
    interp_vertical_lev = 12 # number in levels.
    
    for hi in range(len(wrf_3hour_list)):
        
        print(str(hi) + ' | ', end=' ')

        ## Get dBZ data:
        da_wrf_dbz = ds_wrf_dbz['dBZ'].isel(Time=hi)
        
        ## Get dBZ data at specified sigma level:
        dbz_sigmalev = da_wrf_dbz[interp_vertical_lev,:,:]
        
        ## Convective/Stratiform Separation:
        ## !!! Make sure the array for the masking is in numpy array format (speed issue) !!!
        CS_mask_single = CS_separation( dbz_sigmalev.data
                                      , dbz_sigmalev.XLAT.data
                                      , dbz_sigmalev.XLONG.data
                                      )
        
        ## Stack the CS mask according to hours:
        if ( hi == 0 ):
            # CS_mask = CS_mask_single
            CS_mask = np.expand_dims(CS_mask_single, axis=0)
        else:
            # CS_mask = xr.concat([CS_mask, CS_mask_single], dim='TimeDim')
            CS_mask = np.append(CS_mask, np.expand_dims(CS_mask_single, axis=0), axis=0)

        
    ## Add CS mask to dBZ dataset:
    # ds_wrf_dbz['CS_mask'] = (['Time', 'south_north', 'west_east'], CS_mask)
    
    ds_wrf_dbz.close()
    
    ## Save & Update to NetCDF file:
    nc_wrf_dbz = Dataset(file_name_dict['dbz'], mode='r+')
    
    nc_wrf_dbz['CS_mask'][:] = CS_mask
    nc_wrf_dbz['CS_mask'].description = 'Masked Convective (1-5) and Stratiform (0) echos at sigma level: 12'

    nc_wrf_dbz.close()
    
    return ds_wrf_dbz
    
## ________________________________________________________________________________________________
# %% 
# ### Main Program:
# %%

start = time.time()

## WRF Model Simulation Category:
# wrf_sim_type = 'CTRL3D'
# wrf_sim_type = 'PGW3D'
wrf_sim_type = sys.argv[1]

## Loop through a period:
# target_date_range = pd.date_range(start='2013-9-13', end='2013-9-15', tz=pytz.utc)
target_date_range = pd.date_range(start=sys.argv[2], end=sys.argv[3], tz=pytz.utc)

for dayi in target_date_range:
        
    ## Derive Convective/Stratiform mask and Update the NetCDF file:
    main_function(dayi)

    
end = time.time()

    
run_time_txt = open('./run_time.log','a')
run_time_txt.write(sys.argv[1] + '\n')
run_time_txt.write(sys.argv[2] + ' - ' + sys.argv[3] + '\n')
run_time_txt.write("RUNTIME：%f SEC \n" % (end - start))
run_time_txt.write("RUNTIME：%f MIN \n" % ((end - start)/60))
run_time_txt.write("RUNTIME：%f HOUR \n" % ((end - start)/3600))


## ________________________________________________________________________________________________
## ________________________________________________________________________________________________

